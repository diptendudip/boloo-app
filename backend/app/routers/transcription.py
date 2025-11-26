"""
Transcription Router - Audio Upload and Speech-to-Text
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging
import os
import tempfile
import aiofiles

from app.database import get_db
from app.models import User
from app.utils.auth import get_current_user
from app.services.transcription_service import transcription_service
from app.services.claude_service import get_claude_service, ClaudeServiceError
from app.services.azure_openai_service import (
    get_azure_openai_service,
    AzureOpenAIServiceError
)
from app.services.completeness_analyzer import get_completeness_analyzer, CompletenessAnalyzerError
from app.services.training_service import get_training_service
from app.services.ai_coach_conversation_service import get_ai_coach_conversation_service

router = APIRouter()
logger = logging.getLogger(__name__)


class TranscriptionResponse(BaseModel):
    success: bool
    transcript: str
    language_detected: str
    confidence: float
    error: Optional[str] = None


class TranscribeAndClassifyResponse(BaseModel):
    success: bool
    transcript: str
    language_detected: str
    transcript_confidence: float
    triage_result: Optional[dict] = None
    error: Optional[str] = None


class AICoachTrainingResponse(BaseModel):
    """Response for AI Coach training mode"""
    success: bool
    transcript: str
    language_detected: str

    # AI Coach specific fields
    training_mode: bool
    conversation_id: Optional[str] = None
    turn_number: int
    completeness_score: float
    is_complete: bool

    # Follow-up question (empty if complete)
    next_question_hi: str
    next_question_en: str

    # Fields collected and missing
    collected_fields: list
    missing_fields: list

    # Training progress
    should_graduate: bool = False
    graduation_message: Optional[dict] = None

    error: Optional[str] = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(default="hi-IN")
):
    """
    Transcribe audio file to text using Azure Speech-to-Text

    Supports:
    - Hindi (hi-IN) - Primary language
    - English (en-IN, en-US)
    - Automatic language detection

    Args:
        audio: Audio file (m4a, wav, mp3, ogg)
        language: Primary language code (default: hi-IN)

    Returns:
        TranscriptionResponse with transcript and metadata
    """
    temp_file_path = None

    try:
        logger.info(f"Received audio file: {audio.filename} (TESTING MODE - no auth)")

        # Validate file type
        allowed_extensions = [".m4a", ".wav", ".mp3", ".ogg", ".webm"]
        file_ext = os.path.splitext(audio.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}. "
                       f"Allowed: {', '.join(allowed_extensions)}"
            )

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name

            # Write audio data to temp file
            content = await audio.read()
            temp_file.write(content)

        logger.info(f"Saved audio to temp file: {temp_file_path}")

        # Transcribe audio
        result = await transcription_service.transcribe_audio(
            audio_file_path=temp_file_path,
            language=language,
            enable_auto_language_detection=True
        )

        logger.info(f"Transcription result: success={result['success']}, "
                   f"transcript_length={len(result.get('transcript', ''))}")

        return TranscriptionResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.post("/transcribe-and-classify", response_model=TranscribeAndClassifyResponse)
async def transcribe_and_classify(
    audio: UploadFile = File(...),
    location_hint: Optional[str] = Form(default=None),
    language: str = Form(default="hi-IN")
):
    """
    Complete voice-to-intent pipeline:
    1. Transcribe audio to text (Speech-to-Text)
    2. Classify intent using Claude LLM (Text-to-Intent)

    This is the main endpoint for voice recording flow.

    Args:
        audio: Audio file from voice recording
        location_hint: Optional location context for better classification
        language: Primary language (default: hi-IN for Hindi)

    Returns:
        TranscribeAndClassifyResponse with transcript + triage classification
    """
    temp_file_path = None

    try:
        logger.info(f"[Voice Pipeline] Starting transcribe + classify (TESTING MODE - no auth)")
        logger.info(f"Audio file: {audio.filename}, location: {location_hint}")

        # Validate file type
        allowed_extensions = [".m4a", ".wav", ".mp3", ".ogg", ".webm"]
        file_ext = os.path.splitext(audio.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}"
            )

        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)

        logger.info(f"[Voice Pipeline] Saved audio: {temp_file_path}")

        # Step 1: Transcribe audio → text
        logger.info("[Voice Pipeline] Step 1: Transcribing audio...")
        transcription_result = await transcription_service.transcribe_audio(
            audio_file_path=temp_file_path,
            language=language,
            enable_auto_language_detection=True
        )

        if not transcription_result["success"]:
            return TranscribeAndClassifyResponse(
                success=False,
                transcript="",
                language_detected=language,
                transcript_confidence=0.0,
                triage_result=None,
                error=transcription_result.get("error", "Transcription failed")
            )

        transcript = transcription_result["transcript"]
        logger.info(f"[Voice Pipeline] Transcription successful: '{transcript[:100]}...'")

        # Step 2: Classify the transcript using REAL AI
        logger.info("🤖 [Voice Pipeline] Step 2: Classifying intent with REAL AI...")

        try:
            # Try Azure OpenAI first
            try:
                ai_service = get_azure_openai_service()
                logger.info("✅ [Voice Pipeline] Using Azure OpenAI for classification")
            except AzureOpenAIServiceError as e:
                # Fallback to Claude
                logger.warning(f"⚠️ [Voice Pipeline] Azure OpenAI not available: {e}")
                ai_service = get_claude_service()
                logger.info("✅ [Voice Pipeline] Using Claude API as fallback")

            # Call AI service for real classification
            classification = ai_service.classify_intent(
                transcript=transcript,
                location_hint=location_hint,
                user_context=None
            )

            triage_result = {
                "intent": classification["intent"],
                "confidence": classification["confidence"],
                "confidence_level": classification["confidence_level"],
                "reasoning": classification["reasoning"],
                "suggested_issue_type": classification.get("suggested_issue_type"),
                "transcript_summary": transcript[:100] + "..." if len(transcript) > 100 else transcript
            }

            logger.info(
                f"✅ [Voice Pipeline] Real AI classification: {classification['intent']} "
                f"({classification['confidence']:.2f})"
            )

        except (AzureOpenAIServiceError, ClaudeServiceError) as e:
            # Fallback to keyword matching if AI completely unavailable
            logger.warning(f"⚠️ [Voice Pipeline] AI service unavailable, using keyword fallback: {e}")

            transcript_lower = transcript.lower()
            if any(word in transcript_lower for word in ['पानी', 'water', 'सड़क', 'road', 'बिजली', 'electricity', 'कचरा', 'garbage']):
                intent = "grievance"
                suggested_issue_type = "infrastructure"
                confidence = 0.88
            elif any(word in transcript_lower for word in ['समुदाय', 'community']):
                intent = "community"
                suggested_issue_type = None
                confidence = 0.82
            else:
                intent = "personal"
                suggested_issue_type = None
                confidence = 0.75

            confidence_level = "high" if confidence >= 0.7 else "medium" if confidence >= 0.5 else "low"

            triage_result = {
                "intent": intent,
                "confidence": confidence,
                "confidence_level": confidence_level,
                "reasoning": "⚠️ FALLBACK: Keyword classification (AI unavailable)",
                "suggested_issue_type": suggested_issue_type,
                "transcript_summary": transcript[:100] + "..." if len(transcript) > 100 else transcript
            }

            logger.info(f"⚠️ [Voice Pipeline] Fallback classification: {intent} ({confidence:.2f})")

        # Return complete pipeline result
        return TranscribeAndClassifyResponse(
            success=True,
            transcript=transcript,
            language_detected=transcription_result["language_detected"],
            transcript_confidence=transcription_result["confidence"],
            triage_result=triage_result,
            error=None
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[Voice Pipeline] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Voice pipeline failed: {str(e)}"
        )

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.post("/ai-coach-training", response_model=AICoachTrainingResponse)
async def ai_coach_training_mode(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    conversation_id: Optional[str] = Form(default=None),
    language: str = Form(default="hi-IN"),
    db: Session = Depends(get_db)
):
    """
    AI Coach Training Mode - Voice pipeline with completeness analysis and follow-up questions.

    This endpoint provides intelligent training for new users by:
    1. Transcribing voice audio
    2. Analyzing transcript completeness
    3. Identifying missing information
    4. Generating follow-up questions in Hindi
    5. Tracking conversation turns (max 2 follow-ups)
    6. Auto-graduating after 5 successful reports

    Args:
        audio: Audio file from voice recording
        user_id: User UUID
        conversation_id: Optional conversation ID to continue existing conversation
        language: Primary language (default: hi-IN)
        db: Database session

    Returns:
        AICoachTrainingResponse with completeness analysis and next question
    """
    temp_file_path = None

    try:
        from uuid import UUID
        user_uuid = UUID(user_id)

        logger.info(f"[AI Coach] Starting training mode for user {user_id}")

        # Get user and check training mode status
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        training_service = get_training_service(db)
        in_training_mode = training_service.is_in_training_mode(user)

        logger.info(f"[AI Coach] User training mode: {in_training_mode}")

        # Validate file type
        allowed_extensions = [".m4a", ".wav", ".mp3", ".ogg", ".webm"]
        file_ext = os.path.splitext(audio.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}"
            )

        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)

        logger.info(f"[AI Coach] Saved audio: {temp_file_path}")

        # Step 1: Transcribe audio
        logger.info("[AI Coach] Step 1: Transcribing audio...")
        transcription_result = await transcription_service.transcribe_audio(
            audio_file_path=temp_file_path,
            language=language,
            enable_auto_language_detection=True
        )

        if not transcription_result["success"]:
            return AICoachTrainingResponse(
                success=False,
                transcript="",
                language_detected=language,
                training_mode=in_training_mode,
                turn_number=0,
                completeness_score=0.0,
                is_complete=False,
                next_question_hi="",
                next_question_en="",
                collected_fields=[],
                missing_fields=[],
                error=transcription_result.get("error", "Transcription failed")
            )

        transcript = transcription_result["transcript"]
        language_detected = transcription_result["language_detected"]
        logger.info(f"[AI Coach] Transcription successful: '{transcript[:100]}...'")

        # Step 2: Get or create conversation
        conversation_service = get_ai_coach_conversation_service(db)

        if conversation_id:
            # Continue existing conversation
            from uuid import UUID
            conv_uuid = UUID(conversation_id)
            conversation = conversation_service.get_conversation(conv_uuid)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            logger.info(f"[AI Coach] Continuing conversation {conversation_id}")
        else:
            # Create new conversation
            conversation = conversation_service.create_conversation(user_id=user_uuid)
            logger.info(f"[AI Coach] Created new conversation {conversation.id}")

        # Step 3: Analyze completeness
        logger.info("[AI Coach] Step 2: Analyzing completeness...")
        completeness_analyzer = get_completeness_analyzer()

        # Get conversation history for context
        conversation_history = conversation_service.get_conversation_history_for_ai(
            conversation.id
        )

        # Analyze transcript
        analysis_result = completeness_analyzer.analyze_completeness(
            transcript=transcript,
            conversation_history=conversation_history
        )

        logger.info(
            f"[AI Coach] Completeness: {analysis_result['completeness_score']:.2f}, "
            f"Complete: {analysis_result['is_complete']}"
        )

        # Step 4: Add turn to conversation
        turn = conversation_service.add_turn(
            conversation_id=conversation.id,
            transcript_text=transcript,
            language_detected=language_detected,
            ai_question_asked=analysis_result.get("next_question_hi", ""),
            fields_extracted=analysis_result.get("extracted_data", {})
        )

        # Step 5: Update conversation completeness
        conversation = conversation_service.update_completeness(
            conversation_id=conversation.id,
            completeness_score=analysis_result['completeness_score'],
            collected_fields=analysis_result['collected_fields'],
            missing_fields=analysis_result['missing_fields']
        )

        # Step 6: Determine if conversation should continue
        should_continue = conversation_service.should_continue_conversation(conversation.id)

        # If conversation is complete or at max turns, complete it
        if not should_continue:
            conversation = conversation_service.complete_conversation(conversation.id)
            logger.info(f"[AI Coach] Conversation {conversation.id} completed")

            # Increment user's report count
            report_count = training_service.increment_report_count(user)
            logger.info(f"[AI Coach] User report count: {report_count}")

        # Step 7: Check graduation
        should_graduate = training_service.should_graduate(user)
        graduation_message = None

        if should_graduate:
            graduation_result = training_service.graduate_user(user)
            logger.info(f"[AI Coach] User graduated! {graduation_result}")
            graduation_message = graduation_result

        # Build response
        return AICoachTrainingResponse(
            success=True,
            transcript=transcript,
            language_detected=language_detected,
            training_mode=in_training_mode,
            conversation_id=str(conversation.id),
            turn_number=conversation.turn_count,
            completeness_score=analysis_result['completeness_score'],
            is_complete=analysis_result['is_complete'],
            next_question_hi=analysis_result.get('next_question_hi', ''),
            next_question_en=analysis_result.get('next_question_en', ''),
            collected_fields=analysis_result['collected_fields'],
            missing_fields=analysis_result['missing_fields'],
            should_graduate=should_graduate,
            graduation_message=graduation_message,
            error=None
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[AI Coach] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI Coach training mode failed: {str(e)}"
        )

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for transcription
    """
    return {
        "languages": [
            {
                "code": "hi-IN",
                "name": "Hindi (India)",
                "native_name": "हिन्दी",
                "default": True
            },
            {
                "code": "en-IN",
                "name": "English (India)",
                "native_name": "English",
                "default": False
            },
            {
                "code": "en-US",
                "name": "English (US)",
                "native_name": "English",
                "default": False
            }
        ]
    }
