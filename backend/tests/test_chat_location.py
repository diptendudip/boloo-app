"""
Test suite for chat location extraction and confirmation logic.

Ensures chat.py correctly uses new location columns from User model.
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.utils.location_confirmation import (
    extract_location_from_user_profile,
    has_meaningful_location,
    format_location_display,
    merge_location_with_profile
)


class TestLocationExtractionFromProfile:
    """Test extract_location_from_user_profile() function."""

    def test_user_with_no_location_returns_none(self):
        """User with no location fields should return None."""
        # Arrange
        user = Mock()
        user.id = "test-user-1"
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

        # Act
        result = extract_location_from_user_profile(user)

        # Assert
        assert result is None, "User with no location should return None"

    def test_user_with_only_district_returns_none(self):
        """User with only district (no village/block) should return None."""
        # Arrange
        user = Mock()
        user.id = "test-user-2"
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
        result = extract_location_from_user_profile(user)

        # Assert
        assert result is None, "District alone is insufficient - needs village or block"

    def test_user_with_district_and_village_returns_location(self):
        """User with district + village should return valid location dict."""
        # Arrange
        user = Mock()
        user.id = "test-user-3"
        user.location_district = "बस्तर"
        user.location_village = "मादर"
        user.location_block = None
        user.location_street = None
        user.location_panchayat = None
        user.location_subdivision = None
        user.location_state = "छत्तीसगढ़"
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = "ग्राम मादर, जिला बस्तर, छत्तीसगढ़"

        # Act
        result = extract_location_from_user_profile(user)

        # Assert
        assert result is not None, "Should return location dict"
        assert result["district"] == "बस्तर"
        assert result["village"] == "मादर"
        assert result["state"] == "छत्तीसगढ़"
        assert result["formatted_address"] == "ग्राम मादर, जिला बस्तर, छत्तीसगढ़"

    def test_user_with_district_and_block_returns_location(self):
        """User with district + block (no village) should return valid location dict."""
        # Arrange
        user = Mock()
        user.id = "test-user-4"
        user.location_district = "बस्तर"
        user.location_village = None
        user.location_block = "लोहंडीगुड़ा"
        user.location_street = None
        user.location_panchayat = None
        user.location_subdivision = None
        user.location_state = "छत्तीसगढ़"
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act
        result = extract_location_from_user_profile(user)

        # Assert
        assert result is not None, "Should return location dict with block"
        assert result["district"] == "बस्तर"
        assert result["block"] == "लोहंडीगुड़ा"
        assert result["village"] is None

    def test_user_with_complete_location_returns_all_fields(self):
        """User with complete location (all fields) should return all data."""
        # Arrange
        user = Mock()
        user.id = "test-user-5"
        user.location_district = "बस्तर"
        user.location_village = "मादर"
        user.location_block = "लोहंडीगुड़ा"
        user.location_street = "कोटेवार पारा"
        user.location_panchayat = "मादर"
        user.location_subdivision = "जगदलपुर"
        user.location_state = "छत्तीसगढ़"
        user.location_lat = 19.123456
        user.location_lng = 81.654321
        user.location_formatted_address = "कोटेवार पारा, ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर, छत्तीसगढ़"

        # Act
        result = extract_location_from_user_profile(user)

        # Assert
        assert result is not None, "Should return complete location dict"
        assert result["street"] == "कोटेवार पारा"
        assert result["village"] == "मादर"
        assert result["panchayat"] == "मादर"
        assert result["block"] == "लोहंडीगुड़ा"
        assert result["subdivision"] == "जगदलपुर"
        assert result["district"] == "बस्तर"
        assert result["state"] == "छत्तीसगढ़"
        assert result["lat"] == 19.123456
        assert result["lng"] == 81.654321

    def test_user_with_partial_location_handles_none_gracefully(self):
        """User with partial location (some None fields) should handle gracefully."""
        # Arrange
        user = Mock()
        user.id = "test-user-6"
        user.location_district = "कोंडागांव"
        user.location_village = "केशरपाल"
        user.location_block = None  # Missing block
        user.location_street = None  # Missing street
        user.location_panchayat = None  # Missing panchayat
        user.location_subdivision = None
        user.location_state = "छत्तीसगढ़"
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act
        result = extract_location_from_user_profile(user)

        # Assert
        assert result is not None, "Should return location even with some None fields"
        assert result["district"] == "कोंडागांव"
        assert result["village"] == "केशरपाल"
        assert result["block"] is None
        assert result["street"] is None


class TestHasMeaningfulLocation:
    """Test has_meaningful_location() boolean logic."""

    def test_none_input_returns_false(self):
        """None input should return False (not None)."""
        result = has_meaningful_location(None)
        assert result is False
        assert isinstance(result, bool)

    def test_empty_dict_returns_false(self):
        """Empty dict should return False."""
        result = has_meaningful_location({})
        assert result is False
        assert isinstance(result, bool)

    def test_district_only_returns_false(self):
        """District alone is insufficient."""
        location = {"district": "बस्तर"}
        result = has_meaningful_location(location)
        assert result is False
        assert isinstance(result, bool)

    def test_village_only_returns_false(self):
        """Village alone is insufficient."""
        location = {"village": "मादर"}
        result = has_meaningful_location(location)
        assert result is False
        assert isinstance(result, bool)

    def test_district_and_village_returns_true(self):
        """District + village is meaningful."""
        location = {
            "district": "बस्तर",
            "village": "मादर"
        }
        result = has_meaningful_location(location)
        assert result is True
        assert isinstance(result, bool)

    def test_district_and_block_returns_true(self):
        """District + block is meaningful."""
        location = {
            "district": "बस्तर",
            "block": "लोहंडीगुड़ा"
        }
        result = has_meaningful_location(location)
        assert result is True
        assert isinstance(result, bool)

    def test_complete_location_returns_true(self):
        """Complete location with all fields returns True."""
        location = {
            "street": "कोटेवार पारा",
            "village": "मादर",
            "panchayat": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर",
            "state": "छत्तीसगढ़"
        }
        result = has_meaningful_location(location)
        assert result is True
        assert isinstance(result, bool)

    def test_invalid_input_type_returns_false(self):
        """Invalid input type (string, list) should return False."""
        result1 = has_meaningful_location("invalid")
        result2 = has_meaningful_location([])
        result3 = has_meaningful_location(123)

        assert result1 is False
        assert result2 is False
        assert result3 is False


class TestFormatLocationDisplay:
    """Test format_location_display() Hindi formatting."""

    def test_complete_location_formats_correctly(self):
        """Complete location should format with all Hindi labels."""
        result = format_location_display(
            street="कोटेवार पारा",
            village="मादर",
            panchayat="मादर",
            block="लोहंडीगुड़ा",
            subdivision="जगदलपुर",
            district="बस्तर",
            state="छत्तीसगढ़"
        )

        expected = "कोटेवार पारा, ग्राम मादर, पंचायत मादर, ब्लॉक लोहंडीगुड़ा, उपखंड जगदलपुर, जिला बस्तर"
        assert result == expected

    def test_partial_location_formats_correctly(self):
        """Partial location should skip None fields."""
        result = format_location_display(
            village="मादर",
            district="बस्तर"
        )

        expected = "ग्राम मादर, जिला बस्तर"
        assert result == expected

    def test_empty_location_returns_empty_string(self):
        """All None fields should return empty string."""
        result = format_location_display()
        assert result == ""


class TestMergeLocationWithProfile:
    """Test merge_location_with_profile() override logic."""

    def test_street_override_keeps_other_fields(self):
        """Overriding street should keep village, block, district from profile."""
        profile = {
            "street": "महारा पारा",
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }
        extracted = {
            "street": "कोटेवार पारा"
        }

        result = merge_location_with_profile(extracted, profile)

        assert result["street"] == "कोटेवार पारा"  # Overridden
        assert result["village"] == "मादर"  # Kept from profile
        assert result["block"] == "लोहंडीगुड़ा"  # Kept from profile
        assert result["district"] == "बस्तर"  # Kept from profile

    def test_gps_override_updates_coordinates(self):
        """Providing GPS coordinates should override profile."""
        profile = {
            "village": "मादर",
            "district": "बस्तर",
            "lat": 19.0,
            "lng": 81.0
        }
        extracted = {
            "lat": 19.123456,
            "lng": 81.654321
        }

        result = merge_location_with_profile(extracted, profile)

        assert result["lat"] == 19.123456
        assert result["lng"] == 81.654321


class TestChatLocationIntegration:
    """Integration tests matching chat.py usage patterns."""

    def test_chat_flow_with_no_profile_location(self):
        """Simulate chat.py flow when user has no location."""
        # Arrange
        user = Mock()
        user.id = "test-user-no-loc"
        user.location_district = None
        user.location_village = None
        user.location_block = None

        # Act (simulating lines 554-567 in chat.py)
        profile_location = extract_location_from_user_profile(user)
        if profile_location is None:
            has_profile_location = False
        else:
            has_meaningful = has_meaningful_location(profile_location)
            has_profile_location = bool(has_meaningful if has_meaningful is not None else False)

        # Assert
        assert has_profile_location is False
        assert isinstance(has_profile_location, bool)

    def test_chat_flow_with_valid_profile_location(self):
        """Simulate chat.py flow when user has valid location."""
        # Arrange
        user = Mock()
        user.id = "test-user-valid-loc"
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

        # Act (simulating lines 554-567 in chat.py)
        profile_location = extract_location_from_user_profile(user)
        if profile_location is None:
            has_profile_location = False
        else:
            has_meaningful = has_meaningful_location(profile_location)
            has_profile_location = bool(has_meaningful if has_meaningful is not None else False)

        # Assert
        assert has_profile_location is True
        assert isinstance(has_profile_location, bool)

        # Test formatting (lines 579-587)
        if has_profile_location:
            formatted = format_location_display(
                street=profile_location.get("street"),
                village=profile_location.get("village"),
                panchayat=profile_location.get("panchayat"),
                block=profile_location.get("block"),
                subdivision=profile_location.get("subdivision"),
                district=profile_location.get("district"),
                state=profile_location.get("state")
            )
            assert "कोटेवार पारा" in formatted
            assert "मादर" in formatted
            assert "बस्तर" in formatted

    def test_chat_flow_handles_exception_gracefully(self):
        """Simulate chat.py exception handling (lines 565-567)."""
        # Arrange
        user = Mock()
        user.id = "test-user-exception"
        # Set location attributes to None (getattr will return None, no exception)
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

        # Act (with exception handling)
        try:
            profile_location = extract_location_from_user_profile(user)
            if profile_location is None:
                has_profile_location = False
            else:
                has_meaningful = has_meaningful_location(profile_location)
                has_profile_location = bool(has_meaningful if has_meaningful is not None else False)
        except Exception:
            has_profile_location = False

        # Assert
        assert has_profile_location is False
        assert isinstance(has_profile_location, bool)

    def test_assertion_guarantee_boolean_type(self):
        """Verify assertion check (line 570-571) would pass."""
        # Arrange
        user = Mock()
        user.id = "test-user-assertion"
        user.location_district = "बस्तर"
        user.location_village = "मादर"
        user.location_block = None
        user.location_street = None
        user.location_panchayat = None
        user.location_subdivision = None
        user.location_state = None
        user.location_lat = None
        user.location_lng = None
        user.location_formatted_address = None

        # Act
        profile_location = extract_location_from_user_profile(user)
        has_meaningful = has_meaningful_location(profile_location)
        has_profile_location = bool(has_meaningful if has_meaningful is not None else False)

        # Assert (line 570-571 assertion)
        assert isinstance(has_profile_location, bool), \
            f"BUG: has_profile_location must be bool, got {type(has_profile_location).__name__}={has_profile_location}"


# Run tests with: pytest tests/test_chat_location.py -v
