# Architecture Diagrams - Current vs. Proposed

**Date**: 2025-11-15
**Status**: Design Proposal

---

## Current Architecture (Problems Highlighted)

### Request Flow (Current)

```
┌─────────────────────────────────────────────────────────────────────┐
│ FastAPI Router (/v1/chat/turn)                                      │
│                                                                      │
│ 🔴 PROBLEM: 1,254 lines, complexity 35+                             │
│ 🔴 PROBLEM: Business logic in router layer                          │
│ 🔴 PROBLEM: No dependency injection                                 │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ process_chat_turn() [520 lines, 35+ branches]                 │  │
│  │                                                                │  │
│  │ 1. Validate input (if/else soup)                              │  │
│  │ 2. Transcribe audio (embedded logic)                          │  │
│  │ 3. Load conversation state (direct DB access)                 │  │
│  │ 4. can_submit_now() ← 🔴 BUSINESS LOGIC IN ROUTER!            │  │
│  │ 5. is_meaningful_issue_description() ← 🔴 VALIDATION IN ROUTER!│ │
│  │ 6. Call completeness analyzer                                 │  │
│  │ 7. Call AI service                                             │  │
│  │ 8. try/except with DUPLICATED fallback logic (70+ lines)      │  │
│  │ 9. Save to database                                            │  │
│  │ 10. Build response (16 fields!)                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         │                   │                    │                   │
│         ▼                   ▼                    ▼                   │
│  ┌──────────┐      ┌────────────┐       ┌────────────┐             │
│  │ Global   │      │ Global     │       │ Direct DB  │             │
│  │ Singleton│      │ Singleton  │       │ Access     │             │
│  │ 🔴 Cannot │      │ 🔴 Cannot   │       │ 🔴 Tight    │             │
│  │   Mock!  │      │    Mock!   │       │  Coupling  │             │
│  └──────────┘      └────────────┘       └────────────┘             │
│  Azure OpenAI   Completeness      Conversation DB                   │
│  Service        Analyzer          (SQLAlchemy)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow (Current - Confusing State Ownership)

```
┌─────────────────────────────────────────────────────────────────┐
│ Conversation State (Who owns truth?)                            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Router reads: accumulated_data = conversation.extracted_data │
│    ❓ Is this the source of truth?                              │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Analyzer merges: new_data + accumulated_data                 │
│    ❓ Or is completeness_result["extracted_data"] truth?        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Service updates: conversation.extracted_data = merged        │
│    ❓ Or is conversation object the truth?                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Router reads again: extracted_data = completeness_result[...] │
│    ❓ Which extracted_data is correct?                          │
└─────────────────────────────────────────────────────────────────┘

🔴 PROBLEM: No clear owner of conversation state
🔴 PROBLEM: State scattered across router, service, analyzer
🔴 PROBLEM: Risk of stale data or lost updates
```

---

## Proposed Architecture (After Refactoring)

### Request Flow (Proposed - Clean Separation)

```
┌─────────────────────────────────────────────────────────────────────┐
│ FastAPI Router (/v2/chat/turn)                                      │
│                                                                      │
│ ✅ IMPROVED: ~200 lines, complexity <10                             │
│ ✅ IMPROVED: Only routing logic, no business rules                  │
│ ✅ IMPROVED: Dependency injection (testable!)                       │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ process_chat_turn() [~100 lines, 5 branches]                  │  │
│  │                                                                │  │
│  │ 1. Create processing context                                  │  │
│  │ 2. Build command pipeline                                     │  │
│  │ 3. Execute pipeline                                            │  │
│  │ 4. Return response                                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         │                                                            │
│         ▼                                                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ ChatTurnProcessor (Orchestrator)                              │  │
│  │                                                                │  │
│  │  execute_pipeline([                                            │  │
│  │    ValidateInputCommand(),        ← 30 lines, cplx 5          │  │
│  │    TranscribeAudioCommand(),      ← 40 lines, cplx 4          │  │
│  │    LoadConversationStateCommand(),← 25 lines, cplx 3          │  │
│  │    AnalyzeCompletenessCommand(),  ← 35 lines, cplx 6          │  │
│  │    GenerateAIResponseCommand(),   ← 45 lines, cplx 8          │  │
│  │    SaveConversationTurnCommand()  ← 30 lines, cplx 4          │  │
│  │  ])                                                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         │                   │                    │                   │
│         ▼                   ▼                    ▼                   │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐        │
│  │ Injected     │  │ Injected       │  │ Repository       │        │
│  │ Dependency   │  │ Dependency     │  │ Pattern          │        │
│  │ ✅ Mockable  │  │ ✅ Mockable    │  │ ✅ Clear State   │        │
│  │ ✅ Testable  │  │ ✅ Testable    │  │   Ownership      │        │
│  └──────────────┘  └────────────────┘  └──────────────────┘        │
│  AIServiceProtocol  CompletenessAnalyzer ConversationState          │
│  (Interface)        Protocol (Interface) Repository                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Architecture (Proposed - Proper Separation)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Presentation Layer (Routing)                                        │
├─────────────────────────────────────────────────────────────────────┤
│ - chat_router.py (~200 lines)                                       │
│ - Response models (ChatTurnResponseV2)                              │
│ - Request validation (FastAPI forms)                                │
│ - HTTP concerns only                                                │
└─────────────────────────────────────────────────────────────────────┘
         │ Depends on (interfaces, not implementations)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Application Layer (Orchestration)                                   │
├─────────────────────────────────────────────────────────────────────┤
│ - ChatTurnProcessor (Command Pattern orchestrator)                  │
│ - Commands: ValidateInput, TranscribeAudio, AnalyzeCompleteness...  │
│ - Workflows: ConversationFlow, SubmissionFlow                       │
└─────────────────────────────────────────────────────────────────────┘
         │ Uses
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Domain Layer (Business Logic)                                       │
├─────────────────────────────────────────────────────────────────────┤
│ - ChatValidationService (can_submit_now, is_meaningful_issue)       │
│ - ChatCompletionService (is_conversation_complete)                  │
│ - FieldValidators (Strategy Pattern: LocationValidator, etc.)       │
│ - Business rules (ChatBusinessRules config)                         │
└─────────────────────────────────────────────────────────────────────┘
         │ Uses
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Infrastructure Layer (External Services)                            │
├─────────────────────────────────────────────────────────────────────┤
│ - AzureOpenAIService (implements AIServiceProtocol)                 │
│ - CompletenessAnalyzer (implements CompletenessAnalyzerProtocol)    │
│ - TranscriptionService                                               │
│ - ConversationStateRepository (database abstraction)                │
│ - PromptManager (Jinja2 template rendering)                         │
└─────────────────────────────────────────────────────────────────────┘
         │ Persists to
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Data Layer (Database)                                               │
├─────────────────────────────────────────────────────────────────────┤
│ - Conversation model (SQLAlchemy ORM)                               │
│ - Hybrid schema: location (relational) + contextual_data (JSONB)    │
│ - Repositories handle all database access                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow (Proposed - Clear State Ownership)

```
┌─────────────────────────────────────────────────────────────────┐
│ Conversation State (Repository Pattern - Clear Ownership)       │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ ConversationStateRepository                                      │
│ ✅ Single source of truth for state management                  │
├─────────────────────────────────────────────────────────────────┤
│ get_accumulated_data(conversation_id)                            │
│   → Read current state from database (JSONB)                    │
│   → Return: Dict[str, Any]                                      │
│                                                                  │
│ merge_and_save(conversation_id, new_data)                       │
│   → current = get_accumulated_data(conversation_id)             │
│   → merged = {**current, **new_data}  # New overwrites old      │
│   → Save merged state to database                               │
│   → Return merged state                                         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Usage in Commands                                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. LoadConversationStateCommand:                                 │
│    context.accumulated_data = state_repo.get_accumulated_data()  │
│                                                                  │
│ 2. AnalyzeCompletenessCommand:                                   │
│    result = analyzer.analyze_completeness(                       │
│       already_collected_fields=context.accumulated_data          │
│    )                                                             │
│    context.new_extracted_data = result["extracted_data"]         │
│                                                                  │
│ 3. SaveConversationTurnCommand:                                  │
│    final_data = state_repo.merge_and_save(                       │
│       conversation_id,                                           │
│       context.new_extracted_data                                 │
│    )                                                             │
└─────────────────────────────────────────────────────────────────┘

✅ IMPROVED: Database (via repository) is single source of truth
✅ IMPROVED: Explicit merge logic
✅ IMPROVED: Testable in isolation
✅ IMPROVED: Clear state ownership
```

---

## Component Interaction (Proposed)

### Command Pattern Pipeline

```
┌───────────────────────────────────────────────────────────────────┐
│ ChatTurnContext (Shared State)                                    │
├───────────────────────────────────────────────────────────────────┤
│ - conversation_id: UUID                                           │
│ - user_id: UUID                                                   │
│ - text_message: str                                               │
│ - audio: UploadFile                                               │
│ - user_message: str (set by TranscribeAudioCommand)               │
│ - accumulated_data: Dict (set by LoadConversationStateCommand)    │
│ - completeness_result: Dict (set by AnalyzeCompletenessCommand)   │
│ - ai_response_hi: str (set by GenerateAIResponseCommand)          │
│ - ai_response_en: str (set by GenerateAIResponseCommand)          │
│ - turn: ConversationTurn (set by SaveConversationTurnCommand)     │
└───────────────────────────────────────────────────────────────────┘
         │
         ▼ Passed to each command
┌───────────────────────────────────────────────────────────────────┐
│ Command 1: ValidateInputCommand                                   │
├───────────────────────────────────────────────────────────────────┤
│ execute(context):                                                 │
│   if not context.text_message and not context.audio:              │
│     raise HTTPException(400, "Either text or audio required")     │
│   # Validation logic (30 lines, complexity 5)                     │
└───────────────────────────────────────────────────────────────────┘
         │ Context updated
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ Command 2: TranscribeAudioCommand                                 │
├───────────────────────────────────────────────────────────────────┤
│ execute(context):                                                 │
│   if context.audio:                                               │
│     result = transcription_service.transcribe_audio(...)          │
│     context.user_message = result["transcript"]                   │
│   else:                                                           │
│     context.user_message = context.text_message                   │
│   # Transcription logic (40 lines, complexity 4)                  │
└───────────────────────────────────────────────────────────────────┘
         │ Context updated
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ Command 3: LoadConversationStateCommand                           │
├───────────────────────────────────────────────────────────────────┤
│ execute(context):                                                 │
│   state_repo = ConversationStateRepository(...)                   │
│   context.accumulated_data = state_repo.get_accumulated_data(     │
│     context.conversation_id                                       │
│   )                                                               │
│   # State loading (25 lines, complexity 3)                        │
└───────────────────────────────────────────────────────────────────┘
         │ Context updated
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ Command 4: AnalyzeCompletenessCommand                             │
├───────────────────────────────────────────────────────────────────┤
│ execute(context):                                                 │
│   result = completeness_analyzer.analyze_completeness(            │
│     transcript=context.user_message,                              │
│     already_collected_fields=context.accumulated_data             │
│   )                                                               │
│   context.completeness_result = result                            │
│   # Analysis orchestration (35 lines, complexity 6)               │
└───────────────────────────────────────────────────────────────────┘
         │ Context updated
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ Command 5: GenerateAIResponseCommand                              │
├───────────────────────────────────────────────────────────────────┤
│ execute(context):                                                 │
│   try:                                                            │
│     ai_result = ai_service.generate_conversation_response(...)    │
│     context.ai_response_hi = ai_result["response_hi"]             │
│     context.ai_response_en = ai_result["response_en"]             │
│   except AzureOpenAIServiceError:                                 │
│     # Fallback to template (single source of truth)               │
│     context.ai_response_hi, context.ai_response_en =              │
│       fallback_response_generator(...)                            │
│   # AI generation with fallback (45 lines, complexity 8)          │
└───────────────────────────────────────────────────────────────────┘
         │ Context updated
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ Command 6: SaveConversationTurnCommand                            │
├───────────────────────────────────────────────────────────────────┤
│ execute(context):                                                 │
│   turn = conversation_service.add_turn(...)                       │
│   context.turn = turn                                             │
│                                                                   │
│   state_repo = ConversationStateRepository(...)                   │
│   final_data = state_repo.merge_and_save(                         │
│     context.conversation_id,                                      │
│     context.completeness_result["extracted_data"]                 │
│   )                                                               │
│   # Persistence (30 lines, complexity 4)                          │
└───────────────────────────────────────────────────────────────────┘
         │ Context finalized
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ ChatTurnProcessor                                                  │
├───────────────────────────────────────────────────────────────────┤
│ _build_response(context):                                         │
│   return ChatTurnResponseV2(                                      │
│     conversation_id=context.conversation_id,                      │
│     turn_number=context.turn.turn_number,                         │
│     user_input=UserInputData(...),                                │
│     ai_response=AIResponseData(...),                              │
│     progress=ConversationProgress(...),                           │
│     ui_actions=UIActions(...)                                     │
│   )                                                               │
└───────────────────────────────────────────────────────────────────┘
```

### Testing Flow (Dependency Injection)

```
┌───────────────────────────────────────────────────────────────────┐
│ Production (Real Services)                                         │
├───────────────────────────────────────────────────────────────────┤
│ @router.post("/turn")                                             │
│ async def process_chat_turn(                                      │
│   ai_service: AIServiceProtocol =                                 │
│     Depends(get_azure_openai_service),    ← Real Azure API        │
│   analyzer: CompletenessAnalyzerProtocol =                        │
│     Depends(get_completeness_analyzer)    ← Real Azure API        │
│ )                                                                 │
└───────────────────────────────────────────────────────────────────┘
         │
         │ Override for testing
         ▼
┌───────────────────────────────────────────────────────────────────┐
│ Testing (Mock Services)                                            │
├───────────────────────────────────────────────────────────────────┤
│ class MockAIService:                                              │
│   def generate_conversation_response(self, **kwargs):             │
│     return {                                                      │
│       "response_hi": "मॉक रिस्पॉन्स",                              │
│       "response_en": "Mock response"                              │
│     }                                                             │
│                                                                   │
│ def test_chat_turn():                                             │
│   app.dependency_overrides[                                       │
│     get_azure_openai_service                                      │
│   ] = lambda: MockAIService()    ← Fast, deterministic            │
│                                                                   │
│   response = client.post("/v1/chat/turn", ...)                    │
│   assert response.status_code == 200  ← 100ms (no real API call)  │
│                                                                   │
│   app.dependency_overrides.clear()                                │
└───────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Hybrid Approach)

### Current (JSONB Only)

```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,

  -- ❌ Everything stored in JSONB (not searchable)
  extracted_data JSONB,

  -- Sample data:
  -- extracted_data: {
  --   "location": "Raipur Ward 12",
  --   "issue_description": "बिजली नहीं आ रही",
  --   "service_duration": "3 days",
  --   "affected_scope": "20-30 houses"
  -- }

  -- PROBLEMS:
  -- 🔴 Cannot query: WHERE extracted_data->>'location' = 'Raipur'
  --    (inefficient JSONB scan)
  -- 🔴 Cannot index location for fast lookups
  -- 🔴 Cannot aggregate by issue_type
  -- 🔴 No referential integrity
);
```

### Proposed (Hybrid: Relational + JSONB)

```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,

  -- ✅ Critical searchable fields (indexed, validated)
  location VARCHAR(500) INDEX,          -- Extract from JSONB
  issue_description TEXT,                -- Extract from JSONB
  issue_type VARCHAR(100) INDEX,         -- Taxonomy category
  completeness_score DECIMAL(3,2),       -- 0.00 to 1.00

  -- ✅ Contextual fields (dynamic, problem-type specific)
  contextual_data JSONB,
  -- e.g., {"service_duration": "3 days", "affected_count": "20-30"}

  -- ✅ Full extracted data (backward compatibility)
  extracted_data JSONB,

  created_at TIMESTAMP DEFAULT NOW()
);

-- ✅ Fast queries on critical fields
CREATE INDEX idx_conversations_location ON conversations (location);
CREATE INDEX idx_conversations_issue_type ON conversations (issue_type);
CREATE INDEX idx_conversations_completeness ON conversations (completeness_score);

-- ✅ GIN index for JSONB queries (contextual fields)
CREATE INDEX idx_conversations_contextual_gin
  ON conversations USING GIN (contextual_data);

-- Example queries (FAST with indexes):
SELECT * FROM conversations
WHERE location LIKE 'Raipur%'
  AND issue_type = 'water_supply'
  AND completeness_score >= 0.8;

SELECT issue_type, COUNT(*) as count
FROM conversations
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY issue_type
ORDER BY count DESC;
```

---

## Configuration Architecture

### Current (Scattered Magic Numbers)

```
chat.py:47:     MAX_AUDIO_BYTES = 6 * 1024 * 1024  ← ❓ Why 6MB?
chat.py:97:     if similarity >= 85                ← ❓ Why 85%?
chat.py:1109:   if score >= 0.8                    ← ❓ Why 80%?
azure_openai_service.py:96:  timeout=90.0          ← ❓ Why 90s?
azure_openai_service.py:166: temperature=0.3       ← ❓ Why 0.3?
completeness_analyzer.py:168: timeout=90.0         ← ❌ DUPLICATE!
```

### Proposed (Centralized Configuration)

```python
# config/business_rules.py
class ChatBusinessRules(BaseSettings):
    """
    Business rules for chat flow (tunable parameters).

    All thresholds, timeouts, and magic numbers centralized here.
    Can be overridden via environment variables for A/B testing.
    """

    # Audio upload limits
    max_audio_bytes: int = Field(
        default=6 * 1024 * 1024,  # 6MB
        description="Maximum audio file size. "
                    "Limit: WhatsApp (16MB), Network reliability (6MB).",
        env="CHAT_MAX_AUDIO_BYTES"
    )

    # Completeness thresholds
    completeness_submission_threshold: float = Field(
        default=0.8,  # 80%
        ge=0.0, le=1.0,
        description="Minimum completeness score to auto-submit "
                    "(vs manual moderator review).",
        env="CHAT_COMPLETENESS_THRESHOLD"
    )

    # Duplicate detection
    duplicate_similarity_threshold: int = Field(
        default=85,  # 85%
        ge=0, le=100,
        description="Fuzzy match threshold for duplicate question detection "
                    "(rapidfuzz token_set_ratio).",
        env="CHAT_DUPLICATE_THRESHOLD"
    )

    # AI service timeouts (environment-specific)
    ai_conversation_timeout_seconds: float = Field(
        default=90.0,
        description="Timeout for AI conversation generation. "
                    "Prod: 90s, Dev: 30s for faster tests.",
        env="AI_CONVERSATION_TIMEOUT"
    )

    # AI parameters (experimentation)
    ai_temperature: float = Field(
        default=0.3,
        ge=0.0, le=2.0,
        description="Temperature for AI responses. "
                    "Lower = more deterministic, Higher = more creative.",
        env="AI_TEMPERATURE"
    )

    class Config:
        env_prefix = "BOLOO_"
        case_sensitive = False


# A/B Testing Example
# Terminal 1 (Control group - 80% threshold):
export BOLOO_CHAT_COMPLETENESS_THRESHOLD=0.8
python -m uvicorn app.main:app

# Terminal 2 (Test group - 70% threshold):
export BOLOO_CHAT_COMPLETENESS_THRESHOLD=0.7
python -m uvicorn app.main:app --port 8001
```

---

## Summary: Before vs. After

| Aspect | Before (Current) | After (Proposed) | Improvement |
|--------|------------------|------------------|-------------|
| **Router Size** | 1,254 lines | ~200 lines | **84% reduction** |
| **Cyclomatic Complexity** | 35+ (Very High Risk) | <10 (Maintainable) | **71% reduction** |
| **Code Duplication** | 70 lines duplicated | 0 lines duplicated | **100% eliminated** |
| **Test Coverage** | 35% (Low) | 85% (High) | **143% increase** |
| **Business Logic Location** | Router (mixed with routing) | Domain services (separated) | **Proper layering** |
| **State Ownership** | Unclear (scattered) | Repository (single source) | **Clear ownership** |
| **Dependency Injection** | Global singletons (untestable) | DI with protocols (testable) | **100% mockable** |
| **Configuration** | Scattered magic numbers | Centralized config | **Discoverable, tunable** |
| **API Versioning** | None (risky deployments) | V1 + V2 (graceful migration) | **Backward compatible** |
| **Prompt Management** | Hard-coded in code | Jinja2 templates (versioned) | **A/B testable** |
| **Number of Files** | 3 large files | ~25 focused files | **Better separation** |
| **Estimated Bug Rate** | 2-3 bugs/week | <1 bug/week | **60% reduction** |
| **Feature Development Time** | 1 week | 3 days | **2.3x faster** |
| **Onboarding Time** | 3 hours | 1 hour | **67% faster** |

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Design Proposal
**Next Steps**: Stakeholder review + approval
