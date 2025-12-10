"""
Pydantic data models for the 3-agent Boloo conversation system.

This module defines the complete state management structure for tracking
multi-turn conversations about civic issues reported by rural citizens.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enumerations
# ============================================================================

class ProblemCategory(str, Enum):
    """Categories of civic problems that can be reported."""
    WATER = "WATER"
    ROAD = "ROAD"
    RATION = "RATION"
    ANGANWADI = "ANGANWADI"
    ELECTRICITY = "ELECTRICITY"
    GAS = "GAS"
    OTHER = "OTHER"


class DurationCategory(str, Enum):
    """Time-based categorization of problem duration."""
    DAYS = "DAYS"
    WEEKS = "WEEKS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"
    UNKNOWN = "UNKNOWN"


class ProblemScale(str, Enum):
    """Geographic or demographic scale of the problem."""
    INDIVIDUAL = "INDIVIDUAL"
    HOUSEHOLD = "HOUSEHOLD"
    NEIGHBORHOOD = "NEIGHBORHOOD"
    VILLAGE = "VILLAGE"
    MULTI_VILLAGE = "MULTI_VILLAGE"
    UNKNOWN = "UNKNOWN"


class SeverityLevel(str, Enum):
    """Severity assessment of the problem impact."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class SlotPriority(str, Enum):
    """Priority levels for conversation slots."""
    CORE = "core"  # Must be collected
    IMPORTANT = "important"  # Should be collected
    OPTIONAL = "optional"  # Nice to have


class AgentMode(str, Enum):
    """Directive modes for the conversation agent."""
    ASK_FOR_SLOT = "ASK_FOR_SLOT"
    CONFIRM_AND_SUBMIT = "CONFIRM_AND_SUBMIT"
    SUBMIT_NOW = "SUBMIT_NOW"
    SMALL_TALK_REASSURE = "SMALL_TALK_REASSURE"


class LocationSource(str, Enum):
    """Source of location information."""
    GPS = "GPS"
    USER_INPUT = "USER_INPUT"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


# ============================================================================
# Core Data Models
# ============================================================================

class Location(BaseModel):
    """Geographic location information for the reported problem."""

    village: Optional[str] = Field(None, description="Name of the village")
    hamlet_or_para: Optional[str] = Field(None, description="Hamlet or para within village")
    panchayat: Optional[str] = Field(None, description="Panchayat administrative unit")
    block: Optional[str] = Field(None, description="Block administrative unit")
    district: Optional[str] = Field(None, description="District")
    state: Optional[str] = Field(None, description="State")
    landmark: Optional[str] = Field(None, description="Notable nearby landmark")
    source: LocationSource = Field(
        LocationSource.UNKNOWN,
        description="How location was determined"
    )

    class Config:
        use_enum_values = True


class Problem(BaseModel):
    """Detailed information about the civic problem being reported."""

    category: Optional[ProblemCategory] = Field(
        None,
        description="Categorized type of problem"
    )
    asset_type: Optional[str] = Field(
        None,
        description="Specific asset affected (e.g., hand pump, road, ration shop)"
    )
    description_raw: Optional[str] = Field(
        None,
        description="Raw user description in their own words"
    )
    description_clean_hi: Optional[str] = Field(
        None,
        description="Cleaned Hindi description for official submission"
    )
    duration_text: Optional[str] = Field(
        None,
        description="User's description of how long problem has existed"
    )
    duration_category: DurationCategory = Field(
        DurationCategory.UNKNOWN,
        description="Categorized duration"
    )
    scale: ProblemScale = Field(
        ProblemScale.UNKNOWN,
        description="Geographic/demographic scale of impact"
    )
    health_impact: Optional[str] = Field(
        None,
        description="Health consequences mentioned by user"
    )
    economic_impact: Optional[str] = Field(
        None,
        description="Economic consequences mentioned by user"
    )
    coping_actions: Optional[str] = Field(
        None,
        description="How people are currently managing the problem"
    )
    severity_for_reporter: SeverityLevel = Field(
        SeverityLevel.UNKNOWN,
        description="Assessed severity based on reporter's situation"
    )

    class Config:
        use_enum_values = True


class Attempts(BaseModel):
    """Information about prior attempts to resolve the problem."""

    any_attempt_made: Optional[bool] = Field(
        None,
        description="Whether any attempts were made to resolve the issue"
    )
    attempts_text: Optional[str] = Field(
        None,
        description="User's description of attempts made"
    )
    authorities_contacted: List[str] = Field(
        default_factory=list,
        description="List of authorities or officials contacted"
    )
    attempts_outcome: Optional[str] = Field(
        None,
        description="Result or response from authorities"
    )


class Appeal(BaseModel):
    """User's appeal or request to authorities."""

    included: bool = Field(
        False,
        description="Whether user wants to include an appeal"
    )
    appeal_text_hi: Optional[str] = Field(
        None,
        description="Appeal text in Hindi for submission"
    )


class AuthorityContact(BaseModel):
    """Contact information for a relevant authority."""

    role: str = Field(..., description="Role/position of the authority")
    name: Optional[str] = Field(None, description="Name if known")
    phone: Optional[str] = Field(None, description="Contact phone number")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        # Remove spaces and special characters
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 10:
            raise ValueError("Phone number must be 10 digits")
        return cleaned


class Contacts(BaseModel):
    """Collection of relevant authority contacts."""

    authority_contacts: List[AuthorityContact] = Field(
        default_factory=list,
        description="List of relevant authorities with contact info"
    )


class Reporter(BaseModel):
    """Information about the person reporting the problem."""

    name: Optional[str] = Field(None, description="Reporter's name")
    wants_anonymous: bool = Field(
        False,
        description="Whether reporter wants to remain anonymous"
    )
    phone: Optional[str] = Field(None, description="Reporter's contact number")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 10:
            raise ValueError("Phone number must be 10 digits")
        return cleaned


class SlotStatus(BaseModel):
    """Tracking status for individual conversation slots."""

    value_present: bool = Field(
        False,
        description="Whether this slot has been filled"
    )
    attempts: int = Field(
        0,
        ge=0,
        description="Number of attempts to collect this slot"
    )
    max_attempts: int = Field(
        3,
        ge=1,
        description="Maximum attempts before moving on"
    )
    priority: SlotPriority = Field(
        SlotPriority.OPTIONAL,
        description="Priority level for collecting this slot"
    )
    user_refused: bool = Field(
        False,
        description="Whether user explicitly refused to provide this info"
    )

    class Config:
        use_enum_values = True


class ConversationMeta(BaseModel):
    """Metadata about the conversation flow and user state."""

    language_detected: str = Field(
        "hi",
        description="Detected language code (e.g., 'hi' for Hindi)"
    )
    frustration_level: int = Field(
        0,
        ge=0,
        le=10,
        description="Assessed user frustration level (0-10)"
    )
    user_wants_submit: bool = Field(
        False,
        description="Whether user has indicated readiness to submit"
    )
    conversation_start_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="When conversation started"
    )
    last_update_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )


class Report(BaseModel):
    """Complete report structure containing all collected information."""

    id: str = Field(..., description="Unique report identifier")
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )
    location: Location = Field(
        default_factory=Location,
        description="Location information"
    )
    problem: Problem = Field(
        default_factory=Problem,
        description="Problem details"
    )
    attempts: Attempts = Field(
        default_factory=Attempts,
        description="Prior resolution attempts"
    )
    appeal: Appeal = Field(
        default_factory=Appeal,
        description="User's appeal to authorities"
    )
    contacts: Contacts = Field(
        default_factory=Contacts,
        description="Relevant authority contacts"
    )
    reporter: Reporter = Field(
        default_factory=Reporter,
        description="Reporter information"
    )
    meta: ConversationMeta = Field(
        default_factory=ConversationMeta,
        description="Conversation metadata"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Report creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )


class AgentDirective(BaseModel):
    """Instructions from the directive agent to guide conversation flow."""

    mode: AgentMode = Field(..., description="Action mode for the agent")
    target_slot: Optional[str] = Field(
        None,
        description="Which slot to ask about (if mode is ASK_FOR_SLOT)"
    )
    reason: Optional[str] = Field(
        None,
        description="Explanation for this directive decision"
    )
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this directive"
    )

    class Config:
        use_enum_values = True


class QuestionHistoryEntry(BaseModel):
    """Single entry in the conversation question history."""

    turn: int = Field(..., ge=1, description="Turn number in conversation")
    slot_asked: str = Field(..., description="Slot identifier that was asked about")
    user_response: str = Field(..., description="User's response text")
    extracted_value: Optional[str] = Field(
        None,
        description="Value extracted from response"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this turn occurred"
    )


class ConversationState(BaseModel):
    """
    Complete state of a conversation session.

    This is the master state object that gets passed between agents
    and updated throughout the conversation lifecycle.
    """

    report: Report = Field(
        default_factory=Report,
        description="The report being constructed"
    )
    question_history: List[QuestionHistoryEntry] = Field(
        default_factory=list,
        description="History of all question-answer pairs"
    )
    conversation_meta: ConversationMeta = Field(
        default_factory=ConversationMeta,
        description="Conversation metadata and state"
    )
    last_directive: Optional[AgentDirective] = Field(
        None,
        description="Most recent directive from directive agent"
    )
    turn_count: int = Field(
        0,
        ge=0,
        description="Total number of conversation turns"
    )
    slot_statuses: Dict[str, SlotStatus] = Field(
        default_factory=dict,
        description="Status tracking for each slot"
    )

    def increment_turn(self) -> None:
        """Increment the turn counter and update timestamp."""
        self.turn_count += 1
        self.conversation_meta.last_update_time = datetime.utcnow()
        self.report.updated_at = datetime.utcnow()

    def get_slot_status(self, slot_id: str) -> SlotStatus:
        """Get status for a specific slot, creating default if needed."""
        if slot_id not in self.slot_statuses:
            self.slot_statuses[slot_id] = SlotStatus()
        return self.slot_statuses[slot_id]

    def mark_slot_filled(self, slot_id: str) -> None:
        """Mark a slot as successfully filled."""
        status = self.get_slot_status(slot_id)
        status.value_present = True
        self.conversation_meta.last_update_time = datetime.utcnow()

    def increment_slot_attempts(self, slot_id: str) -> None:
        """Increment attempt counter for a slot."""
        status = self.get_slot_status(slot_id)
        status.attempts += 1


# ============================================================================
# Slot Registry Configuration
# ============================================================================

SLOT_REGISTRY: Dict[str, Dict] = {
    # Location slots
    "location.village": {
        "target_field": "report.location.village",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 3,
        "description": "Village name"
    },
    "location.hamlet": {
        "target_field": "report.location.hamlet_or_para",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "Hamlet or para name"
    },
    "location.district": {
        "target_field": "report.location.district",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 3,
        "description": "District name"
    },
    "location.landmark": {
        "target_field": "report.location.landmark",
        "priority": SlotPriority.OPTIONAL,
        "required": False,
        "max_attempts": 1,
        "description": "Nearby landmark"
    },
    "location.panchayat": {
        "target_field": "report.location.panchayat",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "Panchayat name"
    },
    "location.block": {
        "target_field": "report.location.block",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "Block/Tehsil name"
    },
    "location.state": {
        "target_field": "report.location.state",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "State name"
    },

    # Problem slots
    "problem.category": {
        "target_field": "report.problem.category",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 3,
        "description": "Problem category"
    },
    "problem.description": {
        "target_field": "report.problem.description_raw",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 3,
        "description": "Problem description"
    },
    "problem.duration": {
        "target_field": "report.problem.duration_text",
        "priority": SlotPriority.IMPORTANT,
        "required": True,
        "max_attempts": 2,
        "description": "How long problem has existed"
    },
    "problem.scale": {
        "target_field": "report.problem.scale",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "How many people affected"
    },
    "problem.health_impact": {
        "target_field": "report.problem.health_impact",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "Health consequences"
    },
    "problem.economic_impact": {
        "target_field": "report.problem.economic_impact",
        "priority": SlotPriority.OPTIONAL,
        "required": False,
        "max_attempts": 1,
        "description": "Economic impact"
    },

    # Attempts slots
    "attempts.made": {
        "target_field": "report.attempts.any_attempt_made",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 2,
        "description": "Whether any attempts to resolve were made"
    },
    "attempts.details": {
        "target_field": "report.attempts.attempts_text",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "Details of resolution attempts"
    },
    "attempts.authorities": {
        "target_field": "report.attempts.authorities_contacted",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 2,
        "description": "Which authorities were contacted"
    },

    # Appeal slot
    "appeal.text": {
        "target_field": "report.appeal.appeal_text_hi",
        "priority": SlotPriority.OPTIONAL,
        "required": False,
        "max_attempts": 1,
        "description": "Appeal message to authorities"
    },

    # Reporter slots
    "reporter.name": {
        "target_field": "report.reporter.name",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 2,
        "description": "Reporter's name"
    },
    "reporter.phone": {
        "target_field": "report.reporter.phone",
        "priority": SlotPriority.CORE,
        "required": True,
        "max_attempts": 3,
        "description": "Reporter's phone number"
    },
    "reporter.anonymous": {
        "target_field": "report.reporter.wants_anonymous",
        "priority": SlotPriority.IMPORTANT,
        "required": False,
        "max_attempts": 1,
        "description": "Whether to keep identity anonymous"
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_slot_config(slot_id: str) -> Optional[Dict]:
    """
    Get configuration for a specific slot.

    Args:
        slot_id: The slot identifier

    Returns:
        Slot configuration dict or None if not found
    """
    return SLOT_REGISTRY.get(slot_id)


def get_required_slots() -> List[str]:
    """
    Get list of all required slot IDs.

    Returns:
        List of slot IDs marked as required
    """
    return [
        slot_id for slot_id, config in SLOT_REGISTRY.items()
        if config.get("required", False)
    ]


def get_slots_by_priority(priority: SlotPriority) -> List[str]:
    """
    Get list of slot IDs with a specific priority.

    Args:
        priority: The priority level to filter by

    Returns:
        List of matching slot IDs
    """
    return [
        slot_id for slot_id, config in SLOT_REGISTRY.items()
        if config.get("priority") == priority
    ]


def initialize_conversation_state(report_id: str) -> ConversationState:
    """
    Create a new conversation state with proper initialization.

    Args:
        report_id: Unique identifier for the report

    Returns:
        Initialized ConversationState instance
    """
    report = Report(id=report_id)
    state = ConversationState(report=report)

    # Initialize slot statuses based on registry
    for slot_id, config in SLOT_REGISTRY.items():
        state.slot_statuses[slot_id] = SlotStatus(
            priority=config["priority"],
            max_attempts=config["max_attempts"]
        )

    return state
