"""
Pydantic schemas for slot extraction.

Defines the structure and validation for slots extracted from
voice transcripts for different case types.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted slots"""
    HIGH = "high"      # >= 0.9
    MEDIUM = "medium"  # 0.7-0.89
    LOW = "low"        # < 0.7


class SlotValue(BaseModel):
    """
    A single extracted slot value with confidence.

    Attributes:
        value: The extracted value (can be None if not found)
        confidence: Confidence score (0.0-1.0)
        reasoning: Optional explanation for the extraction
    """
    value: Optional[Any] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level category"""
        if self.confidence >= 0.9:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    @property
    def is_reliable(self) -> bool:
        """Check if confidence is high enough (>= 0.7)"""
        return self.confidence >= 0.7


class GrievanceSlots(BaseModel):
    """Slots for grievance cases"""
    location_text: SlotValue
    issue_type: SlotValue
    when_started: SlotValue
    scope_affected: SlotValue
    prior_contact: SlotValue
    evidence: SlotValue
    contact_phone: SlotValue


class CommunitySlots(BaseModel):
    """Slots for community story cases"""
    topic: SlotValue
    where: SlotValue
    who: SlotValue
    rights_ok: SlotValue
    media: SlotValue
    contact_phone: SlotValue


class PersonalSlots(BaseModel):
    """Slots for personal note cases"""
    short_title: SlotValue
    note: SlotValue
    reminder_when: SlotValue
    convertible: SlotValue
    contact_phone: SlotValue


class SlotExtractionRequest(BaseModel):
    """Request for slot extraction"""
    transcript_text: str = Field(min_length=1)
    kind: str = Field(pattern="^(grievance|community|personal)$")
    location_hint: Optional[str] = None
    existing_slots: Optional[Dict[str, Any]] = None


class SlotExtractionResponse(BaseModel):
    """Response from slot extraction"""
    slots: Dict[str, SlotValue]
    missing_slots: List[str]
    follow_up_questions: List[str]
    completion_percentage: float = Field(ge=0.0, le=100.0)
    is_complete: bool

    def get_reliable_slots(self) -> Dict[str, Any]:
        """Get only reliable slots (confidence >= 0.7)"""
        return {
            k: v.value
            for k, v in self.slots.items()
            if v.is_reliable and v.value is not None
        }

    def get_missing_slots(self) -> List[str]:
        """Get list of unreliable or missing slots"""
        return [
            k for k, v in self.slots.items()
            if not v.is_reliable or v.value is None
        ]
