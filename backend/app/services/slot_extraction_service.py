"""
Slot Extraction Service

Extracts structured data (slots) from voice transcripts using Claude API.
Handles different case types (grievance, community, personal) with
type-specific prompts and validation.
"""

import logging
from typing import Dict, Any, List, Optional
import json

from app.services.claude_service import get_claude_service, ClaudeServiceError
from app.prompts.slot_extraction_prompts import (
    generate_extraction_prompt,
    get_follow_up_question,
)
from app.schemas.slots import (
    SlotExtractionRequest,
    SlotExtractionResponse,
    SlotValue,
    GrievanceSlots,
    CommunitySlots,
    PersonalSlots,
)

logger = logging.getLogger(__name__)


class SlotExtractionService:
    """
    Service for extracting structured slots from transcripts.

    Uses Claude API with type-specific prompts to extract:
    - Grievance slots: location, issue type, timeline, etc.
    - Community slots: topic, participants, permissions, etc.
    - Personal slots: title, content, reminders, etc.
    """

    def __init__(self):
        self.claude = get_claude_service()

    def extract_slots(
        self,
        transcript: str,
        case_kind: str,
        location_hint: Optional[str] = None,
        existing_slots: Optional[Dict[str, Any]] = None,
    ) -> SlotExtractionResponse:
        """
        Extract structured slots from transcript.

        Args:
            transcript: Voice transcript text
            case_kind: Type of case (grievance|community|personal)
            location_hint: Optional location context
            existing_slots: Previously extracted slots for iterative extraction

        Returns:
            SlotExtractionResponse with extracted slots and follow-up questions

        Raises:
            ClaudeServiceError: If extraction fails
        """
        try:
            logger.info(
                f"Extracting {case_kind} slots from transcript "
                f"(length: {len(transcript)})"
            )

            # Generate prompt
            prompt = generate_extraction_prompt(
                transcript_text=transcript,
                case_kind=case_kind,
                location_hint=location_hint,
                existing_slots=existing_slots,
            )

            # Call Claude API
            response = self.claude.client.messages.create(
                model=self.claude.model,
                max_tokens=self.claude.max_tokens,
                temperature=0.2,  # Low temperature for structured extraction
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Parse response
            response_text = response.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")

            # Extract JSON from response
            result = self._parse_extraction_response(response_text)

            # Convert to SlotValue objects
            slots = {
                key: SlotValue(
                    value=slot_data.get("value"),
                    confidence=slot_data.get("confidence", 0.0),
                    reasoning=slot_data.get("reasoning"),
                )
                for key, slot_data in result["slots"].items()
            }

            # Calculate completion
            missing_slots = [
                key for key, slot in slots.items()
                if not slot.is_reliable or slot.value is None
            ]

            total_slots = len(slots)
            filled_slots = total_slots - len(missing_slots)
            completion_percentage = (filled_slots / total_slots * 100) if total_slots > 0 else 0

            # Generate follow-up questions for missing slots
            follow_up_questions = result.get("follow_up_questions", [])

            # Add default follow-ups for any missing slots without questions
            for slot_name in missing_slots[:3]:  # Max 3 follow-ups
                if slot_name not in [q for q in follow_up_questions]:
                    follow_up = get_follow_up_question(slot_name, case_kind)
                    if follow_up:
                        follow_up_questions.append(follow_up)

            is_complete = completion_percentage >= 70  # 70% threshold

            response = SlotExtractionResponse(
                slots=slots,
                missing_slots=missing_slots,
                follow_up_questions=follow_up_questions[:3],  # Max 3 questions
                completion_percentage=completion_percentage,
                is_complete=is_complete,
            )

            logger.info(
                f"Slot extraction complete: {filled_slots}/{total_slots} slots filled "
                f"({completion_percentage:.1f}%), complete={is_complete}"
            )

            return response

        except ClaudeServiceError as e:
            logger.error(f"Claude service error during slot extraction: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in slot extraction: {e}", exc_info=True)
            raise ClaudeServiceError(f"Slot extraction failed: {str(e)}")

    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's slot extraction response.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed extraction result

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from response
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

            # Validate structure
            if "slots" not in result:
                raise ValueError("Response missing 'slots' field")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nResponse: {response_text}")
            raise ValueError(f"Invalid JSON in slot extraction response: {str(e)}")

        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            raise ValueError(f"Failed to parse slot extraction response: {str(e)}")

    def validate_slots(
        self,
        slots: Dict[str, SlotValue],
        case_kind: str,
    ) -> bool:
        """
        Validate extracted slots against schema.

        Args:
            slots: Extracted slots
            case_kind: Type of case

        Returns:
            True if valid, False otherwise
        """
        try:
            if case_kind == "grievance":
                GrievanceSlots(**slots)
            elif case_kind == "community":
                CommunitySlots(**slots)
            elif case_kind == "personal":
                PersonalSlots(**slots)
            else:
                raise ValueError(f"Invalid case_kind: {case_kind}")

            return True

        except Exception as e:
            logger.warning(f"Slot validation failed: {e}")
            return False


# Global instance
_slot_extraction_service: Optional[SlotExtractionService] = None


def get_slot_extraction_service() -> SlotExtractionService:
    """
    Get or create global SlotExtractionService instance.

    Returns:
        SlotExtractionService instance
    """
    global _slot_extraction_service

    if _slot_extraction_service is None:
        _slot_extraction_service = SlotExtractionService()

    return _slot_extraction_service
