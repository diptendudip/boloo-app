#!/usr/bin/env python3
"""
Quick test to verify has_meaningful_location fix.
Run: python test_location_fix.py
"""

import sys
from app.utils.location_confirmation import has_meaningful_location

def test_has_meaningful_location():
    """Test all edge cases for has_meaningful_location"""

    print("Testing has_meaningful_location fix...")
    print("=" * 60)

    # Test 1: None input
    result = has_meaningful_location(None)
    assert result == False, f"Test 1 FAILED: Expected False, got {result}"
    assert isinstance(result, bool), f"Test 1 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 1: None input → False (bool)")

    # Test 2: Empty dict
    result = has_meaningful_location({})
    assert result == False, f"Test 2 FAILED: Expected False, got {result}"
    assert isinstance(result, bool), f"Test 2 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 2: Empty dict → False (bool)")

    # Test 3: Only district (insufficient)
    result = has_meaningful_location({"district": "बस्तर"})
    assert result == False, f"Test 3 FAILED: Expected False, got {result}"
    assert isinstance(result, bool), f"Test 3 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 3: Only district → False (bool)")

    # Test 4: District + village (valid)
    result = has_meaningful_location({"district": "बस्तर", "village": "मादर"})
    assert result == True, f"Test 4 FAILED: Expected True, got {result}"
    assert isinstance(result, bool), f"Test 4 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 4: District + village → True (bool)")

    # Test 5: District + block (valid)
    result = has_meaningful_location({"district": "बस्तर", "block": "लोहंडीगुड़ा"})
    assert result == True, f"Test 5 FAILED: Expected True, got {result}"
    assert isinstance(result, bool), f"Test 5 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 5: District + block → True (bool)")

    # Test 6: Invalid type
    result = has_meaningful_location("not a dict")
    assert result == False, f"Test 6 FAILED: Expected False, got {result}"
    assert isinstance(result, bool), f"Test 6 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 6: Invalid type → False (bool)")

    # Test 7: Empty strings (should be False)
    result = has_meaningful_location({"district": "", "village": ""})
    assert result == False, f"Test 7 FAILED: Expected False, got {result}"
    assert isinstance(result, bool), f"Test 7 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 7: Empty strings → False (bool)")

    # Test 8: Complete location
    result = has_meaningful_location({
        "street": "कोटेवार पारा",
        "village": "मादर",
        "panchayat": "मादर",
        "block": "लोहंडीगुड़ा",
        "district": "बस्तर",
        "state": "छत्तीसगढ़"
    })
    assert result == True, f"Test 8 FAILED: Expected True, got {result}"
    assert isinstance(result, bool), f"Test 8 FAILED: Expected bool, got {type(result)}"
    print("✅ Test 8: Complete location → True (bool)")

    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print()
    print("The fix guarantees:")
    print("  ✓ Always returns bool (True or False)")
    print("  ✓ Never returns None")
    print("  ✓ Handles all edge cases gracefully")
    print("  ✓ Safe for Pydantic validation")
    return True

if __name__ == "__main__":
    try:
        test_has_meaningful_location()
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
