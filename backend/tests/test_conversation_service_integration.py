"""
Integration tests for ConversationService with Azure OpenAI

Tests the real Azure OpenAI integration replacing mock implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.conversation_service import (
    ConversationService,
    ConversationState,
    ConversationSlots,
    IntentType,
    ConfidenceLevel,
    TriageResult
)
from app.services.azure_openai_service import (
    AzureOpenAIService,
    AzureOpenAIAPIError,
    AzureOpenAIServiceError
)


class TestConversationServiceAzureIntegration:
    """Test ConversationService with Azure OpenAI integration"""

    @pytest.fixture
    def mock_azure_service(self):
        """Create mock Azure OpenAI service"""
        mock_service = Mock(spec=AzureOpenAIService)
        return mock_service

    @pytest.fixture
    def conversation_service(self, mock_azure_service):
        """Create ConversationService with mocked Azure OpenAI"""
        return ConversationService(azure_openai_service=mock_azure_service)

    def test_service_initialization(self, conversation_service, mock_azure_service):
        """Test service initializes with Azure OpenAI service"""
        assert conversation_service.azure_openai_service == mock_azure_service

    def test_process_triage_grievance(self, conversation_service, mock_azure_service):
        """Test triage classification for grievance intent"""
        # Mock Azure OpenAI response
        mock_azure_service.classify_intent.return_value = {
            "intent": "grievance",
            "confidence": 0.95,
            "confidence_level": "high",
            "reasoning": "User reporting water supply issue",
            "suggested_issue_type": "water_supply"
        }

        transcript = "हमारे गांव में पानी नहीं आ रहा है 2 हफ्ते से"
        result = conversation_service.process_triage(transcript)

        # Verify result
        assert result.intent == IntentType.GRIEVANCE
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.topic_hint == "water_supply"
        assert "water supply" in result.reasoning.lower()

        # Verify Azure OpenAI was called
        mock_azure_service.classify_intent.assert_called_once_with(
            transcript=transcript,
            location_hint=None
        )

    def test_process_triage_community(self, conversation_service, mock_azure_service):
        """Test triage classification for community intent"""
        mock_azure_service.classify_intent.return_value = {
            "intent": "community",
            "confidence": 0.88,
            "confidence_level": "high",
            "reasoning": "User wants to share traditional song",
            "suggested_issue_type": None
        }

        transcript = "मैं अपनी नानी का गाना सबको सुनाना चाहता हूं"
        result = conversation_service.process_triage(transcript)

        assert result.intent == IntentType.COMMUNITY
        assert result.confidence == ConfidenceLevel.HIGH

    def test_process_triage_personal(self, conversation_service, mock_azure_service):
        """Test triage classification for personal intent"""
        mock_azure_service.classify_intent.return_value = {
            "intent": "personal",
            "confidence": 0.92,
            "confidence_level": "high",
            "reasoning": "User creating personal reminder",
            "suggested_issue_type": None
        }

        transcript = "मुझे कल डॉक्टर के पास जाना है, याद दिलाना"
        result = conversation_service.process_triage(transcript)

        assert result.intent == IntentType.PERSONAL
        assert result.confidence == ConfidenceLevel.HIGH

    def test_process_triage_uncertain(self, conversation_service, mock_azure_service):
        """Test triage classification for uncertain intent"""
        mock_azure_service.classify_intent.return_value = {
            "intent": "uncertain",
            "confidence": 0.45,
            "confidence_level": "low",
            "reasoning": "Unclear user intent",
            "suggested_issue_type": None
        }

        transcript = "हाँ ठीक है"
        result = conversation_service.process_triage(transcript)

        assert result.intent == IntentType.UNCERTAIN
        assert result.confidence == ConfidenceLevel.LOW

    def test_process_triage_retry_on_failure(self, conversation_service, mock_azure_service):
        """Test triage retries on API failure"""
        # First two calls fail, third succeeds
        mock_azure_service.classify_intent.side_effect = [
            AzureOpenAIAPIError("Connection timeout"),
            AzureOpenAIAPIError("Rate limit"),
            {
                "intent": "grievance",
                "confidence": 0.90,
                "confidence_level": "high",
                "reasoning": "Water issue",
                "suggested_issue_type": "water_supply"
            }
        ]

        transcript = "पानी की समस्या है"
        result = conversation_service.process_triage(transcript)

        # Should succeed on third attempt
        assert result.intent == IntentType.GRIEVANCE
        assert mock_azure_service.classify_intent.call_count == 3

    def test_process_triage_fails_after_max_retries(self, conversation_service, mock_azure_service):
        """Test triage fails after max retries"""
        # All calls fail
        mock_azure_service.classify_intent.side_effect = AzureOpenAIAPIError("Connection error")

        transcript = "पानी की समस्या है"

        with pytest.raises(AzureOpenAIServiceError) as exc_info:
            conversation_service.process_triage(transcript)

        assert "Failed to classify intent after 3 attempts" in str(exc_info.value)
        assert mock_azure_service.classify_intent.call_count == 3

    def test_process_turn_grievance(self, conversation_service, mock_azure_service):
        """Test processing a grievance conversation turn"""
        # Create conversation state
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.GRIEVANCE,
            slots=ConversationSlots()
        )

        # Mock Azure OpenAI conversation response
        mock_azure_service.generate_conversation_response.return_value = {
            "response_hi": "समझ गया। आपके गांव का नाम बताइए?",
            "response_en": "I understand. What is your village name?",
            "empathy_used": True,
            "next_field_asked": "location"
        }

        transcript = "हमारे यहां बिजली नहीं आती"
        response, updated_state = conversation_service.process_turn(state, transcript)

        # Verify response
        assert "गांव का नाम" in response
        assert len(updated_state.turns) == 2  # User + Agent turns
        assert updated_state.turns[0].speaker == "user"
        assert updated_state.turns[1].speaker == "agent"

        # Verify Azure OpenAI was called
        mock_azure_service.generate_conversation_response.assert_called_once()

    def test_process_turn_handles_api_error(self, conversation_service, mock_azure_service):
        """Test turn processing handles API errors gracefully"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.GRIEVANCE
        )

        # Mock API failure
        mock_azure_service.generate_conversation_response.side_effect = (
            AzureOpenAIAPIError("Service unavailable")
        )

        transcript = "बिजली नहीं आती"
        response, updated_state = conversation_service.process_turn(state, transcript)

        # Should return fallback template response (not error message)
        # Fallback asks for missing field
        assert response is not None and len(response) > 0
        assert len(updated_state.turns) == 2

    def test_process_turn_empty_transcript_raises_error(self, conversation_service):
        """Test empty transcript raises ValueError"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.GRIEVANCE
        )

        with pytest.raises(ValueError) as exc_info:
            conversation_service.process_turn(state, "")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_grievance_turn_with_conversation_context(self, conversation_service, mock_azure_service):
        """Test grievance turn passes conversation context to Azure OpenAI"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.GRIEVANCE,
            slots=ConversationSlots(location_text="Raipur")
        )

        # Add previous conversation turns
        from app.services.conversation_service import ConversationTurn
        state.turns.append(ConversationTurn(
            speaker="user",
            text_hindi="बिजली की समस्या है"
        ))
        state.turns.append(ConversationTurn(
            speaker="agent",
            text_hindi="कहां की समस्या है?"
        ))

        mock_azure_service.generate_conversation_response.return_value = {
            "response_hi": "ठीक है, कब से यह समस्या है?",
            "response_en": "Okay, since when is this problem?",
            "empathy_used": True,
            "next_field_asked": "when_started"
        }

        transcript = "रायपुर में"
        response, updated_state = conversation_service.process_turn(state, transcript)

        # Verify conversation history was passed
        call_args = mock_azure_service.generate_conversation_response.call_args
        assert call_args[1]["conversation_history"] is not None
        assert call_args[1]["collected_data"]["location"] == "Raipur"

    def test_community_turn_with_azure_openai(self, conversation_service, mock_azure_service):
        """Test community story turn uses Azure OpenAI"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.COMMUNITY,
            slots=ConversationSlots()
        )

        mock_azure_service.generate_conversation_response.return_value = {
            "response_hi": "वाह! बहुत अच्छा! कहां की है यह?",
            "response_en": "Wow! Very nice! Where is this from?",
            "empathy_used": True,
            "next_field_asked": "location"
        }

        transcript = "मेरी नानी का पुराना गाना है"
        response, updated_state = conversation_service.process_turn(state, transcript)

        assert "कहां की" in response
        mock_azure_service.generate_conversation_response.assert_called_once()

    def test_personal_turn_with_azure_openai(self, conversation_service, mock_azure_service):
        """Test personal diary turn uses Azure OpenAI"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.PERSONAL,
            slots=ConversationSlots()
        )

        mock_azure_service.generate_conversation_response.return_value = {
            "response_hi": "समझ गया। कोई रिमाइंडर चाहिए?",
            "response_en": "Got it. Do you need a reminder?",
            "empathy_used": True,
            "next_field_asked": "reminder"
        }

        transcript = "कल डॉक्टर के पास जाना है"
        response, updated_state = conversation_service.process_turn(state, transcript)

        assert "रिमाइंडर" in response
        # Verify title and note were set
        assert updated_state.slots.short_title is not None

    def test_conversation_completion(self, conversation_service, mock_azure_service):
        """Test conversation marks as complete when all fields collected"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.GRIEVANCE,
            slots=ConversationSlots(
                location_text="Raipur",
                issue_type="electricity"
            )
        )

        mock_azure_service.generate_conversation_response.return_value = {
            "response_hi": "बहुत अच्छा! शिकायत तैयार है। पुष्टि करें?",
            "response_en": "Great! Complaint is ready. Confirm?",
            "empathy_used": True,
            "next_field_asked": None
        }

        transcript = "हाँ, ठीक है"
        response, updated_state = conversation_service.process_turn(state, transcript)

        assert updated_state.is_complete
        assert updated_state.formal_summary is not None


class TestConversationServiceRealWorld:
    """Test real-world conversation scenarios"""

    @pytest.fixture
    def mock_azure_service(self):
        mock = Mock(spec=AzureOpenAIService)
        return mock

    @pytest.fixture
    def service(self, mock_azure_service):
        return ConversationService(azure_openai_service=mock_azure_service)

    def test_full_grievance_conversation_flow(self, service, mock_azure_service):
        """Test complete grievance reporting conversation"""
        # Mock triage
        mock_azure_service.classify_intent.return_value = {
            "intent": "grievance",
            "confidence": 0.95,
            "confidence_level": "high",
            "reasoning": "Water supply issue",
            "suggested_issue_type": "water_supply"
        }

        # Start conversation
        triage = service.process_triage("हमारे गांव में पानी नहीं आ रहा")
        assert triage.intent == IntentType.GRIEVANCE

        # Create state
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=triage.intent
        )

        # Mock conversation responses
        mock_azure_service.generate_conversation_response.side_effect = [
            {
                "response_hi": "समझ गया। गांव का नाम बताइए?",
                "response_en": "I understand. Village name?",
                "empathy_used": True,
                "next_field_asked": "location"
            },
            {
                "response_hi": "ठीक है। कब से यह समस्या है?",
                "response_en": "Okay. Since when?",
                "empathy_used": True,
                "next_field_asked": "when_started"
            },
            {
                "response_hi": "शिकायत तैयार है। पुष्टि करें?",
                "response_en": "Complaint ready. Confirm?",
                "empathy_used": True,
                "next_field_asked": None
            }
        ]

        # Conversation turns
        response1, state = service.process_turn(state, "हमारे गांव में पानी नहीं आ रहा")
        assert "गांव" in response1

        response2, state = service.process_turn(state, "नीलकंठपुर")
        assert "कब से" in response2

        response3, state = service.process_turn(state, "2 हफ्ते से")
        assert "तैयार" in response3 or "पुष्टि" in response3

    def test_api_fallback_on_failure(self, service, mock_azure_service):
        """Test service falls back to templates when Azure OpenAI fails"""
        state = ConversationState(
            conversation_id="test-123",
            user_id="user-456",
            intent=IntentType.GRIEVANCE,
            slots=ConversationSlots()  # No location yet
        )

        # Mock all retries fail
        mock_azure_service.generate_conversation_response.side_effect = (
            AzureOpenAIAPIError("Service down")
        )

        transcript = "बिजली नहीं आती"
        response, state = service.process_turn(state, transcript)

        # Should get fallback template response
        assert "गांव" in response or "मोहल्ला" in response
        # User turn should still be recorded
        assert len(state.turns) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
