#!/usr/bin/env python3
"""
Manual test script for ConversationService with Azure OpenAI integration

Run this script to test the real Azure OpenAI integration end-to-end.

Usage:
    python -m tests.manual_test_conversation
"""

import sys
import os
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.conversation_service import (
    ConversationService,
    ConversationState,
    ConversationSlots,
    IntentType
)
from app.services.azure_openai_service import (
    AzureOpenAIServiceError,
    get_azure_openai_service
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_azure_openai_health():
    """Test Azure OpenAI service health"""
    print_section("1. Testing Azure OpenAI Service Health")

    try:
        azure_service = get_azure_openai_service()
        health = azure_service.health_check()

        print(f"Status: {health['status']}")
        print(f"Endpoint: {health['endpoint']}")
        print(f"Deployment: {health['deployment']}")
        print(f"API Version: {health['api_version']}")
        print(f"Connection: {health['connection']}")

        if health['status'] == 'healthy':
            print("\n✅ Azure OpenAI service is healthy and ready!")
            return True
        else:
            print(f"\n❌ Azure OpenAI service is unhealthy: {health.get('error')}")
            return False

    except Exception as e:
        print(f"\n❌ Failed to check Azure OpenAI health: {e}")
        return False


def test_triage_classification():
    """Test intent classification with various transcripts"""
    print_section("2. Testing Intent Classification (Triage)")

    service = ConversationService()

    test_cases = [
        {
            "transcript": "हमारे गांव में 15 दिन से बिजली नहीं आई",
            "expected_intent": IntentType.GRIEVANCE,
            "description": "Power outage complaint (Hindi)"
        },
        {
            "transcript": "पानी की सप्लाई बंद है 2 हफ्ते से",
            "expected_intent": IntentType.GRIEVANCE,
            "description": "Water supply issue (Hindi)"
        },
        {
            "transcript": "मेरी नानी का देसी नुस्खा सबको बताना है",
            "expected_intent": IntentType.COMMUNITY,
            "description": "Community story - traditional remedy (Hindi)"
        },
        {
            "transcript": "मुझे कल डॉक्टर के पास जाना है, याद दिलाना",
            "expected_intent": IntentType.PERSONAL,
            "description": "Personal reminder (Hindi)"
        },
        {
            "transcript": "Road is completely broken near my village",
            "expected_intent": IntentType.GRIEVANCE,
            "description": "Road issue (English)"
        }
    ]

    success_count = 0
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input: '{test_case['transcript']}'")

        try:
            result = service.process_triage(test_case['transcript'])

            print(f"  Intent: {result.intent.value}")
            print(f"  Confidence: {result.confidence.value}")
            print(f"  Topic Hint: {result.topic_hint}")
            print(f"  Reasoning: {result.reasoning}")

            if result.intent == test_case['expected_intent']:
                print("  ✅ PASSED - Correct intent detected")
                success_count += 1
            else:
                print(f"  ❌ FAILED - Expected {test_case['expected_intent'].value}, got {result.intent.value}")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")

    print(f"\n{'='*80}")
    print(f"Triage Tests: {success_count}/{len(test_cases)} passed")
    print(f"{'='*80}")

    return success_count == len(test_cases)


def test_grievance_conversation():
    """Test a complete grievance reporting conversation"""
    print_section("3. Testing Grievance Conversation Flow")

    service = ConversationService()

    # Create conversation state
    state = ConversationState(
        conversation_id="test-grievance-001",
        user_id="test-user-123",
        intent=IntentType.GRIEVANCE,
        slots=ConversationSlots()
    )

    # Simulate conversation turns
    conversation = [
        "हमारे गांव नीलकंठपुर में पानी नहीं आ रहा",
        "2 हफ्ते से",
        "पूरे गांव को",
        "नहीं, किसी से संपर्क नहीं किया",
        "हाँ, ठीक है"
    ]

    print("Starting conversation simulation...\n")

    for i, user_message in enumerate(conversation, 1):
        print(f"\nTurn {i}:")
        print(f"  User: {user_message}")

        try:
            response, state = service.process_turn(state, user_message)
            print(f"  Agent: {response}")

            if state.is_complete:
                print(f"\n  ✅ Conversation completed!")
                print(f"  Formal Summary:")
                print(f"  {state.formal_summary}")
                break

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return False

    return True


def test_conversation_with_context():
    """Test conversation maintains context across turns"""
    print_section("4. Testing Conversation Context Tracking")

    service = ConversationService()

    state = ConversationState(
        conversation_id="test-context-001",
        user_id="test-user-456",
        intent=IntentType.GRIEVANCE,
        slots=ConversationSlots()
    )

    turns = [
        ("बिजली की समस्या है", "First mention"),
        ("रायपुर में", "Location provided"),
        ("3 दिन से", "Duration mentioned")
    ]

    print("Testing context preservation across turns...\n")

    for user_msg, description in turns:
        print(f"{description}: {user_msg}")

        try:
            response, state = service.process_turn(state, user_msg)
            print(f"  Agent: {response}")
            print(f"  Turns recorded: {len(state.turns)}")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return False

    print(f"\n✅ Context tracking working - {len(state.turns)} turns recorded")
    return True


def test_error_handling():
    """Test error handling and retry logic"""
    print_section("5. Testing Error Handling")

    service = ConversationService()

    # Test empty transcript
    print("Test: Empty transcript handling")
    try:
        service.process_triage("")
        print("  ❌ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  ✅ Correctly raised ValueError: {e}")

    # Test invalid state
    print("\nTest: Invalid conversation state handling")
    try:
        state = ConversationState(
            conversation_id="test-error-001",
            user_id="test-user-789",
            intent=IntentType.GRIEVANCE
        )
        response, state = service.process_turn(state, "   ")  # Whitespace only
        print("  ❌ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  ✅ Correctly raised ValueError: {e}")

    return True


def test_multi_language_support():
    """Test support for Hindi, English, and Hinglish"""
    print_section("6. Testing Multi-Language Support")

    service = ConversationService()

    test_cases = [
        ("हमारे गांव में पानी नहीं है", "Pure Hindi"),
        ("Water problem in my village", "Pure English"),
        ("हमारे village में water supply नहीं आ रहा", "Hinglish"),
        ("रोड बहुत खराब है near the school", "Code-mixed")
    ]

    for transcript, lang_type in test_cases:
        print(f"\n{lang_type}: '{transcript}'")

        try:
            result = service.process_triage(transcript)
            print(f"  Intent: {result.intent.value}")
            print(f"  Confidence: {result.confidence.value}")
            print(f"  ✅ Processed successfully")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return False

    return True


def main():
    """Run all manual tests"""
    print("\n" + "🚀" * 40)
    print("  CONVERSATION SERVICE - AZURE OPENAI INTEGRATION TEST")
    print("🚀" * 40)

    results = {}

    # Run tests
    results['health'] = test_azure_openai_health()

    if results['health']:
        results['triage'] = test_triage_classification()
        results['grievance'] = test_grievance_conversation()
        results['context'] = test_conversation_with_context()
        results['errors'] = test_error_handling()
        results['multilang'] = test_multi_language_support()
    else:
        print("\n⚠️  Skipping conversation tests due to unhealthy Azure OpenAI service")
        results['triage'] = False
        results['grievance'] = False
        results['context'] = False
        results['errors'] = False
        results['multilang'] = False

    # Print summary
    print_section("TEST SUMMARY")

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():20} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\n{'='*80}")
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed")
    print(f"{'='*80}\n")

    # Exit with proper code
    sys.exit(0 if passed_tests == total_tests else 1)


if __name__ == "__main__":
    main()
