"""
Test Location Confirmation - Comprehensive tests for location confirmation utilities

Tests location confirmation logic including:
- Keyword detection (Hindi and English)
- Location data extraction
- Location formatting
- Error handling with None values
- Pydantic validation compatibility
"""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.utils.location_confirmation import (
    is_location_confirmation,
    is_location_rejection,
    format_location_display,
    merge_location_with_profile,
    has_meaningful_location,
    extract_location_from_user_profile
)


class TestLocationConfirmationDetection:
    """Test is_location_confirmation function"""

    def test_hindi_confirmation_keywords(self):
        """Test Hindi confirmation keyword detection"""
        hindi_confirmations = [
            "हाँ",
            "हां",
            "जी हां",
            "जी हाँ",
            "ठीक है",
            "सही है",
            "वही",
            "यही",
            "बिल्कुल",
            "सही",
            "ठीक"
        ]

        for keyword in hindi_confirmations:
            result = is_location_confirmation(keyword)
            assert result is True, f"'{keyword}' should be detected as confirmation"

    def test_english_confirmation_keywords(self):
        """Test English confirmation keyword detection"""
        english_confirmations = [
            "yes",
            "yeah",
            "yep",
            "yup",
            "correct",
            "right",
            "ok",
            "okay",
            "sure",
            "fine",
            "exactly",
            "same"
        ]

        for keyword in english_confirmations:
            result = is_location_confirmation(keyword)
            assert result is True, f"'{keyword}' should be detected as confirmation"

    def test_confirmation_case_insensitive(self):
        """Test confirmation detection is case-insensitive"""
        assert is_location_confirmation("YES") is True
        assert is_location_confirmation("Yes") is True
        assert is_location_confirmation("yEs") is True

    def test_confirmation_with_extra_text(self):
        """Test confirmation detection in longer messages"""
        assert is_location_confirmation("हाँ वही है") is True
        assert is_location_confirmation("yes that's correct") is True
        assert is_location_confirmation("ठीक है भाई") is True

    def test_non_confirmation_messages(self):
        """Test messages that are not confirmations"""
        non_confirmations = [
            "नहीं",
            "no",
            "maybe",
            "I don't know",
            "मुझे नहीं पता"
        ]

        for message in non_confirmations:
            result = is_location_confirmation(message)
            assert result is False, f"'{message}' should NOT be confirmation"

    def test_confirmation_with_none_or_empty(self):
        """Test None and empty string handling"""
        assert is_location_confirmation(None) is False
        assert is_location_confirmation("") is False
        assert is_location_confirmation("   ") is False


class TestLocationRejectionDetection:
    """Test is_location_rejection function"""

    def test_hindi_rejection_keywords(self):
        """Test Hindi rejection keyword detection"""
        hindi_rejections = [
            "नहीं",
            "ना",
            "नही",
            "गलत",
            "अलग"
        ]

        for keyword in hindi_rejections:
            result = is_location_rejection(keyword)
            assert result is True, f"'{keyword}' should be detected as rejection"

    def test_english_rejection_keywords(self):
        """Test English rejection keyword detection"""
        english_rejections = [
            "no",
            "nope",
            "nah",
            "wrong",
            "different",
            "not"
        ]

        for keyword in english_rejections:
            result = is_location_rejection(keyword)
            assert result is True, f"'{keyword}' should be detected as rejection"

    def test_rejection_case_insensitive(self):
        """Test rejection detection is case-insensitive"""
        assert is_location_rejection("NO") is True
        assert is_location_rejection("No") is True
        assert is_location_rejection("nO") is True

    def test_rejection_with_extra_text(self):
        """Test rejection detection in longer messages"""
        assert is_location_rejection("नहीं, मादर में है") is True
        assert is_location_rejection("no that's wrong") is True

    def test_non_rejection_messages(self):
        """Test messages that are not rejections"""
        non_rejections = [
            "हाँ",
            "yes",
            "maybe",
            "I think so"
        ]

        for message in non_rejections:
            result = is_location_rejection(message)
            assert result is False, f"'{message}' should NOT be rejection"

    def test_rejection_with_none_or_empty(self):
        """Test None and empty string handling"""
        assert is_location_rejection(None) is False
        assert is_location_rejection("") is False
        assert is_location_rejection("   ") is False


class TestLocationFormatting:
    """Test format_location_display function"""

    def test_complete_location_formatting(self):
        """Test formatting complete location with all fields"""
        result = format_location_display(
            street="कोटेवार पारा",
            village="मादर",
            panchayat="मादर",
            block="लोहंडीगुड़ा",
            subdivision="जगदलपुर",
            district="बस्तर",
            state="छत्तीसगढ़"
        )

        assert "कोटेवार पारा" in result
        assert "ग्राम मादर" in result
        assert "पंचायत मादर" in result
        assert "ब्लॉक लोहंडीगुड़ा" in result
        assert "उपखंड जगदलपुर" in result
        assert "जिला बस्तर" in result

    def test_partial_location_formatting(self):
        """Test formatting with only some fields"""
        result = format_location_display(
            village="मादर",
            district="बस्तर"
        )

        assert result == "ग्राम मादर, जिला बस्तर"

    def test_empty_location_formatting(self):
        """Test formatting with no fields returns empty string"""
        result = format_location_display()
        assert result == ""

    def test_location_formatting_skips_none_fields(self):
        """Test that None fields are skipped in formatting"""
        result = format_location_display(
            street=None,
            village="मादर",
            district="बस्तर",
            panchayat=None
        )

        assert "None" not in result
        assert "ग्राम मादर" in result
        assert "जिला बस्तर" in result

    def test_location_formatting_with_state_chhattisgarh(self):
        """Test that Chhattisgarh state is omitted (default)"""
        result = format_location_display(
            village="मादर",
            district="बस्तर",
            state="छत्तीसगढ़"
        )

        # State should be omitted when it's Chhattisgarh
        assert "राज्य" not in result

    def test_location_formatting_with_other_state(self):
        """Test that non-Chhattisgarh state is included"""
        result = format_location_display(
            village="TestVillage",
            district="TestDistrict",
            state="Maharashtra"
        )

        assert "राज्य Maharashtra" in result


class TestLocationMerging:
    """Test merge_location_with_profile function"""

    def test_street_override_keeps_other_fields(self):
        """Test overriding street keeps village, block, district from profile"""
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
        """Test GPS coordinate override"""
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
        assert result["village"] == "मादर"  # Kept from profile

    def test_complete_override(self):
        """Test complete location override"""
        profile = {
            "village": "Old Village",
            "district": "Old District"
        }
        extracted = {
            "village": "New Village",
            "district": "New District",
            "block": "New Block"
        }

        result = merge_location_with_profile(extracted, profile)

        assert result["village"] == "New Village"
        assert result["district"] == "New District"
        assert result["block"] == "New Block"

    def test_empty_extracted_keeps_profile(self):
        """Test empty extracted dict keeps all profile data"""
        profile = {
            "village": "मादर",
            "district": "बस्तर",
            "block": "लोहंडीगुड़ा"
        }
        extracted = {}

        result = merge_location_with_profile(extracted, profile)

        assert result == profile


class TestHasMeaningfulLocation:
    """Test has_meaningful_location function (critical for Pydantic validation)"""

    def test_none_input_returns_false(self):
        """Test None input returns False (not None)"""
        result = has_meaningful_location(None)

        assert result is False
        assert isinstance(result, bool)

    def test_empty_dict_returns_false(self):
        """Test empty dict returns False"""
        result = has_meaningful_location({})

        assert result is False
        assert isinstance(result, bool)

    def test_district_only_returns_false(self):
        """Test district alone is insufficient"""
        location = {"district": "बस्तर"}
        result = has_meaningful_location(location)

        assert result is False
        assert isinstance(result, bool)

    def test_village_only_returns_false(self):
        """Test village alone is insufficient"""
        location = {"village": "मादर"}
        result = has_meaningful_location(location)

        assert result is False
        assert isinstance(result, bool)

    def test_district_and_village_returns_true(self):
        """Test district + village is meaningful"""
        location = {
            "district": "बस्तर",
            "village": "मादर"
        }
        result = has_meaningful_location(location)

        assert result is True
        assert isinstance(result, bool)

    def test_district_and_block_returns_true(self):
        """Test district + block is meaningful"""
        location = {
            "district": "बस्तर",
            "block": "लोहंडीगुड़ा"
        }
        result = has_meaningful_location(location)

        assert result is True
        assert isinstance(result, bool)

    def test_complete_location_returns_true(self):
        """Test complete location returns True"""
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
        """Test invalid input types return False (not None or exception)"""
        invalid_inputs = [
            "invalid string",
            123,
            [],
            True,
            object()
        ]

        for invalid_input in invalid_inputs:
            result = has_meaningful_location(invalid_input)

            assert isinstance(result, bool), \
                f"Expected bool for {type(invalid_input).__name__}, got {type(result).__name__}"
            assert result is False


class TestExtractLocationFromProfile:
    """Test extract_location_from_user_profile function"""

    def test_user_with_no_location_returns_none(self):
        """Test user with no location fields returns None"""
        user = Mock()
        user.id = uuid4()
        user.location_district = None
        user.location_village = None
        user.location_block = None

        result = extract_location_from_user_profile(user)
        assert result is None

    def test_user_with_complete_location_returns_dict(self):
        """Test user with complete location returns location dict"""
        user = Mock()
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
        user.location_formatted_address = "कोटेवार पारा, ग्राम मादर"

        result = extract_location_from_user_profile(user)

        assert result is not None
        assert result["district"] == "बस्तर"
        assert result["village"] == "मादर"
        assert result["street"] == "कोटेवार पारा"
        assert result["lat"] == 19.123456

    def test_user_with_none_object_returns_none(self):
        """Test None user returns None (not crash)"""
        result = extract_location_from_user_profile(None)
        assert result is None

    def test_user_with_insufficient_location_returns_none(self):
        """Test user with only district (insufficient) returns None"""
        user = Mock()
        user.id = uuid4()
        user.location_district = "बस्तर"
        user.location_village = None
        user.location_block = None

        result = extract_location_from_user_profile(user)
        assert result is None

    def test_user_with_district_and_village_returns_dict(self):
        """Test user with district + village returns location"""
        user = Mock()
        user.id = uuid4()
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

        result = extract_location_from_user_profile(user)

        assert result is not None
        assert result["district"] == "बस्तर"
        assert result["village"] == "मादर"


class TestLocationConfirmationEdgeCases:
    """Test edge cases and error conditions"""

    def test_has_meaningful_location_never_returns_none(self):
        """CRITICAL: has_meaningful_location must NEVER return None (Pydantic validation)"""
        test_cases = [None, {}, [], "", 123, True, object()]

        for test_input in test_cases:
            result = has_meaningful_location(test_input)

            # MUST be bool, never None
            assert isinstance(result, bool), \
                f"Expected bool for {type(test_input).__name__}, got {type(result).__name__}"
            assert result is False

    def test_location_extraction_handles_missing_attributes(self):
        """Test extraction handles user objects missing location attributes"""
        user = Mock()
        user.id = uuid4()
        # Don't set location attributes

        result = extract_location_from_user_profile(user)
        assert result is None

    def test_location_formatting_handles_unicode(self):
        """Test formatting handles Unicode Hindi text correctly"""
        result = format_location_display(
            village="मादर",
            district="बस्तर"
        )

        assert "मादर" in result
        assert "बस्तर" in result
        assert isinstance(result, str)


# Run with: pytest tests/test_location_confirmation.py -v -s
