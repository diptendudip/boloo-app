"""
AI Coach Completeness Analyzer using Azure OpenAI.

This service analyzes voice transcripts to determine completeness of grievance reports,
extracts fields, identifies missing information, and generates follow-up questions in Hindi.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from openai import AzureOpenAI, APIError, APIConnectionError, APITimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


# HYBRID FIX: Deterministic location parser (backup for when Azure fails)
_LOC_MARKERS = {
    "panchayat": ["पंचायत", "panchayat", "पञ्चायत"],
    "block": ["ब्लॉक", "ब्लाक", "block", "विकासखंड", "विकास खंड"],
    "district": ["जिला", "जिल्हा", "district", "ज़िला"],
    "village": ["गांव", "गाँव", "village", "ग्राम"],
    "ward": ["वार्ड", "ward"],
    "tehsil": ["तहसील", "tehsil"],
    "area": ["मोहल्ला", "mohalla", "क्षेत्र", "area", "इलाका"],
}

_VAGUE_LOCATION_TOKENS_HI = ["मेरे गाँव", "हमारे गाँव", "हमारे मोहल्ले", "यहाँ", "यहां", "इस गांव", "हमारा इलाका"]
_VAGUE_LOCATION_TOKENS_EN = ["our village", "my village", "here", "this area", "our area"]


def _looks_vague_location(text: str) -> bool:
    """Check if location description is vague (e.g., 'यहाँ', 'मेरे गाँव')."""
    if not text:
        return False
    t = text.lower().strip()
    return any(tok in t for tok in _VAGUE_LOCATION_TOKENS_HI + _VAGUE_LOCATION_TOKENS_EN)


def deterministic_location_extract(raw: str) -> dict:
    """
    Extract location using deterministic regex patterns.

    This is a BACKUP parser for when Azure OpenAI fails to extract location.
    Uses regex to find पंचायत, ब्लॉक, जिला, गांव etc.

    Args:
        raw: Raw text (user message or transcript)

    Returns:
        {
            "village": "...",
            "panchayat": "...",
            "block": "...",
            "district": "...",
            "ward": "...",
            "tehsil": "...",
            "joined": "full location string",
            "precision": "specific" or "vague"
        }

    Example:
        >>> deterministic_location_extract("डोंगरीगुड़ा पंचायत, अलवा ब्लाक, जिला बस्तर में")
        {
            "village": "डोंगरीगुड़ा",
            "panchayat": "डोंगरीगुड़ा",
            "block": "अलवा",
            "district": "बस्तर",
            "joined": "डोंगरीगुड़ा पंचायत, अलवा ब्लाक, जिला बस्तर",
            "precision": "specific"
        }
    """
    if not raw:
        return {}

    # Check if vague
    if _looks_vague_location(raw):
        return {"precision": "vague", "raw": raw}

    result = {}

    # Extract each component using regex
    for component_type, markers in _LOC_MARKERS.items():
        for marker in markers:
            # Pattern: word(s) before marker
            # Example: "डोंगरीगुड़ा पंचायत" → extract "डोंगरीगुड़ा"
            pattern = r'([^\s,।]+(?:\s+[^\s,।]+)?)\s+' + re.escape(marker)
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                result[component_type] = match.group(1).strip()
                logger.debug(f"[DeterministicParser] Extracted {component_type}: {result[component_type]}")
                break

    # Try to extract district after "जिला" keyword
    district_patterns = [
        r'जिला\s+([^\s,।]+)',
        r'district\s+([^\s,।]+)',
    ]
    for pattern in district_patterns:
        match = re.search(pattern, raw, re.IGNORECASE)
        if match and 'district' not in result:
            result['district'] = match.group(1).strip()
            logger.debug(f"[DeterministicParser] Extracted district: {result['district']}")

    # Build joined location string
    parts = []
    if 'village' in result:
        parts.append(result['village'])
    if 'panchayat' in result and result.get('panchayat') != result.get('village'):
        parts.append(f"पंचायत {result['panchayat']}")
    if 'block' in result:
        parts.append(f"ब्लाक {result['block']}")
    if 'district' in result:
        parts.append(f"जिला {result['district']}")
    if 'ward' in result:
        parts.append(f"वार्ड {result['ward']}")

    if parts:
        result['joined'] = ", ".join(parts)
        result['precision'] = 'specific'
        logger.info(f"[DeterministicParser] ✅ Extracted location: {result['joined']}")
    else:
        result['precision'] = 'unknown'

    result['raw'] = raw
    return result


# UNIVERSAL REQUIRED FIELDS - Apply to ALL grievance types
# These are the MINIMUM needed for government to act
UNIVERSAL_REQUIRED_FIELDS = {
    "issue_description": {
        "name_hi": "समस्या का विवरण",
        "name_en": "Issue Description",
        "importance": "critical",
        "prompt_hi": "कृपया अपनी समस्या के बारे में बताएं।",
        "prompt_en": "Please describe your issue."
    },
    "location": {
        "name_hi": "समस्या का स्थान",
        "name_en": "Issue Location",
        "importance": "critical",
        "prompt_hi": "यह समस्या कहाँ हो रही है? गाँव/क्षेत्र का नाम बताएं।",
        "prompt_en": "Where is this issue occurring? Village/area name."
    }
}

# CONTEXT-SPECIFIC FIELDS - Dynamically selected based on problem type
# These are OPTIONAL but contextually relevant
CONTEXTUAL_FIELDS = {
    # Water/Electricity/Basic Services
    "service_duration": {
        "name_hi": "कब से नहीं मिल रहा",
        "name_en": "How long without service",
        "applies_to": ["water", "electricity", "drainage", "sewage"],
        "prompt_hi": "यह समस्या कब से हो रही है? (कितने दिन/महीने)",
        "prompt_en": "Since when? (days/months)"
    },
    "service_frequency": {
        "name_hi": "कितने घंटे मिलता है",
        "name_en": "Hours of service",
        "applies_to": ["water", "electricity"],
        "prompt_hi": "दिन में कितने घंटे पानी/बिजली मिलती है?",
        "prompt_en": "How many hours per day?"
    },

    # Infrastructure/Roads
    "road_landmark": {
        "name_hi": "कौन सी सड़क/लैंडमार्क",
        "name_en": "Which road/landmark",
        "applies_to": ["road", "bridge", "infrastructure"],
        "prompt_hi": "कौन सी सड़क या नजदीक का लैंडमार्क बताएं।",
        "prompt_en": "Which road or nearby landmark?"
    },
    "damage_severity": {
        "name_hi": "कितनी गंभीर है",
        "name_en": "Severity of damage",
        "applies_to": ["road", "bridge", "building"],
        "prompt_hi": "क्या यह बहुत खराब स्थिति में है?",
        "prompt_en": "How severe is the damage?"
    },

    # Health/Medical
    "health_affected_count": {
        "name_hi": "कितने लोग बीमार",
        "name_en": "Number of people sick",
        "applies_to": ["health", "medical", "disease"],
        "prompt_hi": "कितने लोग बीमार हैं?",
        "prompt_en": "How many people are sick?"
    },
    "health_symptoms": {
        "name_hi": "लक्षण क्या हैं",
        "name_en": "Symptoms",
        "applies_to": ["health", "medical", "disease"],
        "prompt_hi": "क्या लक्षण हैं?",
        "prompt_en": "What are the symptoms?"
    },

    # Education/School
    "school_name": {
        "name_hi": "स्कूल का नाम",
        "name_en": "School name",
        "applies_to": ["education", "school"],
        "prompt_hi": "कौन से स्कूल की बात हो रही है?",
        "prompt_en": "Which school?"
    },
    "students_affected": {
        "name_hi": "कितने बच्चे प्रभावित",
        "name_en": "Students affected",
        "applies_to": ["education", "school"],
        "prompt_hi": "कितने बच्चे प्रभावित हैं?",
        "prompt_en": "How many students affected?"
    },

    # Corruption/Bribery
    "office_name": {
        "name_hi": "कौन सा ऑफिस/विभाग",
        "name_en": "Which office/department",
        "applies_to": ["corruption", "bribery", "harassment"],
        "prompt_hi": "यह किस ऑफिस या विभाग में हुआ?",
        "prompt_en": "Which office or department?"
    },
    "bribe_amount": {
        "name_hi": "कितनी रकम मांगी",
        "name_en": "Amount demanded",
        "applies_to": ["corruption", "bribery"],
        "prompt_hi": "कितनी रकम मांगी गई?",
        "prompt_en": "How much was demanded?"
    },

    # General - Apply to all
    "affected_scope": {
        "name_hi": "कितने लोग प्रभावित",
        "name_en": "Impact scope",
        "applies_to": ["all"],
        "prompt_hi": "क्या यह समस्या सिर्फ आपको है या और लोगों को भी?",
        "prompt_en": "Is this affecting just you or others too?"
    },
    "urgency_level": {
        "name_hi": "कितनी जरूरी है",
        "name_en": "Urgency",
        "applies_to": ["all"],
        "prompt_hi": "क्या यह बहुत जरूरी है?",
        "prompt_en": "Is this urgent?"
    }
}

# Fallback to universal fields for backward compatibility
REQUIRED_FIELDS = UNIVERSAL_REQUIRED_FIELDS


class CompletenessAnalyzerError(Exception):
    """Base exception for completeness analyzer errors"""
    pass


class CompletenessAnalyzer:
    """
    Analyzes transcript completeness for AI Coach training mode.

    Uses Azure OpenAI GPT-4o-mini to:
    - Extract structured fields from voice transcripts
    - Identify missing critical information
    - Calculate completeness score (0-100%)
    - Generate contextual follow-up questions in Hindi
    """

    def __init__(self):
        """Initialize completeness analyzer with Azure OpenAI."""
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            raise CompletenessAnalyzerError(
                "Azure OpenAI not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY."
            )

        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            timeout=90.0  # 90 second timeout for completeness analysis
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4o-mini"
        logger.info(f"CompletenessAnalyzer initialized with deployment: {self.deployment}")

    def _detect_problem_type(self, issue_description: str) -> List[str]:
        """
        Detect problem categories from issue description using AI.

        Args:
            issue_description: Description of the problem

        Returns:
            List of problem categories (e.g., ["water", "all"])
        """
        if not issue_description or not issue_description.strip():
            return ["all"]

        # Build prompt for problem type detection
        prompt = f"""Analyze this grievance and identify the problem categories.

Issue: "{issue_description}"

Available categories:
- water: Water supply, drinking water, water quality
- electricity: Power supply, electricity cuts, transformers
- drainage: Drainage, sewage, sanitation
- sewage: Waste management, sewage systems
- road: Roads, potholes, street repairs
- bridge: Bridges, culverts
- infrastructure: Buildings, public facilities
- health: Disease, medical emergencies, epidemics
- medical: Healthcare services, hospitals, clinics
- disease: Disease outbreaks, health crises
- education: Schools, teachers, education quality
- school: School facilities, school issues
- corruption: Bribery, corruption cases
- bribery: Demands for money, illegal fees
- harassment: Official harassment, abuse of power
- all: General category (always include this)

Respond with a JSON object:
{{
  "categories": ["category1", "category2", "all"]
}}

Rules:
1. ALWAYS include "all" category
2. Include ALL relevant specific categories
3. Be inclusive - if something might relate to a category, include it
4. Minimum 1 specific category + "all" category

Respond ONLY with valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI classifier for Indian government grievances. Respond only with JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            categories = result.get("categories", ["all"])

            # Ensure "all" is always included
            if "all" not in categories:
                categories.append("all")

            logger.info(f"Detected problem types: {categories}")
            return categories

        except Exception as e:
            logger.error(f"Error detecting problem type: {e}")
            # Fallback to "all" category
            return ["all"]

    def _select_contextual_fields(self, problem_types: List[str]) -> Dict[str, Any]:
        """
        Select contextual fields relevant to detected problem types.

        Args:
            problem_types: List of detected problem categories

        Returns:
            Dictionary of relevant contextual fields
        """
        selected_fields = {}

        for field_name, field_config in CONTEXTUAL_FIELDS.items():
            applies_to = field_config.get("applies_to", [])

            # Check if field applies to any of the detected problem types
            if any(problem_type in applies_to for problem_type in problem_types):
                selected_fields[field_name] = field_config
                logger.debug(f"Selected contextual field '{field_name}' for types {problem_types}")

        logger.info(f"Selected {len(selected_fields)} contextual fields for problem types {problem_types}")
        return selected_fields

    def _build_dynamic_field_schema(
        self,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build dynamic field schema combining universal and contextual fields.

        Args:
            extracted_data: Previously extracted data (may contain issue_description)

        Returns:
            Complete field schema (universal + contextual for detected problem type)
        """
        # Start with universal required fields (always apply)
        schema = dict(UNIVERSAL_REQUIRED_FIELDS)

        # If we have an issue description, detect problem type and add contextual fields
        if extracted_data and extracted_data.get("issue_description"):
            issue_desc = extracted_data["issue_description"]

            # Detect problem type
            problem_types = self._detect_problem_type(issue_desc)

            # Select relevant contextual fields
            contextual = self._select_contextual_fields(problem_types)

            # Add contextual fields to schema
            schema.update(contextual)

            logger.info(f"Built dynamic schema with {len(schema)} fields (2 universal + {len(contextual)} contextual)")
        else:
            # No issue description yet - only use universal fields
            logger.info("No issue description yet - using only universal required fields")

        return schema

    def analyze_completeness(
        self,
        transcript: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        already_collected_fields: Optional[Dict[str, Any]] = None,
        question_tracker: Optional[Any] = None  # BUG FIX #1: Accept question tracker
    ) -> Dict[str, Any]:
        """
        Analyze transcript to determine completeness and extract fields.

        STATEFUL: Merges new information with previously collected fields.

        Args:
            transcript: User's voice transcript (Hindi/English/Chhattisgarhi)
            conversation_history: Previous turns in the conversation
            already_collected_fields: Fields already collected in previous turns
                Format: {"field_name": "field_value", ...}

        Returns:
            Dict containing:
                - completeness_score: float (0.0 to 1.0)
                - is_complete: bool (True if score >= 0.8)
                - collected_fields: List[str] - Fields successfully extracted (cumulative)
                - missing_fields: List[Dict] - Fields still missing with follow-up prompts
                - extracted_data: Dict - Merged structured data (old + new)
                - next_question_hi: str - Next follow-up question in Hindi (if incomplete)
                - next_question_en: str - Next follow-up question in English

        Example:
            >>> analyzer = CompletenessAnalyzer()
            >>> # First turn
            >>> result1 = analyzer.analyze_completeness(
            ...     "पानी की सप्लाई नहीं आ रही है रायपुर में"
            ... )
            >>> # Second turn - pass accumulated fields
            >>> result2 = analyzer.analyze_completeness(
            ...     "यह समस्या 3 दिन से है",
            ...     already_collected_fields=result1["extracted_data"]
            ... )
            >>> # Now result2 contains BOTH location AND when_started
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        logger.info(f"Analyzing completeness for transcript (length: {len(transcript)})")
        logger.info(f"Already collected fields: {list(already_collected_fields.keys()) if already_collected_fields else 'None'}")

        try:
            # Build prompt for Azure OpenAI with accumulated state
            prompt = self._build_analysis_prompt(
                transcript,
                conversation_history,
                already_collected_fields,
                question_tracker  # BUG FIX #1: Pass question tracker
            )

            # Call Azure OpenAI
            logger.debug(f"Calling Azure OpenAI with deployment: {self.deployment}")
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant helping analyze grievance reports in India. You understand Hindi, English, and Chhattisgarhi."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            # Parse response
            response_text = response.choices[0].message.content
            logger.debug(f"Azure OpenAI response: {response_text[:200]}...")

            result = json.loads(response_text)

            # HYBRID FIX: If Azure failed to extract location but user provided it, use deterministic parser
            if transcript and len(transcript) > 10:
                azure_location = result.get("extracted_data", {}).get("location")
                if not azure_location or _looks_vague_location(str(azure_location)):
                    # Try deterministic extraction as backup
                    det_loc = deterministic_location_extract(transcript)
                    if det_loc.get("precision") == "specific" and det_loc.get("joined"):
                        logger.warning(
                            f"[HYBRID FIX] Azure missed location, using deterministic parser: "
                            f"Azure='{azure_location}' → Deterministic='{det_loc['joined']}'"
                        )
                        if "extracted_data" not in result:
                            result["extracted_data"] = {}
                        result["extracted_data"]["location"] = det_loc["joined"]
                        result["extracted_data"]["location_precision"] = "specific"

                        # If location was missing, add it to collected_fields
                        if "location" not in result.get("collected_fields", []):
                            result.setdefault("collected_fields", []).append("location")

                        # Remove location from missing_fields if present
                        result["missing_fields"] = [
                            f for f in result.get("missing_fields", [])
                            if f.get("field") != "location"
                        ]

            # Validate and process result
            processed_result = self._process_analysis_result(result)

            # Add metadata
            processed_result["metadata"] = {
                "model": self.deployment,
                "tokens_used": response.usage.total_tokens,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }

            logger.info(
                f"Analysis complete: completeness={processed_result['completeness_score']:.2f}, "
                f"complete={processed_result['is_complete']}"
            )

            return processed_result

        except APITimeoutError as e:
            logger.error(f"Azure OpenAI timeout: {e}")
            raise CompletenessAnalyzerError(f"Azure OpenAI request timed out. Please try again: {str(e)}")

        except APIConnectionError as e:
            logger.error(f"Azure OpenAI connection error: {e}")
            raise CompletenessAnalyzerError(f"Failed to connect to Azure OpenAI: {str(e)}")

        except APIError as e:
            logger.error(f"Azure OpenAI API error: {e}")
            raise CompletenessAnalyzerError(f"Azure OpenAI API error: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Azure OpenAI response as JSON: {e}")
            raise CompletenessAnalyzerError(f"Invalid JSON response: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error in analyze_completeness: {e}", exc_info=True)
            raise CompletenessAnalyzerError(f"Analysis failed: {str(e)}")

    def _build_analysis_prompt(
        self,
        transcript: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        already_collected_fields: Optional[Dict[str, Any]] = None,
        question_tracker: Optional[Any] = None  # BUG FIX #1: Accept question tracker
    ) -> str:
        """Build the STATEFUL analysis prompt for Azure OpenAI with DYNAMIC field schema."""

        # Build conversation context if available
        context = ""
        if conversation_history:
            context = "\n\nPrevious conversation turns:\n"
            for turn in conversation_history:
                context += f"User: {turn.get('user', '')}\n"
                context += f"AI: {turn.get('ai', '')}\n"

        # Build already collected fields context
        collected_context = ""
        if already_collected_fields:
            # Filter out None/empty values
            non_empty_fields = {k: v for k, v in already_collected_fields.items() if v}
            if non_empty_fields:
                collected_context = f"\n\n✅ ALREADY COLLECTED FIELDS (DO NOT ASK AGAIN):\n"
                collected_context += json.dumps(non_empty_fields, indent=2, ensure_ascii=False)
                collected_context += "\n\n⚠️ CRITICAL: You MUST preserve these values in extracted_data. DO NOT ask about these fields again."

        # BUG FIX #1: Build question tracker context
        tracker_context = ""
        if question_tracker:
            asked_fields = question_tracker.get_all_asked_fields()
            if asked_fields:
                tracker_context = f"\n\n🚫 ALREADY ASKED ABOUT (DO NOT ASK AGAIN):\n"
                tracker_context += f"Fields: {', '.join(asked_fields)}\n"
                for field_name in asked_fields:
                    count = question_tracker.get_question_count(field_name)
                    tracker_context += f"  - {field_name}: asked {count} time(s)\n"
                tracker_context += "\n⚠️ CRITICAL: You already asked about these fields. DO NOT repeat these questions!\n"

        # BUILD DYNAMIC FIELD SCHEMA based on problem type
        # This selects relevant fields based on what we already know about the issue
        field_schema = self._build_dynamic_field_schema(already_collected_fields)
        logger.info(f"Using dynamic field schema with {len(field_schema)} fields")

        # BUG FIX #3: Add rich narrative extraction instructions
        rich_extraction_note = """
🎯 RICH NARRATIVE EXTRACTION (BUG FIX #3):
When user provides a detailed narrative, extract ALL these details:
- Technical details (e.g., "120 फिट खुदाई", "पुराना पाइप")
- Impact/affected scope (e.g., "20-30 मकान", "सभी गांववाले")
- Health/safety impacts (e.g., "बीमारियां हो रही हैं", "नदी से पानी पीते हैं")
- Actions already taken (e.g., "सरपंच को बताया", "शिकायत की")
- Urgency indicators (e.g., "बहुत गंभीर", "तुरंत", "जल्दी")
- Duration/frequency (e.g., "पिछले 2 महीने से", "रोज", "कभी-कभी")

Store these details in extracted_data with descriptive keys:
- "technical_details": "120 फिट खुदाई, पुराना पाइप"
- "affected_count": "20-30 मकान"
- "health_impact": "नदी से पानी पीते हैं, बीमारियां हो रही हैं"
- "action_taken": "सरपंच को बोलने पर कहते हैं 'हमने लगा दिया'"
"""

        # BUG FIX #2: Add context-aware question selection instructions
        context_aware_note = """
🎯 CONTEXT-AWARE QUESTION SELECTION (BUG FIX #2):
CRITICAL: Select questions based on problem CONTEXT:

1. For "BROKEN" infrastructure (doesn't work AT ALL):
   - Issue: "पानी नहीं निकलता", "हैंडपंप टूटा है", "बिजली बिल्कुल नहीं आती"
   - DO NOT ask: "दिन में कितने घंटे मिलता है?" (makes no sense if it doesn't work!)
   - ASK INSTEAD: "कब से टूटा है?", "क्या repair की कोशिश की?"

2. For "INTERMITTENT" service (works sometimes):
   - Issue: "पानी कम आता है", "बिजली आती-जाती रहती है"
   - DO ask: "दिन में कितने घंटे मिलता है?"
   - DO ask: "कब से यह problem है?"

3. For "QUALITY" issues:
   - Issue: "पानी गंदा आता है", "बिजली voltage कम है"
   - DO ask: "कितना गंदा?", "voltage कितनी कम है?"
   - DO ask: "यह हमेशा होता है या कभी-कभी?"

BEFORE selecting a question, check the issue_description and problem CONTEXT.
"""

        prompt = f"""You are analyzing a voice transcript from a citizen reporting an issue to the government in India.

This is a STATEFUL conversation. You must MERGE new information with already collected fields.

Current user message: "{transcript}"{context}{collected_context}{tracker_context}

{rich_extraction_note}

{context_aware_note}

Your task is to:
1. Extract NEW information from the current transcript
2. MERGE with already collected fields (preserve old values, add new ones)
3. ACCEPT "don't know" type responses and mark field as collected with value "unknown"
4. NEVER ask the same question more than ONCE - if user says don't know, MOVE ON
5. Calculate completeness based on ALL collected fields (old + new)
6. Generate the next follow-up question ONLY for missing fields

Required fields schema (DYNAMICALLY SELECTED based on problem type):
{json.dumps(field_schema, indent=2, ensure_ascii=False)}

🚨 IMPORTANCE LEVEL GUIDELINES:
- "issue_description" and "location" → ALWAYS mark as "critical" (minimum required for submission)
- "affected_scope", "urgency_level" → ALWAYS mark as "low" (nice-to-have, not required for submission)
- Problem-specific contextual fields (e.g., "service_duration", "health_affected_count") → mark as "medium"

CRITICAL: Only "issue_description" and "location" should have "critical" importance.
All other fields should be "medium" or "low" based on context.

Respond with a JSON object in this exact format:
{{
  "completeness_score": 0.0-1.0,
  "is_complete": true/false,
  "collected_fields": ["field_name1", "field_name2"],
  "missing_fields": [
    {{
      "field": "field_name",
      "importance": "critical/high/medium/low",
      "name_hi": "Hindi name",
      "name_en": "English name",
      "prompt_hi": "Hindi follow-up question",
      "prompt_en": "English follow-up question"
    }}
  ],
  "extracted_data": {{
    "issue_description": "actual problem description (e.g., 'बिजली नहीं आ रही है पांच दिन से') or null",
    "location": "village/ward/area name or null",
    "affected_scope": "value or null"
  }},
  "next_question_hi": "Next follow-up question in Hindi",
  "next_question_en": "Next follow-up question in English"
}}

CRITICAL RULES - RURAL INDIA CONTEXT:
1. ACCEPT "नहीं पता", "मालूम नहीं", "don't know", "no" as VALID answers
   - Set field value to "unknown" and mark as collected
   - DO NOT ask the same question again
2. If user says "don't know" or similar, IMMEDIATELY move to next question
3. extracted_data MUST include ALL previously collected fields plus any new ones
4. If a field was already collected, keep its value even if not mentioned in current turn
5. Only ask about TRULY MISSING fields (not asked before)
6. completeness_score should reflect cumulative progress (all turns combined)

🚨 CRITICAL - issue_description VALIDATION:
- issue_description MUST describe an ACTUAL PROBLEM (e.g., "बिजली नहीं आ रही", "सड़क टूटी है")
- DO NOT extract issue_description from:
  * Location-only statements like "मैं निटाने से बोल रहा हूँ" (just location, no problem!)
  * Generic phrases like "बोल रहा हूँ", "speaking from", "मैं हूँ"
  * Pure introductions with no problem description
- issue_description should be at least 5-7 words describing what is wrong
- If user ONLY mentioned location, set issue_description to null (not extracted yet)
7. next_question_hi should NEVER repeat a question already asked
8. collected_fields list should include ALL fields with values (old + new + unknown)

Example stateful flow with "don't know":
Turn 1: User says "पानी नहीं आ रहा रायपुर में"
→ collected: location="रायपुर", issue_description="पानी नहीं आ रहा"
→ Ask about: affected_scope

Turn 2: User says "नहीं पता" (Don't know)
→ MERGE: location="रायपुर" (keep), issue_description="पानी नहीं आ रहा" (keep), affected_scope="unknown" (new)
→ ALL fields collected → Complete!
→ DO NOT ask any more questions

Example with repeated questioning (WRONG - DO NOT DO THIS):
Turn 1: Ask "यह समस्या कब से हो रही है?"
Turn 2: User says "नहीं पता"
Turn 3: Ask "यह समस्या कब से हो रही है?" ← NEVER DO THIS!

Guidelines:
- completeness_score: Calculate as (collected_critical_fields / total_critical_fields)
  * Critical fields: issue_description, location (BOTH required)
  * High importance fields: Can be "unknown" and still complete
- is_complete: true if ALL critical fields collected (even high importance can be "unknown")
- Be lenient - accept approximate answers, "don't know", vague responses
- For rural context: Government needs WHAT and WHERE - other details are optional
- If user is frustrated or repeating "don't know", mark remaining fields as "unknown" and complete

Respond ONLY with valid JSON."""

        return prompt

    def _process_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process the analysis result from Azure OpenAI (supports dynamic fields)."""

        # Validate required fields
        required_fields = [
            "completeness_score", "is_complete", "collected_fields",
            "missing_fields", "extracted_data"
        ]
        for field in required_fields:
            if field not in result:
                raise CompletenessAnalyzerError(f"Missing required field in response: {field}")

        # Validate completeness score
        score = float(result["completeness_score"])
        if not 0.0 <= score <= 1.0:
            logger.warning(f"Invalid completeness_score {score}, clamping to [0, 1]")
            score = max(0.0, min(1.0, score))
        result["completeness_score"] = score

        # Validate is_complete
        if not isinstance(result["is_complete"], bool):
            result["is_complete"] = score >= 0.8

        # Validate collected_fields
        if not isinstance(result["collected_fields"], list):
            result["collected_fields"] = []

        # Validate missing_fields
        if not isinstance(result["missing_fields"], list):
            result["missing_fields"] = []

        # Ensure extracted_data has universal required fields (minimum)
        if not isinstance(result["extracted_data"], dict):
            result["extracted_data"] = {}

        # Only validate universal required fields exist in extracted_data
        # Contextual fields are optional and added dynamically
        for field_name in UNIVERSAL_REQUIRED_FIELDS.keys():
            if field_name not in result["extracted_data"]:
                result["extracted_data"][field_name] = None

        # Set default questions if missing
        if "next_question_hi" not in result:
            if result["missing_fields"]:
                result["next_question_hi"] = result["missing_fields"][0].get("prompt_hi", "")
            else:
                result["next_question_hi"] = ""

        if "next_question_en" not in result:
            if result["missing_fields"]:
                result["next_question_en"] = result["missing_fields"][0].get("prompt_en", "")
            else:
                result["next_question_en"] = ""

        return result

    def should_ask_followup(
        self,
        completeness_score: float,
        turn_count: int,
        max_followups: int = 2
    ) -> bool:
        """
        Determine if AI Coach should ask a follow-up question.

        Args:
            completeness_score: Current completeness score (0.0-1.0)
            turn_count: Number of conversation turns so far
            max_followups: Maximum allowed follow-up questions (default: 2)

        Returns:
            True if should ask follow-up, False otherwise

        Rules:
            - Don't ask if completeness >= 0.8 (80%)
            - Don't ask if already at max_followups limit
            - Ask if incomplete and under limit
        """
        if completeness_score >= 0.8:
            logger.debug("Completeness >= 0.8, no follow-up needed")
            return False

        if turn_count >= max_followups + 1:  # +1 for initial turn
            logger.debug(f"Turn count {turn_count} >= max {max_followups + 1}, no more follow-ups")
            return False

        logger.debug(f"Completeness {completeness_score:.2f}, turn {turn_count}, asking follow-up")
        return True


# Global instance
_completeness_analyzer: Optional[CompletenessAnalyzer] = None


def get_completeness_analyzer() -> CompletenessAnalyzer:
    """
    Get or create global CompletenessAnalyzer instance.

    Returns:
        CompletenessAnalyzer instance

    Raises:
        CompletenessAnalyzerError: If analyzer cannot be initialized
    """
    global _completeness_analyzer

    if _completeness_analyzer is None:
        _completeness_analyzer = CompletenessAnalyzer()

    return _completeness_analyzer
