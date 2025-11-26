# Performance Optimization Implementation Guide

**Based on:** Performance Bottleneck Analysis (2025-11-15)
**Target:** 60-75% response time reduction
**Effort:** 1-2 weeks (3 phases)

---

## Quick Reference: Priority Matrix

| Priority | Bottleneck | Fix Effort | Expected Gain | Files to Modify |
|----------|------------|------------|---------------|-----------------|
| 🔴 P0 | Cache full transcript | LOW (2-4 hours) | 90% | `models/conversation.py`, `routers/chat.py` |
| 🔴 P0 | Limit conversation history | MEDIUM (4-6 hours) | 70% | `routers/chat.py`, `services/ai_coach_conversation_service.py` |
| 🔴 P0 | Batch DB updates | LOW (2-3 hours) | 60% | `routers/chat.py` |
| 🟠 P1 | Parallelize AI calls | HIGH (1-2 days) | 50% | `routers/chat.py`, `services/azure_openai_service.py` |
| 🟠 P1 | Cache RAG results | MEDIUM (4-6 hours) | 90% | `services/rag/rag_service.py` |
| 🟠 P1 | LSH duplicate detection | MEDIUM (6-8 hours) | 95% | `routers/chat.py`, `utils/question_tracker.py` |

---

## Phase 1: Quick Wins (1-2 days)

### 1. Cache Full Transcript (P0 - 2-4 hours)

**Problem:** Transcript concatenated 3× per submission (lines 1023, 1116, 1184)

**Solution:** Add cached field to `Conversation` model

**Files to modify:**
- `/app/models/conversation.py`
- `/app/routers/chat.py`
- Alembic migration

**Implementation:**

#### Step 1.1: Update Conversation Model

```python
# app/models/conversation.py

class Conversation(Base):
    __tablename__ = "conversations"

    # ... existing fields ...

    # NEW: Cached transcript field
    cached_transcript = Column(Text, nullable=True)
    transcript_cache_updated_at = Column(DateTime, nullable=True)

    def update_transcript_cache(self, db_session):
        """Update cached transcript after new turn"""
        if self.turns:
            self.cached_transcript = " ".join([
                turn.transcript_text for turn in self.turns
            ])
            self.transcript_cache_updated_at = datetime.utcnow()
            db_session.commit()

    def get_full_transcript(self, db_session):
        """Get cached transcript or rebuild if stale"""
        # Check if cache is valid
        if (self.cached_transcript and
            self.transcript_cache_updated_at and
            self.turns):

            latest_turn_time = max(turn.created_at for turn in self.turns)
            if self.transcript_cache_updated_at >= latest_turn_time:
                return self.cached_transcript

        # Rebuild cache
        self.update_transcript_cache(db_session)
        return self.cached_transcript
```

#### Step 1.2: Create Migration

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
alembic revision -m "add_cached_transcript_to_conversation"
```

```python
# alembic/versions/xxx_add_cached_transcript_to_conversation.py

def upgrade():
    op.add_column('conversations',
        sa.Column('cached_transcript', sa.Text(), nullable=True)
    )
    op.add_column('conversations',
        sa.Column('transcript_cache_updated_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_column('conversations', 'transcript_cache_updated_at')
    op.drop_column('conversations', 'cached_transcript')
```

#### Step 1.3: Update Chat Router

```python
# app/routers/chat.py

# BEFORE (lines 1023, 1116, 1184):
full_transcript = " ".join([turn.transcript_text for turn in conversation.turns])

# AFTER:
full_transcript = conversation.get_full_transcript(db)
```

#### Step 1.4: Update Cache After Each Turn

```python
# app/routers/chat.py - in process_chat_turn after adding turn

# After line 890 (after turn is added):
turn = conversation_service.add_turn(...)

# Add cache update:
conversation.update_transcript_cache(db)
```

**Expected gain:** 90% reduction in transcript build time (from 3× to 0× on repeat calls)

---

### 2. Limit Conversation History (P0 - 4-6 hours)

**Problem:** Loads ALL conversation turns without pagination (line 557)

**Solution:** Load only recent N turns for AI context

**Files to modify:**
- `/app/services/ai_coach_conversation_service.py`
- `/app/routers/chat.py`

**Implementation:**

#### Step 2.1: Update Service Method

```python
# app/services/ai_coach_conversation_service.py

def get_conversation_history_for_ai(
    self,
    conversation_id: UUID,
    max_turns: int = 10  # NEW: Limit to recent 10 turns
) -> List[Dict[str, str]]:
    """
    Get recent conversation history for AI context.

    Args:
        conversation_id: Conversation UUID
        max_turns: Maximum number of recent turns to return (default: 10)

    Returns:
        List of {"user": transcript, "ai": response} dicts
    """
    # Get recent turns only (DESC order, then reverse)
    turns = self.db.query(ConversationTurn)\
        .filter(ConversationTurn.conversation_id == conversation_id)\
        .order_by(ConversationTurn.turn_number.desc())\
        .limit(max_turns)\
        .all()

    # Reverse to chronological order
    turns = list(reversed(turns))

    # Build history
    history = []
    for turn in turns:
        history.append({
            "user": turn.transcript_text,
            "ai": turn.ai_response or ""
        })

    return history
```

#### Step 2.2: Update Router Call

```python
# app/routers/chat.py - line 557

# BEFORE:
history = conversation_service.get_conversation_history_for_ai(conv_uuid)

# AFTER:
history = conversation_service.get_conversation_history_for_ai(
    conv_uuid,
    max_turns=10  # Only load recent 10 turns for AI context
)
```

**Expected gain:** 70% reduction in query time for 50+ turn conversations

---

### 3. Batch Database Updates (P0 - 2-3 hours)

**Problem:** Multiple sequential DB updates per turn (lines 667-673, 890)

**Solution:** Batch all updates in single transaction

**Files to modify:**
- `/app/routers/chat.py`

**Implementation:**

```python
# app/routers/chat.py - process_chat_turn function

# BEFORE (lines 667-673, 890):
conversation_service.update_completeness(...)  # DB write #1
turn = conversation_service.add_turn(...)      # DB write #2
conversation.update_transcript_cache(db)       # DB write #3

# AFTER (use single transaction):
from sqlalchemy import begin

with db.begin():
    # Update conversation completeness
    conversation.completeness_score = completeness_result["completeness_score"]
    conversation.collected_fields = completeness_result["collected_fields"]
    conversation.missing_fields = completeness_result["missing_fields"]
    conversation.extracted_data = completeness_result["extracted_data"]

    # Add turn
    new_turn = ConversationTurn(
        conversation_id=conv_uuid,
        turn_number=conversation.turn_count + 1,
        transcript_text=user_message,
        audio_url=None,
        language_detected=language_detected,
        ai_response=ai_response_hi,
        ai_question_asked=ai_response_hi,
        fields_extracted=completeness_result.get("entities", {})
    )
    db.add(new_turn)

    # Update turn count
    conversation.turn_count += 1

    # Update cached transcript
    if conversation.cached_transcript:
        conversation.cached_transcript += f" {user_message}"
        conversation.transcript_cache_updated_at = datetime.utcnow()

    # Single commit for all changes
    db.commit()

turn = new_turn  # For compatibility with rest of code
```

**Expected gain:** 60% reduction in DB write time

---

## Phase 2: Medium Effort (3-5 days)

### 4. Parallelize AI Calls (P1 - 1-2 days)

**Problem:** Sequential Azure OpenAI calls (3-8 seconds total)

**Solution:** Run completeness analysis and response generation in parallel

**Files to modify:**
- `/app/routers/chat.py`
- `/app/services/azure_openai_service.py`
- `/app/services/completeness_analyzer.py`

**Implementation:**

#### Step 4.1: Make Services Async

```python
# app/services/azure_openai_service.py

async def generate_conversation_response_async(
    self,
    user_message: str,
    conversation_history: List[Dict[str, str]],
    missing_fields: List[Dict[str, Any]],
    collected_data: Dict[str, Any],
    is_complete: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """Async version of generate_conversation_response"""
    # Same implementation but use async client
    response = await self.async_client.chat.completions.create(...)
    return result
```

```python
# app/services/completeness_analyzer.py

async def analyze_completeness_async(
    self,
    transcript: str,
    conversation_history: List[Dict[str, str]],
    already_collected_fields: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """Async version of analyze_completeness"""
    # Same implementation but async
    ...
```

#### Step 4.2: Update Router to Use Parallel Execution

```python
# app/routers/chat.py

import asyncio

@router.post("/turn", response_model=ChatTurnResponse)
async def process_chat_turn(...):
    # ... existing code ...

    # BEFORE (sequential):
    # completeness_result = completeness_analyzer.analyze_completeness(...)
    # ai_result = ai_service.generate_conversation_response(...)

    # AFTER (parallel):
    completeness_task = asyncio.create_task(
        completeness_analyzer.analyze_completeness_async(
            transcript=user_message,
            conversation_history=history,
            already_collected_fields=accumulated_data,
            question_tracker=question_tracker
        )
    )

    ai_response_task = asyncio.create_task(
        ai_service.generate_conversation_response_async(
            user_message=user_message,
            conversation_history=history,
            missing_fields=actually_missing_fields,
            collected_data=extracted,
            is_complete=False
        )
    )

    # Wait for both to complete (runs in parallel)
    completeness_result, ai_result = await asyncio.gather(
        completeness_task,
        ai_response_task
    )

    # Rest of code remains the same
    ...
```

**Expected gain:** 40-60% reduction in total response time (max(3s, 5s) = 5s instead of 3s+5s = 8s)

---

### 5. Cache RAG Results (P1 - 4-6 hours)

**Problem:** RAG search on every turn (10-100ms + grows with DB size)

**Solution:** Cache similar cases per conversation

**Files to modify:**
- `/app/services/rag/rag_service.py`

**Implementation:**

```python
# app/services/rag/rag_service.py

from hashlib import md5
import time
from typing import Dict, Tuple

class RAGCache:
    """In-memory cache for RAG search results"""

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize RAG cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default: 5 minutes)
        """
        self._cache: Dict[str, Tuple[str, float]] = {}
        self.ttl = ttl_seconds

    def _get_hash(self, problem_description: str) -> str:
        """Generate cache key from problem description"""
        normalized = problem_description.strip().lower()
        return md5(normalized.encode()).hexdigest()

    def get(self, problem_description: str) -> Optional[str]:
        """Get cached RAG context if available and not expired"""
        cache_key = self._get_hash(problem_description)

        if cache_key in self._cache:
            context, timestamp = self._cache[cache_key]

            # Check if expired
            if time.time() - timestamp < self.ttl:
                return context
            else:
                # Remove expired entry
                del self._cache[cache_key]

        return None

    def set(self, problem_description: str, context: str):
        """Store RAG context in cache"""
        cache_key = self._get_hash(problem_description)
        self._cache[cache_key] = (context, time.time())

    def clear_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self._cache[key]


class RAGService:
    def __init__(self, top_k: int = 3, similarity_threshold: float = 0.5):
        # ... existing init ...
        self.cache = RAGCache(ttl_seconds=300)  # 5 minute cache

    def build_rag_prompt_context(
        self,
        problem_description: str,
        language: str = "hi"
    ) -> str:
        """Build context with caching"""

        # Check cache first
        cached_context = self.cache.get(problem_description)
        if cached_context:
            logger.info("[RAG] Using cached context")
            return cached_context

        # Cache miss - perform search
        similar_cases = self.get_relevant_context(problem_description)

        if not similar_cases:
            return ""

        # Build context (existing logic)
        context = self._build_context_string(similar_cases, language)

        # Store in cache
        self.cache.set(problem_description, context)

        return context
```

**Expected gain:** 90% reduction in RAG search time for repeat queries

---

### 6. LSH Duplicate Detection (P1 - 6-8 hours)

**Problem:** O(n²) fuzzy matching (50-250ms for 50 turns)

**Solution:** Use Locality-Sensitive Hashing for O(log n) detection

**Files to modify:**
- `/app/routers/chat.py`
- `/app/utils/question_tracker.py` (new file)

**Implementation:**

#### Step 6.1: Install Dependencies

```bash
pip install datasketch
```

#### Step 6.2: Create LSH Question Tracker

```python
# app/utils/lsh_question_tracker.py

from datasketch import MinHash, MinHashLSH
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LSHQuestionTracker:
    """
    Fast duplicate question detection using Locality-Sensitive Hashing.

    Reduces O(n) fuzzy matching to O(log n) approximate matching.
    """

    def __init__(self, threshold: float = 0.85, num_perm: int = 128):
        """
        Initialize LSH tracker.

        Args:
            threshold: Similarity threshold (0.0-1.0)
            num_perm: Number of permutations (higher = more accurate)
        """
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.questions: Dict[int, str] = {}  # {question_id: question_text}
        self.next_id = 0

    def _create_minhash(self, text: str) -> MinHash:
        """Create MinHash signature from text"""
        minhash = MinHash(num_perm=self.num_perm)

        # Normalize text
        normalized = text.strip().lower().rstrip('?।')
        tokens = normalized.split()

        for token in tokens:
            minhash.update(token.encode('utf8'))

        return minhash

    def add_question(self, question_text: str, turn_number: int):
        """
        Add question to index.

        Args:
            question_text: Question text
            turn_number: Turn number when question was asked

        Time complexity: O(log n)
        """
        minhash = self._create_minhash(question_text)
        question_id = self.next_id

        self.lsh.insert(question_id, minhash)
        self.questions[question_id] = question_text

        logger.debug(f"[LSH] Added question {question_id}: '{question_text[:50]}'")

        self.next_id += 1

    def is_duplicate(self, question_text: str) -> bool:
        """
        Check if question is duplicate.

        Args:
            question_text: Question to check

        Returns:
            True if similar question exists

        Time complexity: O(log n) - much faster than O(n) fuzzy matching
        """
        minhash = self._create_minhash(question_text)
        similar_ids = self.lsh.query(minhash)

        if similar_ids:
            # Log which question it matched
            for similar_id in similar_ids:
                similar_question = self.questions.get(similar_id, "Unknown")
                logger.info(
                    f"[LSH] Duplicate detected: '{question_text[:50]}' "
                    f"matches '{similar_question[:50]}'"
                )
            return True

        return False

    def get_all_asked_fields(self) -> list:
        """Get list of all asked questions (for compatibility)"""
        return list(self.questions.values())
```

#### Step 6.3: Update Chat Router

```python
# app/routers/chat.py

from app.utils.lsh_question_tracker import LSHQuestionTracker

@router.post("/turn", response_model=ChatTurnResponse)
async def process_chat_turn(...):
    # ... existing code ...

    # BEFORE (lines 813-818 - O(n²)):
    # if conversation.turns:
    #     previously_asked = []
    #     for turn in conversation.turns:
    #         if turn.ai_question_asked:
    #             previously_asked.append(turn.ai_question_asked)
    #     if _is_dup_text(ai_response_hi, previously_asked):
    #         ...

    # AFTER (O(log n)):
    # Initialize LSH tracker from conversation history
    lsh_tracker = LSHQuestionTracker(threshold=0.85)
    if conversation.turns:
        for turn in conversation.turns:
            if turn.ai_question_asked:
                lsh_tracker.add_question(turn.ai_question_asked, turn.turn_number)

    # Fast duplicate check
    if lsh_tracker.is_duplicate(ai_response_hi):
        logger.warning(f"[Chat] 🚫 DUPLICATE QUESTION DETECTED (LSH)!")
        # ... existing duplicate handling logic ...
```

**Expected gain:** 95% reduction in duplicate detection time for 50+ turns

---

## Phase 3: Long-term Improvements (1-2 weeks)

### 7. Add Database Indexes

**Files to modify:**
- Alembic migration

**Implementation:**

```python
# alembic/versions/xxx_add_performance_indexes.py

def upgrade():
    # Index on conversation.user_id (if not already indexed by FK)
    op.create_index(
        'idx_conversations_user_id',
        'conversations',
        ['user_id']
    )

    # Index on conversation.created_at (for recent conversations query)
    op.create_index(
        'idx_conversations_created_at',
        'conversations',
        ['created_at']
    )

    # Composite index on turns (conversation_id, turn_number) for pagination
    op.create_index(
        'idx_conversation_turns_conv_turn',
        'conversation_turns',
        ['conversation_id', 'turn_number']
    )

    # Index on turns.created_at
    op.create_index(
        'idx_conversation_turns_created_at',
        'conversation_turns',
        ['created_at']
    )

def downgrade():
    op.drop_index('idx_conversation_turns_created_at', 'conversation_turns')
    op.drop_index('idx_conversation_turns_conv_turn', 'conversation_turns')
    op.drop_index('idx_conversations_created_at', 'conversations')
    op.drop_index('idx_conversations_user_id', 'conversations')
```

**Expected gain:** 30% improvement in query times

---

### 8. Add Circuit Breaker for Azure OpenAI

**Files to modify:**
- `/app/services/azure_openai_service.py`

**Implementation:**

```python
# app/services/azure_openai_service.py

import time
from typing import Optional

class CircuitBreaker:
    """Circuit breaker for Azure OpenAI failures"""

    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        """Record a failure"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"[CircuitBreaker] OPEN - {self.failures} failures detected"
            )

    def record_success(self):
        """Reset on success"""
        self.failures = 0
        self.state = "CLOSED"

    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state != "OPEN":
            return False

        # Check if timeout elapsed
        if time.time() - self.last_failure_time >= self.timeout:
            # Try half-open
            self.state = "HALF_OPEN"
            logger.info("[CircuitBreaker] Transitioning to HALF_OPEN")
            return False

        return True


class AzureOpenAIService:
    def __init__(self, ...):
        # ... existing init ...
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

    def generate_conversation_response(self, ...):
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            raise AzureOpenAIServiceError(
                "Service temporarily unavailable (circuit breaker open)"
            )

        try:
            # ... existing code ...
            result = json.loads(response_text)
            js_validate(result, CONVO_SCHEMA)

            # Record success
            self.circuit_breaker.record_success()

            return result

        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            raise
```

**Expected gain:** Better resilience, prevents cascading failures

---

## Testing & Validation

### Run Performance Tests

```bash
# Run all performance tests
pytest tests/performance -v -s --tb=short

# Run specific test suite
pytest tests/performance/test_database_performance.py -v -s
pytest tests/performance/test_fuzzy_matching_performance.py -v -s

# Run with profiling
pytest tests/performance -v -s --profile

# Generate performance report
pytest tests/performance --benchmark-only --benchmark-autosave
```

### Benchmarking Commands

```python
# Before optimization
python -m cProfile -o before.prof -m pytest tests/performance/test_database_performance.py

# After optimization
python -m cProfile -o after.prof -m pytest tests/performance/test_database_performance.py

# Compare profiles
python -m pstats before.prof after.prof
```

---

## Rollout Plan

### Week 1: Phase 1 (Quick Wins)
- **Day 1-2:** Implement cache, limit history, batch updates
- **Day 3:** Test and validate improvements
- **Day 4-5:** Deploy to staging, monitor metrics

### Week 2: Phase 2 (Medium Effort)
- **Day 1-2:** Implement parallel AI calls
- **Day 3:** Implement RAG caching and LSH
- **Day 4-5:** Test and validate all improvements

### Week 3: Phase 3 (Long-term)
- **Day 1:** Add database indexes
- **Day 2:** Implement circuit breaker
- **Day 3-5:** Final testing and production deployment

---

## Monitoring Checklist

After each phase, verify:

- [ ] Response time p50/p95/p99 metrics
- [ ] Database query counts
- [ ] Memory usage (RSS, peak)
- [ ] Azure OpenAI latency
- [ ] RAG search latency
- [ ] Error rate
- [ ] Cache hit rate

---

## Success Criteria

### Phase 1 Targets
- Chat turn response (10 turns): < 2.5s (from 3-5s)
- Chat turn response (50 turns): < 5s (from 8-12s)
- Database query time: < 50ms (from 200ms+)

### Phase 2 Targets
- Chat turn response (10 turns): < 1.5s
- Chat turn response (50 turns): < 3s
- Duplicate detection: < 5ms (from 50-250ms)

### Final Targets (All Phases)
- P50 response time: < 2s
- P95 response time: < 4s
- P99 response time: < 6s
- Memory per conversation: < 100KB
- Support 10× more concurrent users

---

**Document Version:** 1.0
**Last Updated:** 2025-11-15
**Next Review:** After Phase 1 completion
