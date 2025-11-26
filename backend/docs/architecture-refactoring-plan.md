# Architecture Refactoring Plan - Quick Reference

**Status**: 🟡 Proposal (Pending Review)
**Priority**: 🔴 High (Technical Debt > Feature Velocity)
**Estimated Effort**: 8 weeks (1 senior engineer)

---

## Problem Summary

### Code Metrics

```
┌─────────────────────────────────────────────────────────┐
│ File                          │ LOC  │ Complexity │ Issues │
├─────────────────────────────────────────────────────────┤
│ routers/chat.py               │ 1254 │    35+     │   🔴   │
│ services/azure_openai.py      │  676 │    18      │   🟡   │
│ services/completeness_analyzer│  721 │    10      │   🟢   │
├─────────────────────────────────────────────────────────┤
│ TOTAL                         │ 2651 │    -       │   -    │
└─────────────────────────────────────────────────────────┘

🔴 Critical: process_chat_turn() is 520 lines with 35+ complexity
   (Recommended: <100 lines, <10 complexity)
```

### Top 5 Critical Issues

1. **🔴 Business Logic in Router** (225-264 chat.py)
   - `can_submit_now()`, `is_meaningful_issue_description()` belong in service layer
   - Violates Single Responsibility Principle
   - Untestable without HTTP mocking

2. **🔴 Error Handling Duplication** (676-810 chat.py)
   - Primary path (710-737) duplicates fallback path (765-780)
   - 70+ lines duplicated (95% similarity)
   - Maintenance risk: must update two places

3. **🔴 No Dependency Injection**
   - Global singletons (`_azure_openai_service`, `_completeness_analyzer`)
   - Cannot mock for testing
   - Requires monkeypatching (fragile)

4. **🔴 Hard-Coded Configuration**
   - Magic numbers scattered (85% similarity, 0.8 completeness, 90s timeout)
   - Cannot tune without code changes
   - No A/B testing capability

5. **🔴 High Cyclomatic Complexity**
   - `process_chat_turn()`: 35+ branches
   - Industry standard: <10 (maintainable), <20 (complex)
   - Estimated test coverage: 20%

---

## Refactoring Strategy

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Improve testability and reduce duplication

```python
# BEFORE (chat.py - 1254 lines)
@router.post("/turn")
async def process_chat_turn(
    conversation_id: str = Form(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # 520 lines of mixed concerns
    # Business logic + routing + validation + orchestration
    ai_service = get_azure_openai_service()  # Global singleton
    completeness_analyzer = get_completeness_analyzer()  # Global singleton

    # Duplicated error handling
    try:
        if is_truly_complete:  # Business logic in router
            ai_response_hi = "धन्यवाद! मैंने आपकी समस्या..."
    except AzureOpenAIServiceError as e:
        if is_truly_complete:  # DUPLICATE LOGIC
            ai_response_hi = "धन्यवाद! मैंने आपकी समस्या..."

# AFTER (refactored)
@router.post("/turn")
async def process_chat_turn(
    conversation_id: str = Form(...),
    user_id: str = Form(...),
    # DEPENDENCY INJECTION (testable!)
    ai_service: AIServiceProtocol = Depends(get_azure_openai_service),
    analyzer: CompletenessAnalyzerProtocol = Depends(get_completeness_analyzer),
    validation_service: ChatValidationService = Depends(get_validation_service),
    db: Session = Depends(get_db)
):
    # Business logic extracted to services
    is_submittable = validation_service.can_submit_now(extracted_data)

    # Error handling centralized
    ai_response_hi, ai_response_en = get_ai_response_or_fallback(
        ai_service=ai_service,
        is_complete=is_truly_complete,
        missing_fields=missing_fields
    )
```

**Deliverables**:
- ✅ Define service protocols (`AIServiceProtocol`, `CompletenessAnalyzerProtocol`)
- ✅ Extract business logic to `ChatValidationService`, `ChatCompletionService`
- ✅ Add dependency injection to router
- ✅ Eliminate 70+ lines of duplicated error handling
- ✅ Centralize configuration in `config/business_rules.py`

**Metrics**:
- Test coverage: 20% → 80%
- Duplicated LOC: 70 → 0
- Router size: 1254 → 800 lines

---

### Phase 2: Complexity Reduction (Weeks 3-4)

**Goal**: Refactor `process_chat_turn()` using Command Pattern

```python
# BEFORE (520 lines, complexity 35+)
async def process_chat_turn(...):
    # Validation
    if not text_message and not audio:
        raise HTTPException(400, ...)

    # Transcription
    if audio:
        result = await transcription_service.transcribe_audio(...)
        user_message = result["transcript"]

    # Completeness analysis
    completeness_result = completeness_analyzer.analyze_completeness(...)

    # AI response generation
    try:
        ai_result = ai_service.generate_conversation_response(...)
    except AzureOpenAIServiceError:
        # Fallback logic...

    # Save to database
    turn = conversation_service.add_turn(...)

    return ChatTurnResponse(...)

# AFTER (Command Pattern - each command <50 lines, complexity <10)
class ChatTurnProcessor:
    def __init__(self, commands: List[ChatTurnCommand]):
        self.commands = commands

    def process(self, context: ChatTurnContext) -> ChatTurnResponse:
        for command in self.commands:
            command.execute(context)
        return self._build_response(context)

async def process_chat_turn(...):
    context = ChatTurnContext(conversation_id, user_id, text_message, audio)

    processor = ChatTurnProcessor([
        ValidateInputCommand(),           # 30 lines, complexity 5
        TranscribeAudioCommand(),         # 40 lines, complexity 4
        LoadConversationStateCommand(),   # 25 lines, complexity 3
        AnalyzeCompletenessCommand(),     # 35 lines, complexity 6
        GenerateAIResponseCommand(),      # 45 lines, complexity 8
        SaveConversationTurnCommand()     # 30 lines, complexity 4
    ])

    return processor.process(context)
```

**Deliverables**:
- ✅ Implement Command Pattern for chat turn processing
- ✅ Extract each step to separate command (6 commands total)
- ✅ Implement Repository Pattern for conversation state
- ✅ Externalize prompts to Jinja2 templates
- ✅ Add prompt versioning for A/B testing

**Metrics**:
- `process_chat_turn()` complexity: 35+ → 8
- Router size: 800 → 400 lines
- Number of files: +15 (6 commands, 5 services, 4 validators)
- Test coverage: 80% → 90%

---

### Phase 3: API Evolution (Weeks 5-6)

**Goal**: Prepare for long-term maintainability

```python
# BEFORE (ChatTurnResponse - 16 fields, redundant)
class ChatTurnResponse(BaseModel):
    success: bool
    conversation_id: str
    turn_number: int
    user_message: str
    language_detected: str
    ai_response_hi: str
    ai_response_en: str
    completeness_score: float
    is_complete: bool                # Redundant with ready_for_submission
    collected_fields: list
    missing_fields: list
    extracted_data: Dict[str, Any]
    should_continue: bool             # Redundant with is_complete
    ready_for_submission: bool        # Redundant with is_complete
    show_submit_button: bool
    show_skip_button: bool
    preview_card: Optional[PreviewCard]
    error: Optional[str]

# AFTER (V2 API - Grouped concerns, clear semantics)
class ChatTurnResponseV2(BaseModel):
    conversation_id: str
    turn_number: int

    user_input: UserInputData         # text, language_detected, source
    ai_response: AIResponseData       # message_hi, message_en, sentiment
    progress: ConversationProgress    # completeness_score, fields, status
    ui_actions: UIActions             # show_submit_button, show_skip_button

class ConversationProgress(BaseModel):
    completeness_score: float
    fields_collected: List[str]
    fields_missing: List[MissingField]
    extracted_data: Dict[str, Any]
    status: Literal["collecting", "complete", "submittable"]  # Single source of truth
```

**Deliverables**:
- ✅ Design V2 API with streamlined response models
- ✅ Implement API versioning (`/v1/chat` and `/v2/chat`)
- ✅ Add deprecation warnings to V1 endpoints
- ✅ Hybrid JSONB + relational schema for searchable fields
- ✅ Add structured error codes with localization

**Metrics**:
- API response fields: 16 → 8 (50% reduction)
- Redundant fields: 3 → 0
- API versions: 1 → 2 (backward compatible)

---

## Architectural Patterns to Implement

### 1. Command Pattern (Chat Turn Processing)

```
┌──────────────────────────────────────────────────────┐
│ ChatTurnProcessor (Orchestrator)                     │
├──────────────────────────────────────────────────────┤
│ execute_pipeline([                                   │
│   ValidateInputCommand()        ← 30 lines, cplx 5   │
│   TranscribeAudioCommand()      ← 40 lines, cplx 4   │
│   LoadConversationStateCommand()← 25 lines, cplx 3   │
│   AnalyzeCompletenessCommand()  ← 35 lines, cplx 6   │
│   GenerateAIResponseCommand()   ← 45 lines, cplx 8   │
│   SaveConversationTurnCommand() ← 30 lines, cplx 4   │
│ ])                                                    │
└──────────────────────────────────────────────────────┘

Benefits:
✅ Testable: Each command tested in isolation
✅ Reusable: Commands composable in different pipelines
✅ Maintainable: Complexity <10 per command
✅ Clear: Processing steps explicit and ordered
```

### 2. Repository Pattern (State Management)

```
┌──────────────────────────────────────────────────────┐
│ ConversationStateRepository                          │
├──────────────────────────────────────────────────────┤
│ get_accumulated_data(conversation_id)                │
│   → Read current state from database (JSONB)         │
│                                                       │
│ merge_and_save(conversation_id, new_data)            │
│   → Merge new_data with existing state               │
│   → Save merged state to database                    │
│   → Return merged state (single source of truth)     │
└──────────────────────────────────────────────────────┘

Current Confusion:
❓ Is conversation.extracted_data the source of truth?
❓ Or completeness_result["extracted_data"]?
❓ Who merges state: router, service, or analyzer?

After Repository Pattern:
✅ Database (via repository) is single source of truth
✅ Explicit merge logic
✅ Testable in isolation
✅ Clear state ownership
```

### 3. Strategy Pattern (Field Validation)

```
┌──────────────────────────────────────────────────────┐
│ FieldValidator (Abstract Strategy)                   │
├──────────────────────────────────────────────────────┤
│ validate(value: Any) → bool                          │
└──────────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
┌────────┴────┐  ┌──────┴───────┐  ┌──┴─────────────┐
│ Location    │  │ IssueDesc    │  │ Phone          │
│ Validator   │  │ Validator    │  │ Validator      │
├─────────────┤  ├──────────────┤  ├────────────────┤
│ validate()  │  │ validate()   │  │ validate()     │
│ - check len │  │ - problem    │  │ - regex check  │
│ - indicators│  │   keywords   │  │ - length check │
└─────────────┘  └──────────────┘  └────────────────┘

Registry:
FIELD_VALIDATORS = {
    "location": LocationValidator(),
    "issue_description": IssueDescriptionValidator(),
    "phone": PhoneValidator()
}

Benefits:
✅ Extensible: Add new validators without changing existing code
✅ Testable: Each validator tested independently
✅ Maintainable: Field-specific logic encapsulated
```

### 4. Dependency Injection (Testability)

```
┌──────────────────────────────────────────────────────┐
│ Production (Real Services)                           │
├──────────────────────────────────────────────────────┤
│ @router.post("/turn")                                │
│ async def process_chat_turn(                         │
│   ai_service: AIServiceProtocol =                    │
│     Depends(get_azure_openai_service),  ← Production │
│   analyzer: CompletenessAnalyzerProtocol =           │
│     Depends(get_completeness_analyzer)  ← Production │
│ )                                                     │
└──────────────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────┐
│ Testing (Mock Services)                              │
├──────────────────────────────────────────────────────┤
│ def test_chat_turn():                                │
│   app.dependency_overrides[                          │
│     get_azure_openai_service                         │
│   ] = lambda: MockAIService()    ← Fast, deterministic│
│                                                       │
│   app.dependency_overrides[                          │
│     get_completeness_analyzer                        │
│   ] = lambda: MockAnalyzer()     ← No real API calls │
│                                                       │
│   response = client.post("/v1/chat/turn", ...)       │
│   assert response.status_code == 200  ← FAST (100ms) │
└──────────────────────────────────────────────────────┘

Benefits:
✅ Fast tests: No real API calls (100x speedup)
✅ Reliable: No network dependencies
✅ Isolated: Each test gets clean mocks
✅ Type-safe: Protocols enforce interface compliance
```

---

## Configuration Management

### Before (Scattered Magic Numbers)

```python
# chat.py
MAX_AUDIO_BYTES = 6 * 1024 * 1024  # Why 6MB?
if similarity >= 85:               # Why 85%?
if completeness_score >= 0.8:      # Why 80%?

# azure_openai_service.py
timeout=90.0                        # Why 90s?
temperature=0.3                     # Why 0.3?
```

### After (Centralized Configuration)

```python
# config/business_rules.py
class ChatBusinessRules(BaseSettings):
    max_audio_bytes: int = Field(
        default=6 * 1024 * 1024,
        description="Max audio size (WhatsApp limit: 16MB, network reliability: 6MB)",
        env="CHAT_MAX_AUDIO_BYTES"
    )

    completeness_submission_threshold: float = Field(
        default=0.8,
        ge=0.0, le=1.0,
        description="Min completeness to auto-submit (vs manual review)",
        env="CHAT_COMPLETENESS_THRESHOLD"
    )

    duplicate_similarity_threshold: int = Field(
        default=85,
        ge=0, le=100,
        description="Fuzzy match threshold for duplicate detection (rapidfuzz)",
        env="CHAT_DUPLICATE_THRESHOLD"
    )

    ai_conversation_timeout_seconds: float = Field(
        default=90.0,
        description="AI conversation timeout (Prod: 90s, Dev: 30s)",
        env="AI_CONVERSATION_TIMEOUT"
    )

    ai_temperature: float = Field(
        default=0.3,
        ge=0.0, le=2.0,
        description="AI temperature (lower = more deterministic)",
        env="AI_TEMPERATURE"
    )

# Usage
business_rules = ChatBusinessRules()
MAX_AUDIO_BYTES = business_rules.max_audio_bytes

# A/B testing via environment variables
# export CHAT_COMPLETENESS_THRESHOLD=0.7  # Test 70% threshold
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /  \       10% E2E (Full chat flows)
       /────\      - Selenium/Playwright
      / Intg \     20% Integration (Service + DB)
     /────────\    - TestClient + real DB
    /   Unit   \   70% Unit Tests (Functions)
   /────────────\  - pytest + mocks
```

### Coverage Targets

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| Chat router | 20% | 80% | +60% |
| Azure OpenAI service | 30% | 90% | +60% |
| Completeness analyzer | 40% | 90% | +50% |
| Business logic functions | 0% | 95% | +95% |
| **Overall Backend** | **35%** | **85%** | **+50%** |

### Example Unit Test

```python
def test_can_submit_with_minimum_fields():
    """Should allow submission with location + issue."""
    service = ChatValidationService()

    extracted_data = {
        "location": "Raipur Ward 12",
        "issue_description": "बिजली नहीं आ रही है 3 दिन से"
    }

    assert service.can_submit_now(extracted_data) is True

def test_reject_placeholder_location():
    """Should reject 'unknown' as location."""
    service = ChatValidationService()

    extracted_data = {
        "location": "unknown",  # Placeholder
        "issue_description": "बिजली नहीं आ रही है"
    }

    assert service.can_submit_now(extracted_data) is False
```

---

## Migration Checklist

### Week 1-2: Foundation
- [ ] Define service protocols
- [ ] Extract `ChatValidationService` with `can_submit_now()`, `is_valid_field_value()`
- [ ] Extract `ChatCompletionService` with completion logic
- [ ] Add dependency injection to router
- [ ] Centralize configuration in `business_rules.py`
- [ ] Eliminate error handling duplication
- [ ] Write unit tests for extracted services (target: 90% coverage)

### Week 3-4: Complexity Reduction
- [ ] Define `ChatTurnCommand` interface
- [ ] Implement 6 commands: Validate, Transcribe, LoadState, Analyze, GenerateAI, Save
- [ ] Implement `ChatTurnProcessor` orchestrator
- [ ] Implement `ConversationStateRepository`
- [ ] Create Jinja2 template directory (`prompts/templates/`)
- [ ] Externalize system prompts to templates
- [ ] Implement `PromptManager` service
- [ ] Write integration tests for command pipeline

### Week 5-6: API Evolution
- [ ] Design V2 response models (`ChatTurnResponseV2`, `ConversationProgress`, etc.)
- [ ] Create `/v2/chat` router (parallel to `/v1/chat`)
- [ ] Add deprecation warnings to V1 endpoints (`deprecated=True`)
- [ ] Design hybrid schema (relational columns for location, issue_type + JSONB for contextual)
- [ ] Create migration script to populate relational columns from JSONB
- [ ] Implement structured error codes (`BolooServiceError` hierarchy)
- [ ] Add localized error messages

### Week 7-8: Optimization & Documentation
- [ ] Implement feature flags system (`FeatureFlags` config)
- [ ] Add monitoring thresholds (`MonitoringConfig`)
- [ ] Implement rate limiting middleware (`slowapi`)
- [ ] Add response streaming for AI responses (`/turn/stream`)
- [ ] Add caching for common AI responses (Redis)
- [ ] Performance testing (load test chat endpoints with Locust)
- [ ] Create architecture diagrams (C4 model)
- [ ] Write ADRs for major decisions
- [ ] Update API documentation (OpenAPI/Swagger)

---

## Success Metrics

### Code Quality
- ✅ Cyclomatic complexity <10 for all functions
- ✅ Router size <500 lines
- ✅ No code duplication (DRY violations)
- ✅ 85%+ test coverage
- ✅ Zero critical security issues (OWASP scan)

### Performance
- ✅ P95 latency <3s for `/chat/turn` (text)
- ✅ P95 latency <5s for `/chat/turn` (audio)
- ✅ 30%+ cache hit rate
- ✅ Zero memory leaks (profiler clean)

### Developer Experience
- ✅ Onboarding time: 3 hours → 1 hour
- ✅ Bug fix time: 2 days → 1 day
- ✅ Feature development time: 1 week → 3 days
- ✅ Test suite runs in <5 minutes

### Business Impact
- ✅ 50% reduction in production bugs
- ✅ A/B testing capability (prompts, thresholds)
- ✅ 2x faster feature development
- ✅ Foundation for advanced features (RAG, neural training)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Regression bugs during refactor | High | Medium | Comprehensive test coverage before refactoring |
| Performance degradation | Medium | Low | Benchmark before/after, load testing |
| Breaking changes for frontend | High | Low | Maintain V1 API for 12 months, deprecation policy |
| Team learning curve | Medium | Medium | Pair programming, code reviews, documentation |
| Timeline slip | Medium | High | Incremental delivery, weekly checkpoints |

---

## Team Alignment

### Stakeholder Approval Required
- [ ] Backend Team Lead (architecture decisions)
- [ ] Product Manager (V2 API design, deprecation timeline)
- [ ] Frontend Team (API changes coordination)
- [ ] DevOps (deployment strategy, monitoring)

### Communication Plan
- Week 1: Kickoff meeting + architecture walkthrough
- Weekly: Progress updates + blockers discussion
- Week 4: Mid-point review + course correction
- Week 8: Final review + production deployment plan

---

**Document Owner**: System Architecture Designer
**Last Updated**: 2025-11-15
**Status**: 🟡 Pending Approval
**Next Review**: 2025-11-20
