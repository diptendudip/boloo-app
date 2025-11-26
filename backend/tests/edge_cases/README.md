# Chat Conversation Edge Case Tests

## Overview

Comprehensive test suite for the chat conversation flow, focusing on edge cases that could break the OR logic fix and conversation completion logic.

## Test Coverage

### 1. OR Logic Edge Cases (`TestORLogicEdgeCases`)
Tests the completion logic from `chat.py` lines 710-718:
```python
is_truly_complete = (
    is_complete
    or len(actually_missing_fields) == 0
    or user_can_submit_now
)
```

**Test Scenarios:**
- ✅ Empty `actually_missing_fields` triggers completion
- ✅ `is_complete=True` triggers completion
- ✅ Invalid data prevents submission
- ✅ All conditions false = continue asking
- ✅ Valid minimum fields trigger completion

### 2. State Management Edge Cases (`TestStateManagementEdgeCases`)
Tests JSONB extraction and state handling from `chat.py` lines 561-564:

**Test Scenarios:**
- ✅ JSONB extraction returns `None` → defaults to `{}`
- ✅ Malformed data (wrong type) → graceful fallback
- ✅ Valid JSONB dict → data preserved correctly

### 3. QuestionTracker Edge Cases (`TestQuestionTrackerEdgeCases`)
Tests question tracking and duplicate prevention from `chat.py` lines 569-570, 689-694:

**Test Scenarios:**
- ✅ Field asked multiple times → filtered out
- ✅ Empty conversation history → no crash
- ✅ Filter already-asked fields from missing_fields

### 4. User Sentiment Edge Cases (`TestUserSentimentEdgeCases`)
Tests sentiment detection and handling from `chat.py` lines 573-652:

**Test Scenarios:**
- ✅ Frustrated user with incomplete data → gentle ask
- ✅ User wants to submit with valid data → show preview

### 5. Validation Edge Cases (`TestValidationEdgeCases`)
Tests field validation from `chat.py` lines 174-264:

**Test Scenarios:**
- ✅ Placeholder values rejected (`"unknown"`, `"problem"`, etc.)
- ✅ Very short descriptions rejected (< 5 words)
- ✅ Location-only responses not valid as issue descriptions
- ✅ Valid issue descriptions accepted
- ✅ Minimum length requirements enforced

### 6. Integration Scenarios (`TestIntegrationScenarios`)
Complex scenarios combining multiple edge cases:

**Test Scenarios:**
- ✅ QuestionTracker + placeholder validation (double filtering)
- ✅ OR logic with empty QuestionTracker
- ✅ Frustrated user + valid data (sentiment override)

### 7. Boundary Conditions (`TestBoundaryConditions`)
Edge cases at exact boundaries:

**Test Scenarios:**
- ✅ Minimum word count boundary (4 vs 5 words)
- ✅ Location minimum length (2 chars)
- ✅ Empty string handling (various forms)

## Running the Tests

### Run all edge case tests:
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
pytest tests/edge_cases/test_chat_conversation_edge_cases.py -v
```

### Run specific test suite:
```bash
# OR logic tests only
pytest tests/edge_cases/test_chat_conversation_edge_cases.py::TestORLogicEdgeCases -v

# Validation tests only
pytest tests/edge_cases/test_chat_conversation_edge_cases.py::TestValidationEdgeCases -v

# Integration scenarios
pytest tests/edge_cases/test_chat_conversation_edge_cases.py::TestIntegrationScenarios -v
```

### Run with coverage:
```bash
pytest tests/edge_cases/test_chat_conversation_edge_cases.py --cov=app.routers.chat --cov-report=html
```

### Run with verbose output:
```bash
pytest tests/edge_cases/test_chat_conversation_edge_cases.py -vv --tb=short
```

## Key Test Patterns

### 1. Mocking Azure OpenAI
```python
@pytest.fixture
def mock_azure_openai_service():
    service = Mock()
    service.generate_conversation_response = Mock(return_value={
        "response_hi": "धन्यवाद!",
        "response_en": "Thank you!"
    })
    return service
```

### 2. Testing OR Logic
```python
is_truly_complete = (
    is_complete
    or len(actually_missing_fields) == 0  # Test this!
    or user_can_submit_now
)
```

### 3. Testing Validation
```python
# Test placeholder rejection
assert is_valid_field_value("location", "unknown") is False

# Test meaningful descriptions
assert is_meaningful_issue_description("ok") is False
```

## Critical Edge Cases Covered

1. **Empty `actually_missing_fields` but `is_complete=False`**
   - Should still trigger completion (OR logic)
   - Tests that QuestionTracker filtering works correctly

2. **Placeholder values like "unknown"**
   - Should be rejected by `is_valid_field_value()`
   - Should NOT count in `collected_field_names`

3. **Location-only responses**
   - "मैं नीलकंठपुर से बोल रहा हूँ"
   - Should extract location BUT NOT issue_description

4. **Frustrated user sentiment**
   - If minimum fields missing → gentle ask
   - If minimum fields present → allow submission

5. **JSONB extraction failures**
   - `None` from database → defaults to `{}`
   - Wrong type → graceful fallback

## Dependencies Required

```bash
pip install pytest pytest-mock pytest-asyncio
```

## Test Data Patterns

### Valid Minimum Data:
```python
{
    "location": "नीलकंठपुर ग्राम पंचायत",
    "issue_description": "बिजली की समस्या पांच दिनों से चल रही है"
}
```

### Invalid Placeholder Data:
```python
{
    "location": "unknown",
    "issue_description": "problem"
}
```

### Location-Only Response:
```python
"मैं नीलकंठपुर से बोल रहा हूँ"  # NOT a valid issue description
```

## Expected Behavior Summary

| Scenario | `is_complete` | `missing_fields` | `can_submit` | Expected |
|----------|---------------|------------------|--------------|----------|
| All fields valid | `True` | `[]` | `True` | ✅ Complete |
| Empty after filter | `False` | `[]` | `False` | ✅ Complete |
| Has placeholders | `False` | `[...]` | `False` | ❌ Continue |
| Minimum valid | `False` | `[...]` | `True` | ✅ Complete |
| All missing | `False` | `[...]` | `False` | ❌ Continue |

## Notes

- All tests use mocks to avoid external dependencies
- Tests focus on pure function logic, not API integration
- QuestionTracker tests verify state management
- Validation tests ensure data quality
- Integration tests verify combined edge cases work correctly
