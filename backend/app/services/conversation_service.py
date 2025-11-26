"""
Conversation Service - AI Journalist Agent
Handles triage, slot extraction, and conversational AI for Boloo

Now using Azure OpenAI for natural conversations!
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.conversation_prompts import (
    SYSTEM_PROMPT_TRIAGE,
    SYSTEM_PROMPT_GRIEVANCE,
    SYSTEM_PROMPT_COMMUNITY,
    SYSTEM_PROMPT_PERSONAL,
    TONE_EXAMPLES,
    SLA_TIMINGS,
    STATUS_MESSAGES,
    WHO_HAS_BALL,
    NEXT_STEPS_TEMPLATES,
)
from app.services.azure_openai_service import (
    AzureOpenAIService,
    AzureOpenAIServiceError,
    AzureOpenAIAPIError,
    get_azure_openai_service
)

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    GRIEVANCE = "grievance"
    COMMUNITY = "community"
    PERSONAL = "personal"
    UNCERTAIN = "uncertain"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TriageResult:
    """Result of initial triage classification"""
    intent: IntentType
    confidence: ConfidenceLevel
    location_hint: Optional[str] = None
    topic_hint: Optional[str] = None
    reasoning: Optional[str] = None


@dataclass
class ConversationSlots:
    """Slots extracted from conversation"""
    # Common slots
    location_text: Optional[str] = None
    location_confidence: ConfidenceLevel = ConfidenceLevel.LOW

    # Grievance-specific slots
    issue_type: Optional[str] = None
    when_started: Optional[str] = None
    scope_affected: Optional[str] = None
    prior_contact: Optional[str] = None
    evidence_mentioned: bool = False

    # Community story-specific slots
    topic: Optional[str] = None  # song/medicine/tradition/news
    who_sharing: Optional[str] = None
    rights_consent: bool = False

    # Personal diary-specific slots
    short_title: Optional[str] = None
    note_text: Optional[str] = None
    reminder_when: Optional[str] = None
    convertible_to_grievance: bool = False


@dataclass
class ConversationTurn:
    """Single turn in conversation"""
    speaker: str  # 'user' or 'agent'
    text_hindi: str
    text_english: Optional[str] = None
    timestamp: str = None
    confidence: Optional[float] = None


@dataclass
class ConversationState:
    """Complete conversation state"""
    conversation_id: str
    user_id: str
    intent: Optional[IntentType] = None
    intent_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    slots: ConversationSlots = None
    turns: List[ConversationTurn] = None
    is_complete: bool = False
    formal_summary: Optional[str] = None

    def __post_init__(self):
        if self.slots is None:
            self.slots = ConversationSlots()
        if self.turns is None:
            self.turns = []


class ConversationService:
    """
    AI Journalist Agent Service

    Uses Azure OpenAI for natural conversation flow and intent classification.
    """

    def __init__(self, azure_openai_service: Optional[AzureOpenAIService] = None):
        """
        Initialize conversation service

        Args:
            azure_openai_service: Azure OpenAI service instance (auto-created if None)
        """
        self.azure_openai_service = azure_openai_service or get_azure_openai_service()
        logger.info("ConversationService initialized with Azure OpenAI")

    def process_triage(self, transcript: str, language_hint: str = "hi") -> TriageResult:
        """
        Classify user's first message into intent category using Azure OpenAI

        Args:
            transcript: User's speech transcript (Hindi/Hinglish)
            language_hint: Language code (hi/en)

        Returns:
            TriageResult with classification

        Raises:
            AzureOpenAIServiceError: If classification fails after retries
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        logger.info(f"🔍 Processing triage for transcript: '{transcript[:50]}...'")

        # Retry logic for API failures (max 3 attempts)
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Call Azure OpenAI for intent classification
                classification_result = self.azure_openai_service.classify_intent(
                    transcript=transcript,
                    location_hint=None  # Will be extracted from transcript if present
                )

                # Map Azure OpenAI result to TriageResult
                intent_mapping = {
                    "grievance": IntentType.GRIEVANCE,
                    "community": IntentType.COMMUNITY,
                    "personal": IntentType.PERSONAL,
                    "uncertain": IntentType.UNCERTAIN
                }

                intent = intent_mapping.get(
                    classification_result["intent"],
                    IntentType.UNCERTAIN
                )

                # Map confidence level
                confidence_level = classification_result["confidence_level"]
                confidence_mapping = {
                    "high": ConfidenceLevel.HIGH,
                    "medium": ConfidenceLevel.MEDIUM,
                    "low": ConfidenceLevel.LOW
                }
                confidence = confidence_mapping.get(confidence_level, ConfidenceLevel.LOW)

                triage_result = TriageResult(
                    intent=intent,
                    confidence=confidence,
                    location_hint=None,  # Extracted later in conversation
                    topic_hint=classification_result.get("suggested_issue_type"),
                    reasoning=classification_result.get("reasoning")
                )

                logger.info(
                    f"✅ Triage complete: intent={intent.value}, "
                    f"confidence={confidence.value}, reasoning={triage_result.reasoning}"
                )

                return triage_result

            except AzureOpenAIAPIError as e:
                last_error = e
                logger.warning(
                    f"⚠️  Triage attempt {attempt}/{max_retries} failed: {e}"
                )
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying triage... (attempt {attempt + 1})")
                    continue
                else:
                    logger.error(f"❌ Triage failed after {max_retries} attempts")
                    raise AzureOpenAIServiceError(
                        f"Failed to classify intent after {max_retries} attempts: {str(e)}"
                    )

            except Exception as e:
                logger.error(f"❌ Unexpected error in triage: {e}", exc_info=True)
                raise AzureOpenAIServiceError(f"Triage processing failed: {str(e)}")


    def process_turn(
        self,
        state: ConversationState,
        user_transcript: str
    ) -> Tuple[str, ConversationState]:
        """
        Process a conversation turn and generate agent response using Azure OpenAI

        Args:
            state: Current conversation state
            user_transcript: User's latest message

        Returns:
            Tuple of (agent_response_hindi, updated_state)

        Raises:
            AzureOpenAIServiceError: If response generation fails
        """
        if not user_transcript or not user_transcript.strip():
            raise ValueError("User transcript cannot be empty")

        logger.info(
            f"🗣️  Processing turn {len(state.turns) + 1} for conversation {state.conversation_id}"
        )

        # Add user turn to conversation
        state.turns.append(ConversationTurn(
            speaker="user",
            text_hindi=user_transcript,
            timestamp=None  # Should be set by caller
        ))

        # Route to appropriate handler based on intent
        try:
            if state.intent == IntentType.GRIEVANCE:
                response = self._process_grievance_turn(state, user_transcript)
            elif state.intent == IntentType.COMMUNITY:
                response = self._process_community_turn(state, user_transcript)
            elif state.intent == IntentType.PERSONAL:
                response = self._process_personal_turn(state, user_transcript)
            else:
                # Ask clarifying question
                response = "क्षमा करें, मैं समझ नहीं पाया। आप क्या करना चाहते हैं - शिकायत दर्ज करनी है, कुछ शेयर करना है, या निजी नोट बनाना है?"

            # Add agent turn
            state.turns.append(ConversationTurn(
                speaker="agent",
                text_hindi=response,
                timestamp=None
            ))

            logger.info(f"✅ Turn processed: {response[:50]}...")
            return response, state

        except AzureOpenAIServiceError as e:
            logger.error(f"❌ Failed to process turn: {e}")
            # Return graceful error message
            error_response = (
                "क्षमा करें, मुझे तकनीकी समस्या आ रही है। "
                "कृपया कुछ देर बाद फिर कोशिश करें। "
                "(Sorry, I'm experiencing a technical issue. Please try again in a moment.)"
            )
            state.turns.append(ConversationTurn(
                speaker="agent",
                text_hindi=error_response,
                timestamp=None
            ))
            return error_response, state

    def _process_grievance_turn(self, state: ConversationState, transcript: str) -> str:
        """
        Process turn for grievance intent using Azure OpenAI for natural conversation

        Uses AI to:
        - Extract slot values from user's natural language
        - Generate empathetic responses
        - Ask follow-up questions naturally
        - Determine when conversation is complete
        """
        slots = state.slots

        # Build conversation history for context
        conversation_history = [
            {"user": turn.text_hindi, "ai": state.turns[i+1].text_hindi if i+1 < len(state.turns) else ""}
            for i, turn in enumerate(state.turns)
            if turn.speaker == "user" and i+1 < len(state.turns)
        ]

        # Build collected data
        collected_data = {}
        if slots.location_text:
            collected_data["location"] = slots.location_text
        if slots.issue_type:
            collected_data["issue_type"] = slots.issue_type
        if slots.when_started:
            collected_data["when_started"] = slots.when_started
        if slots.scope_affected:
            collected_data["scope_affected"] = slots.scope_affected
        if slots.prior_contact:
            collected_data["prior_contact"] = slots.prior_contact

        # Determine missing fields
        missing_fields = []
        if not slots.location_text:
            missing_fields.append({
                "field": "location",
                "prompt_hi": "गांव या मोहल्ला का नाम बताइए।"
            })
        if not slots.issue_type:
            missing_fields.append({
                "field": "issue_type",
                "prompt_hi": "समस्या का प्रकार बताएं।"
            })
        if not slots.when_started:
            missing_fields.append({
                "field": "when_started",
                "prompt_hi": "यह समस्या कब से है?"
            })
        if not slots.scope_affected:
            missing_fields.append({
                "field": "scope_affected",
                "prompt_hi": "कितने लोगों को प्रभावित कर रहा है?"
            })

        # Check if conversation is complete (minimum: location + issue_type)
        is_complete = bool(slots.location_text and slots.issue_type)

        # Retry logic for conversation response
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Call Azure OpenAI for natural conversation response
                ai_response = self.azure_openai_service.generate_conversation_response(
                    user_message=transcript,
                    conversation_history=conversation_history,
                    missing_fields=missing_fields,
                    collected_data=collected_data,
                    is_complete=is_complete
                )

                response_hi = ai_response["response_hi"]

                # Extract any new information from AI's understanding
                # The AI might have extracted data we should store
                if ai_response.get("next_field_asked"):
                    logger.debug(f"AI asked about field: {ai_response['next_field_asked']}")

                # Update completion status
                if is_complete:
                    state.is_complete = True
                    state.formal_summary = self._generate_formal_summary(state)

                return response_hi

            except AzureOpenAIAPIError as e:
                logger.warning(
                    f"⚠️  Conversation response attempt {attempt}/{max_retries} failed: {e}"
                )
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying conversation response... (attempt {attempt + 1})")
                    continue
                else:
                    # Enhanced fallback - extract what we can from the transcript
                    logger.error(f"❌ Conversation response failed after {max_retries} attempts")
                    return self._intelligent_fallback_grievance(state, transcript)

    def _process_community_turn(self, state: ConversationState, transcript: str) -> str:
        """
        Process turn for community story intent using Azure OpenAI

        Community stories require:
        - topic (song/medicine/tradition/news)
        - location
        - who is sharing
        - rights/consent
        """
        slots = state.slots

        # Build conversation history
        conversation_history = [
            {"user": turn.text_hindi, "ai": state.turns[i+1].text_hindi if i+1 < len(state.turns) else ""}
            for i, turn in enumerate(state.turns)
            if turn.speaker == "user" and i+1 < len(state.turns)
        ]

        # Build collected data
        collected_data = {}
        if slots.topic:
            collected_data["topic"] = slots.topic
        if slots.location_text:
            collected_data["location"] = slots.location_text
        if slots.who_sharing:
            collected_data["who_sharing"] = slots.who_sharing
        if slots.rights_consent:
            collected_data["rights_consent"] = "हाँ" if slots.rights_consent else "नहीं"

        # Determine missing fields
        missing_fields = []
        if not slots.topic:
            missing_fields.append({
                "field": "topic",
                "prompt_hi": "यह क्या है - गाना, परंपरा, दवा का नुस्खा या कुछ और?"
            })
        if not slots.location_text:
            missing_fields.append({
                "field": "location",
                "prompt_hi": "यह कहां की है?"
            })
        if not slots.who_sharing:
            missing_fields.append({
                "field": "who_sharing",
                "prompt_hi": "यह किसकी है? बुजुर्गों की? आपकी?"
            })
        if not slots.rights_consent:
            missing_fields.append({
                "field": "rights_consent",
                "prompt_hi": "क्या मैं इसे सबको दिखा सकता हूं?"
            })

        # Check completion
        is_complete = bool(
            slots.topic and slots.location_text and
            slots.who_sharing and slots.rights_consent is not None
        )

        try:
            # Call Azure OpenAI
            ai_response = self.azure_openai_service.generate_conversation_response(
                user_message=transcript,
                conversation_history=conversation_history,
                missing_fields=missing_fields,
                collected_data=collected_data,
                is_complete=is_complete
            )

            response_hi = ai_response["response_hi"]

            if is_complete:
                state.is_complete = True
                state.formal_summary = self._generate_formal_summary(state)

            return response_hi

        except AzureOpenAIAPIError as e:
            logger.warning(f"⚠️  Community turn failed, using intelligent fallback: {e}")
            return self._intelligent_fallback_community(state, transcript)

    def _process_personal_turn(self, state: ConversationState, transcript: str) -> str:
        """
        Process turn for personal diary intent using Azure OpenAI

        Personal notes require:
        - short_title
        - note_text
        - reminder_when (optional)
        """
        slots = state.slots

        # Build conversation history
        conversation_history = [
            {"user": turn.text_hindi, "ai": state.turns[i+1].text_hindi if i+1 < len(state.turns) else ""}
            for i, turn in enumerate(state.turns)
            if turn.speaker == "user" and i+1 < len(state.turns)
        ]

        # Build collected data
        collected_data = {}
        if slots.short_title:
            collected_data["title"] = slots.short_title
        if slots.note_text:
            collected_data["note"] = slots.note_text
        if slots.reminder_when:
            collected_data["reminder"] = slots.reminder_when

        # Determine missing fields
        missing_fields = []
        if not slots.short_title or not slots.note_text:
            missing_fields.append({
                "field": "note",
                "prompt_hi": "क्या लिखना है?"
            })
        if slots.short_title and not slots.reminder_when:
            missing_fields.append({
                "field": "reminder",
                "prompt_hi": "कोई रिमाइंडर चाहिए?"
            })

        # Check completion (minimum: title + note)
        is_complete = bool(slots.short_title and slots.note_text)

        try:
            # Call Azure OpenAI
            ai_response = self.azure_openai_service.generate_conversation_response(
                user_message=transcript,
                conversation_history=conversation_history,
                missing_fields=missing_fields,
                collected_data=collected_data,
                is_complete=is_complete
            )

            response_hi = ai_response["response_hi"]

            # Auto-set title and note from first message if not set
            if not slots.short_title and transcript:
                slots.short_title = transcript[:50]
                slots.note_text = transcript

            if is_complete:
                state.is_complete = True
                state.formal_summary = "निजी नोट"

            return response_hi

        except AzureOpenAIAPIError as e:
            logger.warning(f"⚠️  Personal turn failed, using intelligent fallback: {e}")
            return self._intelligent_fallback_personal(state, transcript)

    def _intelligent_fallback_grievance(
        self, state: ConversationState, transcript: str
    ) -> str:
        """
        Intelligent fallback when Azure OpenAI fails for grievance conversations.
        Uses basic extraction + empathetic templates instead of simple if-elif.
        """
        slots = state.slots

        # Try to extract location from transcript (basic keyword matching)
        if not slots.location_text:
            # Look for location keywords in transcript
            location_keywords = ["गांव", "मोहल्ला", "वार्ड", "ब्लॉक", "जिला", "में", "से"]
            words = transcript.split()
            for i, word in enumerate(words):
                if any(kw in word.lower() for kw in location_keywords):
                    # Next word might be location name
                    if i + 1 < len(words):
                        potential_location = words[i + 1]
                        # Acknowledge what we heard
                        return f"समझ रहा हूं। तो {potential_location} में समस्या है। कृपया समस्या के बारे में थोड़ा और बताइए।"

            # No location found
            return "धन्यवाद। कृपया अपने गांव या मोहल्ले का नाम बताइए ताकि सही अधिकारी तक पहुंच सकें।"

        if not slots.issue_type:
            # Try to extract issue type from transcript
            issue_keywords = {
                "बिजली": "बिजली", "पानी": "पानी", "सड़क": "सड़क",
                "नाली": "स्वच्छता", "कचरा": "स्वच्छता", "शौचालय": "स्वच्छता"
            }
            for keyword, issue_type in issue_keywords.items():
                if keyword in transcript.lower():
                    slots.issue_type = issue_type
                    return f"ठीक है, {issue_type} की समस्या। यह कब से है?"

            return f"{slots.location_text} की बात समझ गया। समस्या किस बारे में है - बिजली, पानी, सड़क या कुछ और?"

        if not slots.when_started:
            return "यह समस्या कब से है? कुछ दिन, हफ्ते या महीने?"

        if not slots.scope_affected:
            return "और कितने लोगों को यह समस्या प्रभावित कर रही है?"

        # All collected - can submit
        state.is_complete = True
        return "धन्यवाद! आपकी शिकायत दर्ज हो गई है। आप जल्द ही अपडेट पाएंगे।"

    def _intelligent_fallback_community(
        self, state: ConversationState, transcript: str
    ) -> str:
        """
        Intelligent fallback for community story conversations.
        """
        slots = state.slots

        if not slots.topic:
            # Try to detect topic from keywords
            topic_keywords = {
                "गाना": "गाना", "गीत": "गाना", "परंपरा": "परंपरा",
                "दवा": "दवा का नुस्खा", "नुस्खा": "दवा का नुस्खा",
                "खबर": "समाचार", "बात": "कहानी"
            }
            for keyword, topic in topic_keywords.items():
                if keyword in transcript.lower():
                    slots.topic = topic
                    return f"वाह! {topic} बहुत अच्छी बात है। यह कहां की है?"

            return "बहुत अच्छा! यह क्या है - गाना, परंपरा, दवा का नुस्खा या कोई खबर?"

        if not slots.location_text:
            return "कहां की है यह? किस गांव या इलाके की?"

        if not slots.who_sharing:
            return "यह किसकी है? बुजुर्गों की, आपकी, या किसी और की?"

        if not slots.rights_consent:
            return "क्या मैं इसे सबको दिखा सकता हूं? (हाँ/नहीं बोलिए)"

        # Complete
        state.is_complete = True
        return "बहुत बढ़िया! आपकी पोस्ट तैयार है। जल्द ही सबको दिखेगी।"

    def _intelligent_fallback_personal(
        self, state: ConversationState, transcript: str
    ) -> str:
        """
        Intelligent fallback for personal diary conversations.
        """
        slots = state.slots

        # Personal notes are simplest - just store what they said
        if not slots.short_title:
            slots.short_title = transcript[:50]
            slots.note_text = transcript
            return "समझ गया। कोई रिमाइंडर लगाना चाहेंगे? (हाँ/नहीं)"

        if not slots.reminder_when:
            # Check if they want reminder
            if any(word in transcript.lower() for word in ["हाँ", "चाहिए", "लगा"]):
                return "कब का रिमाइंडर चाहिए? कल, परसों, या कोई तारीख?"
            else:
                state.is_complete = True
                return "ठीक है। नोट सेव हो गया। यह सिर्फ आपको दिखेगा।"

        # Reminder set - complete
        state.is_complete = True
        return "बहुत अच्छा! आपका नोट रिमाइंडर के साथ सेव हो गया।"

    def _generate_formal_summary(self, state: ConversationState) -> str:
        """Generate formal summary for officials"""
        slots = state.slots

        if state.intent == IntentType.GRIEVANCE:
            return f"""शिकायत सारांश:
स्थान: {slots.location_text or 'अज्ञात'}
समस्या: {slots.issue_type or 'बुनियादी सुविधा'}
कब से: {slots.when_started or 'हाल ही में'}
प्रभावित: {slots.scope_affected or 'स्थानीय समुदाय'}
पूर्व संपर्क: {slots.prior_contact or 'नहीं'}"""

        elif state.intent == IntentType.COMMUNITY:
            return f"""सामुदायिक पोस्ट:
विषय: {slots.topic or 'परंपरा'}
स्थान: {slots.location_text or 'अज्ञात'}
साझाकर्ता: {slots.who_sharing or 'नागरिक'}"""

        else:
            return "निजी नोट"

    def get_next_steps_message(
        self,
        entity_name: str,
        entity_type: str,
        escalation_entity: Optional[str] = None
    ) -> str:
        """
        Generate "Agla Kya Hoga" message

        Args:
            entity_name: Responsible office name
            entity_type: Entity type (gp/block/district/dept)
            escalation_entity: Next escalation level entity

        Returns:
            Formatted next steps message in Hindi
        """
        sla_hours = SLA_TIMINGS.get(entity_type, 72)
        template = NEXT_STEPS_TEMPLATES.get(entity_type, NEXT_STEPS_TEMPLATES["gp"])

        return template.format(
            entity_name=entity_name,
            sla_hours=sla_hours,
            escalation_entity=escalation_entity or "उच्च अधिकारी",
            contact_phone="1800-XXX-XXXX"
        )

    def get_status_message(
        self,
        status: str,
        entity_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get status message in plain Hindi

        Args:
            status: Status key (submitted/acknowledged/in_progress/etc)
            entity_name: Entity name for templating
            **kwargs: Additional template variables

        Returns:
            Status message in Hindi
        """
        template = STATUS_MESSAGES.get(status, "स्थिति अज्ञात")

        return template.format(
            entity_name=entity_name or "कार्यालय",
            **kwargs
        )

    def get_who_has_ball_message(self, ball_holder: str, **kwargs) -> str:
        """
        Get "who has the ball" message

        Args:
            ball_holder: Who currently has responsibility (citizen/moderator/officer/system)
            **kwargs: Additional template variables

        Returns:
            Message in Hindi
        """
        template = WHO_HAS_BALL.get(ball_holder, "प्रक्रिया में...")
        return template.format(**kwargs)


# Global singleton instance
conversation_service = ConversationService()
