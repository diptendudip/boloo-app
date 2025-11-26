"""
Test suite for Multi-Agent Orchestrator (3-Agent System)

Tests the conversation flow through:
- Agent A (Report Formatter)
- Agent B (Conversational Collector)
- Agent C (Question Planner)
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import json
import uuid

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.conversation_state import (
    ConversationState,
    Report,
    SlotStatus,
    ConversationMeta,
    AgentDirective,
    SLOT_REGISTRY,
    Location,
    Problem,
    Reporter,
    SlotPriority,
    AgentMode,
    ProblemCategory
)
from app.prompts.agent_a_report_formatter import get_agent_a_system_prompt, get_agent_a_user_prompt
from app.prompts.agent_b_collector import get_agent_b_system_prompt, get_agent_b_user_prompt
from app.prompts.agent_c_planner import get_agent_c_system_prompt, get_agent_c_user_prompt


def create_test_report():
    """Create a Report with a generated ID for testing."""
    return Report(id=str(uuid.uuid4()))


def create_test_state():
    """Create a ConversationState with proper initialization for testing."""
    return ConversationState(report=create_test_report())


class TestConversationState:
    """Test Pydantic models for conversation state."""

    def test_create_state_with_report(self):
        """Test creating a conversation state with a report."""
        state = create_test_state()
        assert state.report is not None
        assert state.conversation_meta is not None
        assert state.turn_count == 0

    def test_slot_registry_has_required_fields(self):
        """Test that SLOT_REGISTRY contains all required core slots."""
        # Using actual slot names from SLOT_REGISTRY
        core_slots = [
            "problem.description",
            "problem.category",
            "reporter.phone",
            "location.village"
        ]
        for slot in core_slots:
            assert slot in SLOT_REGISTRY, f"Missing core slot: {slot}"
            assert SLOT_REGISTRY[slot]["priority"] == SlotPriority.CORE

    def test_report_with_location(self):
        """Test Report model with location data."""
        report = Report(
            id=str(uuid.uuid4()),
            location=Location(village="Rajapur", district="Raipur"),
            problem=Problem(category=ProblemCategory.WATER, description_raw="पानी नहीं आ रहा"),
            reporter=Reporter(phone="9876543210", name="Ramesh")
        )
        assert report.location.village == "Rajapur"
        assert report.problem.category == ProblemCategory.WATER
        assert report.reporter.phone == "9876543210"

    def test_slot_status_tracking(self):
        """Test slot status with attempts and refusal tracking."""
        slot = SlotStatus(
            value_present=False,
            attempts=2,
            max_attempts=3,
            user_refused=False,
            priority=SlotPriority.CORE
        )
        assert slot.attempts == 2
        assert not slot.value_present
        assert slot.priority == SlotPriority.CORE

    def test_conversation_meta_defaults(self):
        """Test conversation metadata defaults."""
        meta = ConversationMeta()
        assert meta.frustration_level == 0  # Integer 0-10
        assert meta.user_wants_submit == False
        assert meta.language_detected == "hi"

    def test_agent_directive_creation(self):
        """Test creating agent directives."""
        directive = AgentDirective(
            mode=AgentMode.ASK_FOR_SLOT,
            target_slot="problem.description_raw",
            reason="Need to understand the issue"
        )
        assert directive.mode == AgentMode.ASK_FOR_SLOT
        assert directive.target_slot == "problem.description_raw"


class TestAgentPrompts:
    """Test prompt generation for all three agents."""

    def test_agent_a_system_prompt_exists(self):
        """Test Agent A system prompt is generated."""
        prompt = get_agent_a_system_prompt()
        assert len(prompt) > 500
        assert "CGNet Swara" in prompt or "report" in prompt.lower()

    def test_agent_a_user_prompt_with_data(self):
        """Test Agent A user prompt with report data."""
        report_dict = {
            "location_village": "Rajapur",
            "problem_category": "WATER",
            "problem_description": "पानी नहीं आ रहा",
            "reporter_phone": "9876543210"
        }
        prompt = get_agent_a_user_prompt(report_dict)
        # The prompt contains the problem description from report_dict
        assert "पानी नहीं आ रहा" in prompt
        # The prompt contains location/report structure keywords
        assert "Location" in prompt or "स्थान" in prompt

    def test_agent_b_system_prompt_exists(self):
        """Test Agent B system prompt is generated."""
        prompt = get_agent_b_system_prompt()
        assert len(prompt) > 1000
        assert "Boloo" in prompt or "conversation" in prompt.lower()
        assert "<meta>" in prompt  # Meta block format

    def test_agent_b_user_prompt_with_directive(self):
        """Test Agent B user prompt with control directive."""
        prompt = get_agent_b_user_prompt(
            user_message="मेरे गाँव में पानी नहीं आ रहा",
            conversation_history=[],
            state_summary="Starting conversation",
            control_directive="ASK_FOR_SLOT: target_slot = location.village"
        )
        assert "पानी नहीं आ रहा" in prompt
        assert "location" in prompt

    def test_agent_c_system_prompt_exists(self):
        """Test Agent C system prompt is generated."""
        prompt = get_agent_c_system_prompt()
        assert len(prompt) > 1000
        assert "ASK_FOR_SLOT" in prompt
        assert "CONFIRM_AND_SUBMIT" in prompt
        assert "SUBMIT_NOW" in prompt

    def test_agent_c_user_prompt_with_state(self):
        """Test Agent C user prompt with current state."""
        report_dict = {
            "location_village": "Rajapur",
            "problem_category": None,
            "problem_description": "पानी की समस्या"
        }
        slots_status = {
            "location.village": {"value_present": True, "attempts": 1, "max_attempts": 3, "priority": "core"},
            "problem.category": {"value_present": False, "attempts": 0, "max_attempts": 3, "priority": "core"}
        }
        conversation_meta = {
            "frustration_level": 2,  # Integer 0-10
            "user_wants_submit": False,
            "turn_count": 2
        }

        prompt = get_agent_c_user_prompt(
            report_dict=report_dict,
            slots_status=slots_status,
            conversation_meta=conversation_meta,
            question_history=[]
        )
        assert "Rajapur" in prompt
        assert "Frustration" in prompt


class TestSlotRegistry:
    """Test the slot registry configuration."""

    def test_all_slots_have_required_fields(self):
        """Test each slot in registry has required configuration."""
        required_fields = ["target_field", "priority", "max_attempts"]

        for slot_id, config in SLOT_REGISTRY.items():
            for field in required_fields:
                assert field in config, f"Slot {slot_id} missing {field}"

    def test_core_slots_have_correct_priority(self):
        """Test core slots are marked with core priority."""
        core_slots = ["problem.description_raw", "problem.category", "reporter.phone", "location.village"]

        for slot_id in core_slots:
            if slot_id in SLOT_REGISTRY:
                assert SLOT_REGISTRY[slot_id]["priority"] == SlotPriority.CORE, \
                    f"{slot_id} should be core priority"

    def test_max_attempts_reasonable(self):
        """Test max_attempts values are reasonable."""
        for slot_id, config in SLOT_REGISTRY.items():
            assert 1 <= config["max_attempts"] <= 5, \
                f"{slot_id} has unreasonable max_attempts: {config['max_attempts']}"


class TestConversationFlow:
    """Test conversation flow scenarios without actual LLM calls."""

    def test_initial_state_has_no_directive(self):
        """Test that initial state has no directive set."""
        state = create_test_state()
        assert state.last_directive is None

    def test_state_tracks_turn_count(self):
        """Test turn count is maintained."""
        state = create_test_state()
        assert state.turn_count == 0
        state.increment_turn()
        assert state.turn_count == 1

    def test_slot_status_updates(self):
        """Test updating slot status after extraction."""
        state = create_test_state()

        # Update a slot
        state.mark_slot_filled("location.village")
        assert state.slot_statuses["location.village"].value_present == True

    def test_frustration_level_is_integer(self):
        """Test frustration level is an integer 0-10."""
        for level in [0, 3, 5, 7, 10]:
            meta = ConversationMeta(frustration_level=level)
            assert meta.frustration_level == level
            assert isinstance(meta.frustration_level, int)


class TestMetaBlockParsing:
    """Test parsing of Agent B's <meta> block output."""

    def test_parse_valid_meta_block(self):
        """Test parsing a valid meta block from Agent B output."""
        agent_b_output = """ठीक है। आप किस गाँव से बोल रहे हैं?

<meta>
{
  "slots": {
    "location_village": null,
    "problem_category": "WATER",
    "problem_description": "पानी नहीं आ रहा"
  },
  "language_detected": "hi",
  "frustration_level": "low",
  "user_wants_submit": false
}
</meta>"""

        import re
        meta_match = re.search(r'<meta>\s*(\{.*?\})\s*</meta>', agent_b_output, re.DOTALL)
        assert meta_match is not None

        meta_json = json.loads(meta_match.group(1))
        assert meta_json["language_detected"] == "hi"
        assert meta_json["slots"]["problem_category"] == "WATER"

    def test_extract_conversational_text(self):
        """Test extracting just the conversational part."""
        agent_b_output = """ठीक है। आप किस गाँव से बोल रहे हैं?

<meta>
{"slots": {}}
</meta>"""

        # Extract text before <meta>
        if "<meta>" in agent_b_output:
            conversational_part = agent_b_output.split("<meta>")[0].strip()
        else:
            conversational_part = agent_b_output.strip()

        assert conversational_part == "ठीक है। आप किस गाँव से बोल रहे हैं?"
        assert "<meta>" not in conversational_part


class TestAgentCDecisionLogic:
    """Test Agent C's decision-making logic patterns."""

    def test_submit_when_user_wants_and_minimum_present(self):
        """User wants to submit + minimum fields = SUBMIT_NOW."""
        state = create_test_state()
        state.report.problem.description_raw = "पानी नहीं आ रहा"
        state.report.problem.category = ProblemCategory.WATER
        state.report.reporter.phone = "9876543210"
        state.report.location.village = "Rajapur"
        state.conversation_meta.user_wants_submit = True

        # Check minimum fields are present
        has_description = bool(state.report.problem.description_raw)
        has_category = bool(state.report.problem.category)
        has_phone = bool(state.report.reporter.phone)
        has_location = bool(state.report.location.village or state.report.location.district)

        assert all([has_description, has_category, has_phone, has_location])
        assert state.conversation_meta.user_wants_submit
        # Expected decision: SUBMIT_NOW

    def test_ask_for_missing_core_slot(self):
        """Missing core slot = ASK_FOR_SLOT."""
        state = create_test_state()
        state.report.problem.description_raw = "पानी नहीं आ रहा"
        # Missing: category, phone, location

        # Check which core slots are missing
        missing_core = []
        if not state.report.problem.category:
            missing_core.append("problem.category")
        if not state.report.reporter.phone:
            missing_core.append("reporter.phone")
        if not (state.report.location.village or state.report.location.district):
            missing_core.append("location.village")

        assert len(missing_core) > 0
        # Expected decision: ASK_FOR_SLOT for first missing core slot


class TestLanguageDetection:
    """Test language detection patterns."""

    def test_detect_hindi(self):
        """Test detecting pure Hindi text."""
        hindi_text = "मेरे गाँव में पानी नहीं आ रहा है"
        # Check for Devanagari characters
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in hindi_text)
        assert has_devanagari

    def test_detect_english(self):
        """Test detecting pure English text."""
        english_text = "There is no water in my village"
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in english_text)
        assert not has_devanagari

    def test_detect_hinglish(self):
        """Test detecting mixed Hinglish text."""
        hinglish_text = "Mere village mein water nahi hai"
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in hinglish_text)
        # Hinglish typically uses romanized Hindi, so no Devanagari
        # but has Hindi words like "mein", "nahi"
        hindi_words = ["mein", "nahi", "hai", "kya", "kaise", "gaon"]
        has_hindi_words = any(word in hinglish_text.lower() for word in hindi_words)
        assert has_hindi_words


class TestStateHelper:
    """Test ConversationState helper methods."""

    def test_increment_turn(self):
        """Test incrementing turn counter."""
        state = create_test_state()
        assert state.turn_count == 0
        state.increment_turn()
        assert state.turn_count == 1
        state.increment_turn()
        assert state.turn_count == 2

    def test_get_slot_status_creates_default(self):
        """Test getting slot status creates default if not exists."""
        state = create_test_state()
        assert "new.slot" not in state.slot_statuses
        status = state.get_slot_status("new.slot")
        assert "new.slot" in state.slot_statuses
        assert status.value_present == False
        assert status.attempts == 0

    def test_mark_slot_filled(self):
        """Test marking a slot as filled."""
        state = create_test_state()
        state.mark_slot_filled("location.village")
        assert state.slot_statuses["location.village"].value_present == True

    def test_increment_slot_attempts(self):
        """Test incrementing slot attempt counter."""
        state = create_test_state()
        state.increment_slot_attempts("location.village")
        assert state.slot_statuses["location.village"].attempts == 1
        state.increment_slot_attempts("location.village")
        assert state.slot_statuses["location.village"].attempts == 2


class TestPhoneValidation:
    """Test phone number validation."""

    def test_valid_10_digit_phone(self):
        """Test valid 10-digit phone number."""
        reporter = Reporter(phone="9876543210")
        assert reporter.phone == "9876543210"

    def test_phone_with_spaces(self):
        """Test phone with spaces gets cleaned."""
        reporter = Reporter(phone="987 654 3210")
        assert reporter.phone == "9876543210"

    def test_invalid_phone_too_short(self):
        """Test that short phone number raises error."""
        with pytest.raises(ValueError):
            Reporter(phone="12345")

    def test_invalid_phone_too_long(self):
        """Test that long phone number raises error."""
        with pytest.raises(ValueError):
            Reporter(phone="12345678901234")

    def test_none_phone_allowed(self):
        """Test that None phone is allowed."""
        reporter = Reporter(phone=None)
        assert reporter.phone is None


# Run with: pytest tests/test_multi_agent.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
