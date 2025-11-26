"""
Triage API Router

Provides endpoints for intent classification and case triage.
Handles audio transcripts and classifies them into grievance/community/personal categories.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.claude_service import (
    get_claude_service,
    ClaudeService,
    ClaudeServiceError,
    ClaudeAPIError,
    ClaudeParseError
)
from app.services.azure_openai_service import (
    get_azure_openai_service,
    AzureOpenAIService,
    AzureOpenAIServiceError,
    AzureOpenAIAPIError,
    AzureOpenAIParseError
)
from app.models.case import Case, TriageIntent
from app.models.user import User
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Schemas
class TriageRequest(BaseModel):
    """Request schema for case triage endpoint"""

    audio_url: Optional[str] = Field(
        None,
        description="URL to audio file (for reference/storage)",
        max_length=1000
    )
    transcript_text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Conversation transcript to analyze"
    )
    location_hint: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional location context (e.g., 'Raipur, Chhattisgarh')"
    )
    user_context: Optional[dict] = Field(
        None,
        description="Optional user context for better classification"
    )

    @validator('transcript_text')
    def validate_transcript(cls, v):
        """Validate transcript is not just whitespace"""
        if not v.strip():
            raise ValueError("Transcript cannot be empty or whitespace only")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "audio_url": "https://storage.example.com/audio/123.mp3",
                "transcript_text": "हमारे क्षेत्र में पानी की बहुत समस्या है। पिछले 2 हफ्ते से पानी नहीं आ रहा है। Raipur sector 5 में रहते हैं।",
                "location_hint": "Raipur, Chhattisgarh"
            }
        }


class TriageResponse(BaseModel):
    """Response schema for case triage endpoint"""

    intent: str = Field(
        ...,
        description="Classified intent: grievance, community, personal, or uncertain"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    confidence_level: str = Field(
        ...,
        description="Confidence level: high (≥0.7), medium (0.5-0.7), low (<0.5)"
    )
    reasoning: str = Field(
        ...,
        description="Explanation for the classification"
    )
    suggested_issue_type: Optional[str] = Field(
        None,
        description="Suggested issue type from taxonomy (for grievances only)"
    )
    metadata: dict = Field(
        ...,
        description="Additional metadata (tokens used, model info, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "grievance",
                "confidence": 0.92,
                "confidence_level": "high",
                "reasoning": "Clear civic issue (water supply) affecting locality with specific location and duration mentioned",
                "suggested_issue_type": "water_supply",
                "metadata": {
                    "model": "claude-3-5-sonnet-20241022",
                    "tokens_used": 1245,
                    "location_hint": "Raipur, Chhattisgarh"
                }
            }
        }


class TriageErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    error_type: str
    details: Optional[dict] = None
    suggestions: Optional[list] = None


class TriageSuccessResponse(BaseModel):
    """Success response wrapper for mobile app"""
    success: bool = True
    result: TriageResponse


# Endpoints
@router.post(
    "/triage",
    response_model=TriageSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify intent of conversation transcript",
    description="""
    Classify a conversation transcript into one of three categories:
    - **grievance**: Civic complaint requiring government action
    - **community**: Community organizing or collective action
    - **personal**: Personal note or reminder

    Handles code-mixed language (Hindi + English + Chhattisgarhi).
    Returns confidence scores and reasoning for transparency.
    """,
    responses={
        200: {
            "description": "Intent classified successfully",
            "model": TriageResponse
        },
        400: {
            "description": "Invalid request (empty transcript, validation error)",
            "model": TriageErrorResponse
        },
        500: {
            "description": "Server error (Claude API failure, parsing error)",
            "model": TriageErrorResponse
        },
        503: {
            "description": "Service unavailable (Claude API not configured)",
            "model": TriageErrorResponse
        }
    }
)
async def classify_case_intent(
    request: TriageRequest
):
    """
    Classify the intent of a case transcript.

    This endpoint analyzes conversation transcripts to determine whether
    the user is reporting a grievance, organizing community action, or
    creating a personal note.

    **Authentication Required**: No (testing mode with dummy data)

    **Rate Limiting**: Subject to API rate limits

    **Processing**:
    1. Validates transcript text
    2. Calls Claude API for classification
    3. Returns intent with confidence score
    4. Suggests issue type for grievances

    **Confidence Levels**:
    - **High (≥0.7)**: Reliable classification, can auto-route
    - **Medium (0.5-0.7)**: Moderate confidence, may need review
    - **Low (<0.5)**: Uncertain, recommend manual review or follow-up
    """
    try:
        logger.info(
            f"🎯 Triage request with REAL AI: "
            f"transcript_length={len(request.transcript_text)}, "
            f"location_hint={request.location_hint}"
        )

        # PRODUCTION MODE: Use Azure OpenAI for real conversational AI
        try:
            ai_service = get_azure_openai_service()
            logger.info("✅ Using Azure OpenAI for classification")
        except AzureOpenAIServiceError as e:
            # Fallback to Claude if available
            logger.warning(f"⚠️ Azure OpenAI not available: {e}")
            try:
                ai_service = get_claude_service()
                logger.info("✅ Using Claude API as fallback")
            except ClaudeServiceError:
                logger.error("❌ No AI service available, using keyword fallback")
                # Ultimate fallback: keyword matching
                return _dummy_classification(request)

        # Call AI service for real classification
        classification = ai_service.classify_intent(
            transcript=request.transcript_text,
            location_hint=request.location_hint,
            user_context=request.user_context
        )

        logger.info(
            f"✅ Classification complete: intent={classification['intent']}, "
            f"confidence={classification['confidence']:.2f}"
        )

        result = TriageResponse(**classification)
        return TriageSuccessResponse(success=True, result=result)

    except (AzureOpenAIAPIError, ClaudeAPIError) as e:
        logger.error(f"❌ AI API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AI service error",
                "error_type": "api_error",
                "details": {"message": "Failed to connect to classification service"},
                "suggestions": [
                    "Please try again in a few moments",
                    "If problem persists, contact support"
                ]
            }
        )

    except (AzureOpenAIParseError, ClaudeParseError) as e:
        logger.error(f"❌ Response parsing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Response parsing error",
                "error_type": "parse_error",
                "details": {"message": "Failed to parse classification result"},
                "suggestions": [
                    "Please try again",
                    "If problem persists, contact support"
                ]
            }
        )

    except Exception as e:
        logger.error(f"❌ Triage error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )

    except ValueError as e:
        logger.error(f"Validation error in triage: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid request",
                "error_type": "validation_error",
                "details": {"message": str(e)},
                "suggestions": [
                    "Ensure transcript is not empty",
                    "Check that transcript contains meaningful text"
                ]
            }
        )

    except ClaudeAPIError as e:
        logger.error(f"Claude API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AI service error",
                "error_type": "api_error",
                "details": {"message": "Failed to connect to classification service"},
                "suggestions": [
                    "Please try again in a few moments",
                    "If problem persists, contact support"
                ]
            }
        )

    except ClaudeParseError as e:
        logger.error(f"Claude response parsing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Response parsing error",
                "error_type": "parse_error",
                "details": {"message": "Failed to parse classification result"},
                "suggestions": [
                    "Please try again",
                    "If problem persists, contact support"
                ]
            }
        )

    except ClaudeServiceError as e:
        logger.error(f"Claude service error: {e}", exc_info=True)

        # Check if it's a configuration issue
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service not configured",
                    "error_type": "configuration_error",
                    "details": {"message": "AI service is not properly configured"},
                    "suggestions": [
                        "Contact system administrator",
                        "Check API key configuration"
                    ]
                }
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Service error",
                "error_type": "service_error",
                "details": {"message": str(e)},
                "suggestions": ["Please try again later"]
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error in triage endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "error_type": "unknown_error",
                "details": {"message": "An unexpected error occurred"},
                "suggestions": ["Please try again later"]
            }
        )


def _dummy_classification(request: TriageRequest) -> TriageSuccessResponse:
    """
    Fallback dummy classification when no AI service is available.
    """
    transcript_lower = request.transcript_text.lower()

    if any(word in transcript_lower for word in ['पानी', 'water', 'सड़क', 'road', 'बिजली', 'electricity', 'कचरा', 'garbage']):
        intent = "grievance"
        suggested_issue_type = "infrastructure"
        confidence = 0.88
    elif any(word in transcript_lower for word in ['समुदाय', 'community', 'सामूहिक', 'collective']):
        intent = "community"
        suggested_issue_type = None
        confidence = 0.82
    else:
        intent = "personal"
        suggested_issue_type = None
        confidence = 0.75

    confidence_level = "high" if confidence >= 0.7 else "medium" if confidence >= 0.5 else "low"

    result = TriageResponse(
        intent=intent,
        confidence=confidence,
        confidence_level=confidence_level,
        reasoning=f"⚠️ FALLBACK MODE: Keyword-based classification. AI service unavailable.",
        suggested_issue_type=suggested_issue_type,
        metadata={
            "model": "fallback-keyword-matching",
            "location_hint": request.location_hint,
            "transcript_length": len(request.transcript_text)
        }
    )

    return TriageSuccessResponse(success=True, result=result)


@router.get(
    "/triage/health",
    summary="Check triage service health",
    description="Verify that Claude AI service is configured and accessible"
)
async def triage_health_check(
    claude_service: ClaudeService = Depends(get_claude_service)
):
    """
    Health check endpoint for triage service.

    Checks:
    - Claude API connectivity
    - API key configuration
    - Service availability

    **Authentication Required**: No
    """
    try:
        health_status = claude_service.health_check()

        if health_status["status"] == "healthy":
            return {
                "status": "healthy",
                "service": "triage",
                "details": health_status
            }
        else:
            logger.warning(f"Triage service unhealthy: {health_status}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "service": "triage",
                    "details": health_status
                }
            )

    except ClaudeServiceError as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "triage",
                "error": str(e)
            }
        )
