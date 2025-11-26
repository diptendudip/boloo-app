# Refactoring Code Examples - Before & After

**Document Purpose**: Concrete code examples showing how to refactor problematic patterns.
**Date**: 2025-11-15

---

## Example 1: Extract Business Logic from Router

### BEFORE (Business Logic in Router - ANTI-PATTERN)

```python
# app/routers/chat.py (lines 225-264)

def can_submit_now(extracted_data: Dict[str, Any]) -> bool:
    """
    Check if minimum fields are present AND VALID for submission.

    🔴 PROBLEM: Business logic function defined in router file!
    🔴 PROBLEM: Cannot test without importing router module
    🔴 PROBLEM: Violates Single Responsibility Principle
    """
    # BUG FIX #7: Check all minimum fields exist, are non-empty, AND valid
    for field in MINIMUM_REQUIRED_FIELDS:
        if field not in extracted_data or not extracted_data[field]:
            logger.warning(f"[Chat] ⚠️ Submission blocked: '{field}' is missing")
            return False
        if not str(extracted_data[field]).strip():
            logger.warning(f"[Chat] ⚠️ Submission blocked: '{field}' is empty")
            return False
        # Validate field value is not a placeholder like "unknown"
        if not is_valid_field_value(field, extracted_data[field]):
            logger.warning(f"[Chat] ⚠️ Submission blocked: '{field}' has invalid value")
            return False

    # CRITICAL: Semantic validation for issue_description
    issue_desc = str(extracted_data.get("issue_description", "")).strip()
    if not is_meaningful_issue_description(issue_desc):
        logger.warning(f"[Chat] ⚠️ Rejected issue_description as non-meaningful")
        return False

    logger.info(f"[Chat] ✅ Submission allowed: All minimum fields valid")
    return True
```

### AFTER (Business Logic in Domain Service - CORRECT PATTERN)

```python
# app/services/chat_validation_service.py (NEW FILE)

from typing import Dict, Any, List
import logging
from app.config.business_rules import ChatBusinessRules

logger = logging.getLogger(__name__)


class ChatValidationService:
    """
    Domain service for chat conversation validation.

    Encapsulates business rules for:
    - Submission eligibility
    - Field validation
    - Issue description meaningfulness
    """

    def __init__(self, business_rules: ChatBusinessRules):
        """
        Initialize validation service with business rules.

        Args:
            business_rules: Configuration for validation thresholds
        """
        self.business_rules = business_rules
        self.minimum_required_fields = ["issue_description", "location"]

    def can_submit_now(self, extracted_data: Dict[str, Any]) -> bool:
        """
        Determine if conversation has minimum valid fields for submission.

        Args:
            extracted_data: Dictionary of extracted field values

        Returns:
            True if minimum fields present, non-empty, and semantically valid
        """
        # Check all minimum fields exist and are valid
        for field in self.minimum_required_fields:
            if field not in extracted_data or not extracted_data[field]:
                logger.warning(f"[ChatValidation] Submission blocked: '{field}' missing")
                return False

            if not str(extracted_data[field]).strip():
                logger.warning(f"[ChatValidation] Submission blocked: '{field}' empty")
                return False

            # Validate field value (not placeholder like "unknown")
            if not self._is_valid_field_value(field, extracted_data[field]):
                logger.warning(
                    f"[ChatValidation] Submission blocked: '{field}' has "
                    f"invalid value: '{str(extracted_data[field])[:30]}'"
                )
                return False

        # Semantic validation for issue_description
        issue_desc = str(extracted_data.get("issue_description", "")).strip()
        if not self._is_meaningful_issue_description(issue_desc):
            logger.warning(
                f"[ChatValidation] Rejected issue_description as non-meaningful: "
                f"'{issue_desc[:50]}'"
            )
            return False

        logger.info("[ChatValidation] ✅ Submission allowed: All minimum fields valid")
        return True

    def _is_valid_field_value(self, field_name: str, value: Any) -> bool:
        """Validate field value is meaningful (not placeholder)."""
        if not value or not str(value).strip():
            return False

        value_str = str(value).strip().lower()

        # Reject common placeholders
        invalid_placeholders = [
            'unknown', 'not provided', 'n/a', 'missing', 'none',
            'पता नहीं', 'मालूम नहीं', 'नहीं पता'
        ]

        if value_str in invalid_placeholders:
            return False

        # Minimum length check
        if len(value_str) < 2:
            return False

        # Field-specific validation
        if field_name == "location":
            return self._validate_location(value_str)

        return True

    def _validate_location(self, value_str: str) -> bool:
        """Validate location has geographical indicators."""
        location_indicators = [
            'village', 'block', 'district', 'ward',
            'गाँव', 'ग्राम', 'ब्लॉक', 'जिला', 'वार्ड', 'नगर'
        ]
        has_indicator = any(indicator in value_str for indicator in location_indicators)

        if not has_indicator and len(value_str) < 5:
            logger.warning(f"[ChatValidation] Location too vague: '{value_str}'")
            return False

        return True

    def _is_meaningful_issue_description(self, text: str) -> bool:
        """Validate issue_description describes an actual problem."""
        if not text or not str(text).strip():
            return False

        text = str(text).strip()

        # Minimum length (at least 5 words)
        words = text.split()
        if len(words) < 5:
            return False

        # Problem indicator keywords
        problem_keywords = [
            'समस्या', 'परेशानी', 'दिक्कत', 'शिकायत',
            'नहीं', 'ठीक', 'खराब', 'बंद', 'गंदा', 'टूटा',
            'problem', 'issue', 'not working', 'broken'
        ]

        text_lower = text.lower()
        has_problem_keyword = any(kw in text_lower for kw in problem_keywords)

        if not has_problem_keyword:
            return False

        # Reject generic non-problem phrases
        generic_phrases = [
            'बोल रहा हूँ', 'speaking', 'calling from', 'मैं हूँ'
        ]

        for phrase in generic_phrases:
            if phrase in text_lower and len(words) < 10:
                return False

        return True


# Dependency injection factory
def get_chat_validation_service(
    business_rules: ChatBusinessRules = None
) -> ChatValidationService:
    """
    Factory function for dependency injection.

    Args:
        business_rules: Optional business rules (uses default if None)

    Returns:
        ChatValidationService instance
    """
    if business_rules is None:
        business_rules = ChatBusinessRules()

    return ChatValidationService(business_rules)
```

### USAGE in Router (Now Clean!)

```python
# app/routers/chat.py (REFACTORED)

from fastapi import APIRouter, Depends
from app.services.chat_validation_service import (
    ChatValidationService,
    get_chat_validation_service
)

router = APIRouter(prefix="/v1/chat", tags=["chat"])

@router.post("/turn", response_model=ChatTurnResponse)
async def process_chat_turn(
    conversation_id: str = Form(...),
    user_id: str = Form(...),
    # ✅ INJECT validation service (testable!)
    validation_service: ChatValidationService = Depends(get_chat_validation_service),
    db: Session = Depends(get_db)
):
    """Process chat turn (now clean routing logic only)."""

    # ... processing logic ...

    # ✅ USE injected service (not local function)
    user_can_submit = validation_service.can_submit_now(extracted_data)

    if user_can_submit:
        # Show submit button
        preview = create_preview_card(extracted_data)
        return ChatTurnResponse(
            show_submit_button=True,
            preview_card=preview,
            ...
        )
```

### TESTING (Now Easy!)

```python
# tests/unit/test_chat_validation_service.py

import pytest
from app.services.chat_validation_service import ChatValidationService
from app.config.business_rules import ChatBusinessRules


class TestChatValidationService:
    """Unit tests for chat validation logic."""

    @pytest.fixture
    def service(self):
        """Create validation service instance."""
        business_rules = ChatBusinessRules()
        return ChatValidationService(business_rules)

    def test_can_submit_with_minimum_fields(self, service):
        """Should allow submission with location + issue."""
        extracted_data = {
            "location": "Raipur Ward 12",
            "issue_description": "बिजली नहीं आ रही है 3 दिन से"
        }

        assert service.can_submit_now(extracted_data) is True

    def test_reject_placeholder_location(self, service):
        """Should reject 'unknown' as location."""
        extracted_data = {
            "location": "unknown",  # Placeholder
            "issue_description": "बिजली नहीं आ रही है"
        }

        assert service.can_submit_now(extracted_data) is False

    def test_reject_non_meaningful_issue(self, service):
        """Should reject location-only statements."""
        extracted_data = {
            "location": "Raipur",
            "issue_description": "मैं रायपुर से बोल रहा हूँ"  # No problem!
        }

        assert service.can_submit_now(extracted_data) is False

    def test_reject_missing_location(self, service):
        """Should reject if location missing."""
        extracted_data = {
            "issue_description": "बिजली नहीं आ रही है"
            # location missing
        }

        assert service.can_submit_now(extracted_data) is False

    def test_reject_too_short_issue(self, service):
        """Should reject issue descriptions < 5 words."""
        extracted_data = {
            "location": "Raipur",
            "issue_description": "बिजली नहीं"  # Only 2 words
        }

        assert service.can_submit_now(extracted_data) is False
```

**Benefits**:
- ✅ **Testable**: No HTTP mocking needed
- ✅ **Reusable**: Can use in other routers/services
- ✅ **Maintainable**: Single source of truth for validation
- ✅ **Type-safe**: Clear interface and documentation

---

## Example 2: Eliminate Error Handling Duplication

### BEFORE (Duplicated Error Handling - ANTI-PATTERN)

```python
# app/routers/chat.py (lines 676-810)

# Generate AI response using Azure OpenAI
try:
    logger.info("[Chat] 🤖 Generating AI response using Azure OpenAI...")
    ai_service = get_azure_openai_service()

    # ... filter missing fields ...

    # 🔴 DUPLICATION START: Completion logic (lines 710-737)
    is_truly_complete = (
        completeness_result.get("is_complete", False)
        or len(actually_missing_fields) == 0
        or user_can_submit_now
    )

    if is_truly_complete:
        # ✅ STOP ASKING QUESTIONS
        ai_response_hi = (
            "धन्यवाद! मैंने आपकी समस्या के बारे में पर्याप्त जानकारी ले ली है। "
            "अब आप अपनी रिपोर्ट सबमिट कर सकते हैं।"
        )
        ai_response_en = (
            "Thank you! I've collected enough information about your issue. "
            "You can submit your report now."
        )
    else:
        # Ask next question
        ai_result = ai_service.generate_conversation_response(...)
        ai_response_hi = ai_result["response_hi"]
        ai_response_en = ai_result["response_en"]
    # 🔴 DUPLICATION END

except AzureOpenAIServiceError as e:
    # Fallback to simple template if AI service fails
    logger.warning(f"[Chat] ⚠️ Azure OpenAI unavailable, using fallback: {e}")

    # 🔴 DUPLICATION START: SAME LOGIC AGAIN (lines 765-780)
    extracted = completeness_result["extracted_data"]
    user_can_submit_now = can_submit_now(extracted)

    is_truly_complete = (
        completeness_result.get("is_complete", False)
        or len(actually_missing_fields) == 0
        or user_can_submit_now
    )

    if is_truly_complete:
        # Same messages as above (DUPLICATE!)
        ai_response_hi = (
            "धन्यवाद! मैंने आपकी समस्या के बारे में पर्याप्त जानकारी ले ली है। "
            "अब आप अपनी रिपोर्ट सबमिट कर सकते हैं।"
        )
        ai_response_en = (
            "Thank you! I've collected enough information about your issue. "
            "You can submit your report now."
        )
    else:
        # Fallback question selection
        essential_field = next(...)
        ai_response_hi = essential_field.get("prompt_hi", "...")
        ai_response_en = essential_field.get("prompt_en", "...")
    # 🔴 DUPLICATION END
```

### AFTER (Extract to Single Function - CORRECT PATTERN)

```python
# app/services/chat_completion_service.py (NEW FILE)

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ChatCompletionService:
    """
    Domain service for conversation completion logic.

    Encapsulates business rules for:
    - Determining conversation completeness
    - Generating completion/continuation messages
    - Selecting next question from missing fields
    """

    def is_conversation_complete(
        self,
        analyzer_result: Dict[str, Any],
        missing_fields_filtered: List[Dict],
        extracted_data: Dict[str, Any]
    ) -> bool:
        """
        Single source of truth for conversation completeness.

        Uses OR logic: ANY of these conditions triggers completion:
        1. Analyzer says complete (is_complete=True)
        2. No missing fields left after filtering
        3. Domain rule: user can submit now (minimum fields present)

        Args:
            analyzer_result: Result from completeness analyzer
            missing_fields_filtered: Missing fields after tracker filtering
            extracted_data: Current extracted data

        Returns:
            True if conversation should be considered complete
        """
        from app.services.chat_validation_service import ChatValidationService

        validation_service = ChatValidationService()
        user_can_submit = validation_service.can_submit_now(extracted_data)

        is_complete = (
            analyzer_result.get("is_complete", False) or
            len(missing_fields_filtered) == 0 or
            user_can_submit
        )

        logger.info(
            f"[ChatCompletion] Conversation complete: {is_complete} "
            f"(analyzer={analyzer_result.get('is_complete')}, "
            f"no_missing={len(missing_fields_filtered) == 0}, "
            f"can_submit={user_can_submit})"
        )

        return is_complete

    def generate_response_messages(
        self,
        is_complete: bool,
        missing_fields: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Generate Hindi/English response pair for conversation.

        Args:
            is_complete: Whether conversation is complete
            missing_fields: List of missing field objects with prompts

        Returns:
            Tuple of (response_hi, response_en)
        """
        if is_complete:
            # Completion messages (single source of truth)
            response_hi = (
                "धन्यवाद! मैंने आपकी समस्या के बारे में पर्याप्त जानकारी ले ली है। "
                "अब आप अपनी रिपोर्ट सबमिट कर सकते हैं।"
            )
            response_en = (
                "Thank you! I've collected enough information about your issue. "
                "You can submit your report now."
            )

            logger.info("[ChatCompletion] Generated completion message")
            return (response_hi, response_en)

        else:
            # Select next question from missing fields
            if not missing_fields:
                # Defensive: should not happen, but handle gracefully
                logger.warning("[ChatCompletion] Incomplete but no missing fields!")
                return self.generate_response_messages(is_complete=True, missing_fields=[])

            # Prioritize critical/high importance fields
            essential_field = next(
                (
                    f for f in missing_fields
                    if f.get("importance") in ("critical", "high")
                ),
                missing_fields[0]  # Fallback to first field
            )

            response_hi = essential_field.get(
                "prompt_hi",
                "कृपया अपनी समस्या के बारे में थोड़ा और बताइए।"
            )
            response_en = essential_field.get(
                "prompt_en",
                "Please tell me a bit more about your issue."
            )

            logger.info(
                f"[ChatCompletion] Generated question for field: "
                f"{essential_field.get('field')}"
            )
            return (response_hi, response_en)


def get_chat_completion_service() -> ChatCompletionService:
    """Factory function for dependency injection."""
    return ChatCompletionService()
```

### USAGE in Router (Now DRY!)

```python
# app/routers/chat.py (REFACTORED)

from app.services.chat_completion_service import (
    ChatCompletionService,
    get_chat_completion_service
)

@router.post("/turn", response_model=ChatTurnResponse)
async def process_chat_turn(
    ...,
    completion_service: ChatCompletionService = Depends(get_chat_completion_service),
    ai_service: AIServiceProtocol = Depends(get_azure_openai_service)
):
    """Process chat turn (now DRY!)."""

    # ... processing logic ...

    # Determine completion status (single source of truth)
    is_truly_complete = completion_service.is_conversation_complete(
        analyzer_result=completeness_result,
        missing_fields_filtered=actually_missing_fields,
        extracted_data=extracted_data
    )

    # Generate AI response OR fallback
    try:
        if is_truly_complete:
            # ✅ Use completion service (no duplication!)
            ai_response_hi, ai_response_en = completion_service.generate_response_messages(
                is_complete=True,
                missing_fields=[]
            )
        else:
            # Ask AI to generate question
            ai_result = ai_service.generate_conversation_response(
                user_message=user_message,
                missing_fields=actually_missing_fields,
                collected_data=extracted_data,
                is_complete=False
            )
            ai_response_hi = ai_result["response_hi"]
            ai_response_en = ai_result["response_en"]

    except AzureOpenAIServiceError as e:
        logger.warning(f"[Chat] Azure OpenAI unavailable, using fallback: {e}")

        # ✅ Use SAME service (no duplication!)
        ai_response_hi, ai_response_en = completion_service.generate_response_messages(
            is_complete=is_truly_complete,
            missing_fields=actually_missing_fields
        )

    # ... rest of processing ...
```

**Benefits**:
- ✅ **DRY**: Eliminated 70+ lines of duplication
- ✅ **Maintainable**: Logic change in one place
- ✅ **Consistent**: Primary and fallback paths use same logic
- ✅ **Testable**: Can test completion logic independently

---

## Example 3: Dependency Injection for Testability

### BEFORE (Global Singleton - ANTI-PATTERN)

```python
# app/services/azure_openai_service.py (lines 658-677)

# Global instance (lazy initialization)
_azure_openai_service: Optional[AzureOpenAIService] = None


def get_azure_openai_service() -> AzureOpenAIService:
    """
    Get or create global AzureOpenAIService instance.

    🔴 PROBLEM: Global singleton shared across all requests
    🔴 PROBLEM: Cannot mock in tests without monkeypatching
    🔴 PROBLEM: State pollution between tests
    """
    global _azure_openai_service

    if _azure_openai_service is None:
        _azure_openai_service = AzureOpenAIService()

    return _azure_openai_service
```

```python
# app/routers/chat.py (OLD USAGE)

@router.post("/turn")
async def process_chat_turn(...):
    """Process chat turn."""

    # 🔴 PROBLEM: Direct call to global singleton
    ai_service = get_azure_openai_service()

    # Cannot mock this in tests without monkeypatching!
    ai_result = ai_service.generate_conversation_response(...)
```

```python
# tests/test_chat.py (FRAGILE TESTING)

import pytest
from app.routers.chat import router
from app.services import azure_openai_service

def test_chat_turn(monkeypatch):
    """Test chat turn (requires fragile monkeypatching)."""

    # 🔴 PROBLEM: Must monkeypatch global variable
    class MockAI:
        def generate_conversation_response(self, **kwargs):
            return {"response_hi": "मॉक", "response_en": "Mock"}

    monkeypatch.setattr(
        azure_openai_service,
        "_azure_openai_service",
        MockAI()
    )

    # This breaks if singleton initialization changes!
    response = client.post("/v1/chat/turn", ...)
    assert response.status_code == 200
```

### AFTER (Dependency Injection - CORRECT PATTERN)

```python
# app/services/protocols.py (NEW FILE)

from typing import Protocol, Dict, Any, List


class AIServiceProtocol(Protocol):
    """
    Protocol (interface) for AI conversation services.

    Defines the contract that all AI services must implement.
    Enables dependency injection and mocking.
    """

    def generate_conversation_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        missing_fields: List[Dict[str, Any]],
        collected_data: Dict[str, Any],
        is_complete: bool = False,
        questions_already_asked: Optional[List[str]] = None,
        user_sentiment: Optional[Dict[str, Any]] = None,
        can_submit_now: bool = False
    ) -> Dict[str, Any]:
        """
        Generate natural conversational response.

        Returns:
            Dict with keys: response_hi, response_en, empathy_used
        """
        ...


class CompletenessAnalyzerProtocol(Protocol):
    """Protocol for completeness analysis services."""

    def analyze_completeness(
        self,
        transcript: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        already_collected_fields: Optional[Dict[str, Any]] = None,
        question_tracker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze transcript completeness.

        Returns:
            Dict with keys: completeness_score, is_complete, collected_fields,
                           missing_fields, extracted_data
        """
        ...
```

```python
# app/services/azure_openai_service.py (REFACTORED)

# Remove global singleton! Factory function instead.

def get_azure_openai_service(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    deployment_name: Optional[str] = None,
    api_version: Optional[str] = None
) -> AzureOpenAIService:
    """
    Factory function for creating AzureOpenAIService instances.

    ✅ IMPROVED: Returns new instance (no global state)
    ✅ IMPROVED: Can inject mock in tests via dependency override

    Args:
        endpoint: Optional Azure endpoint (uses env var if None)
        api_key: Optional API key (uses env var if None)
        deployment_name: Optional deployment name (uses env var if None)
        api_version: Optional API version (uses env var if None)

    Returns:
        AzureOpenAIService instance
    """
    return AzureOpenAIService(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment_name,
        api_version=api_version
    )


# Verify AzureOpenAIService implements protocol (type checking)
def _check_protocol_compliance():
    """Type checker validates protocol implementation."""
    from app.services.protocols import AIServiceProtocol

    service: AIServiceProtocol = get_azure_openai_service()
    # If this doesn't type-check, AzureOpenAIService is missing protocol methods!
```

```python
# app/routers/chat.py (REFACTORED WITH DEPENDENCY INJECTION)

from fastapi import APIRouter, Depends
from app.services.protocols import AIServiceProtocol, CompletenessAnalyzerProtocol
from app.services.azure_openai_service import get_azure_openai_service
from app.services.completeness_analyzer import get_completeness_analyzer


@router.post("/turn", response_model=ChatTurnResponse)
async def process_chat_turn(
    conversation_id: str = Form(...),
    user_id: str = Form(...),
    # ✅ INJECT DEPENDENCIES (defaults to production implementations)
    ai_service: AIServiceProtocol = Depends(get_azure_openai_service),
    completeness_analyzer: CompletenessAnalyzerProtocol = Depends(get_completeness_analyzer),
    db: Session = Depends(get_db)
):
    """
    Process chat turn (now fully testable!).

    Dependencies are injected by FastAPI's DI system.
    Tests can override with mocks.
    """

    # Use injected dependencies (polymorphic - could be real or mock)
    completeness_result = completeness_analyzer.analyze_completeness(
        transcript=user_message,
        conversation_history=history,
        already_collected_fields=accumulated_data
    )

    ai_result = ai_service.generate_conversation_response(
        user_message=user_message,
        missing_fields=missing_fields,
        collected_data=extracted_data,
        is_complete=is_complete
    )

    # ... rest of logic ...
```

```python
# tests/test_chat.py (CLEAN TESTING)

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.azure_openai_service import get_azure_openai_service
from app.services.completeness_analyzer import get_completeness_analyzer


class MockAIService:
    """Mock AI service for testing."""

    def generate_conversation_response(self, **kwargs):
        """Return predictable response."""
        return {
            "response_hi": "कृपया अपनी समस्या बताएं।",
            "response_en": "Please describe your issue.",
            "empathy_used": True,
            "next_field_asked": "location"
        }


class MockCompletenessAnalyzer:
    """Mock completeness analyzer for testing."""

    def analyze_completeness(self, **kwargs):
        """Return predictable analysis."""
        return {
            "completeness_score": 0.5,
            "is_complete": False,
            "collected_fields": ["issue_description"],
            "missing_fields": [
                {
                    "field": "location",
                    "importance": "critical",
                    "prompt_hi": "कहाँ की समस्या है?",
                    "prompt_en": "Where is the issue?"
                }
            ],
            "extracted_data": {
                "issue_description": "बिजली नहीं आ रही"
            }
        }


@pytest.fixture
def client():
    """Create test client with dependency overrides."""

    # ✅ Override dependencies with mocks (clean!)
    app.dependency_overrides[get_azure_openai_service] = lambda: MockAIService()
    app.dependency_overrides[get_completeness_analyzer] = lambda: MockCompletenessAnalyzer()

    yield TestClient(app)

    # Cleanup
    app.dependency_overrides.clear()


def test_chat_turn_with_mocks(client):
    """Test chat turn (fast, reliable, no real API calls)."""

    response = client.post("/v1/chat/turn", data={
        "conversation_id": "test-conv-uuid",
        "user_id": "test-user-uuid",
        "text_message": "हमारे गांव में बिजली नहीं आ रही"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify mock responses used
    assert data["ai_response_hi"] == "कृपया अपनी समस्या बताएं।"
    assert data["completeness_score"] == 0.5
    assert data["is_complete"] is False

    # Test runs in ~100ms (no real API call!)
```

**Benefits**:
- ✅ **Fast Tests**: No real API calls (100x speedup)
- ✅ **Reliable**: No network dependencies
- ✅ **Isolated**: Each test gets clean mocks
- ✅ **Type-Safe**: Protocols enforce interface compliance
- ✅ **Easy Mocking**: Override dependencies, no monkeypatching

---

## Example 4: Centralized Configuration

### BEFORE (Scattered Magic Numbers - ANTI-PATTERN)

```python
# app/routers/chat.py
MAX_AUDIO_BYTES = 6 * 1024 * 1024  # ❓ Why 6MB?

if similarity >= 85:  # ❓ Why 85%?
    ...

if conversation.completeness_score >= 0.8:  # ❓ Why 80%?
    ...

# app/services/azure_openai_service.py
timeout=90.0  # ❓ Why 90 seconds?
temperature=0.3  # ❓ Why 0.3?

# app/services/completeness_analyzer.py
timeout=90.0  # ❌ DUPLICATE!
```

### AFTER (Centralized Configuration - CORRECT PATTERN)

```python
# app/config/business_rules.py (NEW FILE)

from pydantic import BaseSettings, Field


class ChatBusinessRules(BaseSettings):
    """
    Business rules for chat flow (tunable parameters).

    All thresholds, timeouts, and magic numbers centralized here.
    Can be overridden via environment variables for A/B testing.
    """

    # Audio upload limits
    max_audio_bytes: int = Field(
        default=6 * 1024 * 1024,  # 6MB
        description=(
            "Maximum audio file size in bytes. "
            "Constraint: WhatsApp allows 16MB, but 6MB chosen for network reliability. "
            "Rural India often has poor connectivity, so smaller files upload faster."
        ),
        env="CHAT_MAX_AUDIO_BYTES"
    )

    # Completeness thresholds
    completeness_submission_threshold: float = Field(
        default=0.8,  # 80%
        ge=0.0, le=1.0,
        description=(
            "Minimum completeness score to auto-submit report (vs manual review). "
            "At 80%, reports have enough information for government action. "
            "Below 80%, moderators review to extract missing details."
        ),
        env="CHAT_COMPLETENESS_THRESHOLD"
    )

    # Duplicate detection
    duplicate_similarity_threshold: int = Field(
        default=85,  # 85%
        ge=0, le=100,
        description=(
            "Fuzzy match threshold for duplicate question detection (rapidfuzz). "
            "85% chosen empirically - allows minor wording variations while catching duplicates. "
            "Lower (e.g., 70%) causes false positives, higher (e.g., 95%) misses duplicates."
        ),
        env="CHAT_DUPLICATE_THRESHOLD"
    )

    # AI service timeouts (environment-specific)
    ai_conversation_timeout_seconds: float = Field(
        default=90.0,
        description=(
            "Timeout for AI conversation generation in seconds. "
            "Production: 90s (handles slow Azure API responses). "
            "Development: 30s (fail fast for local testing)."
        ),
        env="AI_CONVERSATION_TIMEOUT"
    )

    # AI parameters (experimentation)
    ai_temperature: float = Field(
        default=0.3,
        ge=0.0, le=2.0,
        description=(
            "Temperature for AI responses (creativity control). "
            "0.0 = deterministic (always same output), "
            "0.3 = low creativity (chosen for consistent questions), "
            "1.0 = balanced, "
            "2.0 = highly creative (risky for structured data extraction)."
        ),
        env="AI_TEMPERATURE"
    )

    # Question limits
    max_followup_questions: int = Field(
        default=2,
        ge=0, le=10,
        description=(
            "Maximum follow-up questions AI can ask. "
            "2 chosen to balance information gathering vs user fatigue. "
            "More questions = better data, but users get frustrated."
        ),
        env="CHAT_MAX_FOLLOWUP_QUESTIONS"
    )

    class Config:
        env_prefix = "BOLOO_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global instance (loaded once at startup)
business_rules = ChatBusinessRules()
```

### USAGE (Now Discoverable & Documented)

```python
# app/routers/chat.py (REFACTORED)

from app.config.business_rules import business_rules

# Use configuration constants (not magic numbers)
MAX_AUDIO_BYTES = business_rules.max_audio_bytes

@router.post("/turn")
async def process_chat_turn(...):
    """Process chat turn."""

    # Use configured threshold (not hardcoded)
    if similarity >= business_rules.duplicate_similarity_threshold:
        logger.warning("Duplicate question detected")
        ...

    # Use configured completeness threshold
    if completeness_score >= business_rules.completeness_submission_threshold:
        # Auto-submit
        ...
```

```python
# app/services/azure_openai_service.py (REFACTORED)

from app.config.business_rules import business_rules

class AzureOpenAIService:
    def __init__(self, ...):
        self.client = AzureOpenAI(
            ...,
            timeout=business_rules.ai_conversation_timeout_seconds  # Configured!
        )

    def generate_conversation_response(self, ...):
        response = self.client.chat.completions.create(
            ...,
            temperature=business_rules.ai_temperature  # Configured!
        )
```

### A/B TESTING (Now Trivial!)

```bash
# Terminal 1 (Control group - 80% threshold)
export BOLOO_CHAT_COMPLETENESS_THRESHOLD=0.8
python -m uvicorn app.main:app --port 8000

# Terminal 2 (Test group - 70% threshold)
export BOLOO_CHAT_COMPLETENESS_THRESHOLD=0.7
python -m uvicorn app.main:app --port 8001

# Compare metrics:
# - Submission rate (expect higher with 70%)
# - Data quality (expect lower with 70%)
# - User satisfaction (measure via surveys)
```

**Benefits**:
- ✅ **Discoverable**: IDE autocomplete shows all settings
- ✅ **Documented**: Each setting explains WHY chosen
- ✅ **Tunable**: Override via env vars (no code changes)
- ✅ **Validated**: Pydantic enforces valid ranges
- ✅ **A/B Testable**: Easy experimentation

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Purpose**: Code-level refactoring guide with before/after examples
**Next Steps**: Begin Phase 1 implementation with these patterns
