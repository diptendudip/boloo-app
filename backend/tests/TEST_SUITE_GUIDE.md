# Boloo App Test Suite Guide

## Overview

This test suite provides comprehensive testing for the chat and OTP systems, focusing on:
1. **Pydantic validation issues** with location fields
2. **OTP system** with phone_number column support
3. **Location confirmation** logic and error handling

## Test Files

### 1. `test_chat_endpoint.py`
**Purpose**: Test chat endpoints with location validation

**Test Classes**:
- `TestChatEndpointLocationValidation` - Tests location field scenarios
  - None values in user location fields
  - Empty string values
  - Partial location data
  - Valid complete location data
  - Boolean type safety for Pydantic validation

- `TestChatEndpointLocationConfirmation` - Tests location confirmation flow
  - Hindi keyword detection
  - English keyword detection
  - Negative response handling

- `TestChatEndpointErrorHandling` - Tests error handling
  - Missing user location attributes
  - None user object handling
  - Invalid data types

- `TestChatEndpointPydanticValidation` - Tests Pydantic validation fixes
  - None values causing validation errors
  - Mixed None and actual values
  - Boolean type guarantees

- `TestChatFlowIntegration` - Integration tests
  - New user without location
  - Existing user with location
  - Location confirmation flow

**Key Tests**:
```python
# Test None values don't cause Pydantic errors
test_user_with_none_location_fields()

# Test location confirmation boolean type safety
test_location_confirmation_boolean_type_safety()

# Test Pydantic validation with None
test_pydantic_location_field_validation_with_none()
```

### 2. `test_otp_endpoint.py`
**Purpose**: Test OTP system with phone_number column

**Test Classes**:
- `TestOTPModelPhoneNumberSupport` - Tests phone_number column
  - OTP creation with phone_number
  - Backward compatibility with email
  - Both phone and email support
  - None phone_number handling

- `TestOTPValidation` - Tests OTP validation logic
  - Valid OTP (not used, not expired)
  - Expired OTP handling
  - Used OTP handling

- `TestOTPCodeGeneration` - Tests OTP code generation
  - 6-digit format
  - Numeric validation
  - Randomness check

- `TestOTPRepresentation` - Tests string representation
  - __repr__ with phone_number
  - __repr__ with email
  - Preference for phone over email

- `TestOTPToDictSerialization` - Tests to_dict serialization
  - phone_number field inclusion
  - All fields included
  - DateTime serialization

- `TestOTPNoneValueHandling` - Tests None value handling
  - All None identifiers
  - __repr__ with None
  - to_dict with None values

**Key Tests**:
```python
# Test phone_number column support
test_otp_creation_with_phone_number()

# Test None handling doesn't crash
test_otp_creation_with_none_phone_number()

# Test OTP validation
test_otp_is_valid_when_not_used_and_not_expired()
```

### 3. `test_location_confirmation.py`
**Purpose**: Test location confirmation utilities

**Test Classes**:
- `TestLocationConfirmationDetection` - Tests confirmation detection
  - Hindi keyword detection
  - English keyword detection
  - Case insensitivity
  - Confirmation with extra text

- `TestLocationRejectionDetection` - Tests rejection detection
  - Hindi rejection keywords
  - English rejection keywords
  - Rejection with extra text

- `TestLocationFormatting` - Tests location formatting
  - Complete location formatting
  - Partial location formatting
  - None field skipping
  - Hindi labels

- `TestLocationMerging` - Tests location merging
  - Street override keeps other fields
  - GPS coordinate override
  - Complete override
  - Empty extracted keeps profile

- `TestHasMeaningfulLocation` - **CRITICAL** for Pydantic validation
  - None input returns False (not None)
  - Empty dict returns False
  - District + village returns True
  - Invalid input types return False
  - **ALWAYS returns bool, never None**

- `TestExtractLocationFromProfile` - Tests profile extraction
  - No location returns None
  - Complete location returns dict
  - None user returns None
  - Insufficient location returns None

**Key Tests**:
```python
# CRITICAL: Test boolean type guarantee (Pydantic fix)
test_has_meaningful_location_never_returns_none()

# Test Hindi confirmation detection
test_hindi_confirmation_keywords()

# Test location extraction from profile
test_user_with_complete_location_returns_dict()
```

## Running Tests

### Quick Run (New Test Files Only)
```bash
# From project root
/Users/diptendu/boloo\ app/scripts/run-tests.sh
```

### With Coverage Report
```bash
/Users/diptendu/boloo\ app/scripts/run-tests.sh --coverage
```

### Run All Tests (Including Existing)
```bash
/Users/diptendu/boloo\ app/scripts/run-tests.sh --all
```

### Individual Test Files
```bash
# From backend directory
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Chat endpoint tests
pytest tests/test_chat_endpoint.py -v -s

# OTP endpoint tests
pytest tests/test_otp_endpoint.py -v -s

# Location confirmation tests
pytest tests/test_location_confirmation.py -v -s
```

### Run Specific Test Class
```bash
pytest tests/test_chat_endpoint.py::TestChatEndpointLocationValidation -v
```

### Run Specific Test Method
```bash
pytest tests/test_chat_endpoint.py::TestChatEndpointLocationValidation::test_user_with_none_location_fields -v
```

## Test Coverage

The test suite covers:

### Chat System Issues ✅
- [x] Pydantic validation errors with None location fields
- [x] Empty string location values
- [x] Partial location data (district only)
- [x] Valid complete location data
- [x] Boolean type safety for `has_meaningful_location`
- [x] Location confirmation keyword detection (Hindi/English)
- [x] Error handling for missing attributes

### OTP System Issues ✅
- [x] phone_number column support in OTP model
- [x] None phone_number handling
- [x] Email backward compatibility
- [x] OTP validation logic (expiry, usage)
- [x] OTP code generation (6 digits, numeric)
- [x] String representation with phone/email
- [x] Serialization to dict

### Location Confirmation ✅
- [x] Hindi and English keyword detection
- [x] Location formatting with Hindi labels
- [x] Location merging (override + keep profile)
- [x] Meaningful location validation
- [x] Profile location extraction
- [x] None value handling throughout

## Critical Fixes Tested

### 1. Pydantic Validation Error (Chat System)
**Issue**: `has_meaningful_location()` was returning `None`, causing Pydantic validation errors.

**Fix**: Function now ALWAYS returns `bool` (True/False), never None.

**Tests**:
- `test_location_confirmation_boolean_type_safety()`
- `test_pydantic_location_field_validation_with_none()`
- `test_has_meaningful_location_never_returns_none()`

### 2. OTP Phone Number Column
**Issue**: OTP model may not have phone_number column.

**Fix**: Added phone_number column with nullable support.

**Tests**:
- `test_otp_creation_with_phone_number()`
- `test_otp_creation_with_none_phone_number()`
- `test_query_otp_by_phone_number()`

### 3. None Value Handling
**Issue**: None values in location fields causing crashes.

**Fix**: Defensive None checks throughout location utilities.

**Tests**:
- `test_user_with_none_location_fields()`
- `test_missing_user_location_attributes_gracefully()`
- `test_user_object_none_handling()`

## Test Requirements

### Python Packages
```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### Database
Tests use mocked database sessions - no actual database required for these tests.

## CI/CD Integration

Add to GitHub Actions workflow:
```yaml
- name: Run Tests
  run: |
    cd backend
    pytest tests/test_chat_endpoint.py tests/test_otp_endpoint.py tests/test_location_confirmation.py -v --cov
```

## Debugging Failed Tests

### View Full Error Output
```bash
pytest tests/test_chat_endpoint.py -vv --tb=long
```

### Stop at First Failure
```bash
pytest tests/test_chat_endpoint.py -x
```

### Show Print Statements
```bash
pytest tests/test_chat_endpoint.py -v -s
```

### Run Only Failed Tests
```bash
pytest --lf  # Last failed
```

## Expected Test Results

All tests should pass. Example output:
```
tests/test_chat_endpoint.py::TestChatEndpointLocationValidation::test_user_with_none_location_fields PASSED
tests/test_chat_endpoint.py::TestChatEndpointLocationValidation::test_location_confirmation_boolean_type_safety PASSED
...
tests/test_otp_endpoint.py::TestOTPModelPhoneNumberSupport::test_otp_creation_with_phone_number PASSED
...
tests/test_location_confirmation.py::TestHasMeaningfulLocation::test_has_meaningful_location_never_returns_none PASSED
...

========== 60+ passed in 2.5s ==========
```

## Troubleshooting

### ImportError: No module named 'app'
```bash
# Ensure you're in the backend directory
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Or set PYTHONPATH
export PYTHONPATH=/Users/diptendu/boloo\ app/boloo-app/backend:$PYTHONPATH
```

### Database Connection Errors
These tests use mocks - no database connection needed. If you see database errors, check imports.

### Fixture Not Found
Ensure pytest is installed and running from correct directory.

## Next Steps

1. **Run tests**: `./scripts/run-tests.sh`
2. **Fix any failures**: Review error messages and fix code
3. **Add to CI/CD**: Integrate into deployment pipeline
4. **Monitor coverage**: Aim for >80% coverage
5. **Expand tests**: Add integration tests with actual database

## Contact

For questions about these tests, refer to the test file comments or check the Boloo App documentation.
