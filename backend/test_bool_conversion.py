"""Test to verify bool conversion works correctly"""

# Test 1: None handling
profile_location = None
has_profile_location = bool(profile_location and True)
print(f"Test 1 - bool(None and True): {has_profile_location}, type: {type(has_profile_location)}")

# Test 2: Function return
def has_meaningful_location(loc):
    if not loc:
        return False
    return True

has_profile_location2 = bool(None and has_meaningful_location(None))
print(f"Test 2 - bool(None and func(None)): {has_profile_location2}, type: {type(has_profile_location2)}")

# Test 3: Direct assignment
test_val = None and has_meaningful_location(None)
print(f"Test 3 - None and func(None) RAW: {test_val}, type: {type(test_val)}")
print(f"Test 3 - bool() wrapper: {bool(test_val)}, type: {type(bool(test_val))}")

# Test 4: What Pydantic sees
from pydantic import BaseModel

class TestModel(BaseModel):
    flag: bool = False

# This should fail if test_val is None
try:
    model = TestModel(flag=test_val)
    print(f"Test 4 PASS - Pydantic accepted: {model.flag}")
except Exception as e:
    print(f"Test 4 FAIL - Pydantic error: {e}")

# This should pass
try:
    model2 = TestModel(flag=bool(test_val))
    print(f"Test 5 PASS - Pydantic with bool(): {model2.flag}")
except Exception as e:
    print(f"Test 5 FAIL - Pydantic error: {e}")
