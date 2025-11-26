"""
Test dynamic context-aware completeness analyzer.

Tests that the system:
1. Detects problem types from issue descriptions
2. Selects relevant contextual fields
3. Asks appropriate follow-up questions based on problem type
"""

import pytest
import logging
from typing import Dict, Any

from app.services.completeness_analyzer import (
    CompletenessAnalyzer,
    get_completeness_analyzer,
    UNIVERSAL_REQUIRED_FIELDS,
    CONTEXTUAL_FIELDS
)

logger = logging.getLogger(__name__)


class TestProblemTypeDetection:
    """Test problem type detection from issue descriptions."""

    def test_water_problem_detection(self):
        """Water supply issues should detect 'water' category."""
        analyzer = get_completeness_analyzer()

        test_cases = [
            "हमारे गाँव में पानी नहीं आ रहा है",
            "पानी की सप्लाई बंद है",
            "पानी की समस्या है",
            "Water supply is not coming"
        ]

        for description in test_cases:
            problem_types = analyzer._detect_problem_type(description)
            assert "water" in problem_types, f"Failed to detect 'water' in: {description}"
            assert "all" in problem_types, f"Missing 'all' category in: {description}"
            logger.info(f"✅ Detected {problem_types} for: {description}")

    def test_electricity_problem_detection(self):
        """Electricity issues should detect 'electricity' category."""
        analyzer = get_completeness_analyzer()

        test_cases = [
            "बिजली नहीं आ रही है",
            "बिजली की सप्लाई बंद है",
            "ट्रांसफॉर्मर खराब है",
            "No electricity supply"
        ]

        for description in test_cases:
            problem_types = analyzer._detect_problem_type(description)
            assert "electricity" in problem_types, f"Failed to detect 'electricity' in: {description}"
            assert "all" in problem_types
            logger.info(f"✅ Detected {problem_types} for: {description}")

    def test_road_problem_detection(self):
        """Road issues should detect 'road' category."""
        analyzer = get_completeness_analyzer()

        test_cases = [
            "सड़क खराब है",
            "सड़क में गड्ढे हैं",
            "Road is damaged",
            "Potholes on the road"
        ]

        for description in test_cases:
            problem_types = analyzer._detect_problem_type(description)
            assert "road" in problem_types, f"Failed to detect 'road' in: {description}"
            assert "all" in problem_types
            logger.info(f"✅ Detected {problem_types} for: {description}")

    def test_health_problem_detection(self):
        """Health issues should detect 'health' or 'medical' category."""
        analyzer = get_completeness_analyzer()

        test_cases = [
            "लोग बीमार हो रहे हैं",
            "बुखार फैल रहा है",
            "अस्पताल में डॉक्टर नहीं हैं",
            "Disease outbreak"
        ]

        for description in test_cases:
            problem_types = analyzer._detect_problem_type(description)
            has_health = any(cat in problem_types for cat in ["health", "medical", "disease"])
            assert has_health, f"Failed to detect health category in: {description}"
            assert "all" in problem_types
            logger.info(f"✅ Detected {problem_types} for: {description}")

    def test_education_problem_detection(self):
        """Education issues should detect 'education' or 'school' category."""
        analyzer = get_completeness_analyzer()

        test_cases = [
            "स्कूल में टीचर नहीं हैं",
            "स्कूल की बिल्डिंग खराब है",
            "Teachers not coming to school",
            "School infrastructure problem"
        ]

        for description in test_cases:
            problem_types = analyzer._detect_problem_type(description)
            has_education = any(cat in problem_types for cat in ["education", "school"])
            assert has_education, f"Failed to detect education category in: {description}"
            assert "all" in problem_types
            logger.info(f"✅ Detected {problem_types} for: {description}")

    def test_corruption_problem_detection(self):
        """Corruption issues should detect 'corruption' or 'bribery' category."""
        analyzer = get_completeness_analyzer()

        test_cases = [
            "रिश्वत मांग रहे हैं",
            "पैसे लिए बिना काम नहीं कर रहे",
            "Bribery in office",
            "Officer demanding money"
        ]

        for description in test_cases:
            problem_types = analyzer._detect_problem_type(description)
            has_corruption = any(cat in problem_types for cat in ["corruption", "bribery", "harassment"])
            assert has_corruption, f"Failed to detect corruption category in: {description}"
            assert "all" in problem_types
            logger.info(f"✅ Detected {problem_types} for: {description}")


class TestContextualFieldSelection:
    """Test contextual field selection based on problem type."""

    def test_water_fields_selected(self):
        """Water problems should select service-related fields."""
        analyzer = get_completeness_analyzer()

        problem_types = ["water", "all"]
        fields = analyzer._select_contextual_fields(problem_types)

        assert "service_duration" in fields
        assert "service_frequency" in fields
        assert "affected_scope" in fields  # applies to "all"
        logger.info(f"✅ Selected {len(fields)} fields for water problem: {list(fields.keys())}")

    def test_road_fields_selected(self):
        """Road problems should select infrastructure-related fields."""
        analyzer = get_completeness_analyzer()

        problem_types = ["road", "all"]
        fields = analyzer._select_contextual_fields(problem_types)

        assert "road_landmark" in fields
        assert "damage_severity" in fields
        assert "affected_scope" in fields  # applies to "all"
        logger.info(f"✅ Selected {len(fields)} fields for road problem: {list(fields.keys())}")

    def test_health_fields_selected(self):
        """Health problems should select health-related fields."""
        analyzer = get_completeness_analyzer()

        problem_types = ["health", "disease", "all"]
        fields = analyzer._select_contextual_fields(problem_types)

        assert "health_affected_count" in fields
        assert "health_symptoms" in fields
        assert "affected_scope" in fields  # applies to "all"
        logger.info(f"✅ Selected {len(fields)} fields for health problem: {list(fields.keys())}")

    def test_education_fields_selected(self):
        """Education problems should select education-related fields."""
        analyzer = get_completeness_analyzer()

        problem_types = ["education", "school", "all"]
        fields = analyzer._select_contextual_fields(problem_types)

        assert "school_name" in fields
        assert "students_affected" in fields
        assert "affected_scope" in fields  # applies to "all"
        logger.info(f"✅ Selected {len(fields)} fields for education problem: {list(fields.keys())}")

    def test_corruption_fields_selected(self):
        """Corruption problems should select corruption-related fields."""
        analyzer = get_completeness_analyzer()

        problem_types = ["corruption", "bribery", "all"]
        fields = analyzer._select_contextual_fields(problem_types)

        assert "office_name" in fields
        assert "bribe_amount" in fields
        assert "affected_scope" in fields  # applies to "all"
        logger.info(f"✅ Selected {len(fields)} fields for corruption problem: {list(fields.keys())}")


class TestDynamicFieldSchema:
    """Test dynamic field schema building."""

    def test_no_issue_description_universal_only(self):
        """Without issue description, should return only universal fields."""
        analyzer = get_completeness_analyzer()

        schema = analyzer._build_dynamic_field_schema(None)

        assert len(schema) == 2  # Only universal fields
        assert "issue_description" in schema
        assert "location" in schema
        logger.info(f"✅ Universal-only schema has {len(schema)} fields")

    def test_water_problem_adds_contextual(self):
        """Water problem should add contextual service fields."""
        analyzer = get_completeness_analyzer()

        extracted_data = {
            "issue_description": "पानी की सप्लाई नहीं आ रही है"
        }

        schema = analyzer._build_dynamic_field_schema(extracted_data)

        assert len(schema) > 2  # Universal + contextual
        assert "issue_description" in schema
        assert "location" in schema
        assert "service_duration" in schema
        assert "service_frequency" in schema
        logger.info(f"✅ Water problem schema has {len(schema)} fields: {list(schema.keys())}")

    def test_road_problem_adds_contextual(self):
        """Road problem should add contextual infrastructure fields."""
        analyzer = get_completeness_analyzer()

        extracted_data = {
            "issue_description": "सड़क में बहुत गड्ढे हैं"
        }

        schema = analyzer._build_dynamic_field_schema(extracted_data)

        assert len(schema) > 2  # Universal + contextual
        assert "road_landmark" in schema
        assert "damage_severity" in schema
        logger.info(f"✅ Road problem schema has {len(schema)} fields: {list(schema.keys())}")

    def test_corruption_problem_adds_contextual(self):
        """Corruption problem should add contextual corruption fields."""
        analyzer = get_completeness_analyzer()

        extracted_data = {
            "issue_description": "ऑफिस में रिश्वत मांग रहे हैं"
        }

        schema = analyzer._build_dynamic_field_schema(extracted_data)

        assert len(schema) > 2  # Universal + contextual
        assert "office_name" in schema
        assert "bribe_amount" in schema
        logger.info(f"✅ Corruption problem schema has {len(schema)} fields: {list(schema.keys())}")


class TestEndToEndContextualAnalysis:
    """Test complete end-to-end contextual completeness analysis."""

    @pytest.mark.integration
    def test_water_problem_flow(self):
        """Test complete flow for water supply problem."""
        analyzer = get_completeness_analyzer()

        # Turn 1: User describes water problem
        result1 = analyzer.analyze_completeness(
            "हमारे गाँव रायपुर में पानी की सप्लाई नहीं आ रही है"
        )

        assert result1["completeness_score"] >= 0.5  # Got issue_description
        assert "issue_description" in result1["collected_fields"]
        assert "location" in result1["collected_fields"]

        # Should ask about contextual water fields (service_duration, service_frequency)
        # or affected_scope
        logger.info(f"✅ Turn 1: {result1['completeness_score']:.2f} complete")
        logger.info(f"   Collected: {result1['collected_fields']}")
        logger.info(f"   Next question: {result1['next_question_hi']}")

        # Turn 2: User says how long
        result2 = analyzer.analyze_completeness(
            "यह समस्या 15 दिन से हो रही है",
            already_collected_fields=result1["extracted_data"]
        )

        assert result2["completeness_score"] > result1["completeness_score"]
        assert "service_duration" in result2["extracted_data"] or "affected_scope" in result2["collected_fields"]
        logger.info(f"✅ Turn 2: {result2['completeness_score']:.2f} complete")
        logger.info(f"   Collected: {result2['collected_fields']}")

    @pytest.mark.integration
    def test_road_problem_flow(self):
        """Test complete flow for road damage problem."""
        analyzer = get_completeness_analyzer()

        # Turn 1: User describes road problem
        result1 = analyzer.analyze_completeness(
            "दुर्ग में मुख्य सड़क पर बहुत गड्ढे हैं"
        )

        assert result1["completeness_score"] >= 0.5
        assert "issue_description" in result1["collected_fields"]
        assert "location" in result1["collected_fields"]

        # Should ask about road-specific fields
        logger.info(f"✅ Turn 1: {result1['completeness_score']:.2f} complete")
        logger.info(f"   Next question: {result1['next_question_hi']}")

        # Turn 2: User provides landmark
        result2 = analyzer.analyze_completeness(
            "यह बस स्टैंड के पास वाली सड़क है",
            already_collected_fields=result1["extracted_data"]
        )

        assert result2["completeness_score"] > result1["completeness_score"]
        logger.info(f"✅ Turn 2: {result2['completeness_score']:.2f} complete")

    @pytest.mark.integration
    def test_corruption_problem_flow(self):
        """Test complete flow for corruption/bribery problem."""
        analyzer = get_completeness_analyzer()

        # Turn 1: User describes corruption problem
        result1 = analyzer.analyze_completeness(
            "नगर पालिका ऑफिस में पैसे मांग रहे हैं"
        )

        assert result1["completeness_score"] >= 0.5
        assert "issue_description" in result1["collected_fields"]

        # Should ask about corruption-specific fields
        logger.info(f"✅ Turn 1: {result1['completeness_score']:.2f} complete")
        logger.info(f"   Next question: {result1['next_question_hi']}")

        # Turn 2: User provides office name
        result2 = analyzer.analyze_completeness(
            "यह जल विभाग में हो रहा है",
            already_collected_fields=result1["extracted_data"]
        )

        # Score should increase or stay same (if location was already extracted in turn 1)
        assert result2["completeness_score"] >= result1["completeness_score"]
        logger.info(f"✅ Turn 2: {result2['completeness_score']:.2f} complete")


if __name__ == "__main__":
    # Run tests with detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    pytest.main([__file__, "-v", "-s"])
