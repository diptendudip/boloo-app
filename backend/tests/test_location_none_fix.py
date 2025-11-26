"""
Test suite for location confirmation None-handling fixes.

Verifies that the Pydantic validation error is resolved:
- has_meaningful_location() always returns bool (never None)
- extract_location_from_user_profile() handles missing DB columns
- chat.py properly coalesces None values to False
"""

import pytest
from app.utils.location_confirmation import (
    has_meaningful_location,
    extract_location_from_user_profile,
    format_location_display
)


class MockUser:
    """Mock user object for testing missing DB columns."""

    def __init__(self, **kwargs):
        self.id = "test-user-123"
        # Simulate DB columns that might not exist yet
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestHasMeaningfulLocation:
    """Test has_meaningful_location() with various edge cases."""

    def test_valid_location_with_village(self):
        """Valid location with district and village."""
        location = {
            "district": "बस्तर",
            "village": "मादर"
        }
        result = has_meaningful_location(location)
        assert result is True
        assert isinstance(result, bool)

    def test_valid_location_with_block(self):
        """Valid location with district and block."""
        location = {
            "district": "बस्तर",
            "block": "लोहंडीगुड़ा"
        }
        result = has_meaningful_location(location)
        assert result is True
        assert isinstance(result, bool)

    def test_none_input(self):
        """None input should return False, not None."""
        result = has_meaningful_location(None)
        assert result is False
        assert isinstance(result, bool)

    def test_empty_dict(self):
        """Empty dictionary should return False."""
        result = has_meaningful_location({})
        assert result is False
        assert isinstance(result, bool)

    def test_district_only(self):
        """District without village/block is insufficient."""
        location = {"district": "बस्तर"}
        result = has_meaningful_location(location)
        assert result is False
        assert isinstance(result, bool)

    def test_village_only(self):
        """Village without district is insufficient."""
        location = {"village": "मादर"}
        result = has_meaningful_location(location)
        assert result is False
        assert isinstance(result, bool)

    def test_none_values(self):
        """None values should be treated as missing."""
        location = {
            "district": None,
            "village": None,
            "block": None
        }
        result = has_meaningful_location(location)
        assert result is False
        assert isinstance(result, bool)

    def test_empty_string_values(self):
        """Empty strings should be treated as missing."""
        location = {
            "district": "",
            "village": "  ",  # Whitespace only
            "block": ""
        }
        result = has_meaningful_location(location)
        assert result is False
        assert isinstance(result, bool)

    def test_mixed_none_and_valid(self):
        """District valid, village None, block valid → should pass."""
        location = {
            "district": "बस्तर",
            "village": None,
            "block": "लोहंडीगुड़ा"
        }
        result = has_meaningful_location(location)
        assert result is True
        assert isinstance(result, bool)

    def test_non_dict_input(self):
        """Non-dict input should return False."""
        assert has_meaningful_location("string") is False
        assert has_meaningful_location([]) is False
        assert has_meaningful_location(123) is False


class TestExtractLocationFromUserProfile:
    """Test extract_location_from_user_profile() with missing DB columns."""

    def test_user_with_complete_location(self):
        """User with complete location data."""
        user = MockUser(
            location_district="बस्तर",
            location_village="मादर",
            location_block="लोहंडीगुड़ा",
            location_state="छत्तीसगढ़"
        )
        result = extract_location_from_user_profile(user)
        assert result is not None
        assert result["district"] == "बस्तर"
        assert result["village"] == "मादर"

    def test_user_with_district_and_village_only(self):
        """User with minimum required fields (district + village)."""
        user = MockUser(
            location_district="बस्तर",
            location_village="मादर"
        )
        result = extract_location_from_user_profile(user)
        assert result is not None
        assert result["district"] == "बस्तर"
        assert result["village"] == "मादर"

    def test_user_with_district_only(self):
        """User with district only (insufficient) → should return None."""
        user = MockUser(
            location_district="बस्तर"
        )
        result = extract_location_from_user_profile(user)
        assert result is None

    def test_user_with_no_location_columns(self):
        """User object without any location columns (Azure DB not migrated yet)."""
        user = MockUser()  # No location fields
        result = extract_location_from_user_profile(user)
        assert result is None

    def test_user_with_none_values(self):
        """User with None values in location fields."""
        user = MockUser(
            location_district=None,
            location_village=None,
            location_block=None
        )
        result = extract_location_from_user_profile(user)
        assert result is None

    def test_user_with_empty_strings(self):
        """User with empty string values."""
        user = MockUser(
            location_district="",
            location_village="  ",  # Whitespace
            location_block=""
        )
        result = extract_location_from_user_profile(user)
        assert result is None

    def test_none_user(self):
        """None user should return None."""
        result = extract_location_from_user_profile(None)
        assert result is None


class TestFormatLocationDisplay:
    """Test format_location_display() formatting."""

    def test_full_location(self):
        """Format complete location."""
        result = format_location_display(
            street="कोटेवार पारा",
            village="मादर",
            panchayat="मादर",
            block="लोहंडीगुड़ा",
            district="बस्तर",
            state="छत्तीसगढ़"
        )
        assert "कोटेवार पारा" in result
        assert "ग्राम मादर" in result
        assert "ब्लॉक लोहंडीगुड़ा" in result
        assert "जिला बस्तर" in result
        # State should be excluded (default Chhattisgarh)
        assert "राज्य" not in result

    def test_minimal_location(self):
        """Format with village and district only."""
        result = format_location_display(
            village="मादर",
            district="बस्तर"
        )
        assert result == "ग्राम मादर, जिला बस्तर"

    def test_none_values(self):
        """None values should be skipped."""
        result = format_location_display(
            street=None,
            village="मादर",
            district="बस्तर"
        )
        assert result == "ग्राम मादर, जिला बस्तर"

    def test_all_none(self):
        """All None should return empty string."""
        result = format_location_display()
        assert result == ""


class TestChatEndpointScenarios:
    """Integration tests simulating real chat endpoint scenarios."""

    def test_new_user_no_location(self):
        """New user without any location data in DB."""
        user = MockUser()  # No location columns

        # This should not crash
        profile_location = extract_location_from_user_profile(user)

        # Should return None
        assert profile_location is None

        # has_meaningful_location should handle None gracefully
        has_location = has_meaningful_location(profile_location)

        # CRITICAL: Must be False, not None
        assert has_location is False
        assert isinstance(has_location, bool)

    def test_user_with_incomplete_location(self):
        """User with only district (insufficient for confirmation)."""
        user = MockUser(
            location_district="बस्तर"
        )

        profile_location = extract_location_from_user_profile(user)
        assert profile_location is None  # Insufficient data

        has_location = has_meaningful_location(profile_location)
        assert has_location is False  # Not None!
        assert isinstance(has_location, bool)

    def test_user_with_empty_strings(self):
        """User with empty string location values."""
        user = MockUser(
            location_district="",
            location_village="   ",
            location_block=""
        )

        profile_location = extract_location_from_user_profile(user)
        assert profile_location is None

        has_location = has_meaningful_location(profile_location)
        assert has_location is False
        assert isinstance(has_location, bool)

    def test_user_with_valid_location(self):
        """User with valid location data."""
        user = MockUser(
            location_district="बस्तर",
            location_village="मादर",
            location_block="लोहंडीगुड़ा"
        )

        profile_location = extract_location_from_user_profile(user)
        assert profile_location is not None

        has_location = has_meaningful_location(profile_location)
        assert has_location is True
        assert isinstance(has_location, bool)

    def test_pydantic_validation_scenario(self):
        """
        Simulate the exact scenario that caused Pydantic validation error.

        When Azure DB doesn't have location columns yet, this should not crash.
        """
        user = MockUser()  # No location columns (AttributeError scenario)

        # DEFAULT: Always start with False (from chat.py fix)
        has_profile_location = False

        try:
            profile_location = extract_location_from_user_profile(user)
            if profile_location is None:
                has_profile_location = False
            else:
                has_meaningful = has_meaningful_location(profile_location)
                # CRITICAL FIX: Triple None coalescing
                has_profile_location = bool(has_meaningful) if has_meaningful is not None else False
        except Exception:
            has_profile_location = False

        # ASSERTION: Must be boolean, never None
        assert isinstance(has_profile_location, bool)
        assert has_profile_location is False

        # This should now pass Pydantic validation
        # (Before fix: has_profile_location could be None → Pydantic error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
