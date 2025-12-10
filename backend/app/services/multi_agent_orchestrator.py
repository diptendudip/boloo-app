"""
Multi-Agent Orchestrator Service - 3-Agent Coordination System

This orchestrator coordinates Agents A, B, and C to conduct natural, empathetic
conversations with rural citizens reporting civic issues.

Architecture:
- Agent B (Conversational Collector): User-facing agent that speaks naturally
- Agent C (Question Planner): Strategic decision-maker for next questions
- Agent A (Report Formatter): Final CGNet-style Hindi report generator

Flow:
1. Agent C determines what to ask next (based on previous turn's directive)
2. Agent B converses with user following Agent C's directive
3. Agent B extracts slots from user's response (returns text + <meta> JSON)
4. Agent C receives updated state and determines next directive
5. Loop continues until Agent C returns SUBMIT_NOW
6. Agent A formats final Hindi narrative report

Key Features:
- Circular dependency resolution (use previous directive for current turn)
- Natural language parsing with <meta> block extraction
- Robust error handling with graceful degradation
- State tracking across conversation turns
- Minimum required fields validation
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from app.services.azure_openai_service import AzureOpenAIService
from app.models.conversation_state import (
    ConversationState,
    AgentDirective,
    AgentMode,
    QuestionHistoryEntry,
    SLOT_REGISTRY,
    get_required_slots,
    SlotPriority,
    Report
)
from app.prompts.agent_a_report_formatter import (
    get_agent_a_system_prompt,
    get_agent_a_user_prompt
)
from app.prompts.agent_b_collector import (
    get_agent_b_system_prompt,
    get_agent_b_user_prompt
)
from app.prompts.agent_c_planner import (
    get_agent_c_system_prompt,
    get_agent_c_user_prompt
)


logger = logging.getLogger(__name__)


# ============================================================================
# Slot ID Mapping (Agent B output → SLOT_REGISTRY keys)
# ============================================================================

AGENT_B_SLOT_MAPPING: Dict[str, str] = {
    # Agent B's slot names → SLOT_REGISTRY keys
    "location_village": "location.village",
    "location_landmark": "location.landmark",
    "location_district": "location.district",
    "location_block": "location.block",
    "location_panchayat": "location.panchayat",
    "location_state": "location.state",
    "problem_category": "problem.category",
    "problem_description": "problem.description",
    "issue_description": "problem.description",
    "problem_duration": "problem.duration",
    "duration": "problem.duration",
    "contact_name": "reporter.name",
    "contact_phone": "reporter.phone",
    "reporter_name": "reporter.name",
    "reporter_phone": "reporter.phone",
    "phone": "reporter.phone",
    "name": "reporter.name",
    # Pass through already correct slot IDs
    "location.village": "location.village",
    "location.district": "location.district",
    "location.block": "location.block",
    "location.panchayat": "location.panchayat",
    "location.state": "location.state",
    "location.landmark": "location.landmark",
    "problem.category": "problem.category",
    "problem.description": "problem.description",
    "problem.duration": "problem.duration",
    "reporter.name": "reporter.name",
    "reporter.phone": "reporter.phone",
}


# ============================================================================
# Result Models
# ============================================================================

class OrchestratorResult(BaseModel):
    """Result from a single orchestration turn."""

    bot_response: str  # What the user sees (Hindi/English natural text)
    final_report_hi: Optional[str] = None  # Only populated if conversation completed
    conversation_complete: bool = False
    updated_state: ConversationState
    tokens_used: int = 0
    agents_called: List[str] = []  # e.g., ["B", "C"] or ["B", "C", "A"]

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Multi-Agent Orchestrator
# ============================================================================

class MultiAgentOrchestrator:
    """
    Orchestrates the 3-agent conversation system for civic complaint collection.

    This class coordinates Agent B (conversational), Agent C (planning), and
    Agent A (formatting) to conduct natural multi-turn conversations with users.
    """

    def __init__(self, openai_service: AzureOpenAIService):
        """
        Initialize the orchestrator.

        Args:
            openai_service: Configured AzureOpenAI service for LLM calls
        """
        self.openai_service = openai_service
        self.client = openai_service.client
        self.deployment_name = openai_service.deployment_name

        logger.info("MultiAgentOrchestrator initialized with 3-agent architecture")

    def process_user_turn(
        self,
        user_message: str,
        conversation_state: ConversationState
    ) -> OrchestratorResult:
        """
        Process a single user turn through the multi-agent system.

        Flow:
        1. Use PREVIOUS turn's directive for Agent B (circular dependency solution)
        2. Call Agent B with user message → get response + extracted slots
        3. Update state with extracted slots
        4. Call Agent C with updated state → get next directive
        5. If directive is SUBMIT_NOW → call Agent A → final report
        6. Return result to user

        Args:
            user_message: User's message text
            conversation_state: Current conversation state

        Returns:
            OrchestratorResult with bot response and updated state

        Raises:
            Exception: If orchestration fails critically
        """
        logger.info(
            f"🎭 Starting orchestration turn #{conversation_state.turn_count + 1} "
            f"for report {conversation_state.report.id}"
        )

        agents_called = []
        total_tokens = 0

        try:
            # ================================================================
            # STEP 1: Get directive for Agent B (use previous turn's directive)
            # ================================================================

            # First turn: default directive
            if conversation_state.turn_count == 0:
                current_directive = AgentDirective(
                    mode=AgentMode.ASK_FOR_SLOT,
                    target_slot="problem.description",
                    reason="First turn - ask user to describe their problem",
                    confidence=1.0
                )
                logger.info("📝 First turn - using default ASK_FOR_SLOT directive")
            else:
                # Use last directive from previous turn
                current_directive = conversation_state.last_directive
                if not current_directive:
                    # Fallback if somehow missing
                    current_directive = AgentDirective(
                        mode=AgentMode.ASK_FOR_SLOT,
                        target_slot="problem.description",
                        reason="Fallback directive",
                        confidence=0.8
                    )
                    logger.warning("⚠️  No previous directive found, using fallback")
                else:
                    logger.info(
                        f"♻️  Using previous directive: {current_directive.mode} "
                        f"(target: {current_directive.target_slot})"
                    )

            # ================================================================
            # STEP 2: Call Agent B (Conversational Collector)
            # ================================================================

            logger.info("🗣️  Calling Agent B (Conversational Collector)")
            agent_b_response = self._call_agent_b(
                user_message=user_message,
                conversation_history=self._build_conversation_history_summary(
                    conversation_state
                ),
                state_summary=self._build_state_summary(conversation_state),
                directive=current_directive
            )
            agents_called.append("B")
            total_tokens += agent_b_response.get("tokens_used", 0)

            # Extract bot response text and metadata
            bot_response_text = agent_b_response["response_text"]
            meta_dict = agent_b_response.get("meta", {})

            logger.info(
                f"✅ Agent B response: {bot_response_text[:80]}... "
                f"(extracted {len(meta_dict.get('slots', {}))} slot values)"
            )

            # ================================================================
            # STEP 3: Update state with extracted slots
            # ================================================================

            self._update_state_from_meta(conversation_state, meta_dict)

            # Update conversation history
            conversation_state.question_history.append(
                QuestionHistoryEntry(
                    turn=conversation_state.turn_count + 1,
                    slot_asked=current_directive.target_slot or "none",
                    user_response=user_message,
                    extracted_value=json.dumps(meta_dict.get("slots", {})),
                    timestamp=datetime.utcnow()
                )
            )

            # Update conversation metadata from Agent B's analysis
            if "frustration_level" in meta_dict:
                # Map low/medium/high to 0-10 scale
                frustration_map = {"low": 2, "medium": 5, "high": 8}
                conversation_state.conversation_meta.frustration_level = frustration_map.get(
                    meta_dict["frustration_level"],
                    5
                )

            if "user_wants_submit" in meta_dict:
                conversation_state.conversation_meta.user_wants_submit = meta_dict[
                    "user_wants_submit"
                ]

            # Increment turn counter
            conversation_state.increment_turn()

            # ================================================================
            # STEP 4: Call Agent C (Question Planner)
            # ================================================================

            logger.info("🤔 Calling Agent C (Question Planner)")
            next_directive = self._call_agent_c(
                report=conversation_state.report,
                slots_status=conversation_state.slot_statuses,
                conversation_meta=conversation_state.conversation_meta,
                question_history=conversation_state.question_history
            )
            agents_called.append("C")
            total_tokens += next_directive.get("tokens_used", 0)

            # Store directive for next turn
            conversation_state.last_directive = AgentDirective(
                mode=next_directive["mode"],
                target_slot=next_directive.get("target_slot"),
                reason=next_directive.get("reason", ""),
                confidence=1.0
            )

            logger.info(
                f"✅ Agent C directive: {next_directive['mode']} "
                f"(target: {next_directive.get('target_slot')})"
            )

            # ================================================================
            # STEP 5: Check if ready to submit
            # ================================================================

            conversation_complete = False
            final_report_hi = None

            # CONFIRM_AND_SUBMIT means all required info collected, user can submit
            if next_directive["mode"] == AgentMode.CONFIRM_AND_SUBMIT:
                logger.info("📋 Agent C says CONFIRM_AND_SUBMIT - user can submit when ready")
                conversation_complete = True  # Allow submission

            if next_directive["mode"] == AgentMode.SUBMIT_NOW:
                logger.info("📄 Agent C says SUBMIT_NOW - calling Agent A for final report")

                # Call Agent A to format final report
                final_report_hi = self._call_agent_a(conversation_state.report)
                agents_called.append("A")
                total_tokens += 500  # Approximate tokens for Agent A

                conversation_complete = True

                # Update bot response to include submission confirmation
                bot_response_text += (
                    "\n\n✅ आपकी शिकायत सफलतापूर्वक दर्ज हो गई है। "
                    "जल्द ही संबंधित अधिकारियों को भेजी जाएगी।"
                )

                logger.info("✅ Final report generated successfully")

            # ================================================================
            # STEP 6: Return orchestrator result
            # ================================================================

            result = OrchestratorResult(
                bot_response=bot_response_text,
                final_report_hi=final_report_hi,
                conversation_complete=conversation_complete,
                updated_state=conversation_state,
                tokens_used=total_tokens,
                agents_called=agents_called
            )

            logger.info(
                f"🎉 Orchestration turn complete: "
                f"agents={agents_called}, tokens={total_tokens}, "
                f"complete={conversation_complete}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}", exc_info=True)

            # Graceful fallback response
            fallback_response = (
                "माफ़ कीजिए, कुछ तकनीकी समस्या हो गई है। "
                "कृपया फिर से कोशिश करें। "
                "(Sorry, there was a technical issue. Please try again.)"
            )

            return OrchestratorResult(
                bot_response=fallback_response,
                final_report_hi=None,
                conversation_complete=False,
                updated_state=conversation_state,
                tokens_used=total_tokens,
                agents_called=agents_called
            )

    # ========================================================================
    # Agent B: Conversational Collector
    # ========================================================================

    def _call_agent_b(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        state_summary: str,
        directive: AgentDirective
    ) -> Dict[str, Any]:
        """
        Call Agent B to generate conversational response and extract slots.

        Agent B outputs:
        - Natural conversational text (Hindi/English)
        - <meta> JSON block with extracted slot values and conversation metadata

        Args:
            user_message: User's current message
            conversation_history: Previous conversation turns
            state_summary: Summary of current state
            directive: Current directive from Agent C

        Returns:
            Dict with:
                - response_text: str (natural language response)
                - meta: dict (parsed metadata with slots)
                - tokens_used: int
        """
        try:
            # Build directive string for Agent B
            directive_str = self._format_directive_for_agent_b(directive)

            # Get prompts
            system_prompt = get_agent_b_system_prompt()
            user_prompt = get_agent_b_user_prompt(
                user_message=user_message,
                conversation_history=conversation_history,
                state_summary=state_summary,
                control_directive=directive_str
            )

            # Call LLM (temperature=0.7, NO json response_format)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Higher temperature for natural conversation
                max_tokens=1000
                # NO response_format - Agent B needs to output natural text + <meta>
            )

            raw_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Parse response (extract text and <meta> block)
            parsed = self._parse_agent_b_response(raw_response)

            return {
                "response_text": parsed["text"],
                "meta": parsed["meta"],
                "tokens_used": tokens_used
            }

        except Exception as e:
            logger.error(f"Agent B call failed: {e}", exc_info=True)

            # Return safe fallback
            return {
                "response_text": "कृपया अपनी समस्या के बारे में बताएं।",
                "meta": {
                    "slots": {},
                    "frustration_level": "low",
                    "user_wants_submit": False
                },
                "tokens_used": 0
            }

    def _parse_agent_b_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Agent B's response to extract conversational text and <meta> JSON.

        Expected format:
        ```
        Natural conversational text here...

        <meta>
        {
          "slots": {...},
          "frustration_level": "low|medium|high",
          "user_wants_submit": false
        }
        </meta>
        ```

        Args:
            response_text: Raw response from Agent B

        Returns:
            Dict with "text" (conversational part) and "meta" (parsed JSON)
        """
        try:
            # Extract <meta> block using regex
            meta_pattern = r'<meta>(.*?)</meta>'
            meta_match = re.search(meta_pattern, response_text, re.DOTALL)

            if meta_match:
                # Extract text before <meta>
                text_part = response_text[:meta_match.start()].strip()

                # Extract and parse JSON from <meta>
                meta_json = meta_match.group(1).strip()
                meta_dict = json.loads(meta_json)

                return {
                    "text": text_part,
                    "meta": meta_dict
                }
            else:
                # No <meta> block found - use default values
                logger.warning("<meta> block not found in Agent B response, using defaults")
                return {
                    "text": response_text.strip(),
                    "meta": {
                        "slots": {},
                        "frustration_level": "low",
                        "user_wants_submit": False
                    }
                }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse <meta> JSON: {e}")
            # Return text with default meta
            return {
                "text": response_text.strip(),
                "meta": {
                    "slots": {},
                    "frustration_level": "low",
                    "user_wants_submit": False
                }
            }
        except Exception as e:
            logger.error(f"Agent B response parsing failed: {e}")
            return {
                "text": response_text.strip(),
                "meta": {
                    "slots": {},
                    "frustration_level": "low",
                    "user_wants_submit": False
                }
            }

    def _format_directive_for_agent_b(self, directive: AgentDirective) -> str:
        """
        Format directive into natural language instruction for Agent B.

        Args:
            directive: AgentDirective object

        Returns:
            Natural language directive string
        """
        if directive.mode == AgentMode.ASK_FOR_SLOT:
            slot_id = directive.target_slot or "problem.description"
            slot_config = SLOT_REGISTRY.get(slot_id, {})
            description = slot_config.get("description", slot_id)

            return (
                f"**Control Directive**: ASK_FOR_SLOT\n"
                f"**Target Slot**: {slot_id} ({description})\n"
                f"**Action**: Ask the user naturally about {description}. "
                f"Use conversational phrasing, not robotic questions."
            )

        elif directive.mode == AgentMode.CONFIRM_AND_SUBMIT:
            return (
                f"**Control Directive**: CONFIRM_AND_SUBMIT\n"
                f"**Action**: Summarize what you've collected and ask for confirmation. "
                f"Show them their report summary and ask if they want to submit."
            )

        elif directive.mode == AgentMode.SUBMIT_NOW:
            return (
                f"**Control Directive**: SUBMIT_NOW\n"
                f"**Action**: Thank them and confirm submission. "
                f"Let them know their report is being submitted."
            )

        elif directive.mode == AgentMode.SMALL_TALK_REASSURE:
            return (
                f"**Control Directive**: SMALL_TALK_REASSURE\n"
                f"**Action**: Give a reassuring response. Acknowledge their frustration "
                f"or concern, and gently guide them back to the conversation."
            )

        # Fallback
        return (
            f"**Control Directive**: {directive.mode}\n"
            f"**Action**: Continue the conversation naturally."
        )

    # ========================================================================
    # Agent C: Question Planner
    # ========================================================================

    def _call_agent_c(
        self,
        report: Report,
        slots_status: Dict,
        conversation_meta: Any,
        question_history: List[QuestionHistoryEntry]
    ) -> Dict[str, Any]:
        """
        Call Agent C to determine next directive.

        Agent C analyzes current state and returns one of:
        - ASK_FOR_SLOT (with target_slot)
        - CONFIRM_AND_SUBMIT
        - SUBMIT_NOW
        - SMALL_TALK_REASSURE

        Args:
            report: Current Report object
            slots_status: Status of each slot
            conversation_meta: Conversation metadata
            question_history: History of questions asked

        Returns:
            Dict with:
                - mode: AgentMode
                - target_slot: str (optional)
                - reason: str
                - tokens_used: int
        """
        try:
            # Convert report to dict for prompt
            report_dict = report.model_dump()

            # Convert slots_status to dict format
            slots_dict = {
                slot_id: {
                    "value_present": status.value_present,
                    "attempts": status.attempts,
                    "max_attempts": status.max_attempts,
                    "priority": status.priority,
                    "user_refused": status.user_refused
                }
                for slot_id, status in slots_status.items()
            }

            # Convert conversation_meta to dict
            meta_dict = {
                "frustration_level": conversation_meta.frustration_level,
                "user_wants_submit": conversation_meta.user_wants_submit,
                "turn_count": len(question_history)
            }

            # Convert question_history to list of dicts
            history_list = [
                {
                    "turn_index": entry.turn,
                    "slot_id": entry.slot_asked
                }
                for entry in question_history[-5:]  # Last 5 questions
            ]

            # Get prompts
            system_prompt = get_agent_c_system_prompt()
            user_prompt = get_agent_c_user_prompt(
                report_dict=report_dict,
                slots_status=slots_dict,
                conversation_meta=meta_dict,
                question_history=history_list
            )

            # Call LLM (temperature=0.1, JSON response format)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Very low temperature for consistent planning
                max_tokens=500,
                response_format={"type": "json_object"}  # Force JSON output
            )

            raw_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Parse JSON response
            result = json.loads(raw_response)

            # Validate mode
            mode_str = result.get("mode", "ASK_FOR_SLOT")
            try:
                result["mode"] = AgentMode(mode_str)
            except ValueError:
                logger.warning(f"Invalid mode '{mode_str}', defaulting to ASK_FOR_SLOT")
                result["mode"] = AgentMode.ASK_FOR_SLOT
                result["target_slot"] = "problem.description"

            result["tokens_used"] = tokens_used

            return result

        except Exception as e:
            logger.error(f"Agent C call failed: {e}", exc_info=True)

            # Return safe fallback - ask for core field
            unfilled_core_slots = [
                slot_id for slot_id, config in SLOT_REGISTRY.items()
                if config["priority"] == SlotPriority.CORE
                and not slots_status.get(slot_id, {}).get("value_present", False)
            ]

            target_slot = unfilled_core_slots[0] if unfilled_core_slots else "problem.description"

            return {
                "mode": AgentMode.ASK_FOR_SLOT,
                "target_slot": target_slot,
                "reason": "Fallback directive due to Agent C failure",
                "tokens_used": 0
            }

    # ========================================================================
    # Agent A: Report Formatter
    # ========================================================================

    def _call_agent_a(self, report: Report) -> str:
        """
        Call Agent A to generate final CGNet-style Hindi report.

        Agent A converts structured report data into a polished Hindi narrative
        following CGNet moderator style.

        Args:
            report: Completed Report object

        Returns:
            Hindi narrative report string
        """
        try:
            # Convert report to dict format for prompt
            report_dict = report.model_dump()

            # Get prompts
            system_prompt = get_agent_a_system_prompt()
            user_prompt = get_agent_a_user_prompt(report_dict)

            # Call LLM (temperature=0.3, NO json response_format)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent formatting
                max_tokens=1500
                # NO response_format - Agent A outputs Hindi narrative text
            )

            hindi_report = response.choices[0].message.content.strip()

            logger.info(f"✅ Agent A generated report: {len(hindi_report)} characters")

            return hindi_report

        except Exception as e:
            logger.error(f"Agent A call failed: {e}", exc_info=True)

            # Return basic fallback report
            location_str = (
                f"{report.location.village or 'अज्ञात गांव'}, "
                f"{report.location.district or 'अज्ञात जिला'}"
            )
            problem_str = report.problem.description_raw or "समस्या का विवरण उपलब्ध नहीं"

            return (
                f"{location_str} में {problem_str}। "
                f"ग्रामीण संबंधित विभाग से समाधान की मांग कर रहे हैं। "
                f"संपर्क: {report.reporter.phone or 'उपलब्ध नहीं'}"
            )

    # ========================================================================
    # State Management Helpers
    # ========================================================================

    def _update_state_from_meta(
        self,
        state: ConversationState,
        meta_dict: Dict[str, Any]
    ) -> None:
        """
        Update conversation state with extracted slots from Agent B's <meta>.

        Uses last-write-wins strategy to merge slot values into the report.
        Handles slot ID mapping from Agent B format to SLOT_REGISTRY format.

        Args:
            state: ConversationState to update
            meta_dict: Metadata dictionary from Agent B
        """
        slots = meta_dict.get("slots", {})

        for agent_b_slot_id, value in slots.items():
            if value is None or value == "null":
                continue

            # Map Agent B's slot ID to SLOT_REGISTRY slot ID
            slot_id = AGENT_B_SLOT_MAPPING.get(agent_b_slot_id, agent_b_slot_id)

            # Get slot configuration
            slot_config = SLOT_REGISTRY.get(slot_id)
            if not slot_config:
                logger.warning(f"Unknown slot ID: {agent_b_slot_id} (mapped to: {slot_id})")
                continue

            # Get target field path (e.g., "report.location.village")
            target_field = slot_config["target_field"]

            # Update report using dot notation path
            self._set_nested_field(state.report, target_field, value)

            # Mark slot as filled
            state.mark_slot_filled(slot_id)

            logger.info(f"✅ Updated slot {agent_b_slot_id} → {slot_id} = {value}")

    def _set_nested_field(self, obj: Any, field_path: str, value: Any) -> None:
        """
        Set a nested field using dot notation path.

        Example: "report.location.village" → obj.location.village = value

        Args:
            obj: Object to update
            field_path: Dot-separated field path
            value: Value to set
        """
        parts = field_path.split(".")

        # Skip "report" prefix if present
        if parts[0] == "report":
            parts = parts[1:]

        # Navigate to parent object
        current = obj
        for part in parts[:-1]:
            current = getattr(current, part)

        # Set final field
        setattr(current, parts[-1], value)

    def _build_state_summary(self, state: ConversationState) -> str:
        """
        Build compact state summary for Agent B.

        Shows what's been collected so far and what's still needed.

        Args:
            state: ConversationState

        Returns:
            Human-readable state summary string
        """
        filled_slots = [
            slot_id for slot_id, status in state.slot_statuses.items()
            if status.value_present
        ]

        unfilled_core = [
            slot_id for slot_id, config in SLOT_REGISTRY.items()
            if config["priority"] == SlotPriority.CORE
            and not state.slot_statuses.get(slot_id, {}).value_present
        ]

        summary = f"**State Summary**\n"
        summary += f"- Turn: {state.turn_count}\n"
        summary += f"- Filled slots: {len(filled_slots)}/{len(SLOT_REGISTRY)}\n"
        summary += f"- Core slots remaining: {len(unfilled_core)}\n"
        summary += f"- Frustration level: {state.conversation_meta.frustration_level}/10\n"
        summary += f"- User wants submit: {state.conversation_meta.user_wants_submit}\n"

        return summary

    def _build_conversation_history_summary(
        self,
        state: ConversationState
    ) -> List[Dict[str, str]]:
        """
        Build conversation history summary for Agent B.

        Truncates to last 5 turns to avoid context bloat.

        Args:
            state: ConversationState

        Returns:
            List of conversation turns with user/ai roles
        """
        # For now, return empty list (would need to track full conversation)
        # This would be populated from actual conversation turns stored in state
        return []

    # ========================================================================
    # Validation Helpers
    # ========================================================================

    def _has_minimum_required_fields(self, report: Report) -> bool:
        """
        Check if report has minimum required fields for submission.

        Minimum requirements:
        - problem.description_raw (MUST have)
        - problem.category (MUST have)
        - reporter.phone (MUST have)
        - location.village OR location.district (MUST have at least one)

        Args:
            report: Report to validate

        Returns:
            True if minimum fields present, False otherwise
        """
        has_description = bool(report.problem.description_raw)
        has_category = bool(report.problem.category)
        has_phone = bool(report.reporter.phone)
        has_location = bool(report.location.village or report.location.district)

        return all([has_description, has_category, has_phone, has_location])


# ============================================================================
# Global Instance
# ============================================================================

_orchestrator_instance: Optional[MultiAgentOrchestrator] = None


def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """
    Get or create global MultiAgentOrchestrator instance.

    Returns:
        MultiAgentOrchestrator instance
    """
    global _orchestrator_instance

    if _orchestrator_instance is None:
        from app.services.azure_openai_service import get_azure_openai_service
        openai_service = get_azure_openai_service()
        _orchestrator_instance = MultiAgentOrchestrator(openai_service)

    return _orchestrator_instance
