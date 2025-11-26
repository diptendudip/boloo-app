"""
LGD (Local Government Directory) Location Validator.

Validates locations against authoritative government data with fuzzy matching,
phonetic algorithms, and Hindi/English transliteration support.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class LGDLocationValidator:
    """
    Validate locations against LGD (Local Government Directory) authoritative data.

    Features:
    - Hierarchical validation (village → panchayat → block → district)
    - Fuzzy matching with Levenshtein distance
    - Phonetic matching (Soundex/Metaphone)
    - Hindi/English transliteration handling
    - Confidence scoring (0.0 to 1.0)
    - Spelling correction suggestions
    """

    def __init__(self, db_session=None):
        """
        Initialize LGD validator.

        Args:
            db_session: SQLAlchemy database session for LGD data queries
        """
        self.db = db_session

        # Confidence thresholds
        self.EXACT_MATCH_THRESHOLD = 1.0
        self.HIGH_CONFIDENCE_THRESHOLD = 0.9
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.7
        self.LOW_CONFIDENCE_THRESHOLD = 0.6

        # Fuzzy match parameters
        self.MAX_EDIT_DISTANCE = 3
        self.MIN_SIMILARITY_RATIO = 0.6

        # Administrative levels
        self.ADMIN_LEVELS = ["state", "district", "block", "panchayat", "village"]

        logger.info("LGDLocationValidator initialized")

    def validate_hierarchy(
        self,
        village: str,
        panchayat: Optional[str] = None,
        block: Optional[str] = None,
        district: Optional[str] = None,
        state: str = "Chhattisgarh"
    ) -> Dict[str, Any]:
        """
        Validate that village → panchayat → block → district hierarchy is correct.

        Args:
            village: Village name (required)
            panchayat: Gram panchayat name (optional)
            block: Block/Tehsil name (optional)
            district: District name (optional)
            state: State name (default: Chhattisgarh)

        Returns:
            {
                "is_valid": True/False,
                "lgd_codes": {
                    "state": "22",
                    "district": "398",
                    "block": "3151",
                    "panchayat": "123456",
                    "village": "234567"
                },
                "standardized_names": {
                    "village": "मादर",
                    "panchayat": "मादर ग्राम पंचायत",
                    "block": "लोहंडीगुड़ा",
                    "district": "बस्तर",
                    "state": "छत्तीसगढ़"
                },
                "confidence": 0.95,
                "issues": [],  # List of validation issues found
                "match_details": {
                    "village_match_type": "exact|fuzzy|phonetic",
                    "village_match_confidence": 0.95
                }
            }
        """
        if not village:
            return self._validation_error("Village name is required")

        try:
            issues = []
            lgd_codes = {}
            standardized_names = {}
            match_details = {}
            overall_confidence = 0.0
            confidence_sum = 0.0
            confidence_count = 0

            # 1. Validate state
            state_result = self._validate_single_level(state, "state")
            if state_result["found"]:
                lgd_codes["state"] = state_result["lgd_code"]
                standardized_names["state"] = state_result["name"]
                match_details["state_match_confidence"] = state_result["confidence"]
                confidence_sum += state_result["confidence"]
                confidence_count += 1
            else:
                issues.append(f"State '{state}' not found in LGD")

            # 2. Validate district (if provided)
            district_lgd_code = None
            if district:
                district_result = self._validate_single_level(
                    district, "district",
                    parent_lgd_code=lgd_codes.get("state")
                )
                if district_result["found"]:
                    district_lgd_code = district_result["lgd_code"]
                    lgd_codes["district"] = district_lgd_code
                    standardized_names["district"] = district_result["name"]
                    match_details["district_match_type"] = district_result["match_type"]
                    match_details["district_match_confidence"] = district_result["confidence"]
                    confidence_sum += district_result["confidence"]
                    confidence_count += 1
                else:
                    issues.append(f"District '{district}' not found in state '{state}'")

            # 3. Validate block (if provided)
            block_lgd_code = None
            if block:
                block_result = self._validate_single_level(
                    block, "block",
                    parent_lgd_code=district_lgd_code
                )
                if block_result["found"]:
                    block_lgd_code = block_result["lgd_code"]
                    lgd_codes["block"] = block_lgd_code
                    standardized_names["block"] = block_result["name"]
                    match_details["block_match_type"] = block_result["match_type"]
                    match_details["block_match_confidence"] = block_result["confidence"]
                    confidence_sum += block_result["confidence"]
                    confidence_count += 1
                else:
                    issues.append(f"Block '{block}' not found")

            # 4. Validate panchayat (if provided)
            panchayat_lgd_code = None
            if panchayat:
                panchayat_result = self._validate_single_level(
                    panchayat, "panchayat",
                    parent_lgd_code=block_lgd_code
                )
                if panchayat_result["found"]:
                    panchayat_lgd_code = panchayat_result["lgd_code"]
                    lgd_codes["panchayat"] = panchayat_lgd_code
                    standardized_names["panchayat"] = panchayat_result["name"]
                    match_details["panchayat_match_type"] = panchayat_result["match_type"]
                    match_details["panchayat_match_confidence"] = panchayat_result["confidence"]
                    confidence_sum += panchayat_result["confidence"]
                    confidence_count += 1
                else:
                    issues.append(f"Panchayat '{panchayat}' not found")

            # 5. Validate village (required)
            village_result = self._validate_single_level(
                village, "village",
                parent_lgd_code=panchayat_lgd_code or block_lgd_code
            )
            if village_result["found"]:
                lgd_codes["village"] = village_result["lgd_code"]
                standardized_names["village"] = village_result["name"]
                match_details["village_match_type"] = village_result["match_type"]
                match_details["village_match_confidence"] = village_result["confidence"]
                confidence_sum += village_result["confidence"]
                confidence_count += 1
            else:
                issues.append(f"Village '{village}' not found")

            # Calculate overall confidence
            if confidence_count > 0:
                overall_confidence = confidence_sum / confidence_count

            # Determine if valid
            is_valid = len(issues) == 0 and overall_confidence >= self.LOW_CONFIDENCE_THRESHOLD

            return {
                "is_valid": is_valid,
                "lgd_codes": lgd_codes,
                "standardized_names": standardized_names,
                "confidence": round(overall_confidence, 2),
                "issues": issues,
                "match_details": match_details
            }

        except Exception as e:
            logger.error(f"Error validating hierarchy: {e}", exc_info=True)
            return self._validation_error(f"Validation error: {str(e)}")

    def fuzzy_match_location(
        self,
        name: str,
        level: str,
        parent_lgd_code: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy match user input to LGD records using multiple algorithms.

        Uses:
        - Levenshtein distance (edit distance)
        - Sequence matching (similarity ratio)
        - Phonetic matching (Soundex-like algorithm)

        Args:
            name: Location name to match
            level: Administrative level (village, panchayat, block, district, state)
            parent_lgd_code: Optional parent unit LGD code to narrow search
            limit: Maximum number of matches to return (default: 3)

        Returns:
            List of matches, each containing:
            {
                "lgd_code": "123456",
                "name": "मादर",
                "name_en": "Madar",
                "match_type": "exact|fuzzy|phonetic",
                "confidence": 0.85,
                "edit_distance": 2,
                "similarity_ratio": 0.87
            }
        """
        if not name or not level:
            return []

        if level not in self.ADMIN_LEVELS:
            logger.warning(f"Invalid admin level: {level}")
            return []

        try:
            # Clean and normalize input
            normalized_name = self._normalize_text(name)

            # Get candidate records from database
            candidates = self._get_candidates(level, parent_lgd_code)

            if not candidates:
                logger.info(f"No candidates found for level '{level}'")
                return []

            # Score each candidate
            matches = []
            for candidate in candidates:
                score = self._calculate_match_score(normalized_name, candidate)
                if score["confidence"] >= self.MIN_SIMILARITY_RATIO:
                    matches.append(score)

            # Sort by confidence (descending) and return top N
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            return matches[:limit]

        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}", exc_info=True)
            return []

    def suggest_corrections(
        self,
        name: str,
        level: str,
        parent_lgd_code: Optional[str] = None
    ) -> List[str]:
        """
        Suggest correct names for misspellings.

        Args:
            name: Potentially misspelled location name
            level: Administrative level
            parent_lgd_code: Optional parent unit LGD code

        Returns:
            List of up to 5 suggested corrections, ordered by confidence
            Example: ["मादर", "मादुर", "मदार", "माडर", "महादर"]
        """
        if not name or not level:
            return []

        try:
            # Use fuzzy matching to find similar names
            matches = self.fuzzy_match_location(
                name, level, parent_lgd_code, limit=5
            )

            # Extract just the names
            suggestions = []
            for match in matches:
                if match["confidence"] < 1.0:  # Don't suggest exact matches
                    # Prefer Hindi name if available, fallback to English
                    suggestion = match.get("name") or match.get("name_en")
                    if suggestion and suggestion not in suggestions:
                        suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}", exc_info=True)
            return []

    def enrich_with_lgd_data(
        self,
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Take user-provided location, add LGD codes and official names.

        Args:
            location: Dictionary with location data
                {
                    "village": "मादर",
                    "panchayat": "मादर",
                    "block": "लोहंडीगुड़ा",
                    "district": "बस्तर",
                    "state": "छत्तीसगढ़"
                }

        Returns:
            Enhanced location with LGD codes:
                {
                    "village": "मादर",
                    "village_lgd_code": "234567",
                    "panchayat": "मादर ग्राम पंचायत",
                    "panchayat_lgd_code": "123456",
                    ...
                    "validated_by_lgd": True,
                    "lgd_confidence": 0.95,
                    "lgd_match_details": {...}
                }
        """
        if not location:
            return location

        try:
            # Validate the hierarchy
            validation_result = self.validate_hierarchy(
                village=location.get("village", ""),
                panchayat=location.get("panchayat"),
                block=location.get("block"),
                district=location.get("district"),
                state=location.get("state", "Chhattisgarh")
            )

            # Merge with original location
            enriched = location.copy()

            # Add LGD codes
            for level, code in validation_result.get("lgd_codes", {}).items():
                enriched[f"{level}_lgd_code"] = code

            # Update with standardized names (preserve original if LGD not found)
            for level, name in validation_result.get("standardized_names", {}).items():
                if name:
                    enriched[level] = name

            # Add validation metadata
            enriched["validated_by_lgd"] = validation_result["is_valid"]
            enriched["lgd_confidence"] = validation_result["confidence"]
            enriched["lgd_match_details"] = validation_result.get("match_details", {})
            enriched["lgd_issues"] = validation_result.get("issues", [])

            return enriched

        except Exception as e:
            logger.error(f"Error enriching location: {e}", exc_info=True)
            # Return original location if enrichment fails
            return location

    # ========== Private Helper Methods ==========

    def _validate_single_level(
        self,
        name: str,
        level: str,
        parent_lgd_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a single administrative level.

        Returns:
            {
                "found": True/False,
                "lgd_code": "123456",
                "name": "मादर",
                "confidence": 0.95,
                "match_type": "exact|fuzzy|phonetic"
            }
        """
        if not name:
            return {"found": False, "confidence": 0.0}

        # Try exact match first
        exact_match = self._exact_match(name, level, parent_lgd_code)
        if exact_match:
            return {
                "found": True,
                "lgd_code": exact_match["lgd_code"],
                "name": exact_match["name"],
                "confidence": 1.0,
                "match_type": "exact"
            }

        # Try fuzzy matching
        fuzzy_matches = self.fuzzy_match_location(name, level, parent_lgd_code, limit=1)
        if fuzzy_matches:
            best_match = fuzzy_matches[0]
            match_type = "phonetic" if best_match.get("phonetic_match") else "fuzzy"
            return {
                "found": True,
                "lgd_code": best_match["lgd_code"],
                "name": best_match["name"],
                "confidence": best_match["confidence"],
                "match_type": match_type
            }

        # No match found
        return {"found": False, "confidence": 0.0}

    def _exact_match(
        self,
        name: str,
        level: str,
        parent_lgd_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Try exact match against LGD database.

        Checks both Hindi and English names, and aliases.
        """
        if not self.db:
            # Database not available, simulate for now
            logger.warning("Database not connected, using mock data")
            return self._mock_exact_match(name, level)

        # TODO: Implement actual database query when schema is ready
        # Example query:
        # from app.models.lgd import LGDAdminUnit
        #
        # query = self.db.query(LGDAdminUnit).filter(
        #     LGDAdminUnit.level == level,
        #     or_(
        #         LGDAdminUnit.name_en == name,
        #         LGDAdminUnit.name_hi == name,
        #         LGDAdminUnit.name_local == name
        #     )
        # )
        #
        # if parent_lgd_code:
        #     query = query.filter(LGDAdminUnit.parent_lgd_code == parent_lgd_code)
        #
        # result = query.first()
        #
        # if result:
        #     return {
        #         "lgd_code": result.lgd_code,
        #         "name": result.name_hi or result.name_en
        #     }

        return None

    def _get_candidates(
        self,
        level: str,
        parent_lgd_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get candidate records from database for fuzzy matching.

        Returns list of candidates with their names and codes.
        """
        if not self.db:
            # Database not available, return mock data
            logger.warning("Database not connected, using mock candidates")
            return self._mock_candidates(level)

        # TODO: Implement actual database query
        # from app.models.lgd import LGDAdminUnit
        #
        # query = self.db.query(LGDAdminUnit).filter(
        #     LGDAdminUnit.level == level,
        #     LGDAdminUnit.is_active == True
        # )
        #
        # if parent_lgd_code:
        #     query = query.filter(LGDAdminUnit.parent_lgd_code == parent_lgd_code)
        #
        # results = query.limit(1000).all()
        #
        # return [
        #     {
        #         "lgd_code": r.lgd_code,
        #         "name": r.name_hi,
        #         "name_en": r.name_en,
        #         "name_local": r.name_local
        #     }
        #     for r in results
        # ]

        return []

    def _calculate_match_score(
        self,
        input_name: str,
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate match score between input and candidate using multiple algorithms.

        Combines:
        - Edit distance (Levenshtein)
        - Sequence similarity
        - Phonetic similarity
        """
        candidate_names = [
            candidate.get("name", ""),
            candidate.get("name_en", ""),
            candidate.get("name_local", "")
        ]

        best_similarity = 0.0
        best_edit_distance = float('inf')
        best_name = candidate.get("name", "")
        is_phonetic_match = False

        for cand_name in candidate_names:
            if not cand_name:
                continue

            # Normalize for comparison
            normalized_candidate = self._normalize_text(cand_name)

            # Calculate similarity ratio
            similarity = SequenceMatcher(None, input_name, normalized_candidate).ratio()

            # Calculate edit distance
            edit_dist = self._levenshtein_distance(input_name, normalized_candidate)

            # Check phonetic similarity
            if self._phonetic_match(input_name, normalized_candidate):
                similarity = max(similarity, 0.8)  # Boost for phonetic match
                is_phonetic_match = True

            if similarity > best_similarity:
                best_similarity = similarity
                best_edit_distance = edit_dist
                best_name = cand_name

        # Calculate confidence score
        confidence = self._calculate_confidence(best_similarity, best_edit_distance)

        return {
            "lgd_code": candidate.get("lgd_code"),
            "name": best_name,
            "name_en": candidate.get("name_en"),
            "match_type": "phonetic" if is_phonetic_match else "fuzzy",
            "confidence": round(confidence, 2),
            "edit_distance": best_edit_distance,
            "similarity_ratio": round(best_similarity, 2),
            "phonetic_match": is_phonetic_match
        }

    def _calculate_confidence(
        self,
        similarity_ratio: float,
        edit_distance: int
    ) -> float:
        """
        Calculate overall confidence score from similarity metrics.

        Weights:
        - 70% from similarity ratio
        - 30% from inverse edit distance
        """
        # Normalize edit distance (0 = perfect, >3 = poor)
        normalized_edit = max(0, 1 - (edit_distance / self.MAX_EDIT_DISTANCE))

        # Weighted combination
        confidence = (0.7 * similarity_ratio) + (0.3 * normalized_edit)

        return min(1.0, max(0.0, confidence))

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein (edit) distance between two strings.

        Returns minimum number of single-character edits needed to transform s1 into s2.
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertion, deletion, or substitution
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _phonetic_match(self, s1: str, s2: str) -> bool:
        """
        Check if two strings are phonetically similar.

        Uses simplified Soundex-like algorithm for Hindi/English transliteration.
        """
        # Get phonetic codes
        code1 = self._phonetic_code(s1)
        code2 = self._phonetic_code(s2)

        # Match if codes are similar
        return code1 == code2 if code1 and code2 else False

    def _phonetic_code(self, text: str) -> str:
        """
        Generate phonetic code for text.

        Handles common Hindi-English transliteration variations:
        - व/w, ब/b, द/d/th, त/t/th, etc.
        """
        if not text:
            return ""

        text = text.lower()

        # Transliteration mappings (Hindi sounds to simplified code)
        replacements = {
            'व': 'v', 'ब': 'b', 'द': 'd', 'त': 't',
            'ध': 'd', 'थ': 't', 'ष': 's', 'श': 's',
            'स': 's', 'क': 'k', 'ख': 'k', 'ग': 'g',
            'घ': 'g', 'च': 'c', 'छ': 'c', 'ज': 'j',
            'झ': 'j', 'ट': 't', 'ठ': 't', 'ड': 'd',
            'ढ': 'd', 'ण': 'n', 'न': 'n', 'प': 'p',
            'फ': 'p', 'म': 'm', 'य': 'y', 'र': 'r',
            'ल': 'l', 'ह': 'h', 'ā': 'a', 'ī': 'i',
            'ū': 'u', 'े': 'e', 'ै': 'ai', 'ो': 'o',
            'ौ': 'au', 'ं': '', 'ः': '', '्': ''
        }

        # Apply replacements
        code = text
        for hindi, eng in replacements.items():
            code = code.replace(hindi, eng)

        # Remove vowels except first character
        if len(code) > 1:
            code = code[0] + re.sub(r'[aeiou]', '', code[1:])

        # Remove duplicate consonants
        code = re.sub(r'(.)\1+', r'\1', code)

        return code[:6]  # Return first 6 characters

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        - Remove extra whitespace
        - Convert to lowercase (for English)
        - Remove diacritics
        - Trim
        """
        if not text:
            return ""

        # Remove extra whitespace
        normalized = ' '.join(text.split())

        # Lowercase (for English text)
        normalized = normalized.lower()

        # Remove common suffixes/prefixes for better matching
        suffixes = ['gram panchayat', 'ग्राम पंचायत', 'village', 'गांव']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        return normalized.strip()

    def _validation_error(self, message: str) -> Dict[str, Any]:
        """Return error result for validation."""
        return {
            "is_valid": False,
            "lgd_codes": {},
            "standardized_names": {},
            "confidence": 0.0,
            "issues": [message],
            "match_details": {}
        }

    # ========== Mock Data Methods (for testing without database) ==========

    def _mock_exact_match(self, name: str, level: str) -> Optional[Dict[str, Any]]:
        """Mock exact match for testing."""
        mock_data = {
            "state": {
                "छत्तीसगढ़": {"lgd_code": "22", "name": "छत्तीसगढ़"},
                "chhattisgarh": {"lgd_code": "22", "name": "छत्तीसगढ़"}
            },
            "district": {
                "बस्तर": {"lgd_code": "398", "name": "बस्तर"},
                "bastar": {"lgd_code": "398", "name": "बस्तर"}
            },
            "block": {
                "लोहंडीगुड़ा": {"lgd_code": "3151", "name": "लोहंडीगुड़ा"},
                "lohandiguda": {"lgd_code": "3151", "name": "लोहंडीगुड़ा"}
            }
        }

        normalized = self._normalize_text(name)
        level_data = mock_data.get(level, {})

        return level_data.get(normalized)

    def _mock_candidates(self, level: str) -> List[Dict[str, Any]]:
        """Mock candidates for testing."""
        mock_candidates = {
            "village": [
                {"lgd_code": "234567", "name": "मादर", "name_en": "Madar"},
                {"lgd_code": "234568", "name": "मादुर", "name_en": "Madur"},
                {"lgd_code": "234569", "name": "महादर", "name_en": "Mahadar"}
            ],
            "panchayat": [
                {"lgd_code": "123456", "name": "मादर ग्राम पंचायत", "name_en": "Madar Gram Panchayat"}
            ],
            "block": [
                {"lgd_code": "3151", "name": "लोहंडीगुड़ा", "name_en": "Lohandiguda"}
            ],
            "district": [
                {"lgd_code": "398", "name": "बस्तर", "name_en": "Bastar"}
            ],
            "state": [
                {"lgd_code": "22", "name": "छत्तीसगढ़", "name_en": "Chhattisgarh"}
            ]
        }

        return mock_candidates.get(level, [])
