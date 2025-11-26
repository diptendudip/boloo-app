"""
Tests for Smart Location Confirmation feature.

Tests all 4 user flows from the design document:
1. User confirms profile location
2. User provides different location
3. Street-level override
4. No profile location
"""

import pytest
from app.utils.location_confirmation import (
    is_location_confirmation,
    is_location_rejection,
    format_location_display,
    merge_location_with_profile,
    has_meaningful_location,
    extract_location_from_user_profile
)


class TestLocationConfirmation:
    """Test confirmation keyword detection"""

    def test_hindi_confirmation_keywords(self):
        """Test Hindi confirmation keywords"""
        assert is_location_confirmation("हाँ") is True
        assert is_location_confirmation("जी हां") is True
        assert is_location_confirmation("ठीक है") is True
        assert is_location_confirmation("सही है") is True
        assert is_location_confirmation("बिल्कुल") is True

    def test_english_confirmation_keywords(self):
        """Test English confirmation keywords"""
        assert is_location_confirmation("yes") is True
        assert is_location_confirmation("Yeah") is True
        assert is_location_confirmation("OK") is True
        assert is_location_confirmation("Sure") is True
        assert is_location_confirmation("Correct") is True

    def test_mixed_responses(self):
        """Test mixed language responses"""
        assert is_location_confirmation("हाँ वही") is True
        assert is_location_confirmation("yes, same") is True

    def test_rejection_keywords(self):
        """Test rejection keyword detection"""
        assert is_location_rejection("नहीं") is True
        assert is_location_rejection("ना") is True
        assert is_location_rejection("no") is True
        assert is_location_rejection("नहीं, अलग जगह है") is True

    def test_no_keywords(self):
        """Test messages without keywords"""
        assert is_location_confirmation("मादर में समस्या है") is False
        assert is_location_rejection("मादर में समस्या है") is False


class TestLocationFormatting:
    """Test location formatting functions"""

    def test_full_location_formatting(self):
        """Test formatting with all fields"""
        formatted = format_location_display(
            street="कोटेवार पारा",
            village="मादर",
            panchayat="मादर",
            block="लोहंडीगुड़ा",
            district="बस्तर"
        )
        assert "कोटेवार पारा" in formatted
        assert "ग्राम मादर" in formatted
        assert "पंचायत मादर" in formatted
        assert "ब्लॉक लोहंडीगुड़ा" in formatted
        assert "जिला बस्तर" in formatted

    def test_partial_location_formatting(self):
        """Test formatting with only village and district"""
        formatted = format_location_display(
            village="मादर",
            district="बस्तर"
        )
        assert "ग्राम मादर" in formatted
        assert "जिला बस्तर" in formatted
        assert "ब्लॉक" not in formatted

    def test_empty_location_formatting(self):
        """Test formatting with no fields"""
        formatted = format_location_display()
        assert formatted == ""


class TestLocationMerging:
    """Test location merging for street-level overrides"""

    def test_street_override(self):
        """Test street-level override keeps village/block/district"""
        profile = {
            "street": "महारा पारा",
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर",
            "state": "छत्तीसगढ़"
        }
        extracted = {
            "street": "कोटेवार पारा"
        }
        merged = merge_location_with_profile(extracted, profile)

        assert merged["street"] == "कोटेवार पारा"  # Updated
        assert merged["village"] == "मादर"  # Kept from profile
        assert merged["block"] == "लोहंडीगुड़ा"  # Kept from profile
        assert merged["district"] == "बस्तर"  # Kept from profile

    def test_village_override(self):
        """Test village override updates village but keeps district"""
        profile = {
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }
        extracted = {
            "village": "डोंगरीगुड़ा"
        }
        merged = merge_location_with_profile(extracted, profile)

        assert merged["village"] == "डोंगरीगुड़ा"  # Updated
        assert merged["block"] == "लोहंडीगुड़ा"  # Kept from profile
        assert merged["district"] == "बस्तर"  # Kept from profile

    def test_complete_override(self):
        """Test complete location override"""
        profile = {
            "street": "महारा पारा",
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }
        extracted = {
            "street": "नया पारा",
            "village": "नया गाँव",
            "block": "नया ब्लॉक",
            "district": "नया जिला"
        }
        merged = merge_location_with_profile(extracted, profile)

        assert merged["street"] == "नया पारा"
        assert merged["village"] == "नया गाँव"
        assert merged["block"] == "नया ब्लॉक"
        assert merged["district"] == "नया जिला"

    def test_gps_override(self):
        """Test GPS coordinates override"""
        profile = {
            "village": "मादर",
            "district": "बस्तर",
            "lat": 19.0,
            "lng": 82.0
        }
        extracted = {
            "lat": 19.5,
            "lng": 82.5
        }
        merged = merge_location_with_profile(extracted, profile)

        assert merged["lat"] == 19.5
        assert merged["lng"] == 82.5
        assert merged["village"] == "मादर"  # Location unchanged


class TestMeaningfulLocation:
    """Test meaningful location validation"""

    def test_meaningful_with_village_and_district(self):
        """Test location with village and district is meaningful"""
        location = {
            "village": "मादर",
            "district": "बस्तर"
        }
        assert has_meaningful_location(location) is True

    def test_meaningful_with_block_and_district(self):
        """Test location with block and district is meaningful"""
        location = {
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }
        assert has_meaningful_location(location) is True

    def test_not_meaningful_district_only(self):
        """Test location with only district is not meaningful"""
        location = {
            "district": "बस्तर"
        }
        assert has_meaningful_location(location) is False

    def test_not_meaningful_village_only(self):
        """Test location with only village is not meaningful"""
        location = {
            "village": "मादर"
        }
        assert has_meaningful_location(location) is False

    def test_not_meaningful_empty(self):
        """Test empty location is not meaningful"""
        assert has_meaningful_location({}) is False
        assert has_meaningful_location(None) is False


class TestUserProfileExtraction:
    """Test extracting location from user profile"""

    class MockUser:
        """Mock user object for testing"""
        def __init__(self, **kwargs):
            self.location_street = kwargs.get("location_street")
            self.location_village = kwargs.get("location_village")
            self.location_panchayat = kwargs.get("location_panchayat")
            self.location_block = kwargs.get("location_block")
            self.location_subdivision = kwargs.get("location_subdivision")
            self.location_district = kwargs.get("location_district")
            self.location_state = kwargs.get("location_state")
            self.location_lat = kwargs.get("location_lat")
            self.location_lng = kwargs.get("location_lng")
            self.location_formatted_address = kwargs.get("location_formatted_address")

    def test_extract_complete_location(self):
        """Test extracting complete location from user"""
        user = self.MockUser(
            location_street="कोटेवार पारा",
            location_village="मादर",
            location_block="लोहंडीगुड़ा",
            location_district="बस्तर",
            location_state="छत्तीसगढ़",
            location_lat=19.0,
            location_lng=82.0
        )
        location = extract_location_from_user_profile(user)

        assert location is not None
        assert location["street"] == "कोटेवार पारा"
        assert location["village"] == "मादर"
        assert location["block"] == "लोहंडीगुड़ा"
        assert location["district"] == "बस्तर"
        assert location["lat"] == 19.0
        assert location["lng"] == 82.0

    def test_extract_minimal_location(self):
        """Test extracting minimal location (village + district)"""
        user = self.MockUser(
            location_village="मादर",
            location_district="बस्तर"
        )
        location = extract_location_from_user_profile(user)

        assert location is not None
        assert location["village"] == "मादर"
        assert location["district"] == "बस्तर"

    def test_extract_no_location(self):
        """Test extracting from user with no location"""
        user = self.MockUser()
        location = extract_location_from_user_profile(user)

        assert location is None

    def test_extract_incomplete_location(self):
        """Test extracting incomplete location (district only)"""
        user = self.MockUser(
            location_district="बस्तर"
        )
        location = extract_location_from_user_profile(user)

        assert location is None  # Not meaningful without village/block


class TestUserFlows:
    """Test complete user flows from design document"""

    def test_flow_1_user_confirms_location(self):
        """
        Flow 1: User Confirms Profile Location

        AI: "आपके प्रोफाइल में यह पता दर्ज है: ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर।
             क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?"
        User: "हाँ"
        Expected: Location auto-filled from profile
        """
        profile_location = {
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }

        user_response = "हाँ"

        # User confirms
        assert is_location_confirmation(user_response) is True

        # Location should be auto-filled (in actual code, this happens in chat.py)
        formatted = format_location_display(**profile_location)
        assert "ग्राम मादर" in formatted
        assert "ब्लॉक लोहंडीगुड़ा" in formatted
        assert "जिला बस्तर" in formatted

    def test_flow_2_user_provides_different_location(self):
        """
        Flow 2: User Provides Different Location

        AI: "आपके प्रोफाइल में यह पता दर्ज है: ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर।
             क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?"
        User: "नहीं, समस्या डोंगरीगुड़ा में है"
        Expected: Extract new location: village=डोंगरीगुड़ा, keep block/district from profile
        """
        profile_location = {
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }

        user_response = "नहीं, समस्या डोंगरीगुड़ा में है"

        # User rejects
        assert is_location_rejection(user_response) is True

        # New location would be extracted (simulation)
        extracted_location = {
            "village": "डोंगरीगुड़ा"
        }

        # Merge keeps district/block from profile
        merged = merge_location_with_profile(extracted_location, profile_location)
        assert merged["village"] == "डोंगरीगुड़ा"  # New
        assert merged["block"] == "लोहंडीगुड़ा"  # From profile
        assert merged["district"] == "बस्तर"  # From profile

    def test_flow_3_street_level_override(self):
        """
        Flow 3: Street-Level Override

        AI: "आपके प्रोफाइल में यह पता दर्ज है: कोटेवार पारा, ग्राम मादर, ब्लॉक लोहंडीगुड़ा।
             क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?"
        User: "नहीं, महारा पारा में है"
        Expected: street=महारा पारा, village/block/district from profile
        """
        profile_location = {
            "street": "कोटेवार पारा",
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर"
        }

        user_response = "नहीं, महारा पारा में है"

        # User rejects and provides alternative
        assert is_location_rejection(user_response) is True

        # New street extracted (simulation)
        extracted_location = {
            "street": "महारा पारा"
        }

        # Merge updates only street
        merged = merge_location_with_profile(extracted_location, profile_location)
        assert merged["street"] == "महारा पारा"  # Updated
        assert merged["village"] == "मादर"  # Kept
        assert merged["block"] == "लोहंडीगुड़ा"  # Kept
        assert merged["district"] == "बस्तर"  # Kept

    def test_flow_4_no_profile_location(self):
        """
        Flow 4: No Profile Location

        AI: "नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ। कृपया बताएं कि क्या समस्या है और कहाँ है?"
        User: "मादर गाँव में हैंडपंप खराब है"
        Expected: Normal flow - asks for location if not clear
        """
        # User has no profile location
        user = TestUserProfileExtraction.MockUser()
        location = extract_location_from_user_profile(user)

        assert location is None

        # No confirmation needed, normal flow proceeds
        # Location would be extracted from user's message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
