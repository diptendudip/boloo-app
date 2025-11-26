"""
Claude AI Service for intent classification and triage.

This service uses Anthropic's Claude API to classify user intents,
handle code-mixed language (Hindi-English-Chhattisgarhi), and provide
confidence scores for triage decisions.
"""

import logging
from typing import Dict, Optional, Any
from anthropic import Anthropic, APIError, APIConnectionError
import json

from app.config import settings
from app.prompts.triage_prompts import get_intent_classification_prompt, ISSUE_TAXONOMY

logger = logging.getLogger(__name__)


class ClaudeServiceError(Exception):
    """Base exception for Claude service errors"""
    pass


class ClaudeAPIError(ClaudeServiceError):
    """Error when Claude API call fails"""
    pass


class ClaudeParseError(ClaudeServiceError):
    """Error when parsing Claude response"""
    pass


class ClaudeService:
    """
    Service for interacting with Anthropic Claude API.

    Handles:
    - Intent classification (grievance/community/personal)
    - Confidence scoring
    - Code-mixed language understanding
    - Error handling and retries
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude service.

        Args:
            api_key: Anthropic API key. Uses settings.ANTHROPIC_API_KEY if not provided.

        Raises:
            ClaudeServiceError: If API key is not configured
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

        if not self.api_key:
            raise ClaudeServiceError(
                "ANTHROPIC_API_KEY not configured. Please set it in environment variables."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.max_tokens = 2048
        logger.info("ClaudeService initialized successfully")

    def classify_intent(
        self,
        transcript: str,
        location_hint: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify the intent of a conversation transcript.

        Analyzes code-mixed (Hindi-English-Chhattisgarhi) text to determine
        whether it's a grievance, community action, or personal note.

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
            ClaudeAPIError: If API call fails
            ClaudeParseError: If response parsing fails

        Example:
            >>> service = ClaudeService()
            >>> result = service.classify_intent(
            ...     "पानी की सप्लाई नहीं आ रही है 2 हफ्ते से",
            ...     location_hint="Raipur"
            ... )
            >>> print(result["intent"])  # "grievance"
            >>> print(result["confidence"])  # 0.95
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        logger.info(f"Classifying intent for transcript (length: {len(transcript)})")

        try:
            # Generate prompt with context
            prompt = get_intent_classification_prompt(
                transcript=transcript,
                location_hint=location_hint,
                user_context=user_context
            )

            # Call Claude API
            logger.debug(f"Calling Claude API with model: {self.model}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for more consistent classification
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract response text
            response_text = response.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")

            # Parse JSON response
            result = self._parse_classification_response(response_text)

            # Add metadata
            result["metadata"] = {
                "model": self.model,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "location_hint": location_hint,
                "transcript_length": len(transcript)
            }

            logger.info(
                f"Classification complete: intent={result['intent']}, "
                f"confidence={result['confidence']:.2f}"
            )

            return result

        except APIConnectionError as e:
            logger.error(f"Claude API connection error: {e}")
            raise ClaudeAPIError(f"Failed to connect to Claude API: {str(e)}")

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeAPIError(f"Claude API error: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise ClaudeParseError(f"Invalid JSON response from Claude: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error in classify_intent: {e}", exc_info=True)
            raise ClaudeServiceError(f"Classification failed: {str(e)}")

    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate Claude's classification response.

        Args:
            response_text: Raw text response from Claude

        Returns:
            Validated classification result dictionary

        Raises:
            ClaudeParseError: If response is invalid
        """
        try:
            # Try to extract JSON from response (Claude might add explanation)
            # Look for JSON block between ``` or direct JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                # Try to find JSON object
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                else:
                    json_text = response_text

            result = json.loads(json_text)

            # Validate required fields
            required_fields = ["intent", "confidence", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise ClaudeParseError(f"Missing required field: {field}")

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
                raise ClaudeParseError(
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
            raise ClaudeParseError(f"Invalid JSON in response: {str(e)}")

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Response validation failed: {e}")
            raise ClaudeParseError(f"Invalid response structure: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check if Claude API is accessible and configured correctly.

        Returns:
            Dict with health status and details
        """
        try:
            # Make a minimal API call to verify connectivity
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )

            return {
                "status": "healthy",
                "api_key_configured": bool(self.api_key),
                "model": self.model,
                "connection": "ok"
            }

        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_key_configured": bool(self.api_key),
                "model": self.model,
                "connection": "failed",
                "error": str(e)
            }


# Global instance (lazy initialization)
_claude_service: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """
    Get or create global ClaudeService instance.

    Returns:
        ClaudeService instance

    Raises:
        ClaudeServiceError: If service cannot be initialized
    """
    global _claude_service

    if _claude_service is None:
        _claude_service = ClaudeService()

    return _claude_service
