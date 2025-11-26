"""
Chat Router - ChatGPT-like Conversational Interface for AI Coach

Provides endpoints for natural conversational reporting with text and voice support.
Replaces the structured multi-screen flow with a single chat interface.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
import tempfile
import os
from rapidfuzz import fuzz

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user, get_current_user_or_dev
from app.services.ai_coach_conversation_service import (
    get_ai_coach_conversation_service,
    AICoachConversationServiceError
)
from app.services.transcription_service import transcription_service
from app.services.completeness_analyzer import get_completeness_analyzer
from app.services.training_service import get_training_service
from app.routers.triage import TriageRequest
from app.services.claude_service import get_claude_service
from app.services.azure_openai_service import (
    get_azure_openai_service,
    AzureOpenAIServiceError
)
from app.services.journalist_summary import (
    generate_journalist_summary,
    generate_journalist_summary_english
)
# BUG FIX #1 & #4: Import question tracking and Hindi response detection utilities
from app.utils.question_tracker import QuestionTracker
from app.utils.hindi_response_detector import get_hindi_response_detector
# Smart location confirmation utilities
from app.utils.location_confirmation import (
    is_location_confirmation,
    is_location_rejection,
    format_location_display,
    merge_location_with_profile,
    has_meaningful_location,
    extract_location_from_user_profile
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["chat"])

# Constants for security and DoS prevention
MAX_AUDIO_BYTES = 6 * 1024 * 1024  # 6MB max audio file size

# FSM: Slot-filling state machine for structured data collection
REQUIRED_SLOTS = ("issue_description", "location", "evidence_urls")

ALLOWED_TRANSITIONS = {
    None: ("issue_description", "location"),              # Start state
    "issue_description": ("location", "evidence_urls"),   # After issue described
    "location": ("evidence_urls",),                       # After location provided
    "evidence_urls": (),                                  # Terminal state
}


def is_duplicate_question(new_question: str, previous_questions: list[str], threshold: int = 85) -> bool:
    """
    Check if a new question is a duplicate of any previously asked question.

    Uses fuzzy string matching (rapidfuzz) to detect similar questions even with different phrasing.

    Args:
        new_question: The new question to check
        previous_questions: List of previously asked questions
        threshold: Similarity threshold (0-100), default 85% match

    Returns:
        True if the question is a duplicate (similarity >= threshold), False otherwise
    """
    if not new_question or not previous_questions:
        return False

    for prev_question in previous_questions:
        if not prev_question:
            continue
        # Use partial_ratio for more flexible matching (handles substring matches)
        similarity = fuzz.partial_ratio(new_question.lower(), prev_question.lower())
        if similarity >= threshold:
            logger.debug(f"[Chat] Duplicate question detected: '{new_question}' ~= '{prev_question}' (similarity: {similarity}%)")
            return True

    return False


def _looks_like_question(text: str) -> bool:
    """
    Check if text looks like a question (to avoid polluting question history with statements).

    Args:
        text: Text to check

    Returns:
        True if text appears to be a question, False otherwise
    """
    if not text:
        return False

    text_stripped = text.strip()

    # Check for question mark
    if text_stripped.endswith("?") or "?" in text_stripped[-3:]:
        return True

    # Check for Hindi interrogatives at start
    hindi_interrogatives = ["क्या", "कहाँ", "कब", "कैसे", "किस", "कौन", "क्यों", "कितना", "कितने"]
    text_start = text_stripped[:15].lower()
    if any(interrog in text_start for interrog in hindi_interrogatives):
        return True

    return False


def _pick_next_field_to_ask(
    actually_missing_fields: list,
    already_asked_fields: list,
    extracted_data: dict
) -> Optional[str]:
    """
    HARD GATE: Pick exactly ONE safe field to ask next (or None).

    This prevents Azure from asking about multiple fields or sneaking in duplicate questions.

    Args:
        actually_missing_fields: List of missing field dicts from completeness analyzer
        already_asked_fields: List of field names already asked about
        extracted_data: Data already collected

    Returns:
        Field name to ask about, or None if nothing safe to ask

    Example:
        >>> _pick_next_field_to_ask(
        ...     [{"field": "location"}, {"field": "when_started"}],
        ...     ["issue_description"],
        ...     {"issue_description": "पानी नहीं आता"}
        ... )
        "location"  # Returns first critical field not yet asked
    """
    if not actually_missing_fields:
        return None

    # Priority order: critical > high > medium > low
    # ONLY ask about critical/high fields. Skip low-importance fields to avoid confusion.
    priority_order = ["critical", "high", "medium"]  # Removed "low" - don't ask about nice-to-have fields

    # Context-aware filtering: skip irrelevant fields
    # Example: If service is broken (doesn't work at all), skip frequency questions
    issue_desc = str(extracted_data.get("issue_description", "")).lower()
    is_broken_service = any(
        keyword in issue_desc
        for keyword in ["नहीं", "टूटा", "ख़राब", "बंद", "not working", "broken"]
    )

    for priority in priority_order:
        # Find fields with this priority that haven't been asked yet
        for field_dict in actually_missing_fields:
            field_name = field_dict.get("field")
            field_importance = field_dict.get("importance", "medium")

            # Skip if already asked
            if field_name in already_asked_fields:
                continue

            # Skip if wrong priority
            if field_importance != priority:
                continue

            # Context-aware skip: Don't ask frequency if service is completely broken
            if is_broken_service and "frequency" in field_name:
                logger.debug(
                    f"[HARD GATE] Skipping '{field_name}' because service is broken "
                    f"(issue: {issue_desc[:50]}...)"
                )
                continue

            # This is a safe field to ask
            logger.info(f"[HARD GATE] ✅ Selected safe field to ask: '{field_name}' (priority: {priority})")
            return field_name

    # No safe fields to ask
    logger.info("[HARD GATE] No safe fields to ask (all already asked or irrelevant)")
    return None


def next_legal_slot(last_slot: Optional[str], collected: set[str]) -> Optional[str]:
    """
    Determine next legal slot based on FSM transitions.

    Args:
        last_slot: The slot we just filled (or None for start)
        collected: Set of slot names already collected

    Returns:
        Next legal slot name, or None if no valid transitions
    """
    for candidate_slot in ALLOWED_TRANSITIONS.get(last_slot, ()):
        if candidate_slot not in collected:
            return candidate_slot
    return None


def _is_dup_text(current: str, priors: list[str]) -> bool:
    """
    Fuzzy duplicate detection using rapidfuzz.

    Args:
        current: Current question text
        priors: List of previously asked questions

    Returns:
        True if current matches any prior question (>= 85% similarity)
    """
    if not current or not priors:
        return False

    cur_normalized = current.strip().lower().rstrip('?।')

    for prior in priors:
        prior_normalized = prior.strip().lower().rstrip('?।')
        similarity = fuzz.token_set_ratio(cur_normalized, prior_normalized)

        if similarity >= 85:  # 85% similarity threshold
            logger.info(f"[Fuzzy Dup] Match found: '{current[:40]}' ~= '{prior[:40]}' ({similarity}%)")
            return True

    return False


# Option B: Minimum fields for submission (replaces rigid FSM)
MINIMUM_REQUIRED_FIELDS = ["issue_description", "location"]
ALL_FIELDS = [
    "issue_description",
    "location",
    "reporter_name",
    "phone",
    "actions_taken",
    "evidence_urls"
]


def is_meaningful_issue_description(text: str) -> bool:
    """
    Validate that issue_description is a meaningful problem description.

    Rejects:
    - Generic phrases like "बोल रहा हूँ", "speaking", "मैं हूँ"
    - Location-only descriptions
    - Too short descriptions (< 5 words)
    - Descriptions without problem indicators

    Args:
        text: The issue description text

    Returns:
        True if text describes an actual problem
    """
    if not text or not str(text).strip():
        return False

    text = str(text).strip()

    # Minimum length check (at least 5 words)
    words = text.split()
    if len(words) < 5:
        return False

    # Problem indicator keywords (Hindi/English)
    problem_keywords = [
        # Hindi problem indicators
        'समस्या', 'परेशानी', 'दिक्कत', 'तकलीफ', 'शिकायत',
        'नहीं', 'ठीक', 'खराब', 'बंद', 'गंदा', 'टूटा',
        'काम नहीं', 'आती नहीं', 'मिल नहीं', 'हो नहीं',
        'बिजली', 'पानी', 'सड़क', 'नाली', 'कचरा',
        # English problem indicators
        'problem', 'issue', 'not working', 'broken', 'damaged',
        'no water', 'no electricity', 'road', 'drain', 'garbage'
    ]

    # Check if text contains at least one problem indicator
    text_lower = text.lower()
    has_problem_keyword = any(keyword in text_lower for keyword in problem_keywords)

    if not has_problem_keyword:
        return False

    # Reject generic non-problem phrases
    generic_phrases = [
        'बोल रहा हूँ', 'बोल रही हूँ', 'speaking', 'calling from',
        'से हूँ', 'मैं हूँ', 'i am from', 'यहाँ से', 'का रहने वाला'
    ]

    for phrase in generic_phrases:
        if phrase in text_lower and len(words) < 10:
            return False

    return True


def is_valid_field_value(field_name: str, value: Any) -> bool:
    """
    Validate that a field value is meaningful and not a placeholder.

    Rejects common placeholder values like:
    - "unknown", "not provided", "n/a", "missing"
    - Too short values (< 2 chars for most fields)
    - Generic non-specific values

    Args:
        field_name: Name of the field being validated
        value: The field value to validate

    Returns:
        True if value is meaningful and valid for the field
    """
    if not value or not str(value).strip():
        return False

    value_str = str(value).strip().lower()

    # Reject common placeholder values
    invalid_placeholders = [
        'unknown', 'not provided', 'n/a', 'na', 'missing', 'none',
        'पता नहीं', 'मालूम नहीं', 'नहीं पता', 'not known',
        'to be determined', 'tbd', '?', '-', 'not specified'
    ]

    if value_str in invalid_placeholders:
        logger.warning(f"[Chat] ⚠️ Field '{field_name}' has invalid placeholder value: '{value_str}'")
        return False

    # Minimum length check (at least 2 characters for most fields)
    if len(value_str) < 2:
        return False

    # Field-specific validation
    if field_name == "location":
        # Location must have some geographical indicators
        location_indicators = [
            'village', 'block', 'district', 'ward', 'गाँव', 'ग्राम', 'ब्लॉक',
            'जिला', 'वार्ड', 'पंचायत', 'नगर', 'शहर', 'क्षेत्र'
        ]
        has_location_indicator = any(indicator in value_str for indicator in location_indicators)
        if not has_location_indicator and len(value_str) < 5:
            logger.warning(f"[Chat] ⚠️ Location too vague: '{value_str}'")
            return False

    return True


def can_submit_now(extracted_data: Dict[str, Any]) -> bool:
    """
    Check if minimum fields are present AND VALID for submission (Option B).

    User can submit with just location + issue_description, BUT:
    - issue_description must be a MEANINGFUL problem description (not just location info)
    - location must be a MEANINGFUL location (not "unknown" or placeholders)
    - Both fields must have substantive content

    This prevents false positives when user only mentions location or when AI uses placeholders.

    Args:
        extracted_data: Dictionary of extracted field values

    Returns:
        True if minimum fields present, non-empty, AND semantically valid
    """
    # BUG FIX #7: Check all minimum fields exist, are non-empty, AND are valid values (not placeholders)
    for field in MINIMUM_REQUIRED_FIELDS:
        if field not in extracted_data or not extracted_data[field]:
            logger.warning(f"[Chat] ⚠️ Submission blocked: '{field}' is missing")
            return False
        if not str(extracted_data[field]).strip():
            logger.warning(f"[Chat] ⚠️ Submission blocked: '{field}' is empty")
            return False
        # BUG FIX #7: Validate field value is not a placeholder like "unknown"
        if not is_valid_field_value(field, extracted_data[field]):
            logger.warning(f"[Chat] ⚠️ Submission blocked: '{field}' has invalid value: '{str(extracted_data[field])[:30]}'")
            return False

    # CRITICAL: Semantic validation for issue_description
    # Prevent submission when user only mentioned location
    issue_desc = str(extracted_data.get("issue_description", "")).strip()
    if not is_meaningful_issue_description(issue_desc):
        logger.warning(f"[Chat] ⚠️ OPTION B: Rejected issue_description as non-meaningful: '{issue_desc[:50]}'")
        return False

    # All validations passed
    logger.info(f"[Chat] ✅ Submission allowed: All minimum fields are valid and meaningful")
    return True


def create_preview_card(extracted_data: Dict[str, Any], user_phone: Optional[str] = None) -> Optional["PreviewCard"]:
    """
    Create preview card showing what will be submitted (Option B).

    Shows user exactly what data will be submitted before final confirmation.
    Builds trust and allows user to verify accuracy.

    Args:
        extracted_data: Dictionary of extracted field values
        user_phone: User's phone number (from auth context)

    Returns:
        PreviewCard object or None if minimum fields not present
    """
    if not can_submit_now(extracted_data):
        return None

    return PreviewCard(
        location=extracted_data.get("location"),
        issue_description=extracted_data.get("issue_description"),
        reporter_name=extracted_data.get("reporter_name"),
        phone=user_phone or extracted_data.get("phone"),
        actions_taken=extracted_data.get("actions_taken")
    )


# Response Models
class ChatStartResponse(BaseModel):
    """Response when starting a new chat conversation"""
    success: bool
    conversation_id: str
    greeting_hi: str
    greeting_en: str
    in_training_mode: bool
    # NEW: Profile location info for smart confirmation
    profile_location_available: bool = False
    profile_location_formatted: Optional[str] = None


class PreviewCard(BaseModel):
    """Preview card showing what will be submitted"""
    location: Optional[str] = None
    issue_description: Optional[str] = None
    reporter_name: Optional[str] = None
    phone: Optional[str] = None
    actions_taken: Optional[str] = None


class ChatTurnResponse(BaseModel):
    """Response for a chat turn (text or voice)"""
    success: bool
    conversation_id: str
    turn_number: int

    # User input
    user_message: str
    language_detected: str

    # AI response (AUTHORITATIVE - frontend must use these)
    ai_response_hi: str
    ai_response_en: str

    # Completeness analysis
    completeness_score: float
    is_complete: bool
    collected_fields: list  # Field names that have been collected
    missing_fields: list    # Missing field objects with prompts
    extracted_data: Dict[str, Any]  # ACTUAL VALUES: {field_name: user_value}

    # Continuation
    should_continue: bool
    ready_for_submission: bool

    # NEW: UX Enhancement flags (Option B implementation)
    show_submit_button: bool = False  # Show submit button immediately if minimum fields present
    show_skip_button: bool = False    # Allow skipping this question
    preview_card: Optional[PreviewCard] = None  # Preview of what will be submitted

    error: Optional[str] = None


class ChatSummaryResponse(BaseModel):
    """Response with conversation summary for confirmation"""
    success: bool
    conversation_id: str
    summary_hi: str  # Keep for backwards compatibility
    summary_en: str  # Keep for backwards compatibility
    narrative_summary_hi: str  # NEW - Journalist-style narrative in Hindi
    narrative_summary_en: str  # NEW - Journalist-style narrative in English
    completeness_score: float
    collected_fields: list  # Field names
    missing_fields: list
    extracted_data: Dict[str, Any]  # ACTUAL VALUES for display
    detected_taxonomy: Optional[Dict[str, Any]] = None


class ChatSubmitResponse(BaseModel):
    """Response after submitting report"""
    success: bool
    case_id: Optional[str] = None
    submitted_to_moderator: bool
    training_progress: Optional[Dict[str, Any]] = None
    message_hi: str
    message_en: str


@router.post("/start", response_model=ChatStartResponse)
async def start_chat_conversation(
    user_id: str,
    language: str = "hi",
    db: Session = Depends(get_db)
):
    """
    Start a new chat conversation with AI Coach.

    Returns greeting message to initiate conversation.

    Args:
        user_id: User UUID
        language: Preferred language (hi/en)
        db: Database session

    Returns:
        ChatStartResponse with greeting and conversation ID
    """
    try:
        user_uuid = UUID(user_id)

        # Get user
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Check training status
        training_service = get_training_service(db)
        in_training_mode = training_service.is_in_training_mode(user)

        # Create new conversation
        conversation_service = get_ai_coach_conversation_service(db)
        conversation = conversation_service.create_conversation(
            user_id=user_uuid
        )

        # CHECK USER PROFILE LOCATION (Smart Location Confirmation)
        # QUADRUPLE-LAYER DEFENSE: Absolutely prevent None from reaching Pydantic
        # BUGFIX: Explicit None coalescing at every step to handle DB columns that don't exist yet
        has_profile_location = False  # DEFAULT: Always start with False

        try:
            profile_location = extract_location_from_user_profile(user)
            if profile_location is None:
                has_profile_location = False
                logger.debug(f"[Location] No profile location data for user {user_id}")
            else:
                try:
                    has_meaningful = has_meaningful_location(profile_location)
                    # CRITICAL FIX: Triple None coalescing to handle any edge case
                    # If has_meaningful is None, False, or any falsy value → False
                    # If has_meaningful is True or truthy → True
                    has_profile_location = bool(has_meaningful) if has_meaningful is not None else False
                    logger.debug(f"[Location] has_meaningful_location returned: {has_meaningful} (type: {type(has_meaningful)})")
                except Exception as e:
                    logger.error(f"[Location] Error in has_meaningful_location: {e}", exc_info=True)
                    has_profile_location = False
        except Exception as e:
            logger.error(f"[Location] Error extracting profile location: {e}", exc_info=True)
            has_profile_location = False

        # ASSERTION: Guarantee boolean type before Pydantic validation
        assert isinstance(has_profile_location, bool), \
            f"BUG: has_profile_location must be bool, got {type(has_profile_location).__name__}={has_profile_location}"

        profile_location_formatted = None
        greeting_hi = None
        greeting_en = None

        if has_profile_location:
            # Format location for display
            profile_location_formatted = format_location_display(
                street=profile_location.get("street"),
                village=profile_location.get("village"),
                panchayat=profile_location.get("panchayat"),
                block=profile_location.get("block"),
                subdivision=profile_location.get("subdivision"),
                district=profile_location.get("district"),
                state=profile_location.get("state")
            )

            # Store in conversation session_metadata for later use
            conversation.session_metadata = {
                "profile_location_available": True,
                "profile_location_formatted": profile_location_formatted,
                "profile_location_confirmed": False,  # Will be set to True when user confirms
                "location_data": profile_location
            }
            db.commit()

            # Generate greeting WITH location confirmation
            greeting_hi = f"""नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ।

आपके प्रोफाइल में यह पता दर्ज है:
📍 {profile_location_formatted}

क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?

अगर समस्या किसी अलग जगह पर है (जैसे गाँव के किसी दूसरे क्षेत्र में), तो कृपया वह नया पता बताएं।"""

            greeting_en = f"""Hello! I'm here to help you.

Your profile has this address:
📍 {profile_location_formatted}

Should we use this address for this report?

If the issue is at a different location (like a different area in the village), please let me know the new address."""

            logger.info(f"[Chat Start] User has profile location: {profile_location_formatted[:50]}...")

        else:
            # No profile location → Use default greeting
            greetings = conversation_service.generate_greeting(language)
            greeting_hi = greetings["hi"]
            greeting_en = greetings["en"]

            logger.info(f"[Chat Start] No profile location available for user {user_id}")

        logger.info(f"Started chat conversation {conversation.id} for user {user_id}")

        # FINAL SAFETY CHECK: Explicit type conversion with assertion
        profile_location_bool = bool(has_profile_location)
        assert isinstance(profile_location_bool, bool), \
            f"BUG: profile_location_bool must be bool, got {type(profile_location_bool)}"

        logger.info(f"[Chat Start] Creating response: has_profile_location={profile_location_bool}")

        return ChatStartResponse(
            success=True,
            conversation_id=str(conversation.id),
            greeting_hi=greeting_hi,
            greeting_en=greeting_en,
            in_training_mode=in_training_mode,
            # GUARANTEED boolean value (triple-checked above)
            profile_location_available=profile_location_bool,
            profile_location_formatted=profile_location_formatted
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting chat conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )


@router.post("/turn", response_model=ChatTurnResponse)
async def process_chat_turn(
    conversation_id: str = Form(...),
    user_id: str = Form(...),  # Keep for backward compatibility, but verify with current_user
    text_message: Optional[str] = Form(default=None),
    audio: Optional[UploadFile] = File(default=None),
    language: str = Form(default="hi-IN"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user_or_dev),  # Allow dev mode bypass
    db: Session = Depends(get_db)
):
    """
    Process a chat turn - either text or voice input.

    Handles:
    1. Text message or voice transcription
    2. Completeness analysis
    3. AI response generation
    4. Follow-up question (if incomplete)

    Args:
        conversation_id: Conversation UUID
        user_id: User UUID
        text_message: Optional text message (if user typed)
        audio: Optional audio file (if user used voice)
        language: Language code
        db: Database session

    Returns:
        ChatTurnResponse with AI response and completeness analysis
    """
    temp_file_path = None

    try:
        # FIX #1: Track which field/question we decided to ask so we can persist it after we create `turn`
        pending_question_to_record = None  # (field_name, question_text)
        field_name_asked_about = None  # Track explicitly for fallback path

        user_uuid = UUID(user_id)
        conv_uuid = UUID(conversation_id)

        # Validate inputs
        if not text_message and not audio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either text_message or audio must be provided"
            )

        # Get user message (transcribe if audio)
        if audio:
            # DoS Prevention: Check audio file size
            if hasattr(audio, "size") and audio.size and audio.size > MAX_AUDIO_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error": "AUDIO_TOO_LARGE",
                        "message_hi": f"ऑडियो फ़ाइल बहुत बड़ी है। अधिकतम {MAX_AUDIO_BYTES // (1024*1024)}MB की अनुमति है।",
                        "message_en": f"Audio file too large. Maximum {MAX_AUDIO_BYTES // (1024*1024)}MB allowed."
                    }
                )

            # Validate file type
            allowed_extensions = [".m4a", ".wav", ".mp3", ".ogg", ".webm"]
            file_ext = os.path.splitext(audio.filename)[1].lower()

            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported audio format: {file_ext}"
                )

            # Save and transcribe audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file_path = temp_file.name
                content = await audio.read()
                temp_file.write(content)

            # Register background cleanup to prevent disk space leaks
            background_tasks.add_task(
                lambda p=temp_file_path: os.unlink(p) if os.path.exists(p) else None
            )

            logger.info(f"[Chat] Transcribing audio for conversation {conversation_id}")
            transcription_result = await transcription_service.transcribe_audio(
                audio_file_path=temp_file_path,
                language=language,
                enable_auto_language_detection=True
            )

            if not transcription_result["success"]:
                error_detail = transcription_result.get("error", "Transcription failed")
                logger.warning(f"[Chat] Transcription failed: {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": error_detail,
                        "message_hi": "आवाज़ में कोई बोल नहीं सुनाई दिया। कृपया फिर से बोलें।",
                        "message_en": "No speech detected in audio. Please try again."
                    }
                )

            user_message = transcription_result["transcript"]
            language_detected = transcription_result.get("language_detected", "hi")
        else:
            user_message = text_message
            language_detected = "hi" if language.startswith("hi") else "en"

        logger.info(f"[Chat] Processing turn for conversation {conversation_id}: {user_message[:100]}")

        # Get conversation service
        conversation_service = get_ai_coach_conversation_service(db)
        conversation = conversation_service.get_conversation(conv_uuid)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        # Security: Verify ownership (prevent unauthorized access)
        if str(conversation.user_id) != str(current_user.id):
            logger.warning(f"[Security] User {current_user.id} attempted to access conversation {conversation_id} owned by {conversation.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this conversation"
            )

        # Get conversation history for context
        history = conversation_service.get_conversation_history_for_ai(conv_uuid)

        # SMART LOCATION CONFIRMATION: Check if profile location was offered
        # BUGFIX: Ensure session_metadata is a dict (avoid SQLAlchemy MetaData class collision)
        session_meta = conversation.session_metadata
        if not isinstance(session_meta, dict):
            conversation_metadata = {}
        else:
            conversation_metadata = session_meta or {}

        profile_location_available = conversation_metadata.get("profile_location_available", False)
        profile_location_confirmed = conversation_metadata.get("profile_location_confirmed", False)

        # Get accumulated extracted data from previous turns (STATEFUL)
        # This is critical for avoiding repeated questions
        accumulated_data = {}
        if conversation.extracted_data:
            # CRITICAL FIX: Validate and recover JSONB data to prevent silent data loss
            if isinstance(conversation.extracted_data, dict):
                accumulated_data = conversation.extracted_data
                logger.info(f"[Chat] ✅ Successfully loaded accumulated data: {list(accumulated_data.keys())}")
            else:
                # RACE CONDITION DETECTED: extracted_data is corrupted
                logger.error(
                    f"🚨 CRITICAL: JSONB extracted_data corruption detected! "
                    f"Type: {type(conversation.extracted_data)}, "
                    f"Value: {str(conversation.extracted_data)[:100]}"
                )

                # Attempt to recover partial data
                try:
                    import json
                    if isinstance(conversation.extracted_data, str):
                        accumulated_data = json.loads(conversation.extracted_data)
                        logger.warning(
                            f"⚠️  RECOVERED corrupted JSONB data from string. "
                            f"Fields recovered: {list(accumulated_data.keys())}"
                        )
                    else:
                        # Cannot recover - notify user
                        logger.error(
                            f"❌ FAILED to recover JSONB data. User will need to re-answer questions. "
                            f"Conversation ID: {conversation_id}"
                        )
                        accumulated_data = {}
                except Exception as recovery_error:
                    logger.error(
                        f"❌ JSONB recovery attempt failed: {recovery_error}. "
                        f"Data permanently lost for conversation {conversation_id}"
                    )
                    accumulated_data = {}
        else:
            logger.info(f"[Chat] No accumulated data yet (new conversation)")

        # SMART LOCATION CONFIRMATION: Handle location confirmation if offered
        if profile_location_available and not profile_location_confirmed:
            logger.info(f"[Chat] 📍 Profile location offered but not yet confirmed")

            # Check if user is confirming the location
            if is_location_confirmation(user_message):
                logger.info(f"[Chat] ✅ User confirmed profile location!")

                # Auto-fill location from profile
                location_data = conversation_metadata.get("location_data", {})

                accumulated_data["location"] = conversation_metadata.get("profile_location_formatted")
                accumulated_data["location_street"] = location_data.get("street")
                accumulated_data["location_village"] = location_data.get("village")
                accumulated_data["location_panchayat"] = location_data.get("panchayat")
                accumulated_data["location_block"] = location_data.get("block")
                accumulated_data["location_subdivision"] = location_data.get("subdivision")
                accumulated_data["location_district"] = location_data.get("district")
                accumulated_data["location_state"] = location_data.get("state")
                accumulated_data["location_lat"] = location_data.get("lat")
                accumulated_data["location_lng"] = location_data.get("lng")

                # Mark as confirmed in session_metadata
                conversation_metadata["profile_location_confirmed"] = True
                conversation.session_metadata = conversation_metadata

                # Update conversation with location data
                conversation.extracted_data = accumulated_data
                db.commit()

                logger.info(f"[Chat] 📍 Auto-filled location: {accumulated_data.get('location', '')[:50]}...")

                # Acknowledge and ask for issue description
                ai_response_hi = "धन्यवाद! अब कृपया बताएं कि क्या समस्या है?"
                ai_response_en = "Thank you! Now please tell me what the issue is?"

                # Add turn to conversation
                turn = conversation_service.add_turn(
                    conversation_id=conv_uuid,
                    transcript_text=user_message,
                    audio_url=None,
                    language_detected=language_detected,
                    ai_response=ai_response_hi,
                    ai_question_asked=ai_response_hi,
                    fields_extracted={"location": accumulated_data.get("location")}
                )

                # Re-analyze completeness with the new location data
                completeness_analyzer = get_completeness_analyzer()
                completeness_result = completeness_analyzer.analyze_completeness(
                    transcript=user_message,
                    conversation_history=history,
                    already_collected_fields=accumulated_data,
                    question_tracker=None  # Skip question tracking for this confirmation turn
                )

                # Update conversation completeness
                conversation_service.update_completeness(
                    conversation_id=conv_uuid,
                    completeness_score=completeness_result["completeness_score"],
                    collected_fields=completeness_result["collected_fields"],
                    missing_fields=completeness_result["missing_fields"],
                    extracted_data=completeness_result["extracted_data"]
                )

                return ChatTurnResponse(
                    success=True,
                    conversation_id=str(conversation.id),
                    turn_number=turn.turn_number,
                    user_message=user_message,
                    language_detected=language_detected,
                    ai_response_hi=ai_response_hi,
                    ai_response_en=ai_response_en,
                    completeness_score=completeness_result["completeness_score"],
                    is_complete=completeness_result["is_complete"],
                    collected_fields=completeness_result["collected_fields"],
                    missing_fields=completeness_result["missing_fields"],
                    extracted_data=completeness_result["extracted_data"],
                    should_continue=not completeness_result["is_complete"],
                    ready_for_submission=completeness_result["is_complete"],
                    show_submit_button=can_submit_now(completeness_result["extracted_data"]),
                    show_skip_button=completeness_result["completeness_score"] > 0.5,
                    preview_card=create_preview_card(completeness_result["extracted_data"], user_phone=current_user.phone)
                )

            elif is_location_rejection(user_message):
                logger.info(f"[Chat] ❌ User rejected profile location or providing alternative")

                # Mark as not confirmed (user wants to provide different location)
                conversation_metadata["profile_location_confirmed"] = False
                conversation_metadata["profile_location_used"] = False
                conversation.session_metadata = conversation_metadata
                db.commit()

                # Let the normal completeness analysis handle the new location extraction
                # The location from user's message will be extracted and possibly merged
                logger.info(f"[Chat] 🔄 Will extract alternative location from user's message")

        # BUG FIX #1: Initialize question tracker from conversation history
        question_tracker = QuestionTracker.from_conversation_history(history)
        logger.info(f"[Chat] Question tracker initialized: {len(question_tracker.get_all_asked_fields())} fields already asked about")

        # BUG FIX #4: Check user's response sentiment (Haa/Nahi/Kar dijiye/Frustration)
        response_detector = get_hindi_response_detector()
        user_sentiment = response_detector.detect(user_message)
        logger.info(f"[Chat] User sentiment detected: {user_sentiment['type']} (confidence: {user_sentiment['confidence']:.2f})")

        # CRITICAL FIX #7: Count frustration events to prevent infinite loops
        MAX_FRUSTRATION_RETRIES = 1  # EMERGENCY FIX: Reduced from 2 to 1 to prevent repetitive questioning loops
        frustration_count = 0

        # Get list of previously asked questions for duplicate detection
        previously_asked_questions = []
        if conversation.turns:
            # Count how many times user has been frustrated in this conversation
            for turn in conversation.turns:
                # Track asked questions
                if turn.ai_question_asked:
                    previously_asked_questions.append(turn.ai_question_asked)

                # Check if this turn's AI response was a "frustrated but asking gently" response
                if turn.ai_response and "बस एक आखिरी जानकारी चाहिए" in turn.ai_response:
                    frustration_count += 1

        # Also count duplicate questions as frustration events (user had to answer same thing twice)
        duplicate_question_count = 0
        for i in range(len(previously_asked_questions)):
            for j in range(i + 1, len(previously_asked_questions)):
                if is_duplicate_question(previously_asked_questions[j], [previously_asked_questions[i]]):
                    duplicate_question_count += 1
                    break  # Only count each duplicate once

        total_frustration = frustration_count + duplicate_question_count
        logger.info(f"[Chat] Frustration count in this conversation: explicit={frustration_count}, duplicates={duplicate_question_count}, total={total_frustration}/{MAX_FRUSTRATION_RETRIES}")

        # BUG FIX #4 & #5: If user is frustrated or wants to proceed, stop asking questions
        if user_sentiment["should_stop_asking"]:
            logger.warning(f"[Chat] 🛑 User sentiment: {user_sentiment['type']} - stopping further questions!")
            logger.warning(f"[Chat] Message: {user_sentiment['message']}")
            # Check if we have minimum fields to submit
            if can_submit_now(accumulated_data):
                logger.info(f"[Chat] ✅ User wants to proceed and minimum fields present - allowing submission")
                # Generate confirmation message and show preview
                preview = create_preview_card(accumulated_data, user_phone=current_user.phone)
                ai_response_hi = f"बहुत अच्छा! मैं समझ गया। आप अभी अपनी रिपोर्ट सबमिट कर सकते हैं।"
                ai_response_en = f"Great! I understand. You can submit your report now."

                # Add turn to conversation
                turn = conversation_service.add_turn(
                    conversation_id=conv_uuid,
                    transcript_text=user_message,
                    audio_url=None,
                    language_detected=language_detected,
                    ai_response=ai_response_hi,
                    ai_question_asked=None,  # No question asked
                    fields_extracted={}
                )

                return ChatTurnResponse(
                    success=True,
                    conversation_id=str(conversation.id),
                    turn_number=turn.turn_number,
                    user_message=user_message,
                    language_detected=language_detected,
                    ai_response_hi=ai_response_hi,
                    ai_response_en=ai_response_en,
                    completeness_score=1.0,
                    is_complete=True,
                    collected_fields=list(accumulated_data.keys()),
                    missing_fields=[],
                    extracted_data=accumulated_data,
                    should_continue=False,
                    ready_for_submission=True,
                    show_submit_button=True,
                    show_skip_button=False,
                    preview_card=preview
                )
            else:
                # CRITICAL FIX #7: Frustration Escalation Path
                # User wants to proceed but minimum fields missing

                if total_frustration >= MAX_FRUSTRATION_RETRIES:
                    # ESCALATION: User has been frustrated too many times - FORCE submission
                    logger.error(
                        f"[Chat] 🚨 FRUSTRATION LIMIT REACHED ({total_frustration}/{MAX_FRUSTRATION_RETRIES})! "
                        f"Forcing submission with incomplete data to prevent user abandonment."
                    )

                    # Generate preview with whatever data we have
                    preview = create_preview_card(accumulated_data, user_phone=current_user.phone)

                    ai_response_hi = (
                        "मैं समझता हूँ, आप व्यस्त हैं। कोई बात नहीं! "
                        "मैंने जो जानकारी मिली है उसके साथ आपकी रिपोर्ट सबमिट कर देता हूँ। "
                        "बाद में आप और जानकारी जोड़ सकते हैं। धन्यवाद!"
                    )
                    ai_response_en = (
                        "I understand you're busy. No problem! "
                        "I'll submit your report with the information I have. "
                        "You can add more details later. Thank you!"
                    )

                    turn = conversation_service.add_turn(
                        conversation_id=conv_uuid,
                        transcript_text=user_message,
                        audio_url=None,
                        language_detected=language_detected,
                        ai_response=ai_response_hi,
                        ai_question_asked=None,
                        fields_extracted={}
                    )

                    return ChatTurnResponse(
                        success=True,
                        conversation_id=str(conversation.id),
                        turn_number=turn.turn_number,
                        user_message=user_message,
                        language_detected=language_detected,
                        ai_response_hi=ai_response_hi,
                        ai_response_en=ai_response_en,
                        completeness_score=0.7,  # Mark as reasonably complete
                        is_complete=True,  # Force completion
                        collected_fields=list(accumulated_data.keys()),
                        missing_fields=[],
                        extracted_data=accumulated_data,
                        should_continue=False,
                        ready_for_submission=True,
                        show_submit_button=True,
                        show_skip_button=False,
                        preview_card=preview
                    )
                else:
                    # Still within retry limit - ask gently ONE MORE TIME
                    logger.warning(
                        f"[Chat] ⚠️ User frustrated but minimum fields missing "
                        f"(retry {total_frustration + 1}/{MAX_FRUSTRATION_RETRIES}) - acknowledging and asking gently"
                    )
                    ai_response_hi = "मैं समझता हूँ। बस एक आखिरी जानकारी चाहिए: कहाँ की समस्या है और क्या समस्या है? फिर हम तुरंत रिपोर्ट सबमिट कर देंगे।"
                    ai_response_en = "I understand. Just need one last thing: where is the problem and what is the problem? Then we'll submit immediately."

                    turn = conversation_service.add_turn(
                        conversation_id=conv_uuid,
                        transcript_text=user_message,
                        audio_url=None,
                        language_detected=language_detected,
                        ai_response=ai_response_hi,
                        ai_question_asked=ai_response_hi,
                        fields_extracted={}
                    )

                    return ChatTurnResponse(
                        success=True,
                        conversation_id=str(conversation.id),
                        turn_number=turn.turn_number,
                        user_message=user_message,
                        language_detected=language_detected,
                        ai_response_hi=ai_response_hi,
                        ai_response_en=ai_response_en,
                        completeness_score=0.5,
                        is_complete=False,
                        collected_fields=list(accumulated_data.keys()),
                        missing_fields=MINIMUM_REQUIRED_FIELDS,
                        extracted_data=accumulated_data,
                        should_continue=True,
                        ready_for_submission=False,
                        show_submit_button=False,
                        show_skip_button=True
                    )

        # Analyze completeness with STATEFUL merging
        completeness_analyzer = get_completeness_analyzer()
        completeness_result = completeness_analyzer.analyze_completeness(
            transcript=user_message,
            conversation_history=history,
            already_collected_fields=accumulated_data,  # Pass accumulated fields
            question_tracker=question_tracker  # BUG FIX #1: Pass question tracker to avoid repeating questions
        )

        logger.info(f"[Chat] Merged collected fields: {completeness_result['collected_fields']}")
        logger.info(f"[Chat] Missing fields: {[f.get('field') for f in completeness_result['missing_fields']]}")

        # Update conversation with MERGED completeness (old + new)
        conversation_service.update_completeness(
            conversation_id=conv_uuid,
            completeness_score=completeness_result["completeness_score"],
            collected_fields=completeness_result["collected_fields"],
            missing_fields=completeness_result["missing_fields"],
            extracted_data=completeness_result["extracted_data"]  # Store merged data
        )

        # Generate REAL AI response using Azure OpenAI (replaces hardcoded templates)
        # CRITICAL FIX #6: Track which field is asked in BOTH main and fallback paths
        field_name_asked_about = None  # Tracks field for QuestionTracker update later

        try:
            logger.info("[Chat] 🤖 Generating AI response using Azure OpenAI...")
            ai_service = get_azure_openai_service()

            # FIX 2: Filter missing_fields to EXCLUDE already-collected data
            # This prevents AI from being told to ask about fields we already have
            # BUG FIX #7: Only mark fields as "collected" if they have VALID values (not placeholders like "unknown")
            collected_field_names = set([
                field_name for field_name, field_value in completeness_result["extracted_data"].items()
                if is_valid_field_value(field_name, field_value)  # Validate VALUE, not just KEY existence
            ])

            # BUG FIX #1: Also filter out fields that were already asked about
            already_asked_fields = question_tracker.get_all_asked_fields()

            # CRITICAL FIX #5: OR Logic None Check - Validate field structure before processing
            # Prevents crash from malformed field dictionaries and ensures accurate completion detection
            actually_missing_fields = []
            for field in completeness_result["missing_fields"]:
                # Validate field structure
                if not isinstance(field, dict):
                    logger.warning(f"⚠️  Skipping malformed field (not a dict): {field}")
                    continue

                field_name = field.get("field")

                # CRITICAL: Skip fields with None or empty field names
                if not field_name:
                    logger.warning(
                        f"⚠️  Skipping field with missing/None field name: {field}. "
                        f"This prevents false 'incomplete' status."
                    )
                    continue

                # Check if field is actually missing (not collected and not previously asked)
                if field_name not in collected_field_names and not question_tracker.has_been_asked(field_name):
                    actually_missing_fields.append(field)

            logger.info(f"[Chat] 📊 Field status: {len(collected_field_names)} collected, "
                       f"{len(actually_missing_fields)} actually missing (filtered from {len(completeness_result['missing_fields'])})")
            logger.info(f"[Chat] Collected fields: {list(collected_field_names)}")
            logger.info(f"[Chat] Already asked about: {list(already_asked_fields)}")  # BUG FIX #1: Log asked fields
            # ----- COMPLETENESS & RESPONSE LOGIC (FRIEND'S FIX) -----
            logger.info(
                f"[Chat] Actually missing: {[f.get('field') for f in actually_missing_fields]}"
            )

            extracted = completeness_result["extracted_data"]

            # 1) Domain rule: can user submit now based on extracted data?
            user_can_submit_now = can_submit_now(extracted)

            # 2) Single definition of "truly complete" (OR LOGIC - ANY condition triggers completion):
            #    - extractor says complete OR
            #    - no allowed missing fields left (after QuestionTracker) OR
            #    - domain rule says user can submit
            is_truly_complete = (
                completeness_result.get("is_complete", False)
                or len(actually_missing_fields) == 0
                or user_can_submit_now
            )

            if is_truly_complete:
                # ✅ STOP ASKING QUESTIONS – just tell user to submit
                logger.info(
                    "[Chat] ✅ Conversation complete "
                    f"(is_complete={completeness_result.get('is_complete', False)}, "
                    f"can_submit_now={user_can_submit_now}, "
                    f"missing_after_filter={len(actually_missing_fields)}) "
                    "- telling user to submit"
                )

                ai_response_hi = (
                    "धन्यवाद! मैंने आपकी समस्या के बारे में पर्याप्त जानकारी ले ली है। "
                    "अब आप अपनी रिपोर्ट सबमिट कर सकते हैं।"
                )
                ai_response_en = (
                    "Thank you! I've collected enough information about your issue. "
                    "You can submit your report now."
                )

            else:
                # ❓ Not complete yet → HARD GATE: pick ONE safe field to ask
                allowed_field_to_ask = _pick_next_field_to_ask(
                    actually_missing_fields=actually_missing_fields,
                    already_asked_fields=already_asked_fields,
                    extracted_data=extracted
                )
                logger.info(f"[HARD GATE] Pre-Azure field selection: '{allowed_field_to_ask}'")

                # ❓ Ask ONE more targeted question via Azure
                ai_result = ai_service.generate_conversation_response(
                    user_message=user_message,
                    conversation_history=history,
                    missing_fields=actually_missing_fields,   # filtered by QuestionTracker
                    collected_data=extracted,
                    is_complete=False,                        # by definition, not complete here
                    questions_already_asked=list(already_asked_fields),
                    user_sentiment=user_sentiment,
                    can_submit_now=False,                     # we *know* user can't submit yet
                    allowed_field_to_ask=allowed_field_to_ask  # HARD GATE enforcement
                )

                ai_response_hi = ai_result["response_hi"]
                ai_response_en = ai_result["response_en"]

            logger.info(f"[Chat] ✅ AI response generated: {ai_response_hi[:80]}...")

        except AzureOpenAIServiceError as e:
            # Fallback to simple template if AI service fails
            logger.warning(f"[Chat] ⚠️ Azure OpenAI unavailable, using fallback: {e}")

            # Use SAME OR logic as main path for consistency
            extracted = completeness_result["extracted_data"]
            user_can_submit_now = can_submit_now(extracted)

            is_truly_complete = (
                completeness_result.get("is_complete", False)
                or len(actually_missing_fields) == 0
                or user_can_submit_now
            )

            if is_truly_complete:
                # Same behaviour as main path: no more questions
                ai_response_hi = (
                    "धन्यवाद! मैंने आपकी समस्या के बारे में पर्याप्त जानकारी ले ली है। "
                    "अब आप अपनी रिपोर्ट सबमिट कर सकते हैं।"
                )
                ai_response_en = (
                    "Thank you! I've collected enough information about your issue. "
                    "You can submit your report now."
                )
            else:
                if actually_missing_fields:
                    # Prefer critical/high importance fields if you track that
                    essential_field = next(
                        (
                            f for f in actually_missing_fields
                            if f.get("importance") in ("critical", "high")
                        ),
                        actually_missing_fields[0],
                    )

                    # CRITICAL FIX #6: Track field for QuestionTracker (prevents infinite loops in fallback)
                    field_name_asked_about = essential_field.get("field")
                    logger.info(
                        f"[Chat] 🔄 FALLBACK: Asking about field '{field_name_asked_about}' "
                        f"(will be tracked to prevent repeats)"
                    )

                    ai_response_hi = essential_field.get(
                        "prompt_hi",
                        "कृपया अपनी समस्या के बारे में थोड़ा और बताइए।",
                    )
                    ai_response_en = essential_field.get(
                        "prompt_en",
                        "Please tell me a bit more about your issue.",
                    )
                else:
                    # Ultra-defensive: no fields listed but not marked complete
                    ai_response_hi = (
                        "धन्यवाद! मैंने आपकी समस्या के बारे में पर्याप्त जानकारी ले ली है। "
                        "अब आप अपनी रिपोर्ट सबमिट कर सकते हैं।"
                    )
                    ai_response_en = (
                        "Thank you! I've collected enough information about your issue. "
                        "You can submit your report now."
                    )

        # BUG FIX #1: Check for duplicate questions across ENTIRE conversation history
        # Build list of all previously asked questions (for fuzzy comparison)
        if conversation.turns:
            # Collect ALL questions asked in this conversation
            previously_asked = []
            for turn in conversation.turns:
                if turn.ai_question_asked:
                    previously_asked.append(turn.ai_question_asked)

            # Use fuzzy duplicate detection (85% similarity threshold via rapidfuzz)
            if _is_dup_text(ai_response_hi, previously_asked):
                logger.warning(f"[Chat] 🚫 DUPLICATE QUESTION DETECTED!")
                logger.warning(f"[Chat] Question: '{ai_response_hi[:60]}...'")
                logger.warning(f"[Chat] This was already asked in a previous turn.")
                logger.warning(f"[Chat] Collected data: {list(completeness_result['extracted_data'].keys())}")

                # UX ENHANCEMENT: Prioritize essential fields (critical/high) during conversation
                # Medium importance fields are deferred to summary dialog
                found_alternative = False
                if actually_missing_fields:
                    # First pass: Look for critical or high importance fields
                    for idx, missing_field in enumerate(actually_missing_fields):
                        field_name = missing_field.get("field")
                        importance = missing_field.get("importance", "medium")

                        # Only ask critical/high importance fields during chat
                        if (field_name
                            and field_name not in completeness_result["extracted_data"]
                            and not question_tracker.has_been_asked(field_name)
                            and importance in ["critical", "high"]):  # ESSENTIAL FIELDS ONLY
                            ai_response_hi = missing_field.get("prompt_hi", "कृपया और जानकारी दें")
                            ai_response_en = missing_field.get("prompt_en", "Please provide more information")
                            logger.info(f"[Chat] ✅ Asking ESSENTIAL field #{idx}: {field_name} (importance: {importance})")
                            # FIX #2: Replace premature question_tracker.add_question() - track pending instead
                            pending_question_to_record = (field_name, ai_response_hi)
                            found_alternative = True
                            break

                    # Second pass: If no essential fields left, consider medium importance
                    if not found_alternative:
                        for idx, missing_field in enumerate(actually_missing_fields):
                            field_name = missing_field.get("field")
                            importance = missing_field.get("importance", "medium")

                            if (field_name
                                and field_name not in completeness_result["extracted_data"]
                                and not question_tracker.has_been_asked(field_name)):
                                ai_response_hi = missing_field.get("prompt_hi", "कृपया और जानकारी दें")
                                ai_response_en = missing_field.get("prompt_en", "Please provide more information")
                                logger.info(f"[Chat] ℹ️ Asking optional field #{idx}: {field_name} (importance: {importance})")
                                # FIX #2: Replace premature question_tracker.add_question() - track pending instead
                                pending_question_to_record = (field_name, ai_response_hi)
                                found_alternative = True
                                break

                if not found_alternative:
                    # BUG FIX #8: If user responded with a question, don't repeat "show summary"
                    # Instead, acknowledge their question and let them proceed
                    if user_sentiment["type"] == "question":
                        logger.info(f"[Chat] ❓ User responded with a question instead of answering - acknowledging and proceeding")
                        # User asked a clarifying question - acknowledge it and let them proceed or add more details
                        ai_response_hi = "मैं समझता हूँ आपके सवाल को। आप अभी रिपोर्ट सबमिट कर सकते हैं, या अगर आप और जानकारी जोड़ना चाहते हैं तो बता सकते हैं।"
                        ai_response_en = "I understand your question. You can submit the report now, or add more information if you'd like."
                    else:
                        # All fields collected or no alternatives - ask for summary
                        logger.info(f"[Chat] ℹ️ No more fields to collect, offering summary")

                        # BUG FIX #10B: Check if summary question was already asked
                        summary_question = "धन्यवाद! मुझे लगता है कि मैंने पर्याप्त जानकारी एकत्र कर ली है। क्या मैं आपको सारांश दिखाऊं?"
                        if _is_dup_text(summary_question, previously_asked):
                            # Summary already asked, user likely wants to proceed - show preview instead
                            logger.warning(f"[Chat] 🔄 Summary question already asked! Switching to direct preview.")
                            ai_response_hi = "मैं आपकी रिपोर्ट का सारांश दिखाता हूँ। नीचे 'सबमिट करें' बटन दबाएं।"
                            ai_response_en = "I will show your report summary. Press the 'Submit' button below."
                        else:
                            ai_response_hi = summary_question
                            ai_response_en = "Thank you! I think I have collected enough information. Should I show you the summary?"

        # BUG FIX #1: Detect question from AI response and record it
        # This helps track what we asked so we don't repeat
        # Add turn to conversation FIRST (so we have turn.turn_number for question tracking)
        turn = conversation_service.add_turn(
            conversation_id=conv_uuid,
            transcript_text=user_message,
            audio_url=None,
            language_detected=language_detected,
            ai_response=ai_response_hi,
            # FIX #4: Use _looks_like_question() to determine if this is actually a question
            ai_question_asked=ai_response_hi if _looks_like_question(ai_response_hi) else None,
            fields_extracted=completeness_result.get("entities", {})
        )

        logger.info(f"[Chat] Turn {turn.turn_number} complete for conversation {conversation_id}")

        # FIX #3: Persist the pending question to tracker (now that turn exists)
        if pending_question_to_record:
            _fname, _qtext = pending_question_to_record
            if _fname:
                question_tracker.add_question(_fname, _qtext, turn.turn_number)
                logger.info(f"[Chat] 📝 Recorded question about field '{_fname}' (turn {turn.turn_number})")
            pending_question_to_record = None

        # CRITICAL FIX #6: Use explicit field tracking from fallback, or fuzzy matching for main path
        if field_name_asked_about:
            # Fallback path explicitly tracked the field - use it directly
            question_tracker.add_question(field_name_asked_about, ai_response_hi, turn.turn_number + 1)
            logger.info(
                f"[Chat] 📝 Recorded question about field '{field_name_asked_about}' "
                f"(from fallback path - prevents infinite loops)"
            )
        else:
            # Main path - use fuzzy matching to detect which field was asked
            for missing_field in actually_missing_fields:
                field_name = missing_field.get("field")
                prompt_hi = missing_field.get("prompt_hi", "")
                # Check if AI response contains this field's prompt
                if prompt_hi and prompt_hi in ai_response_hi:
                    question_tracker.add_question(field_name, ai_response_hi, turn.turn_number + 1)
                    logger.info(f"[Chat] 📝 Recorded question about field '{field_name}'")
                    break

        # OPTION B: Check if user can submit now (minimum fields present)
        extracted_data = completeness_result["extracted_data"]
        user_can_submit = can_submit_now(extracted_data)

        # Generate preview card if submittable
        preview = None
        if user_can_submit:
            preview = create_preview_card(extracted_data, user_phone=current_user.phone)
            logger.info(f"[Chat] ✅ OPTION B: Minimum fields present! User can submit now.")
            logger.info(f"[Chat] Preview card: location={preview.location if preview else 'none'}, issue={preview.issue_description[:30] if preview and preview.issue_description else 'none'}...")
        else:
            logger.info(f"[Chat] ⏳ OPTION B: Still need minimum fields. Location: {bool(extracted_data.get('location'))}, Issue: {bool(extracted_data.get('issue_description'))}")

        # Allow skipping questions if completeness > 50%
        can_skip = completeness_result["completeness_score"] > 0.5

        return ChatTurnResponse(
            success=True,
            conversation_id=str(conversation.id),
            turn_number=turn.turn_number,
            user_message=user_message,
            language_detected=language_detected,
            ai_response_hi=ai_response_hi,
            ai_response_en=ai_response_en,
            completeness_score=completeness_result["completeness_score"],
            is_complete=completeness_result["is_complete"],
            collected_fields=completeness_result["collected_fields"],
            missing_fields=completeness_result["missing_fields"],
            extracted_data=completeness_result["extracted_data"],  # Include actual values
            should_continue=not completeness_result["is_complete"],
            ready_for_submission=completeness_result["is_complete"],
            # OPTION B: UX Enhancement flags
            show_submit_button=user_can_submit,  # Show submit immediately if minimum fields present
            show_skip_button=can_skip,  # Allow skipping if >50% complete
            preview_card=preview  # Preview of what will be submitted
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat turn: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat turn: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.get("/{conversation_id}/summary", response_model=ChatSummaryResponse)
async def get_conversation_summary(
    conversation_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get conversation summary for confirmation before submission.

    Includes:
    - Summary of collected information
    - Missing fields (if any)
    - Detected taxonomy
    - Completeness score

    Args:
        conversation_id: Conversation UUID
        user_id: User UUID
        db: Database session

    Returns:
        ChatSummaryResponse with summary and analysis
    """
    try:
        conv_uuid = UUID(conversation_id)
        user_uuid = UUID(user_id)

        # Get conversation
        conversation_service = get_ai_coach_conversation_service(db)
        conversation = conversation_service.get_conversation(conv_uuid)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        # Verify user owns conversation
        if conversation.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation"
            )

        # Generate summary
        summary = conversation_service.generate_summary_confirmation(conv_uuid)

        # Generate journalist-style narrative summary
        extracted_data = conversation.extracted_data or {}
        narrative_hi = generate_journalist_summary(extracted_data)
        narrative_en = generate_journalist_summary_english(extracted_data)

        logger.info(f"Generated journalist narrative: {narrative_hi[:100]}...")

        # Get all transcripts for taxonomy detection
        full_transcript = " ".join([turn.transcript_text for turn in conversation.turns])

        # Detect taxonomy (auto-classification) - optional if Claude API is configured
        taxonomy_result = None
        try:
            claude_service = get_claude_service()
            triage_request = TriageRequest(
                transcript_text=full_transcript
            )
            taxonomy_result = await claude_service.classify_transcript(
                transcript=triage_request.transcript_text,
                location_hint=triage_request.location_hint
            )
        except Exception as e:
            logger.info(f"Taxonomy detection skipped (Claude API not configured): {e}")
            taxonomy_result = None

        logger.info(f"Generated summary for conversation {conversation_id}")

        return ChatSummaryResponse(
            success=True,
            conversation_id=str(conversation.id),
            summary_hi=summary["hi"],
            summary_en=summary["en"],
            narrative_summary_hi=narrative_hi,  # NEW - Journalist narrative
            narrative_summary_en=narrative_en,  # NEW - Journalist narrative
            completeness_score=conversation.completeness_score,
            collected_fields=conversation.collected_fields or [],
            missing_fields=conversation.missing_fields or [],
            extracted_data=conversation.extracted_data or {},  # Include actual values
            detected_taxonomy=taxonomy_result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}"
        )


@router.post("/{conversation_id}/submit", response_model=ChatSubmitResponse)
async def submit_conversation_report(
    conversation_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Submit conversation as a report.

    Logic:
    - If completeness >= 80%: Create case and submit
    - If completeness < 80%: Send to moderator review with transcript

    Args:
        conversation_id: Conversation UUID
        user_id: User UUID
        db: Database session

    Returns:
        ChatSubmitResponse with submission result
    """
    try:
        conv_uuid = UUID(conversation_id)
        user_uuid = UUID(user_id)

        # Get conversation
        conversation_service = get_ai_coach_conversation_service(db)
        conversation = conversation_service.get_conversation(conv_uuid)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        # Verify user owns conversation
        if conversation.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation"
            )

        # Check completeness
        if conversation.completeness_score >= 0.8:
            # Complete - submit as case
            # Create case from conversation
            from app.models.case import Case, CaseStatus, CaseKind
            from geoalchemy2.elements import WKTElement

            # Build full transcript from all turns
            full_transcript = " ".join([turn.transcript_text for turn in conversation.turns])

            # Generate journalist summary for case title
            from app.services.journalist_summary import generate_journalist_summary
            extracted_data = conversation.extracted_data or {}
            case_summary = generate_journalist_summary(extracted_data)

            # Extract location if available
            location_text = extracted_data.get('location', '')
            location_point = None  # Can be geocoded later if needed

            # Get reporter personal details from user profile (like social media account)
            # These are auto-populated from signup, not extracted from conversation
            user = db.query(User).filter(User.id == user_uuid).first()
            reporter_name = user.name or ''
            reporter_phone = user.phone or ''  # Always available from OTP login
            reporter_address = user.address or ''

            # Create case
            new_case = Case(
                user_id=user_uuid,
                title=extracted_data.get('issue_description', 'नई शिकायत')[:500],
                summary=case_summary,
                transcript_text=full_transcript,
                location_text=location_text,
                reporter_name=reporter_name,
                reporter_phone=reporter_phone,
                reporter_address=reporter_address,
                status=CaseStatus.SUBMITTED.value,
                kind=CaseKind.GRIEVANCE.value,
                is_public=True,  # Grievances are public by default
                case_metadata={
                    'extracted_data': extracted_data,
                    'completeness_score': conversation.completeness_score,
                    'conversation_id': str(conversation.id)
                }
            )
            db.add(new_case)
            db.commit()
            db.refresh(new_case)

            logger.info(f"Created case {new_case.id} from conversation {conversation.id}")

            # Link conversation to case
            conversation.case_id = new_case.id
            conversation_service.complete_conversation(conv_uuid)

            # Update training progress
            user = db.query(User).filter(User.id == user_uuid).first()
            training_service = get_training_service(db)

            if training_service.is_in_training_mode(user):
                training_service.increment_report_count(user)
                training_progress = training_service.get_training_progress(user)
            else:
                training_progress = None

            message_hi = "आपकी रिपोर्ट सफलतापूर्वक जमा कर दी गई है। धन्यवाद!"
            message_en = "Your report has been submitted successfully. Thank you!"
            submitted_to_moderator = False

        else:
            # Incomplete - create case with "under_review" status
            # BUG FIX: Create case even for incomplete reports so they show in "My Reports"
            from app.models.case import Case, CaseStatus, CaseKind
            from geoalchemy2.elements import WKTElement

            # Build full transcript from all turns
            full_transcript = " ".join([turn.transcript_text for turn in conversation.turns])

            # Generate journalist summary for case title
            from app.services.journalist_summary import generate_journalist_summary
            extracted_data = conversation.extracted_data or {}
            case_summary = generate_journalist_summary(extracted_data)

            # Extract location if available
            location_text = extracted_data.get('location', '')
            location_point = None

            # Get reporter personal details from user profile
            user = db.query(User).filter(User.id == user_uuid).first()
            reporter_name = user.name or ''
            reporter_phone = user.phone or ''
            reporter_address = user.address or ''

            # Create case with "IN_PROGRESS" status (under review)
            new_case = Case(
                user_id=user_uuid,
                title=extracted_data.get('issue_description', 'नई शिकायत')[:500],
                summary=case_summary,
                transcript_text=full_transcript,
                location_text=location_text,
                reporter_name=reporter_name,
                reporter_phone=reporter_phone,
                reporter_address=reporter_address,
                status=CaseStatus.IN_PROGRESS.value,  # Under review status
                kind=CaseKind.GRIEVANCE.value,
                is_public=False,  # Keep private until reviewed
                case_metadata={
                    'extracted_data': extracted_data,
                    'completeness_score': conversation.completeness_score,
                    'conversation_id': str(conversation.id),
                    'under_review': True  # Flag for moderators
                }
            )
            db.add(new_case)
            db.commit()
            db.refresh(new_case)

            logger.info(f"Created UNDER_REVIEW case {new_case.id} from incomplete conversation {conversation.id}")

            # Link conversation to case
            conversation.case_id = new_case.id
            conversation_service.complete_conversation(conv_uuid)

            message_hi = "आपकी रिपोर्ट को समीक्षा के लिए भेजा गया है। हम जल्द ही संपर्क करेंगे।"
            message_en = "Your report has been sent for review. We will contact you soon."
            submitted_to_moderator = True
            training_progress = None

        logger.info(f"Submitted conversation {conversation_id} (completeness: {conversation.completeness_score})")

        return ChatSubmitResponse(
            success=True,
            case_id=str(conversation.case_id) if conversation.case_id else None,
            submitted_to_moderator=submitted_to_moderator,
            training_progress=training_progress,
            message_hi=message_hi,
            message_en=message_en
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit report: {str(e)}"
        )
