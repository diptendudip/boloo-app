"""
Test Suite for Bug Fix #7: Premature Submission with Invalid Placeholder Data

Bug Description (IMG_0987):
- Location shows "unknown" (invalid placeholder)
- System still offers submission: "आप अभी अपनी रिपोर्ट सबमिट कर सकते हैं!"
- User only gave 1 message about handpump problem
- Critical data is missing but submission is allowed

Root Cause:
- can_submit_now() only checked if fields exist and are non-empty
- Did NOT validate field VALUES - "unknown" passed validation!
- No check for placeholder values like "unknown", "n/a", "not provided"

Fix Implemented:
- Created is_valid_field_value() helper function
- Validates field values are not placeholders
- Added location-specific validation for geographical indicators
- Prevents submission with invalid/placeholder data

Evidence: IMG_0987.png
"""

import pytest
from app.routers.chat import can_submit_now, is_valid_field_value


class TestBugFix7_PlaceholderValidation:
    """Test that placeholder values like 'unknown' are rejected"""

    def test_unknown_location_rejected(self):
        """
        Test the EXACT scenario from IMG_0987:
        Location = "unknown" should BLOCK submission
        """
        # This is the exact data from IMG_0987
        data_with_unknown_location = {
            "issue_description": "Humare yahan paani ka samasya hai. Handpump kharab hai aur paani nahi milta",
            "location": "unknown"  # ⚠️ INVALID PLACEHOLDER!
        }

        # Should NOT allow submission with "unknown" location
        result = can_submit_now(data_with_unknown_location)
        assert result is False, "CRITICAL: Should NOT allow submission with 'unknown' location (IMG_0987)"

    def test_valid_location_allowed(self):
        """
        Test that VALID locations ARE allowed for submission
        """
        data_with_valid_location = {
            "issue_description": "हमारे यहां पानी की बहुत समस्या है। हैंडपंप खराब है और पानी नहीं मिलता है, बहुत परेशानी हो रही है",
            "location": "ग्राम पंचायत नोगोई कटरापारा, ब्लॉक ओडगी, जिला सूरजपुर"
        }

        # Should allow submission with valid location
        result = can_submit_now(data_with_valid_location)
        assert result is True, "Should allow submission with valid geographical location"

    def test_placeholder_variations_rejected(self):
        """
        Test that various placeholder formats are all rejected
        """
        placeholder_values = [
            "unknown",
            "not provided",
            "n/a",
            "na",
            "missing",
            "none",
            "पता नहीं",
            "मालूम नहीं",
            "नहीं पता",
            "not known",
            "tbd",
            "?",
            "-"
        ]

        for placeholder in placeholder_values:
            data = {
                "issue_description": "Humare yahan paani ka samasya hai. Handpump kharab hai aur paani nahi milta",
                "location": placeholder
            }

            result = can_submit_now(data)
            assert result is False, f"Should reject placeholder location: '{placeholder}'"

    def test_is_valid_field_value_function(self):
        """
        Test the is_valid_field_value() helper function directly
        """
        # Invalid values
        assert is_valid_field_value("location", "unknown") is False
        assert is_valid_field_value("location", "n/a") is False
        assert is_valid_field_value("location", "") is False
        assert is_valid_field_value("location", None) is False
        assert is_valid_field_value("location", "पता नहीं") is False

        # Valid values with geographical indicators
        assert is_valid_field_value("location", "ग्राम पंचायत नोगोई") is True
        assert is_valid_field_value("location", "village Nogoi") is True
        assert is_valid_field_value("location", "block Odagi, district Surajpur") is True
        assert is_valid_field_value("location", "जिला सूरजपुर") is True

    def test_location_too_vague_rejected(self):
        """
        Test that vague locations without geographical indicators are rejected
        """
        # Too vague - no geographical context
        vague_locations = ["here", "यहाँ", "abc", "xyz"]

        for location in vague_locations:
            result = is_valid_field_value("location", location)
            assert result is False, f"Should reject vague location: '{location}'"

    def test_minimum_length_validation(self):
        """
        Test that very short values are rejected
        """
        # Too short (< 2 chars)
        assert is_valid_field_value("location", "a") is False
        assert is_valid_field_value("location", "1") is False

        # Valid length
        assert is_valid_field_value("location", "ग्राम नोगोई") is True

    def test_issue_description_still_validated(self):
        """
        Test that issue_description validation still works alongside location validation
        """
        # Valid location but invalid issue description
        data_with_short_issue = {
            "issue_description": "समस्या है",  # Too short (< 5 words)
            "location": "ग्राम पंचायत नोगोई"
        }

        result = can_submit_now(data_with_short_issue)
        assert result is False, "Should reject too-short issue description"

        # Valid location but non-meaningful issue description
        data_with_generic_issue = {
            "issue_description": "मैं नोगोई गांव से बोल रहा हूँ",  # No problem indicator
            "location": "ग्राम पंचायत नोगोई"
        }

        result = can_submit_now(data_with_generic_issue)
        assert result is False, "Should reject non-meaningful issue description"


class TestBugFix7_IntegrationScenarios:
    """Integration tests for complete submission validation"""

    def test_img_0987_exact_scenario(self):
        """
        Replicate EXACT scenario from IMG_0987:
        - User: "Humare yahan paani ka samasya hai. Handpump kharab hai aur paani nahi milta"
        - System extracted: issue_description (valid) + location "unknown" (INVALID)
        - Old behavior: Offered submission immediately ❌
        - New behavior: Should NOT offer submission ✅
        """
        extracted_data_from_img_0987 = {
            "issue_description": "Humare yahan paani ka samasya hai. Handpump kharab hai aur paani nahi milta",
            "location": "unknown"
        }

        # This should BLOCK submission
        can_submit = can_submit_now(extracted_data_from_img_0987)
        assert can_submit is False, "BUG FIX #7: Should NOT allow submission with 'unknown' location (IMG_0987)"

    def test_minimum_valid_submission(self):
        """
        Test that VALID minimum data IS allowed for submission
        """
        valid_minimum_data = {
            "issue_description": "हैंडपंप खराब है और पानी नहीं मिलता है, बहुत परेशानी हो रही है",
            "location": "ग्राम पंचायत नोगोई कटरापारा, जिला सूरजपुर"
        }

        # This SHOULD allow submission
        can_submit = can_submit_now(valid_minimum_data)
        assert can_submit is True, "Should allow submission with valid minimum fields"

    def test_both_fields_invalid(self):
        """
        Test that submission is blocked if EITHER field is invalid
        """
        # Invalid location
        data1 = {
            "issue_description": "हैंडपंप खराब है और पानी नहीं मिलता है, बहुत परेशानी हो रही है",
            "location": "unknown"
        }
        assert can_submit_now(data1) is False, "Should block with invalid location"

        # Invalid issue_description
        data2 = {
            "issue_description": "बोल रहा हूँ",  # Too short, no problem
            "location": "ग्राम पंचायत नोगोई"
        }
        assert can_submit_now(data2) is False, "Should block with invalid issue_description"

        # Both invalid
        data3 = {
            "issue_description": "समस्या",
            "location": "unknown"
        }
        assert can_submit_now(data3) is False, "Should block with both invalid"

    def test_empty_vs_placeholder_distinction(self):
        """
        Test that we correctly distinguish between empty fields and placeholder values
        """
        # Empty fields should block (as before)
        assert can_submit_now({"issue_description": "", "location": "ग्राम नोगोई"}) is False
        assert can_submit_now({"issue_description": "हैंडपंप खराब है", "location": ""}) is False

        # Placeholder fields should also block (NEW behavior)
        assert can_submit_now({"issue_description": "हैंडपंप खराब है", "location": "unknown"}) is False
        assert can_submit_now({"issue_description": "हैंडपंप खराब है", "location": "n/a"}) is False

    def test_case_insensitive_placeholder_detection(self):
        """
        Test that placeholder detection is case-insensitive
        """
        placeholders_mixed_case = [
            "Unknown",
            "UNKNOWN",
            "Not Provided",
            "NOT PROVIDED",
            "N/A",
            "n/A"
        ]

        for placeholder in placeholders_mixed_case:
            data = {
                "issue_description": "हैंडपंप खराब है और पानी नहीं मिलता",
                "location": placeholder
            }
            assert can_submit_now(data) is False, f"Should reject case variation: '{placeholder}'"


class TestBugFix7_EdgeCases:
    """Edge case tests for robust validation"""

    def test_whitespace_padding(self):
        """
        Test that whitespace-padded placeholders are still detected
        """
        padded_placeholders = [
            "  unknown  ",
            "\tunknown\t",
            "\nunknown\n",
            "  not provided  "
        ]

        for placeholder in padded_placeholders:
            data = {
                "issue_description": "हैंडपंप खराब है और पानी नहीं मिलता",
                "location": placeholder
            }
            assert can_submit_now(data) is False, f"Should reject padded placeholder: '{repr(placeholder)}'"

    def test_mixed_language_locations(self):
        """
        Test locations with mixed Hindi/English geographical indicators
        """
        mixed_locations = [
            "village नोगोई, district सूरजपुर",
            "ग्राम Nogoi, block Odagi",
            "gram panchayat नोगोई कटरापारा"
        ]

        for location in mixed_locations:
            result = is_valid_field_value("location", location)
            assert result is True, f"Should accept mixed-language location: '{location}'"

    def test_none_vs_string_none(self):
        """
        Test that we handle both None and string "none" correctly
        """
        # Python None
        assert is_valid_field_value("location", None) is False

        # String "none"
        assert is_valid_field_value("location", "none") is False
        assert is_valid_field_value("location", "None") is False

    def test_numerical_locations_rejected(self):
        """
        Test that purely numerical values are rejected (likely invalid)
        """
        numerical_locations = ["123", "456", "1", "99"]

        for location in numerical_locations:
            result = is_valid_field_value("location", location)
            assert result is False, f"Should reject numerical location: '{location}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
