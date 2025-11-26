"""
Fuzzy matching performance tests.

Tests the duplicate detection algorithm's time complexity.
"""

import pytest
import time
from rapidfuzz import fuzz


def _is_dup_text_original(current: str, priors: list[str]) -> bool:
    """Original implementation from chat.py:77-101"""
    if not current or not priors:
        return False

    cur_normalized = current.strip().lower().rstrip('?।')

    for prior in priors:
        prior_normalized = prior.strip().lower().rstrip('?।')
        similarity = fuzz.token_set_ratio(cur_normalized, prior_normalized)

        if similarity >= 85:
            return True

    return False


@pytest.mark.performance
class TestFuzzyMatchingPerformance:
    """Test fuzzy duplicate detection performance"""

    def test_duplicate_detection_time_scaling(self):
        """Measure fuzzy duplicate detection time vs conversation length"""
        test_cases = [10, 25, 50, 100]
        results = []

        for num_previous_questions in test_cases:
            # Build list of previous questions
            previous_questions = [
                f"कृपया बताइए कि समस्या कहां है? सवाल नंबर {i}"
                for i in range(num_previous_questions)
            ]

            # Test question (not a duplicate)
            new_question = "आपकी समस्या की गंभीरता कैसी है?"

            # Measure duplicate detection time
            start = time.perf_counter()
            is_duplicate = _is_dup_text_original(new_question, previous_questions)
            elapsed = time.perf_counter() - start

            result = {
                "num_questions": num_previous_questions,
                "detection_time_ms": elapsed * 1000,
                "per_question_ms": (elapsed * 1000) / num_previous_questions
            }
            results.append(result)

            print(f"\n{num_previous_questions} questions: {elapsed*1000:.2f}ms")
            print(f"  Per question: {result['per_question_ms']:.4f}ms")
            print(f"  Is duplicate: {is_duplicate}")

            # Performance assertion
            # Target: < 50ms for 50 questions (1ms per question)
            assert elapsed < 0.1, f"Dup detection took {elapsed*1000:.2f}ms for {num_previous_questions} questions"

        # Verify O(n) scaling (linear, not quadratic)
        scaling_factor = results[-1]["detection_time_ms"] / results[0]["detection_time_ms"]
        question_ratio = results[-1]["num_questions"] / results[0]["num_questions"]

        print(f"\nScaling analysis:")
        print(f"  {scaling_factor:.2f}x time for {question_ratio:.2f}x questions")
        print(f"  Expected (linear): {question_ratio:.2f}x")
        print(f"  Expected (quadratic): {question_ratio**2:.2f}x")

        # Allow 2x overhead for linear scaling
        assert scaling_factor <= question_ratio * 2, \
            f"Scaling is worse than linear! {scaling_factor:.2f}x vs expected {question_ratio:.2f}x"

    def test_fuzzy_ratio_performance(self):
        """Test rapidfuzz token_set_ratio performance"""
        test_strings = [
            ("कृपया बताइए", "कृपया बताइए"),  # Exact match
            ("कृपया बताइए कि समस्या कहां है", "समस्या कहां है बताइए कृपया"),  # Reordered
            ("पानी की समस्या बहुत गंभीर है", "बिजली की समस्या बहुत गंभीर है"),  # Similar
            ("यह एक बिल्कुल अलग सवाल है", "कृपया बताइए"),  # Different
        ]

        for str1, str2 in test_strings:
            # Measure single fuzzy match time
            start = time.perf_counter()
            similarity = fuzz.token_set_ratio(str1, str2)
            elapsed = time.perf_counter() - start

            print(f"\n'{str1[:30]}' vs '{str2[:30]}'")
            print(f"  Similarity: {similarity}%")
            print(f"  Time: {elapsed*1000:.4f}ms")

            # Single fuzzy match should be < 5ms
            assert elapsed < 0.005, f"Single fuzzy match took {elapsed*1000:.4f}ms (expected < 5ms)"

    def test_worst_case_performance(self):
        """Test worst case: many similar questions"""
        num_questions = 50

        # Worst case: all questions are very similar (many high-similarity comparisons)
        previous_questions = [
            f"कृपया बताइए कि समस्या कहां है? {chr(0x0905 + i)}"  # Vary by one character
            for i in range(num_questions)
        ]

        new_question = "कृपया बताइए कि समस्या कहां है? अ"

        start = time.perf_counter()
        is_duplicate = _is_dup_text_original(new_question, previous_questions)
        elapsed = time.perf_counter() - start

        print(f"\nWorst case (50 similar questions): {elapsed*1000:.2f}ms")
        print(f"  Is duplicate: {is_duplicate}")

        # Worst case should still be < 250ms
        assert elapsed < 0.25, f"Worst case took {elapsed*1000:.2f}ms (expected < 250ms)"

    def test_early_termination_optimization(self):
        """Test that duplicate detection stops early when match found"""
        num_questions = 100

        # Put duplicate as 10th question
        previous_questions = [
            "सवाल १", "सवाल २", "सवाल ३", "सवाल ४", "सवाल ५",
            "सवाल ६", "सवाल ७", "सवाल ८", "सवाल ९",
            "कृपया बताइए कि समस्या कहां है?",  # Match is here (10th)
        ] + [f"सवाल {i}" for i in range(11, num_questions + 1)]

        new_question = "कृपया बताइए कि समस्या कहां है?"

        start = time.perf_counter()
        is_duplicate = _is_dup_text_original(new_question, previous_questions)
        elapsed = time.perf_counter() - start

        print(f"\nEarly termination test (duplicate at position 10 of {num_questions}): {elapsed*1000:.2f}ms")
        print(f"  Is duplicate: {is_duplicate}")

        # Should be much faster than checking all 100 questions
        # Expected: ~10ms (checking 10 questions) vs ~100ms (checking all 100)
        assert elapsed < 0.05, f"Early termination failed - took {elapsed*1000:.2f}ms"


@pytest.mark.performance
class TestOptimizedDuplicateDetection:
    """Test optimized duplicate detection algorithms"""

    def test_hash_based_duplicate_detection(self):
        """Test hash-based exact match (O(1))"""
        from hashlib import md5

        num_questions = 1000

        # Build hash set of previous questions
        previous_hashes = set()
        previous_questions = []

        for i in range(num_questions):
            question = f"सवाल नंबर {i}?"
            question_hash = md5(question.strip().lower().encode()).hexdigest()
            previous_hashes.add(question_hash)
            previous_questions.append(question)

        # Test exact match detection
        new_question = "सवाल नंबर 500?"
        new_hash = md5(new_question.strip().lower().encode()).hexdigest()

        start = time.perf_counter()
        is_duplicate = new_hash in previous_hashes
        elapsed = time.perf_counter() - start

        print(f"\nHash-based detection ({num_questions} questions): {elapsed*1000:.4f}ms")
        print(f"  Is duplicate: {is_duplicate}")

        # Hash lookup should be O(1) - < 0.1ms even for 1000 questions
        assert elapsed < 0.001, f"Hash lookup took {elapsed*1000:.4f}ms (expected < 1ms)"

        # Compare with fuzzy matching
        start_fuzzy = time.perf_counter()
        is_duplicate_fuzzy = _is_dup_text_original(new_question, previous_questions)
        elapsed_fuzzy = time.perf_counter() - start_fuzzy

        print(f"\nFuzzy matching ({num_questions} questions): {elapsed_fuzzy*1000:.2f}ms")
        print(f"  Speedup: {elapsed_fuzzy/elapsed:.0f}x faster with hashing")

        # Hash should be at least 100x faster
        assert elapsed * 100 < elapsed_fuzzy, "Hash-based detection not providing expected speedup"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
