"""
LGD Location Validator - Demo Script

Demonstrates the capabilities of the LGD validator including:
- Hierarchy validation
- Fuzzy matching
- Phonetic matching
- Spelling corrections
- Location enrichment
"""

import sys
sys.path.insert(0, '/Users/diptendu/boloo app/boloo-app/backend')

from app.services.lgd_location_validator import LGDLocationValidator


def demo_hierarchy_validation():
    """Demonstrate hierarchy validation."""
    print("\n" + "="*80)
    print("1. HIERARCHY VALIDATION")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    # Test case 1: Exact match (Hindi)
    print("\n📍 Test 1: Exact match (Hindi)")
    result = validator.validate_hierarchy(
        village="मादर",
        block="लोहंडीगुड़ा",
        district="बस्तर",
        state="छत्तीसगढ़"
    )
    print(f"Valid: {result['is_valid']}")
    print(f"Confidence: {result['confidence']}")
    print(f"LGD Codes: {result['lgd_codes']}")
    print(f"Issues: {result['issues']}")

    # Test case 2: English transliteration
    print("\n📍 Test 2: English transliteration")
    result = validator.validate_hierarchy(
        village="Madar",
        block="Lohandiguda",
        district="Bastar",
        state="Chhattisgarh"
    )
    print(f"Valid: {result['is_valid']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Match Details: {result['match_details']}")

    # Test case 3: Partial hierarchy
    print("\n📍 Test 3: Partial hierarchy (village + district only)")
    result = validator.validate_hierarchy(
        village="मादर",
        district="बस्तर"
    )
    print(f"Valid: {result['is_valid']}")
    print(f"Confidence: {result['confidence']}")


def demo_fuzzy_matching():
    """Demonstrate fuzzy matching capabilities."""
    print("\n" + "="*80)
    print("2. FUZZY MATCHING")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    # Test case 1: Exact match
    print("\n🔍 Test 1: Exact match")
    matches = validator.fuzzy_match_location(
        name="बस्तर",
        level="district"
    )
    if matches:
        print(f"Found {len(matches)} match(es)")
        for match in matches:
            print(f"  - {match['name']} ({match['name_en']}) - Confidence: {match['confidence']}")

    # Test case 2: Spelling variation
    print("\n🔍 Test 2: Spelling variation")
    matches = validator.fuzzy_match_location(
        name="बसतर",  # Missing diacritic
        level="district"
    )
    if matches:
        print(f"Found {len(matches)} match(es) for misspelling")
        for match in matches:
            print(f"  - {match['name']} - Confidence: {match['confidence']} - Edit Distance: {match['edit_distance']}")

    # Test case 3: English transliteration
    print("\n🔍 Test 3: English input")
    matches = validator.fuzzy_match_location(
        name="Bastar",
        level="district",
        limit=3
    )
    if matches:
        print(f"Found {len(matches)} match(es) for English input")
        for match in matches:
            print(f"  - {match['name']} ({match['name_en']}) - Type: {match['match_type']}")


def demo_phonetic_matching():
    """Demonstrate phonetic matching."""
    print("\n" + "="*80)
    print("3. PHONETIC MATCHING")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    # Test phonetic codes
    print("\n🎵 Phonetic code generation:")
    test_words = [
        ("बस्तर", "Bastar"),
        ("मादर", "Madar"),
        ("लोहंडीगुड़ा", "Lohandiguda")
    ]

    for hindi, english in test_words:
        code_hindi = validator._phonetic_code(hindi)
        code_english = validator._phonetic_code(english)
        print(f"  '{hindi}' -> {code_hindi}")
        print(f"  '{english}' -> {code_english}")
        match = validator._phonetic_match(hindi, english)
        print(f"  Match: {match}\n")


def demo_spelling_corrections():
    """Demonstrate spelling correction suggestions."""
    print("\n" + "="*80)
    print("4. SPELLING CORRECTIONS")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    # Test case 1: Hindi misspelling
    print("\n✏️  Test 1: Hindi misspelling")
    suggestions = validator.suggest_corrections(
        name="बसतर",  # Should be "बस्तर"
        level="district"
    )
    print(f"Input: 'बसतर'")
    print(f"Suggestions: {suggestions}")

    # Test case 2: English misspelling
    print("\n✏️  Test 2: English misspelling")
    suggestions = validator.suggest_corrections(
        name="Baster",  # Should be "Bastar"
        level="district"
    )
    print(f"Input: 'Baster'")
    print(f"Suggestions: {suggestions}")


def demo_location_enrichment():
    """Demonstrate location enrichment."""
    print("\n" + "="*80)
    print("5. LOCATION ENRICHMENT")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    # Test case: Basic location
    print("\n🌟 Enriching location with LGD data...")
    location = {
        "village": "मादर",
        "block": "लोहंडीगुड़ा",
        "district": "बस्तर",
        "state": "छत्तीसगढ़"
    }

    print(f"\nOriginal location:")
    for key, value in location.items():
        print(f"  {key}: {value}")

    enriched = validator.enrich_with_lgd_data(location)

    print(f"\nEnriched location:")
    print(f"  Validated by LGD: {enriched.get('validated_by_lgd')}")
    print(f"  LGD Confidence: {enriched.get('lgd_confidence')}")
    print(f"\n  LGD Codes:")
    for level in ['state', 'district', 'block', 'village']:
        code_key = f"{level}_lgd_code"
        if code_key in enriched:
            print(f"    {level}: {enriched[code_key]}")


def demo_edit_distance():
    """Demonstrate Levenshtein distance calculations."""
    print("\n" + "="*80)
    print("6. EDIT DISTANCE CALCULATIONS")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    test_pairs = [
        ("test", "test"),      # Identical
        ("test", "best"),      # 1 edit
        ("Bastar", "Baster"),  # 1 edit
        ("मादर", "मादुर"),      # 1 edit
        ("abc", "xyz"),        # 3 edits
    ]

    print("\n📏 Calculating edit distances:")
    for s1, s2 in test_pairs:
        distance = validator._levenshtein_distance(s1, s2)
        print(f"  '{s1}' -> '{s2}': {distance} edit(s)")


def demo_confidence_scoring():
    """Demonstrate confidence score calculations."""
    print("\n" + "="*80)
    print("7. CONFIDENCE SCORING")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    test_cases = [
        (1.0, 0),    # Perfect match
        (0.9, 1),    # Very close
        (0.8, 2),    # Good match
        (0.6, 3),    # Acceptable
        (0.4, 5),    # Poor match
    ]

    print("\n🎯 Confidence calculations:")
    print("  (Similarity Ratio, Edit Distance) -> Confidence")
    for ratio, distance in test_cases:
        confidence = validator._calculate_confidence(ratio, distance)
        level = (
            "Exact" if confidence == 1.0 else
            "High" if confidence >= 0.9 else
            "Medium" if confidence >= 0.7 else
            "Low" if confidence >= 0.6 else
            "Very Low"
        )
        print(f"  ({ratio:.2f}, {distance}) -> {confidence:.2f} ({level})")


def demo_edge_cases():
    """Demonstrate edge case handling."""
    print("\n" + "="*80)
    print("8. EDGE CASES")
    print("="*80)

    validator = LGDLocationValidator(db_session=None)

    # Test case 1: Empty input
    print("\n⚠️  Test 1: Empty village name")
    result = validator.validate_hierarchy(
        village="",
        district="बस्तर"
    )
    print(f"Valid: {result['is_valid']}")
    print(f"Issues: {result['issues']}")

    # Test case 2: Very long name
    print("\n⚠️  Test 2: Unreasonably long name")
    long_name = "अ" * 100
    result = validator.validate_hierarchy(
        village=long_name,
        district="बस्तर"
    )
    print(f"Valid: {result['is_valid']}")
    print(f"Confidence: {result['confidence']}")

    # Test case 3: Special characters
    print("\n⚠️  Test 3: Name with special characters")
    result = validator.validate_hierarchy(
        village="मादर-123",
        district="बस्तर"
    )
    print(f"Valid: {result['is_valid']}")


def main():
    """Run all demonstrations."""
    print("\n" + "="*80)
    print("LGD LOCATION VALIDATOR - DEMONSTRATION")
    print("="*80)
    print("\nThis demo showcases the LGD validator capabilities using mock data.")
    print("In production, it will connect to the actual LGD database.")

    try:
        demo_hierarchy_validation()
        demo_fuzzy_matching()
        demo_phonetic_matching()
        demo_spelling_corrections()
        demo_location_enrichment()
        demo_edit_distance()
        demo_confidence_scoring()
        demo_edge_cases()

        print("\n" + "="*80)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*80)
        print("\nFor more details, see:")
        print("  - Documentation: docs/LGD_VALIDATOR_USAGE.md")
        print("  - Tests: tests/test_lgd_location_validator.py")
        print("  - Source: app/services/lgd_location_validator.py")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
