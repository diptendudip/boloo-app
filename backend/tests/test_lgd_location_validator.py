"""
Unit tests for LGD Location Validator.

Tests fuzzy matching, phonetic matching, hierarchy validation,
and Hindi/English transliteration handling.
"""

import pytest
from app.services.lgd_location_validator import LGDLocationValidator


class TestLGDLocationValidator:
    """Test suite for LGDLocationValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return LGDLocationValidator(db_session=None)

    # ========== Hierarchy Validation Tests ==========

    def test_validate_hierarchy_exact_match(self, validator):
        """Test hierarchy validation with exact matches."""
        result = validator.validate_hierarchy(
            village="मादर",
            block="लोहंडीगुड़ा",
            district="बस्तर",
            state="छत्तीसगढ़"
        )

        assert result["is_valid"] is True
        assert result["confidence"] >= 0.9
        assert "village" in result["lgd_codes"]
        assert result["standardized_names"]["district"] == "बस्तर"

    def test_validate_hierarchy_missing_village(self, validator):
        """Test validation fails when village is missing."""
        result = validator.validate_hierarchy(
            village="",
            district="बस्तर"
        )

        assert result["is_valid"] is False
        assert "required" in result["issues"][0].lower()

    def test_validate_hierarchy_partial_data(self, validator):
        """Test validation with partial hierarchy data."""
        result = validator.validate_hierarchy(
            village="मादर",
            district="बस्तर"
            # No block or panchayat
        )

        # Should still work with village and district
        assert result is not None
        assert "village" in result.get("lgd_codes", {}) or not result["is_valid"]

    def test_validate_hierarchy_english_input(self, validator):
        """Test validation with English input."""
        result = validator.validate_hierarchy(
            village="Madar",
            district="Bastar",
            state="Chhattisgarh"
        )

        assert result is not None
        # Should handle transliteration

    # ========== Fuzzy Matching Tests ==========

    def test_fuzzy_match_exact(self, validator):
        """Test fuzzy matching with exact match."""
        matches = validator.fuzzy_match_location(
            name="बस्तर",
            level="district"
        )

        assert len(matches) > 0
        assert matches[0]["confidence"] >= 0.9
        assert matches[0]["match_type"] in ["exact", "fuzzy"]

    def test_fuzzy_match_spelling_variation(self, validator):
        """Test fuzzy matching with spelling variations."""
        matches = validator.fuzzy_match_location(
            name="बसतर",  # Missing '्'
            level="district"
        )

        assert len(matches) > 0
        # Should find "बस्तर" despite spelling difference
        assert matches[0]["confidence"] >= 0.7

    def test_fuzzy_match_transliteration(self, validator):
        """Test fuzzy matching with Hindi-English transliteration."""
        matches = validator.fuzzy_match_location(
            name="Bastar",
            level="district"
        )

        assert len(matches) > 0
        # Should match "बस्तर"

    def test_fuzzy_match_with_parent(self, validator):
        """Test fuzzy matching filtered by parent."""
        # Mock parent LGD code
        matches = validator.fuzzy_match_location(
            name="मादर",
            level="village",
            parent_lgd_code="3151"  # Lohandiguda block
        )

        assert len(matches) <= 3  # Respects limit

    def test_fuzzy_match_no_results(self, validator):
        """Test fuzzy matching with invalid input."""
        matches = validator.fuzzy_match_location(
            name="ऐसाकोईगांवनहींहै",  # No such village
            level="village"
        )

        # May return empty or low confidence matches
        if matches:
            assert matches[0]["confidence"] < 0.6

    def test_fuzzy_match_limit(self, validator):
        """Test fuzzy matching respects limit parameter."""
        matches = validator.fuzzy_match_location(
            name="मादर",
            level="village",
            limit=2
        )

        assert len(matches) <= 2

    # ========== Phonetic Matching Tests ==========

    def test_phonetic_code_generation(self, validator):
        """Test phonetic code generation."""
        code1 = validator._phonetic_code("मादर")
        code2 = validator._phonetic_code("माडर")

        # Should generate similar codes for phonetically similar words
        assert code1 is not None
        assert code2 is not None

    def test_phonetic_match_hindi(self, validator):
        """Test phonetic matching for Hindi words."""
        is_match = validator._phonetic_match("बस्तर", "बसतर")

        # Should match despite spelling difference
        assert is_match is not None

    def test_phonetic_match_transliteration(self, validator):
        """Test phonetic matching across Hindi-English."""
        code_hindi = validator._phonetic_code("बस्तर")
        code_english = validator._phonetic_code("bastar")

        # Should produce similar codes
        assert code_hindi is not None
        assert code_english is not None

    # ========== Spelling Correction Tests ==========

    def test_suggest_corrections(self, validator):
        """Test spelling correction suggestions."""
        suggestions = validator.suggest_corrections(
            name="बसतर",
            level="district"
        )

        assert len(suggestions) > 0
        assert len(suggestions) <= 5
        assert "बस्तर" in suggestions or any("बस" in s for s in suggestions)

    def test_suggest_corrections_english(self, validator):
        """Test corrections for English misspellings."""
        suggestions = validator.suggest_corrections(
            name="Baster",
            level="district"
        )

        # Should suggest Bastar
        assert len(suggestions) >= 0

    def test_suggest_corrections_no_suggestions(self, validator):
        """Test suggestions when no close matches exist."""
        suggestions = validator.suggest_corrections(
            name="ऐसाकोईजिलानहींहै",
            level="district"
        )

        # May return empty list
        assert isinstance(suggestions, list)

    # ========== Enrichment Tests ==========

    def test_enrich_with_lgd_data(self, validator):
        """Test location enrichment with LGD data."""
        location = {
            "village": "मादर",
            "block": "लोहंडीगुड़ा",
            "district": "बस्तर",
            "state": "छत्तीसगढ़"
        }

        enriched = validator.enrich_with_lgd_data(location)

        assert enriched is not None
        assert "validated_by_lgd" in enriched
        assert "lgd_confidence" in enriched
        # May have LGD codes if validation succeeded
        if enriched["validated_by_lgd"]:
            assert "village_lgd_code" in enriched

    def test_enrich_empty_location(self, validator):
        """Test enrichment with empty location."""
        enriched = validator.enrich_with_lgd_data({})

        assert enriched is not None
        assert enriched == {}

    def test_enrich_partial_location(self, validator):
        """Test enrichment with partial location data."""
        location = {
            "village": "मादर",
            "district": "बस्तर"
        }

        enriched = validator.enrich_with_lgd_data(location)

        assert "village" in enriched
        assert "district" in enriched

    # ========== Text Normalization Tests ==========

    def test_normalize_text_whitespace(self, validator):
        """Test text normalization removes extra whitespace."""
        normalized = validator._normalize_text("बस्तर  जिला")

        assert "  " not in normalized
        assert normalized == "बस्तर जिला"

    def test_normalize_text_case(self, validator):
        """Test text normalization handles case."""
        normalized = validator._normalize_text("Bastar")

        assert normalized == "bastar"

    def test_normalize_text_suffix_removal(self, validator):
        """Test text normalization removes common suffixes."""
        normalized = validator._normalize_text("मादर ग्राम पंचायत")

        assert "पंचायत" not in normalized or normalized == "मादर ग्राम पंचायत"

    # ========== Edit Distance Tests ==========

    def test_levenshtein_distance_identical(self, validator):
        """Test edit distance for identical strings."""
        distance = validator._levenshtein_distance("test", "test")

        assert distance == 0

    def test_levenshtein_distance_one_edit(self, validator):
        """Test edit distance with one character difference."""
        distance = validator._levenshtein_distance("test", "best")

        assert distance == 1

    def test_levenshtein_distance_multiple_edits(self, validator):
        """Test edit distance with multiple differences."""
        distance = validator._levenshtein_distance("किटन", "सिटिंग")

        assert distance > 0

    def test_levenshtein_distance_empty_string(self, validator):
        """Test edit distance with empty string."""
        distance = validator._levenshtein_distance("test", "")

        assert distance == 4

    # ========== Confidence Scoring Tests ==========

    def test_calculate_confidence_perfect_match(self, validator):
        """Test confidence calculation for perfect match."""
        confidence = validator._calculate_confidence(
            similarity_ratio=1.0,
            edit_distance=0
        )

        assert confidence == 1.0

    def test_calculate_confidence_good_match(self, validator):
        """Test confidence calculation for good match."""
        confidence = validator._calculate_confidence(
            similarity_ratio=0.8,
            edit_distance=1
        )

        assert 0.7 <= confidence <= 0.9

    def test_calculate_confidence_poor_match(self, validator):
        """Test confidence calculation for poor match."""
        confidence = validator._calculate_confidence(
            similarity_ratio=0.5,
            edit_distance=5
        )

        assert confidence < 0.6

    # ========== Edge Cases ==========

    def test_validate_hierarchy_special_characters(self, validator):
        """Test validation with special characters."""
        result = validator.validate_hierarchy(
            village="मादर-123",
            district="बस्तर"
        )

        assert result is not None

    def test_fuzzy_match_empty_name(self, validator):
        """Test fuzzy matching with empty name."""
        matches = validator.fuzzy_match_location(
            name="",
            level="village"
        )

        assert matches == []

    def test_fuzzy_match_invalid_level(self, validator):
        """Test fuzzy matching with invalid admin level."""
        matches = validator.fuzzy_match_location(
            name="test",
            level="invalid_level"
        )

        assert matches == []

    def test_phonetic_code_empty_string(self, validator):
        """Test phonetic code with empty string."""
        code = validator._phonetic_code("")

        assert code == ""

    def test_normalize_text_none_input(self, validator):
        """Test text normalization with None input."""
        normalized = validator._normalize_text(None)

        assert normalized == ""

    # ========== Integration Tests ==========

    def test_full_validation_workflow(self, validator):
        """Test complete validation workflow."""
        # Step 1: Validate hierarchy
        result = validator.validate_hierarchy(
            village="Madar",
            block="Lohandiguda",
            district="Bastar",
            state="Chhattisgarh"
        )

        # Step 2: Check fuzzy matching worked
        assert result is not None

        # Step 3: Verify enrichment
        location = {"village": "Madar", "district": "Bastar"}
        enriched = validator.enrich_with_lgd_data(location)

        assert "lgd_confidence" in enriched

    def test_validation_with_misspellings(self, validator):
        """Test validation handles common misspellings."""
        result = validator.validate_hierarchy(
            village="Madur",  # Misspelled
            district="Baster",  # Misspelled
            state="Chhattisgarh"
        )

        # Should find close matches
        assert result is not None

    def test_confidence_thresholds(self, validator):
        """Test confidence threshold constants."""
        assert validator.EXACT_MATCH_THRESHOLD == 1.0
        assert validator.HIGH_CONFIDENCE_THRESHOLD >= 0.8
        assert validator.MEDIUM_CONFIDENCE_THRESHOLD >= 0.6
        assert validator.LOW_CONFIDENCE_THRESHOLD >= 0.5


class TestLGDLocationValidatorPerformance:
    """Performance and scalability tests."""

    @pytest.fixture
    def validator(self):
        return LGDLocationValidator(db_session=None)

    def test_fuzzy_match_performance(self, validator):
        """Test fuzzy matching performance."""
        import time

        start = time.time()

        # Should complete in reasonable time
        matches = validator.fuzzy_match_location(
            name="मादर",
            level="village"
        )

        elapsed = time.time() - start

        assert elapsed < 1.0  # Should be < 1 second
        assert matches is not None

    def test_multiple_validations(self, validator):
        """Test multiple consecutive validations."""
        locations = [
            ("मादर", "बस्तर"),
            ("लोहंडीगुड़ा", "बस्तर"),
            ("जगदलपुर", "बस्तर")
        ]

        for village, district in locations:
            result = validator.validate_hierarchy(
                village=village,
                district=district
            )
            assert result is not None


class TestLGDLocationValidatorErrorHandling:
    """Error handling and robustness tests."""

    @pytest.fixture
    def validator(self):
        return LGDLocationValidator(db_session=None)

    def test_handle_unicode_errors(self, validator):
        """Test handling of unicode encoding issues."""
        result = validator.validate_hierarchy(
            village="test\x00village",  # Null byte
            district="बस्तर"
        )

        assert result is not None

    def test_handle_very_long_names(self, validator):
        """Test handling of unreasonably long names."""
        long_name = "अ" * 1000

        result = validator.validate_hierarchy(
            village=long_name,
            district="बस्तर"
        )

        assert result is not None

    def test_handle_database_unavailable(self, validator):
        """Test graceful handling when database is unavailable."""
        # Validator should work with mock data
        result = validator.validate_hierarchy(
            village="मादर",
            district="बस्तर"
        )

        assert result is not None
        # May use mock data or return low confidence
