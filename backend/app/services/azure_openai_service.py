"""
Azure OpenAI Service for conversational AI and intent classification.

This service uses Azure OpenAI's GPT models to classify user intents,
handle code-mixed language (Hindi-English-Chhattisgarhi), and provide
intelligent grievance extraction with conversational understanding.
"""

import logging
import os
from typing import Dict, Optional, Any, List
from openai import AzureOpenAI, APIError, APIConnectionError, RateLimitError
import json
from jsonschema import validate as js_validate, ValidationError as JsonSchemaValidationError

from app.config import settings
from app.prompts.triage_prompts import get_intent_classification_prompt, ISSUE_TAXONOMY
from app.utils.input_sanitizer import sanitize_user_input, detect_suspicious_patterns

# Gate RAG import behind environment variable (requires heavy ML dependencies)
# On Azure B1 tier (1.75GB RAM), ML libraries (FAISS, sentence-transformers, PyTorch) cause OOM
ENABLE_VECTOR_SEARCH = os.getenv("ENABLE_VECTOR_SEARCH", "0") == "1"

if ENABLE_VECTOR_SEARCH:
    from app.services.rag.rag_service import get_rag_service
else:
    # Stub function when RAG is disabled - returns None to gracefully skip RAG context
    def get_rag_service():
        return None

logger = logging.getLogger(__name__)

# JSON Schema for conversation response validation
CONVO_SCHEMA = {
    "type": "object",
    "properties": {
        "response_hi": {"type": "string", "minLength": 1},
        "response_en": {"type": "string", "minLength": 1},
        "empathy_used": {"type": "boolean"},
        "next_field_asked": {"type": ["string", "null"]}
    },
    "required": ["response_hi", "response_en"],
    "additionalProperties": True
}


class AzureOpenAIServiceError(Exception):
    """Base exception for Azure OpenAI service errors"""
    pass


class AzureOpenAIAPIError(AzureOpenAIServiceError):
    """Error when Azure OpenAI API call fails"""
    pass


class AzureOpenAIParseError(AzureOpenAIServiceError):
    """Error when parsing Azure OpenAI response"""
    pass


class AzureOpenAIService:
    """
    Service for interacting with Azure OpenAI API.

    Handles:
    - Intent classification (grievance/community/personal)
    - Conversational AI understanding
    - Confidence scoring
    - Code-mixed language understanding (Hindi-English-Chhattisgarhi)
    - Error handling and retries
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        """
        Initialize Azure OpenAI service.

        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            deployment_name: Model deployment name
            api_version: API version

        Raises:
            AzureOpenAIServiceError: If service cannot be initialized
        """
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY  # Fixed: was AZURE_OPENAI_KEY
        self.deployment_name = deployment_name or settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION

        if not all([self.endpoint, self.api_key, self.deployment_name]):
            raise AzureOpenAIServiceError(
                "Azure OpenAI not fully configured. Please set AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME in environment variables."
            )

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            timeout=90.0  # 90 second timeout for AI conversations
        )
        self.max_tokens = 2048
        logger.info(f"AzureOpenAIService initialized with deployment: {self.deployment_name}")

    def classify_intent(
        self,
        transcript: str,
        location_hint: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify the intent of a conversation transcript using Azure OpenAI.

        Analyzes code-mixed (Hindi-English-Chhattisgarhi) text to determine
        whether it's a grievance, community action, or personal note.
        Uses conversational AI to deeply understand the user's intent.

        Args:
            transcript: The conversation transcript to classify
            location_hint: Optional location context (e.g., "Raipur, Chhattisgarh")
            user_context: Optional user context (history, preferences)

        Returns:
            Dict containing:
                - intent: str - One of "grievance", "community", "personal", "uncertain"
                - confidence: float - Confidence score (0.0 to 1.0)
                - confidence_level: str - "high" (≥0.7), "medium" (0.5-0.7), "low" (<0.5)
                - reasoning: str - Explanation for the classification
                - suggested_issue_type: str - For grievances, matched taxonomy category
                - metadata: dict - Additional classification details

        Raises:
            AzureOpenAIAPIError: If API call fails
            AzureOpenAIParseError: If response parsing fails

        Example:
            >>> service = AzureOpenAIService()
            >>> result = service.classify_intent(
            ...     "पानी की सप्लाई नहीं आ रही है 2 हफ्ते से",
            ...     location_hint="Raipur"
            ... )
            >>> print(result["intent"])  # "grievance"
            >>> print(result["confidence"])  # 0.95
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        logger.info(f"🤖 Classifying intent with Azure OpenAI (length: {len(transcript)})")

        try:
            # Generate system prompt for conversational AI
            system_prompt = self._get_system_prompt()

            # Generate user prompt with context
            user_prompt = get_intent_classification_prompt(
                transcript=transcript,
                location_hint=location_hint,
                user_context=user_context
            )

            # Call Azure OpenAI API
            logger.debug(f"Calling Azure OpenAI: {self.deployment_name}")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for more consistent classification
                response_format={"type": "json_object"}  # Force JSON output
            )

            # Extract response text
            response_text = response.choices[0].message.content
            logger.debug(f"Azure OpenAI response: {response_text[:200]}...")

            # Parse JSON response
            result = self._parse_classification_response(response_text)

            # Add metadata
            result["metadata"] = {
                "model": self.deployment_name,
                "tokens_used": response.usage.total_tokens,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "location_hint": location_hint,
                "transcript_length": len(transcript),
                "service": "azure_openai"
            }

            logger.info(
                f"✅ Classification complete: intent={result['intent']}, "
                f"confidence={result['confidence']:.2f}"
            )

            return result

        except APIConnectionError as e:
            logger.error(f"❌ Azure OpenAI connection error: {e}")
            raise AzureOpenAIAPIError(f"Failed to connect to Azure OpenAI: {str(e)}")

        except APIError as e:
            logger.error(f"❌ Azure OpenAI API error: {e}")
            raise AzureOpenAIAPIError(f"Azure OpenAI API error: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse response as JSON: {e}")
            raise AzureOpenAIParseError(f"Invalid JSON response: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Unexpected error in classify_intent: {e}", exc_info=True)
            raise AzureOpenAIServiceError(f"Classification failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for conversational AI classification.

        Returns:
            System prompt defining the AI assistant's role
        """
        return """You are an intelligent assistant for Boloo, a civic engagement platform in India.
Your role is to analyze user messages and determine their intent with high accuracy.

You understand code-mixed language (Hindi, English, and Chhattisgarhi) and can extract
meaningful civic complaints from natural conversations.

Your task is to classify messages into THREE categories:

1. **GRIEVANCE** - Civic complaints requiring government action
   - Infrastructure issues (roads, water, electricity, sanitation)
   - Public service failures
   - Safety and security concerns
   - Environmental issues
   - Specific problems with clear location and impact

2. **COMMUNITY** - Community organizing or collective action
   - Neighborhood initiatives
   - Group activities
   - Community announcements
   - Collective petitions or demands

3. **PERSONAL** - Personal notes or reminders
   - Shopping lists
   - Personal to-dos
   - Private reminders
   - Non-civic messages

For GRIEVANCES, also identify the specific issue type from the taxonomy.

Respond with JSON ONLY in this exact format:
{
  "intent": "grievance|community|personal|uncertain",
  "confidence": 0.0-1.0,
  "reasoning": "Clear explanation in English",
  "suggested_issue_type": "category_from_taxonomy (only for grievances)"
}

Be conversational and intelligent - understand context, implied meaning, and user frustration."""

    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate Azure OpenAI's classification response.

        Args:
            response_text: Raw text response from Azure OpenAI

        Returns:
            Validated classification result dictionary

        Raises:
            AzureOpenAIParseError: If response is invalid
        """
        try:
            result = json.loads(response_text)

            # Validate required fields
            required_fields = ["intent", "confidence", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise AzureOpenAIParseError(f"Missing required field: {field}")

            # Validate intent value
            valid_intents = {"grievance", "community", "personal", "uncertain"}
            if result["intent"] not in valid_intents:
                logger.warning(
                    f"Invalid intent '{result['intent']}', defaulting to 'uncertain'"
                )
                result["intent"] = "uncertain"
                result["confidence"] = min(result["confidence"], 0.5)

            # Validate confidence score
            confidence = float(result["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise AzureOpenAIParseError(
                    f"Confidence must be between 0.0 and 1.0, got {confidence}"
                )
            result["confidence"] = confidence

            # Add confidence level
            if confidence >= 0.7:
                result["confidence_level"] = "high"
            elif confidence >= 0.5:
                result["confidence_level"] = "medium"
            else:
                result["confidence_level"] = "low"

            # Validate suggested_issue_type for grievances
            if result["intent"] == "grievance":
                suggested_type = result.get("suggested_issue_type")
                if suggested_type and suggested_type not in ISSUE_TAXONOMY:
                    logger.warning(
                        f"Issue type '{suggested_type}' not in taxonomy, "
                        f"defaulting to 'other'"
                    )
                    result["suggested_issue_type"] = "other"
                elif not suggested_type:
                    result["suggested_issue_type"] = "other"

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nResponse: {response_text}")
            raise AzureOpenAIParseError(f"Invalid JSON in response: {str(e)}")

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Response validation failed: {e}")
            raise AzureOpenAIParseError(f"Invalid response structure: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check if Azure OpenAI API is accessible and configured correctly.

        Returns:
            Dict with health status and details
        """
        try:
            # Make a minimal API call to verify connectivity
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )

            return {
                "status": "healthy",
                "endpoint": self.endpoint,
                "deployment": self.deployment_name,
                "api_version": self.api_version,
                "connection": "ok"
            }

        except Exception as e:
            logger.error(f"Azure OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "endpoint": self.endpoint,
                "deployment": self.deployment_name,
                "connection": "failed",
                "error": str(e)
            }

    def generate_conversation_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        missing_fields: List[Dict[str, Any]],
        collected_data: Dict[str, Any],
        is_complete: bool = False,
        questions_already_asked: Optional[List[str]] = None,  # BUG FIX #1: Track asked questions
        user_sentiment: Optional[Dict[str, Any]] = None,  # BUG FIX #4: User sentiment
        can_submit_now: bool = False,  # BUG FIX #5: Can submit flag
        skip_sanitization: bool = False,  # SECURITY: Allow bypassing for trusted input
        allowed_field_to_ask: Optional[str] = None  # HARD GATE: Pre-determined field to ask
    ) -> Dict[str, Any]:
        """
        Generate natural conversational response for grievance collection.

        This replaces hardcoded template responses with real AI-powered conversations.
        The AI acknowledges what the user said and naturally asks for missing information.

        Args:
            user_message: User's latest message
            conversation_history: Previous turns for context
            missing_fields: Fields still needed
            collected_data: Data already collected
            is_complete: Whether all required fields are collected

        Returns:
            Dict containing:
                - response_hi: Natural response in Hindi
                - response_en: Natural response in English
                - empathy_used: Whether empathetic acknowledgment was included
                - next_field_asked: Field name asked for (if any)

        Example:
            >>> service.generate_conversation_response(
            ...     user_message="हमारे गांव में पानी नहीं आ रहा",
            ...     conversation_history=[],
            ...     missing_fields=[{"field": "location", "prompt_hi": "कहाँ की बात कर रहे हो?"}],
            ...     collected_data={},
            ...     is_complete=False
            ... )
            {
                "response_hi": "समझ रहा हूँ, पानी की समस्या बहुत गंभीर है। आप किस गांव या मोहल्ले की बात कर रहे हैं?",
                "response_en": "I understand, water issues are very serious. Which village or area are you talking about?",
                "empathy_used": True,
                "next_field_asked": "location"
            }
        """
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty")

        # SECURITY FIX: Sanitize user input to prevent prompt injection
        if not skip_sanitization:
            try:
                sanitized_message = sanitize_user_input(
                    user_message,
                    max_length=5000,  # Reasonable limit for chat messages
                    strip_html=True,
                    log_suspicious=True
                )

                # Log if suspicious patterns detected
                if detect_suspicious_patterns(user_message):
                    logger.warning(
                        f"[SECURITY] Suspicious pattern in user message (non-blocking). "
                        f"Message: '{user_message[:100]}...'"
                    )

                # Use sanitized message for AI processing
                user_message = sanitized_message

            except ValueError as e:
                # Prompt injection detected - reject with user-friendly error
                logger.error(f"[SECURITY] Prompt injection blocked: {e}")
                raise AzureOpenAIServiceError(
                    "Your message contains patterns that look like system commands. "
                    "Please rephrase naturally. "
                    "(आपके संदेश में सिस्टम कमांड जैसे शब्द हैं। कृपया साधारण भाषा में लिखें।)"
                )

        logger.info(f"🤖 Generating conversation response with Azure OpenAI (is_complete: {is_complete})")

        try:
            # Build conversation context from history - INCLUDE ALL TURNS to avoid repeated questions
            conversation_context = "\n".join([
                f"User: {turn['user']}\nAI: {turn['ai']}"
                for turn in conversation_history  # ALL turns, not just last 3
            ]) if conversation_history else "यह बातचीत का पहला मोड़ है।"

            # Build collected data summary
            collected_summary = ", ".join([
                f"{field}: {value}"
                for field, value in collected_data.items()
                if value and value != "null"
            ]) if collected_data else "कोई जानकारी अभी तक एकत्र नहीं की गई"

            # BUG FIX #1: Build list of already-asked questions to avoid repeats
            questions_asked_info = ""
            if questions_already_asked:
                questions_asked_info = f"\n\n🚫 ALREADY ASKED ABOUT THESE FIELDS (DO NOT ASK AGAIN):\n{', '.join(questions_already_asked)}\n⚠️ CRITICAL: You have ALREADY asked about these fields. DO NOT repeat these questions!\n"

            # BUG FIX #4: Build user sentiment info
            sentiment_info = ""
            if user_sentiment and user_sentiment.get("type") != "neutral":
                sentiment_info = f"\n\n😤 USER SENTIMENT: {user_sentiment['type'].upper()}\n"
                if user_sentiment['type'] == 'frustration':
                    sentiment_info += "⚠️ User is FRUSTRATED! They said something like 'मज़ाक कर रहे हैं', 'phir se same question'.\n"
                    sentiment_info += "DO NOT ask more questions. Acknowledge their frustration and offer to submit.\n"
                elif user_sentiment['type'] == 'proceed':
                    sentiment_info += "✅ User wants to PROCEED! They said 'कर दीजिए', 'theek hai', 'submit kar do'.\n"
                    sentiment_info += "DO NOT ask more questions. Tell them they can submit now.\n"

            # BUG FIX #5: Build can_submit flag info
            submit_flag_info = ""
            if can_submit_now:
                submit_flag_info = "\n\n✅ USER CAN SUBMIT NOW!\nMinimum fields (location + issue_description) are present.\nDO NOT ask more questions unless user explicitly wants to add more details.\nTell them they can submit now!\n"

            # RAG INTEGRATION: Get relevant historical context for the problem
            rag_context = ""
            try:
                # Extract problem description from collected data or user message
                problem_description = (
                    collected_data.get('issue_description', '') or
                    user_message
                )

                # Only get RAG context if we have a meaningful problem description
                if problem_description and len(problem_description.strip()) > 10:
                    rag_service = get_rag_service()

                    # Check if RAG is enabled (returns None when ENABLE_VECTOR_SEARCH=0)
                    if rag_service is not None:
                        rag_context = rag_service.build_rag_prompt_context(
                            problem_description=problem_description,
                            language="hi"
                        )

                        if rag_context:
                            logger.info(f"[RAG] Retrieved historical context for problem: {problem_description[:50]}...")
                        else:
                            logger.debug("[RAG] No relevant historical cases found")
                    else:
                        logger.debug("[RAG] Vector search disabled (ENABLE_VECTOR_SEARCH=0)")

            except Exception as e:
                # Don't fail the conversation if RAG fails
                logger.warning(f"[RAG] Failed to retrieve context: {e}")
                rag_context = ""

            # HARD GATE: Build field restriction for AI
            gate_restriction = ""
            if allowed_field_to_ask:
                gate_restriction = f"""
🚨 HARD GATE RESTRICTION:
You may ONLY ask about this field: **{allowed_field_to_ask}**
DO NOT ask about any other field, even if it seems missing.
If user doesn't provide {allowed_field_to_ask}, acknowledge and move on.
"""

            # BUG FIX #6: Remove AI self-doubt by making instructions clearer
            system_prompt = f"""आप एक सहानुभूतिपूर्ण AI सहायक हैं जो नागरिकों की शिकायतें एकत्र करते हैं।
{gate_restriction}

🎯 OPTION B - NEW APPROACH: Extract First, Ask Rarely
The user often provides ALL information in their FIRST message. Your job is to:
1. EXTRACT all information from their narrative (don't ask what they already told you!)
2. Show empathy and acknowledge their problem
3. If they provided location + problem description → Tell them they can SUBMIT NOW
4. Only ask questions if TRULY necessary for clarity

आपका कार्य:
1. उपयोगकर्ता के संदेश को ध्यान से सुनें और सभी जानकारी निकालें (extract)
2. सहानुभूति दिखाएं और उनकी समस्या को स्वीकार करें
3. अगर location + issue_description मिल गया → उन्हें बताएं कि वे अभी रिपोर्ट सबमिट कर सकते हैं
4. केवल तभी प्रश्न पूछें जब वाकई जरूरी हो (उन्होंने पहले से बता दिया हो तो मत पूछें!)
{rag_context}

🚨 बेहद महत्वपूर्ण - EXTRACTION > ASKING:
- User's narrative contains rich information - EXTRACT it, don't ignore it!
- If user said "मेरे गांव नीलकंठपुर में बिजली नहीं आती" → You now have BOTH location AND problem!
- Do NOT ask "कहाँ की समस्या है?" when they already told you "नीलकंठपुर में"!
- Do NOT ask "क्या समस्या है?" when they already told you "बिजली नहीं आती"!
- If location + issue_description present → USER CAN SUBMIT NOW (tell them!){questions_asked_info}{sentiment_info}{submit_flag_info}

महत्वपूर्ण नियम:
- सहानुभूतिपूर्ण लहजा रखें (empathetic tone)
- रोबोट की तरह नहीं, दोस्त की तरह बात करें
- जो उन्होंने बताया उसे acknowledge करें
- छोटे, सरल वाक्य उपयोग करें
- दोनों हिंदी और अंग्रेजी में जवाब दें
- NEVER question yourself or say things like "आपने तो नाम भी नहीं पूछा?" - be confident!

JSON में उत्तर दें:
{{
  "response_hi": "सहानुभूतिपूर्ण acknowledgment + (या तो submit option या जरूरी clarification)",
  "response_en": "Empathetic acknowledgment + (either submit option or necessary clarification)",
  "empathy_used": true/false,
  "can_submit_now": true/false,
  "next_field_asked": "field_name या null"
}}"""

            # Build user prompt with context - OPTION B: EXTRACTION-FIRST
            if is_complete:
                user_prompt = f"""उपयोगकर्ता ने कहा: "{user_message}"

✅ सभी आवश्यक जानकारी एकत्र हो गई है। उपयोगकर्ता को बताएं कि वे अभी सबमिट कर सकते हैं।

एकत्रित जानकारी: {collected_summary}

कृपया एक स्वाभाविक पुष्टि संदेश लिखें जो बताता है कि वे अभी रिपोर्ट सबमिट कर सकते हैं।"""
            else:
                # Check if minimum fields present for early submission
                has_location = 'location' in collected_data and collected_data['location']
                has_issue = 'issue_description' in collected_data and collected_data['issue_description']
                can_submit = has_location and has_issue

                # Build explicit list of collected fields
                collected_fields_list = list(collected_data.keys()) if collected_data else []
                collected_fields_info = f"Already collected: {', '.join(collected_fields_list)}" if collected_fields_list else "No fields collected yet"

                if can_submit:
                    # User has minimum fields - offer submit option
                    user_prompt = f"""बातचीत का संदर्भ:
{conversation_context}

उपयोगकर्ता का नवीनतम संदेश: "{user_message}"

✅ MINIMUM FIELDS PRESENT - User can submit NOW!
एकत्रित जानकारी: {collected_summary}
{collected_fields_info}

🎯 IMPORTANT: The user has provided BOTH location and problem description!
They can SUBMIT their report right now if they want.

कृपया एक सहानुभूतिपूर्ण प्रतिक्रिया लिखें जो:
1. उनकी समस्या को acknowledge करती है (show empathy)
2. जो information उन्होंने दी उसे briefly summarize करती है
3. उन्हें बताती है कि वे अभी रिपोर्ट सबमिट कर सकते हैं
4. OPTIONAL: पूछती है कि क्या वे और जानकारी जोड़ना चाहते हैं (जैसे नाम, फोटो आदि)

Example response:
"धन्यवाद! मैं समझ गया कि {{location}} में {{problem}} की समस्या है।
आप चाहें तो अभी यह रिपोर्ट सबमिट कर सकते हैं, या फिर आप अपना नाम और फोटो भी जोड़ सकते हैं।"

महत्वपूर्ण: Natural, friendly tone - NOT robotic!"""
                else:
                    # Still need minimum fields - but extract first, don't just ask
                    missing_critical = []
                    if not has_location:
                        missing_critical.append("location")
                    if not has_issue:
                        missing_critical.append("issue_description")

                    user_prompt = f"""बातचीत का संदर्भ:
{conversation_context}

उपयोगकर्ता का नवीनतम संदेश: "{user_message}"

पहले से एकत्रित जानकारी: {collected_summary}
{collected_fields_info}

⚠️ Still need: {', '.join(missing_critical)} for submission

🎯 IMPORTANT: First try to EXTRACT from their message!
- Check if their message contains location information (village/ward/city names)
- Check if their message describes the problem
- ONLY ask questions if you truly cannot extract from what they said

कृपया एक सहानुभूतिपूर्ण प्रतिक्रिया लिखें जो:
1. उनकी समस्या को acknowledge करती है
2. जो information आप उनके message से निकाल सकते हैं उसे acknowledge करती है
3. अगर ज़रूरी हो तो सिर्फ़ missing critical field के बारे में पूछती है (natural way में)

महत्वपूर्ण: Extract first, ask rarely! Natural conversation, not interrogation!"""

            # Call Azure OpenAI API with timeout protection
            logger.debug(f"Calling Azure OpenAI for conversation response")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=settings.AZURE_OPENAI_TEMPERATURE,  # Use configured temperature (0.3)
                response_format={"type": "json_object"},  # Force JSON output
                timeout=30.0  # 30 second timeout to prevent hung requests
            )

            # Extract and parse response
            response_text = response.choices[0].message.content
            logger.debug(f"Azure OpenAI conversation response: {response_text[:200]}...")

            result = json.loads(response_text)

            # HARD GATE VALIDATION: Ensure AI didn't sneak in a different field
            if allowed_field_to_ask and result.get("next_field_asked"):
                if result["next_field_asked"] != allowed_field_to_ask:
                    logger.warning(
                        f"[HARD GATE] AI tried to ask about '{result['next_field_asked']}' "
                        f"but was only allowed to ask '{allowed_field_to_ask}'. Blocking."
                    )
                    # Block the sneaky question
                    result["next_field_asked"] = None

            # Validate response against JSON schema (fail-fast validation)
            try:
                js_validate(result, CONVO_SCHEMA)
            except JsonSchemaValidationError as e:
                logger.error(f"Response failed schema validation: {e}")
                raise AzureOpenAIParseError(f"Response schema validation failed: {e.message}")

            # Add metadata
            result["metadata"] = {
                "model": self.deployment_name,
                "tokens_used": response.usage.total_tokens,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "service": "azure_openai",
                "is_complete": is_complete
            }

            logger.info(
                f"✅ Conversation response generated: {result['response_hi'][:50]}..."
            )

            return result

        except RateLimitError as e:
            logger.warning(f"⚠️  Azure OpenAI rate limit hit: {e}")
            raise AzureOpenAIAPIError(
                "The AI service is currently experiencing high demand. Please try again in a few moments. "
                "(AI सेवा अभी व्यस्त है। कृपया कुछ देर बाद फिर से प्रयास करें।)"
            )

        except APIConnectionError as e:
            logger.error(f"❌ Azure OpenAI connection error: {e}")
            raise AzureOpenAIAPIError(
                "Unable to connect to AI service. Please check your internet connection. "
                "(AI सेवा से कनेक्ट नहीं हो पा रहा। कृपया अपना इंटरनेट कनेक्शन जांचें।)"
            )

        except APIError as e:
            logger.error(f"❌ Azure OpenAI API error: {e}")
            raise AzureOpenAIAPIError(f"Azure OpenAI API error: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse response as JSON: {e}")
            raise AzureOpenAIParseError(f"Invalid JSON response: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Unexpected error in generate_conversation_response: {e}", exc_info=True)
            raise AzureOpenAIServiceError(f"Conversation generation failed: {str(e)}")


# Global instance (lazy initialization)
_azure_openai_service: Optional[AzureOpenAIService] = None


def get_azure_openai_service() -> AzureOpenAIService:
    """
    Get or create global AzureOpenAIService instance.

    Returns:
        AzureOpenAIService instance

    Raises:
        AzureOpenAIServiceError: If service cannot be initialized
    """
    global _azure_openai_service

    if _azure_openai_service is None:
        _azure_openai_service = AzureOpenAIService()

    return _azure_openai_service
