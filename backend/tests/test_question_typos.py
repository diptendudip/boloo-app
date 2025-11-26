#!/usr/bin/env python3
"""
Test question detection with typo variants and opinion requests
Specifically tests Bug #8 fix with the user's exact message
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.hindi_response_detector import HindiResponseDetector

def test_question_detection():
    detector = HindiResponseDetector()

    # Test cases - including user's EXACT message that caused the loop
    test_cases = [
        # User's exact message with typo "चाइए"
        ("आपको क्या लगता है ऐसा समस्या का कैसा सुनवाई होनी चाइए?", "question", 0.9),

        # Typo variants of "चाहिए"
        ("सुनवाई होनी चाइए?", "question", 0.9),  # चाइए typo
        ("सुनवाई होनी चाहीए?", "question", 0.9),  # चाहीए typo
        ("सुनवाई होनी चाहिये?", "question", 0.9),  # चाहिये typo
        ("sunvaai honi chaiye?", "question", 0.9),  # Hinglish typo

        # Opinion requests
        ("आपको क्या लगता है?", "question", 0.9),
        ("आप बताइए", "question", 0.9),
        ("aapko kya lagta hai?", "question", 0.9),
        ("what do you think?", "question", 0.9),

        # Question words without "?"
        ("क्या यह ठीक है", "question", 0.9),
        ("कैसे होगा", "question", 0.9),

        # Still detect correct spelling
        ("सुनवाई होनी चाहिए?", "question", 0.9),

        # Non-questions should still work
        ("हाँ", "affirmative", 0.8),
        ("नहीं", "negative", 0.8),
        ("कर दीजिए", "proceed", 0.9),
    ]

    print("=" * 80)
    print("Testing Enhanced Question Detection (Bug #8 - Typo Variants)")
    print("=" * 80)
    print()

    all_passed = True

    for message, expected_type, expected_confidence in test_cases:
        result = detector.detect(message)

        passed = (
            result["type"] == expected_type and
            result["confidence"] >= expected_confidence
        )

        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"{status}: {message}")
        print(f"   Expected: {expected_type} (conf >= {expected_confidence})")
        print(f"   Got:      {result['type']} (conf {result['confidence']})")

        if not passed:
            all_passed = False
            print(f"   Message: {result['message']}")
            print(f"   Pattern: {result['matched_pattern']}")

        print()

    print("=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = test_question_detection()
    sys.exit(0 if success else 1)
