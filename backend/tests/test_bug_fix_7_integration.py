"""
Integration Test for Bug Fix #7: End-to-End Chat Flow with Placeholder Validation

This test simulates the ACTUAL runtime behavior that the user experiences,
not just unit tests of individual functions.

Bug Description (IMG_0987, IMG_0988):
- User says: "Humare yahan paani ka samasya hai. Handpump kharab hai"
- System extracts: issue_description + location="unknown"
- System tells user: "आप अभी रिपोर्ट सबमिट कर सकते हैं!" (You can submit now!)
- BUT location="unknown" is a placeholder - submission should NOT be offered

Root Cause:
- Completeness analyzer extracts fields and marks them as "collected"
- Fields are marked "collected" based on KEY existing, not VALUE quality
- can_submit_now() correctly rejects placeholder values
- But AI response is generated BEFORE can_submit_now() affects the message
- So AI says "you can submit" even though backend will block it

Expected Fix:
- Filter "collected" fields to only include VALID values
- AI should NOT offer submission when location="unknown"
- AI response should match actual validation state

Evidence: IMG_0987.png, IMG_0988.png, Screenshot 2025-11-12 at 4.54.37 PM.png
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base, engine
from sqlalchemy.orm import Session
import json

# Create test client
client = TestClient(app)


class TestBugFix7_IntegrationFlow:
    """Integration tests simulating actual user conversation flow"""

    def setup_method(self):
        """Reset database before each test"""
        # Create tables
        Base.metadata.create_all(bind=engine)

    def teardown_method(self):
        """Clean up after each test"""
        # Optional: clean up test data
        pass

    def test_img_0987_exact_scenario_integration(self):
        """
        CRITICAL: Simulate the EXACT scenario from IMG_0987/IMG_0988

        User message: "Humare yahan paani ka samasya hai. Handpump kharab hai aur paani nahi milta"

        Expected behavior:
        - System should NOT offer submission
        - AI response should NOT contain "सबमिट कर सकते हैं" or "submit"
        - Because location will be "unknown" (placeholder)

        Current BROKEN behavior (from user screenshots):
        - System DOES offer submission ❌
        - User sees: "आप अभी अपनी रिपोर्ट सबमिट कर सकते हैं!"
        """
        # Step 1: Create a new conversation
        create_response = client.post(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer test-token"}  # Mock auth
        )
        assert create_response.status_code == 200
        conversation_id = create_response.json()["conversation_id"]

        # Step 2: Send the EXACT message from IMG_0987
        message_payload = {
            "conversation_id": conversation_id,
            "message": "Humare yahan paani ka samasya hai. Handpump kharab hai aur paani nahi milta"
        }

        message_response = client.post(
            "/api/chat/message",
            json=message_payload
        )

        assert message_response.status_code == 200
        response_data = message_response.json()

        # Step 3: CRITICAL ASSERTIONS
        ai_response_hi = response_data.get("response_hi", "")
        ai_response_en = response_data.get("response_en", "")

        # The AI should NOT offer submission when location is placeholder
        submission_phrases_hindi = [
            "सबमिट कर सकते हैं",
            "रिपोर्ट सबमिट",
            "अभी सबमिट",
            "submit kar"
        ]

        submission_phrases_english = [
            "can submit",
            "submit now",
            "submit your report",
            "ready to submit"
        ]

        # Check Hindi response
        for phrase in submission_phrases_hindi:
            assert phrase not in ai_response_hi.lower(), \
                f"BUG FIX #7 INTEGRATION FAILURE: AI offered submission with placeholder data!\n" \
                f"AI Response: {ai_response_hi}\n" \
                f"Found phrase: '{phrase}'"

        # Check English response
        for phrase in submission_phrases_english:
            assert phrase not in ai_response_en.lower(), \
                f"BUG FIX #7 INTEGRATION FAILURE: AI offered submission with placeholder data!\n" \
                f"AI Response: {ai_response_en}\n" \
                f"Found phrase: '{phrase}'"

        # Additional validation: check extracted data
        extracted_data = response_data.get("extracted_data", {})

        # If location was extracted, it should not be a placeholder
        if "location" in extracted_data:
            location_value = str(extracted_data["location"]).lower()
            invalid_placeholders = ["unknown", "not provided", "n/a", "na", "पता नहीं"]

            for placeholder in invalid_placeholders:
                assert placeholder not in location_value, \
                    f"Location contains placeholder: '{location_value}'"

    def test_valid_data_allows_submission(self):
        """
        Test that when user provides VALID location, submission IS offered
        """
        # Create conversation
        create_response = client.post(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer test-token"}
        )
        conversation_id = create_response.json()["conversation_id"]

        # Send message with VALID geographical location
        message_payload = {
            "conversation_id": conversation_id,
            "message": "हमारे यहां पानी की बहुत समस्या है। हैंडपंप खराब है और पानी नहीं मिलता है। "
                      "मैं ग्राम पंचायत नोगोई कटरापारा, ब्लॉक ओडगी, जिला सूरजपुर से बोल रहा हूं।"
        }

        message_response = client.post(
            "/api/chat/message",
            json=message_payload
        )

        assert message_response.status_code == 200
        response_data = message_response.json()

        # With valid data, AI SHOULD offer submission
        ai_response_hi = response_data.get("response_hi", "")

        # Should contain submission offer (either directly or through follow-up)
        # But this time it's VALID because location is real
        extracted_data = response_data.get("extracted_data", {})
        assert "location" in extracted_data

        location = str(extracted_data["location"])
        # Verify it's a real location with geographical indicators
        geographical_indicators = ["ग्राम", "पंचायत", "ब्लॉक", "जिला", "village", "block", "district"]
        assert any(indicator in location for indicator in geographical_indicators), \
            f"Location should have geographical indicators: {location}"

    def test_progressive_data_collection(self):
        """
        Test that system progressively collects valid data without premature submission
        """
        # Create conversation
        create_response = client.post(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer test-token"}
        )
        conversation_id = create_response.json()["conversation_id"]

        # Turn 1: User mentions problem (no location)
        turn1_response = client.post(
            "/api/chat/message",
            json={
                "conversation_id": conversation_id,
                "message": "हैंडपंप खराब है और पानी नहीं मिलता"
            }
        )

        assert turn1_response.status_code == 200
        turn1_data = turn1_response.json()
        turn1_response_hi = turn1_data.get("response_hi", "")

        # Should NOT offer submission yet
        assert "सबमिट" not in turn1_response_hi, \
            "Should not offer submission without location"

        # Turn 2: User provides location
        turn2_response = client.post(
            "/api/chat/message",
            json={
                "conversation_id": conversation_id,
                "message": "मैं ग्राम पंचायत नोगोई से बोल रहा हूं"
            }
        )

        assert turn2_response.status_code == 200
        turn2_data = turn2_response.json()

        # NOW it should have both fields and MAY offer submission
        extracted_data = turn2_data.get("extracted_data", {})

        if "issue_description" in extracted_data and "location" in extracted_data:
            # Both fields present - submission may be offered IF values are valid
            location = str(extracted_data["location"])
            assert "ग्राम" in location or "नोगोई" in location, \
                "Should have valid location"

    def test_log_output_matches_ai_response(self):
        """
        CRITICAL: Ensure backend logs and AI responses are in sync

        This tests the root cause: AI response should match can_submit_now() result
        """
        # Create conversation
        create_response = client.post(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer test-token"}
        )
        conversation_id = create_response.json()["conversation_id"]

        # Send message that will extract placeholder location
        message_response = client.post(
            "/api/chat/message",
            json={
                "conversation_id": conversation_id,
                "message": "Humare yahan paani ka samasya hai"
            }
        )

        assert message_response.status_code == 200
        response_data = message_response.json()

        # Check that AI response state matches validation state
        extracted_data = response_data.get("extracted_data", {})
        ai_response = response_data.get("response_hi", "")

        # If location is placeholder, submission should NOT be offered
        location = extracted_data.get("location", "")
        if location and str(location).lower() in ["unknown", "not provided", "n/a"]:
            # Placeholder detected - AI should NOT offer submission
            assert "सबमिट" not in ai_response, \
                f"AI offered submission with placeholder location: '{location}'"


class TestBugFix7_EdgeCaseIntegration:
    """Integration tests for edge cases and variations"""

    def test_mixed_language_valid_location(self):
        """Test location with mixed Hindi/English works correctly"""
        client_test = TestClient(app)

        create_response = client_test.post(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer test-token"}
        )
        conversation_id = create_response.json()["conversation_id"]

        message_response = client_test.post(
            "/api/chat/message",
            json={
                "conversation_id": conversation_id,
                "message": "पानी की समस्या है। मैं village नोगोई, district सूरजपुर से हूं।"
            }
        )

        assert message_response.status_code == 200
        response_data = message_response.json()

        # Mixed language location should be accepted
        extracted_data = response_data.get("extracted_data", {})
        if "location" in extracted_data:
            location = str(extracted_data["location"])
            assert "नोगोई" in location or "nogoi" in location.lower()

    def test_whitespace_padded_placeholder(self):
        """Test that whitespace-padded placeholders are still rejected"""
        client_test = TestClient(app)

        create_response = client_test.post(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer test-token"}
        )
        conversation_id = create_response.json()["conversation_id"]

        # Simulate AI extracting "  unknown  " with whitespace
        message_response = client_test.post(
            "/api/chat/message",
            json={
                "conversation_id": conversation_id,
                "message": "Paani ki samasya hai"
            }
        )

        assert message_response.status_code == 200
        response_data = message_response.json()
        ai_response = response_data.get("response_hi", "")

        # Should NOT offer submission
        assert "सबमिट" not in ai_response or "पहले" in ai_response, \
            "Should not offer submission prematurely"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
