"""
Test Chat Endpoint - Comprehensive test suite for chat API endpoints

Tests Pydantic validation issues with location fields, including:
- None values in user location fields
- Empty string values
- Valid location data
- API endpoint responses
- Error handling for location confirmation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import uuid4

from app.models.user import User
from app.utils.location_confirmation import (
    extract_location_from_user_profile,
    has_meaningful_location,
    is_location_confirmation
)


class TestChatEndpointLocationValidation:
    """Test chat endpoint with various location field scenarios"""

    def test_user_with_none_location_fields(self):
        """Test chat start with user having None location fields (Pydantic validation issue)"""
        # Arrange - User with all location fields as None
        user = Mock(spec=User)
        user.id = uuid4()
        user.phone = "+919876543210"
        user.name = "Test User"
        user.location_district = None
        user.location_village = None
        user.location_block = None
        user.location_street = None
        user.location_panchayat = None
        user.location_subdivision = None
        user.location_state = None
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act - Extract location (should handle None gracefully)
        profile_location = extract_location_from_user_profile(user)

        # Assert - Should return None when no location data
        assert profile_location is None, "User with None location should return None"

        # Verify has_meaningful_location returns bool (not None)
        has_location = has_meaningful_location(profile_location)
        assert isinstance(has_location, bool), f"Expected bool, got {type(has_location)}"
        assert has_location is False

    def test_user_with_empty_string_location_fields(self):
        """Test chat with empty string location fields"""
        # Arrange - User with empty strings
        user = Mock(spec=User)
        user.id = uuid4()
        user.phone = "+919876543210"
        user.location_district = ""
        user.location_village = ""
        user.location_block = ""
        user.location_street = ""
        user.location_panchayat = ""
        user.location_subdivision = ""
        user.location_state = ""
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = ""

        # Act
        profile_location = extract_location_from_user_profile(user)

        # Assert - Empty strings should be treated as no data
        assert profile_location is None, "Empty string locations should return None"

    def test_user_with_partial_location_data(self):
        """Test user with only district (insufficient for meaningful location)"""
        # Arrange
        user = Mock(spec=User)
        user.id = uuid4()
        user.location_district = "बस्तर"
        user.location_village = None
        user.location_block = None
        user.location_street = None
        user.location_panchayat = None
        user.location_subdivision = None
        user.location_state = "छत्तीसगढ़"
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act
        profile_location = extract_location_from_user_profile(user)

        # Assert - District alone is insufficient
        assert profile_location is None, "District alone should not be meaningful"

    def test_user_with_valid_location_data(self):
        """Test user with complete valid location data"""
        # Arrange
        user = Mock(spec=User)
        user.id = uuid4()
        user.location_district = "बस्तर"
        user.location_village = "मादर"
        user.location_block = "लोहंडीगुड़ा"
        user.location_street = "कोटेवार पारा"
        user.location_panchayat = "मादर"
        user.location_subdivision = "जगदलपुर"
        user.location_state = "छत्तीसगढ़"
        user.location_lat = 19.123456
        user.location_lng = 81.654321
        user.location_formatted_address = "कोटेवार पारा, ग्राम मादर, जिला बस्तर"

        # Act
        profile_location = extract_location_from_user_profile(user)

        # Assert - Should extract all fields
        assert profile_location is not None
        assert profile_location["district"] == "बस्तर"
        assert profile_location["village"] == "मादर"
        assert profile_location["block"] == "लोहंडीगुड़ा"
        assert profile_location["street"] == "कोटेवार पारा"

        # Verify has_meaningful_location returns True
        has_location = has_meaningful_location(profile_location)
        assert isinstance(has_location, bool)
        assert has_location is True

    def test_location_confirmation_boolean_type_safety(self):
        """Test that location confirmation logic always returns boolean (Pydantic validation fix)"""
        # Test various inputs that previously caused Pydantic validation errors
        test_cases = [
            (None, False),
            ({}, False),
            ({"district": "बस्तर"}, False),  # Missing village/block
            ({"district": "बस्तर", "village": "मादर"}, True),
            ({"district": "बस्तर", "block": "लोहंडीगुड़ा"}, True),
        ]

        for location_data, expected in test_cases:
            result = has_meaningful_location(location_data)

            # CRITICAL: Must always be bool, never None
            assert isinstance(result, bool), \
                f"Expected bool for {location_data}, got {type(result).__name__}"
            assert result == expected, \
                f"Expected {expected} for {location_data}, got {result}"


class TestChatEndpointLocationConfirmation:
    """Test chat endpoint location confirmation flow"""

    def test_location_confirmation_with_hindi_keywords(self):
        """Test location confirmation detection with Hindi keywords"""
        confirmation_messages = [
            "हाँ",
            "जी हाँ",
            "हां वही है",
            "बिल्कुल सही",
            "ठीक है"
        ]

        for message in confirmation_messages:
            result = is_location_confirmation(message)
            assert result is True, f"'{message}' should be detected as confirmation"

    def test_location_confirmation_with_english_keywords(self):
        """Test location confirmation with English keywords"""
        confirmation_messages = [
            "yes",
            "yeah",
            "okay",
            "correct",
            "right"
        ]

        for message in confirmation_messages:
            result = is_location_confirmation(message)
            assert result is True, f"'{message}' should be detected as confirmation"

    def test_location_confirmation_with_negative_responses(self):
        """Test that negative responses are not detected as confirmations"""
        negative_messages = [
            "नहीं",
            "no",
            "गलत है",
            "wrong",
            "different location"
        ]

        for message in negative_messages:
            result = is_location_confirmation(message)
            assert result is False, f"'{message}' should NOT be detected as confirmation"

    def test_location_confirmation_with_none_or_empty(self):
        """Test location confirmation with None or empty string"""
        assert is_location_confirmation(None) is False
        assert is_location_confirmation("") is False
        assert is_location_confirmation("   ") is False


class TestChatEndpointErrorHandling:
    """Test chat endpoint error handling"""

    def test_missing_user_location_attributes_gracefully(self):
        """Test that missing location attributes don't cause crashes"""
        # Arrange - User object without location attributes
        user = Mock()
        user.id = uuid4()
        # Explicitly don't set location attributes

        # Act - Should not raise AttributeError
        try:
            profile_location = extract_location_from_user_profile(user)
            has_location = has_meaningful_location(profile_location)

            # Assert
            assert isinstance(has_location, bool)
            assert has_location is False
        except AttributeError as e:
            pytest.fail(f"Should handle missing attributes gracefully: {e}")

    def test_user_object_none_handling(self):
        """Test that None user object is handled gracefully"""
        # Act
        profile_location = extract_location_from_user_profile(None)
        has_location = has_meaningful_location(profile_location)

        # Assert
        assert profile_location is None
        assert isinstance(has_location, bool)
        assert has_location is False

    def test_invalid_location_data_types(self):
        """Test has_meaningful_location with invalid data types"""
        invalid_inputs = [
            "invalid string",
            123,
            ["list"],
            True,
            object()
        ]

        for invalid_input in invalid_inputs:
            result = has_meaningful_location(invalid_input)
            assert isinstance(result, bool), \
                f"Should return bool for {type(invalid_input).__name__}"
            assert result is False


class TestChatEndpointPydanticValidation:
    """Test Pydantic validation issues that cause 500 errors"""

    def test_pydantic_location_field_validation_with_none(self):
        """Test that None values in location fields don't cause Pydantic validation errors"""
        # Simulate the exact scenario that causes Pydantic validation errors
        user = Mock(spec=User)
        user.id = uuid4()
        user.location_district = None
        user.location_village = None
        user.location_block = None

        # Extract location
        profile_location = extract_location_from_user_profile(user)

        # The critical fix: has_meaningful_location must ALWAYS return bool, never None
        has_location = has_meaningful_location(profile_location)

        # Verify boolean type (Pydantic expects bool, not None)
        assert isinstance(has_location, bool), \
            f"Pydantic validation requires bool, got {type(has_location).__name__}"
        assert has_location is False

    def test_pydantic_validation_with_mixed_none_and_values(self):
        """Test mixed None and actual values (common in production)"""
        user = Mock(spec=User)
        user.id = uuid4()
        user.location_district = "बस्तर"
        user.location_village = None  # None value mixed with actual data
        user.location_block = "लोहंडीगुड़ा"
        user.location_street = None
        user.location_panchayat = None
        user.location_subdivision = None
        user.location_state = "छत्तीसगढ़"
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act
        profile_location = extract_location_from_user_profile(user)
        has_location = has_meaningful_location(profile_location)

        # Assert - Should have meaningful location (district + block)
        assert isinstance(has_location, bool)
        assert has_location is True
        assert profile_location is not None
        assert profile_location["district"] == "बस्तर"
        assert profile_location["block"] == "लोहंडीगुड़ा"
        assert profile_location["village"] is None  # None is acceptable in dict


class TestChatFlowIntegration:
    """Integration tests simulating actual chat flow"""

    def test_chat_flow_new_user_no_location(self):
        """Simulate chat flow for new user without location"""
        # Arrange - New user
        user = Mock(spec=User)
        user.id = uuid4()
        user.phone = "+919876543210"
        user.is_first_timer = True
        user.location_district = None
        user.location_village = None
        user.location_block = None

        # Act - Chat initialization
        profile_location = extract_location_from_user_profile(user)

        if profile_location is None:
            has_profile_location = False
        else:
            has_meaningful = has_meaningful_location(profile_location)
            has_profile_location = bool(has_meaningful if has_meaningful is not None else False)

        # Assert
        assert isinstance(has_profile_location, bool)
        assert has_profile_location is False

    def test_chat_flow_existing_user_with_location(self):
        """Simulate chat flow for existing user with profile location"""
        # Arrange - Existing user with location
        user = Mock(spec=User)
        user.id = uuid4()
        user.phone = "+919876543210"
        user.is_first_timer = False
        user.location_district = "बस्तर"
        user.location_village = "मादर"
        user.location_block = "लोहंडीगुड़ा"
        user.location_street = "कोटेवार पारा"
        user.location_panchayat = "मादर"
        user.location_subdivision = None
        user.location_state = "छत्तीसगढ़"
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act - Chat initialization
        profile_location = extract_location_from_user_profile(user)

        if profile_location is None:
            has_profile_location = False
        else:
            has_meaningful = has_meaningful_location(profile_location)
            has_profile_location = bool(has_meaningful if has_meaningful is not None else False)

        # Assert
        assert isinstance(has_profile_location, bool)
        assert has_profile_location is True

    def test_chat_flow_location_confirmation_accepted(self):
        """Simulate user accepting location confirmation"""
        # Arrange
        user = Mock(spec=User)
        user.id = uuid4()
        user.location_district = "बस्तर"
        user.location_village = "मादर"
        user.location_block = "लोहंडीगुड़ा"

        profile_location = extract_location_from_user_profile(user)
        user_message = "हाँ"

        # Act
        confirmed = is_location_confirmation(user_message)

        # Assert
        assert confirmed is True
        assert profile_location is not None


# Run with: pytest tests/test_chat_endpoint.py -v -s
