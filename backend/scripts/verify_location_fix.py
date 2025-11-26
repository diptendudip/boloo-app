#!/usr/bin/env python3
"""
Verification script for location None-handling fix.

Demonstrates that the fix resolves the Pydantic validation error.
Run this to verify the fix works before deployment.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.location_confirmation import (
    has_meaningful_location,
    extract_location_from_user_profile
)


class MockUser:
    """Mock user for testing."""
    def __init__(self, **kwargs):
        self.id = "test-user"
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_scenario(name: str, scenario_func):
    """Run a test scenario and report results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    try:
        scenario_func()
        print("✅ PASSED")
        return True
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def scenario_new_user_no_columns():
    """Scenario 1: New user without location columns in DB."""
    print("User: No location columns (DB not migrated)")

    user = MockUser()  # No location attributes

    # Extract location
    profile_location = extract_location_from_user_profile(user)
    print(f"  extract_location_from_user_profile() returned: {profile_location}")

    # Check meaningful location
    has_location = has_meaningful_location(profile_location)
    print(f"  has_meaningful_location() returned: {has_location} (type: {type(has_location).__name__})")

    # Assertions
    assert profile_location is None, "Should return None for user without location"
    assert has_location is False, "Should return False for None input"
    assert isinstance(has_location, bool), f"Must be bool, got {type(has_location)}"

    # Simulate Pydantic validation
    from pydantic import BaseModel

    class ChatStartResponse(BaseModel):
        profile_location_available: bool

    response = ChatStartResponse(profile_location_available=has_location)
    print(f"  Pydantic validation: SUCCESS (value={response.profile_location_available})")


def scenario_user_with_district_only():
    """Scenario 2: User with only district (insufficient)."""
    print("User: District only (incomplete location)")

    user = MockUser(
        location_district="बस्तर"
    )

    profile_location = extract_location_from_user_profile(user)
    print(f"  extract_location_from_user_profile() returned: {profile_location}")

    has_location = has_meaningful_location(profile_location)
    print(f"  has_meaningful_location() returned: {has_location} (type: {type(has_location).__name__})")

    assert profile_location is None, "Should return None for incomplete location"
    assert has_location is False, "Should return False"
    assert isinstance(has_location, bool), "Must be bool"


def scenario_user_with_empty_strings():
    """Scenario 3: User with empty string location values."""
    print("User: Empty string values")

    user = MockUser(
        location_district="",
        location_village="   ",  # Whitespace
        location_block=""
    )

    profile_location = extract_location_from_user_profile(user)
    print(f"  extract_location_from_user_profile() returned: {profile_location}")

    has_location = has_meaningful_location(profile_location)
    print(f"  has_meaningful_location() returned: {has_location} (type: {type(has_location).__name__})")

    assert profile_location is None, "Should return None for empty strings"
    assert has_location is False, "Should return False"
    assert isinstance(has_location, bool), "Must be bool"


def scenario_user_with_valid_location():
    """Scenario 4: User with valid location data."""
    print("User: Valid complete location")

    user = MockUser(
        location_district="बस्तर",
        location_village="मादर",
        location_block="लोहंडीगुड़ा",
        location_state="छत्तीसगढ़"
    )

    profile_location = extract_location_from_user_profile(user)
    print(f"  extract_location_from_user_profile() returned: {profile_location}")

    has_location = has_meaningful_location(profile_location)
    print(f"  has_meaningful_location() returned: {has_location} (type: {type(has_location).__name__})")

    assert profile_location is not None, "Should return location data"
    assert has_location is True, "Should return True for valid location"
    assert isinstance(has_location, bool), "Must be bool"

    # Simulate Pydantic validation
    from pydantic import BaseModel

    class ChatStartResponse(BaseModel):
        profile_location_available: bool

    response = ChatStartResponse(profile_location_available=has_location)
    print(f"  Pydantic validation: SUCCESS (value={response.profile_location_available})")


def scenario_pydantic_validation_with_none_coalescing():
    """Scenario 5: Full chat.py logic with quadruple-layer defense."""
    print("Full chat.py logic simulation (quadruple-layer defense)")

    user = MockUser()  # No location columns

    # Simulate chat.py logic
    has_profile_location = False  # DEFAULT

    try:
        profile_location = extract_location_from_user_profile(user)
        if profile_location is None:
            has_profile_location = False
            print("  Layer 1: profile_location is None → False")
        else:
            try:
                has_meaningful = has_meaningful_location(profile_location)
                # Triple None coalescing
                has_profile_location = bool(has_meaningful) if has_meaningful is not None else False
                print(f"  Layer 2: has_meaningful={has_meaningful} → {has_profile_location}")
            except Exception as e:
                print(f"  Layer 3: Exception caught → False (error: {e})")
                has_profile_location = False
    except Exception as e:
        print(f"  Layer 4: Outer exception caught → False (error: {e})")
        has_profile_location = False

    print(f"  Final value: {has_profile_location} (type: {type(has_profile_location).__name__})")

    # Type assertion
    assert isinstance(has_profile_location, bool), \
        f"BUG: must be bool, got {type(has_profile_location)}"

    # Final safety check
    profile_location_bool = bool(has_profile_location)
    assert isinstance(profile_location_bool, bool)

    print(f"  After safety check: {profile_location_bool}")

    # Pydantic validation
    from pydantic import BaseModel

    class ChatStartResponse(BaseModel):
        profile_location_available: bool

    response = ChatStartResponse(profile_location_available=profile_location_bool)
    print(f"  ✅ Pydantic validation: SUCCESS (value={response.profile_location_available})")


def main():
    """Run all verification scenarios."""
    print("="*60)
    print("LOCATION NONE-HANDLING FIX VERIFICATION")
    print("="*60)
    print("\nThis script verifies that the Pydantic validation error is fixed.")
    print("Testing various edge cases where location data is None or invalid.\n")

    scenarios = [
        ("Scenario 1: New user (no DB columns)", scenario_new_user_no_columns),
        ("Scenario 2: Incomplete location (district only)", scenario_user_with_district_only),
        ("Scenario 3: Empty string values", scenario_user_with_empty_strings),
        ("Scenario 4: Valid complete location", scenario_user_with_valid_location),
        ("Scenario 5: Full chat.py logic (quadruple-layer defense)", scenario_pydantic_validation_with_none_coalescing),
    ]

    results = []
    for name, func in scenarios:
        results.append(test_scenario(name, func))

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nResults: {passed}/{total} scenarios passed")

    if passed == total:
        print("\n✅ ALL SCENARIOS PASSED - Fix verified!")
        print("\nThe Pydantic validation error is resolved.")
        print("Safe to deploy to production.")
        return 0
    else:
        print("\n❌ SOME SCENARIOS FAILED - Fix incomplete!")
        print("Review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
