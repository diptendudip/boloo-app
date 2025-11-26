# Performance Test Suite

This directory contains comprehensive performance benchmarks for the Boloo Chat System.

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-benchmark datasketch tracemalloc

# Run all performance tests
pytest tests/performance -v -s --tb=short

# Run specific test suite
pytest tests/performance/test_database_performance.py -v -s
pytest tests/performance/test_fuzzy_matching_performance.py -v -s

# Generate HTML report
pytest tests/performance --html=performance_report.html --self-contained-html
```

## Test Suites

### 1. Database Performance (`test_database_performance.py`)

Tests database query performance and scalability:

- **Conversation history query time** - Measures N+1 query impact
- **Transcript concatenation time** - Measures string operations
- **Duplicate query count** - Detects N+1 patterns
- **Update batching performance** - Compares sequential vs batched writes
- **Missing index detection** - Identifies slow queries

**Expected Results (Before Optimization):**
- 50 turns: ~1000ms query time
- N+1 queries detected (50+ queries for 50 turns)

**Expected Results (After Optimization):**
- 50 turns: < 50ms query time
- 2 queries total (1 conversation + 1 batch of turns)

### 2. Fuzzy Matching Performance (`test_fuzzy_matching_performance.py`)

Tests duplicate question detection algorithms:

- **Duplicate detection time scaling** - Verifies O(n) vs O(n²) complexity
- **Fuzzy ratio performance** - Measures rapidfuzz speed
- **Worst case performance** - Tests many similar questions
- **Early termination optimization** - Verifies short-circuit logic
- **Hash-based duplicate detection** - Compares O(1) vs O(n) approaches
- **LSH optimization** - Tests Locality-Sensitive Hashing (O(log n))

**Expected Results (Before Optimization):**
- 50 questions: 50-250ms (O(n) fuzzy matching)
- 100 questions: 100-500ms (quadratic growth risk)

**Expected Results (After LSH Optimization):**
- All sizes: < 5ms (O(log n) LSH)
- 95% improvement

### 3. Memory Usage (`test_database_performance.py::TestMemoryUsage`)

Tests memory consumption and growth:

- **Conversation memory footprint** - Measures object sizes
- **History list memory growth** - Tests list overhead

**Expected Results (Before Optimization):**
- 100 turns: ~500KB memory
- Linear growth with conversation length

**Expected Results (After Optimization):**
- 100 turns: < 100KB memory (80% reduction)
- Bounded memory usage

## Running Performance Benchmarks

### Baseline Measurement (Before Optimization)

```bash
# Generate baseline profile
python -m cProfile -o baseline.prof -m pytest tests/performance

# View baseline stats
python -m pstats baseline.prof
```

### After Optimization

```bash
# Generate optimized profile
python -m cProfile -o optimized.prof -m pytest tests/performance

# Compare profiles
python -c "
import pstats
baseline = pstats.Stats('baseline.prof')
optimized = pstats.Stats('optimized.prof')
baseline.strip_dirs().sort_stats('cumulative').print_stats(20)
optimized.strip_dirs().sort_stats('cumulative').print_stats(20)
"
```

### Continuous Benchmarking

```bash
# Save benchmark results
pytest tests/performance --benchmark-only --benchmark-autosave

# Compare against previous runs
pytest tests/performance --benchmark-compare
```

## Performance Targets

| Metric | Current | Target | Test |
|--------|---------|--------|------|
| Query time (50 turns) | 1000ms | < 50ms | `test_conversation_history_query_time` |
| Duplicate detection (50 q's) | 50-250ms | < 5ms | `test_duplicate_detection_time_scaling` |
| Transcript concatenation | 100ms | < 10ms | `test_transcript_concatenation_time` |
| Memory per 100 turns | 500KB | < 100KB | `test_conversation_memory_footprint` |
| DB query count (50 turns) | 51 | ≤ 2 | `test_duplicate_query_count` |

## Interpreting Results

### Green Flags ✅
- Linear scaling (O(n)) or better
- Query time < 100ms
- Memory usage < 100KB per 100 turns
- ≤ 2 database queries per operation

### Yellow Flags ⚠️
- Quadratic scaling (O(n²)) detected
- Query time 100-500ms
- Memory usage 100-300KB per 100 turns
- 3-10 database queries per operation

### Red Flags 🔴
- Exponential scaling detected
- Query time > 500ms
- Memory usage > 300KB per 100 turns
- > 10 database queries (N+1 pattern)

## Adding New Performance Tests

```python
import pytest
import time

@pytest.mark.performance
class TestMyFeaturePerformance:
    """Test performance of my feature"""

    def test_my_operation_time(self, create_test_conversation):
        """Measure operation time"""
        conversation = create_test_conversation(50)

        # Measure time
        start = time.perf_counter()
        result = my_expensive_operation(conversation)
        elapsed = time.perf_counter() - start

        print(f"Operation took {elapsed*1000:.2f}ms")

        # Assert performance target
        assert elapsed < 0.1, f"Too slow: {elapsed*1000:.2f}ms"
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on: [pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run performance tests
        run: |
          pytest tests/performance -v --tb=short
          pytest tests/performance --benchmark-only

      - name: Check for regressions
        run: |
          pytest tests/performance --benchmark-compare=baseline
```

## Troubleshooting

### Tests Failing?

1. **Check database state:**
   ```bash
   pytest tests/performance -v -s --pdb
   ```

2. **Enable detailed logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Profile individual tests:**
   ```bash
   python -m cProfile -o test.prof tests/performance/test_database_performance.py::TestDatabasePerformance::test_conversation_history_query_time
   ```

### Inconsistent Results?

- Run tests multiple times: `pytest tests/performance -v --count=5`
- Disable other applications to reduce noise
- Use dedicated test database (not shared)

## Related Documentation

- [Performance Bottleneck Analysis](/docs/PERFORMANCE_BOTTLENECK_ANALYSIS.md)
- [Optimization Implementation Guide](/docs/PERFORMANCE_OPTIMIZATION_GUIDE.md)
- [Executive Summary](/docs/PERFORMANCE_EXECUTIVE_SUMMARY.md)

## Contributing

When adding performance-critical features:

1. Write performance tests FIRST
2. Measure baseline performance
3. Implement optimization
4. Verify improvement with tests
5. Add to CI/CD pipeline
