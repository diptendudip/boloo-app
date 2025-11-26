# LGD Location Validator - Usage Guide

## Overview

The LGD (Local Government Directory) Location Validator provides authoritative location validation against official Indian government data. It enhances the existing geocoding services with:

- ✅ Hierarchical validation (village → panchayat → block → district → state)
- ✅ Fuzzy matching for spelling variations
- ✅ Phonetic matching for Hindi/English transliteration
- ✅ Confidence scoring (0.0 to 1.0)
- ✅ Spelling correction suggestions
- ✅ LGD code assignment

## Features

### 1. Hierarchy Validation

Validates that administrative units belong to their correct parents:

```python
from app.services.lgd_location_validator import LGDLocationValidator

validator = LGDLocationValidator(db_session=db)

result = validator.validate_hierarchy(
    village="मादर",
    panchayat="मादर ग्राम पंचायत",
    block="लोहंडीगुड़ा",
    district="बस्तर",
    state="छत्तीसगढ़"
)

print(result)
# {
#     "is_valid": True,
#     "lgd_codes": {
#         "state": "22",
#         "district": "398",
#         "block": "3151",
#         "panchayat": "123456",
#         "village": "234567"
#     },
#     "standardized_names": {
#         "village": "मादर",
#         "panchayat": "मादर ग्राम पंचायत",
#         "block": "लोहंडीगुड़ा",
#         "district": "बस्तर",
#         "state": "छत्तीसगढ़"
#     },
#     "confidence": 0.95,
#     "issues": [],
#     "match_details": {
#         "village_match_type": "exact",
#         "village_match_confidence": 1.0
#     }
# }
```

### 2. Fuzzy Matching

Handles spelling variations and misspellings:

```python
# User input with misspelling
matches = validator.fuzzy_match_location(
    name="Baster",  # Should be "Bastar"
    level="district",
    limit=3
)

print(matches)
# [
#     {
#         "lgd_code": "398",
#         "name": "बस्तर",
#         "name_en": "Bastar",
#         "match_type": "fuzzy",
#         "confidence": 0.87,
#         "edit_distance": 1,
#         "similarity_ratio": 0.85
#     }
# ]
```

### 3. Phonetic Matching

Handles Hindi-English transliteration:

```python
# English transliteration
matches = validator.fuzzy_match_location(
    name="Madar",
    level="village"
)

# Matches "मादर" with high confidence
print(matches[0]["confidence"])  # 0.85
```

### 4. Spelling Corrections

Suggests correct names for misspellings:

```python
suggestions = validator.suggest_corrections(
    name="Lodanguda",  # Should be "Lohandiguda"
    level="block"
)

print(suggestions)
# ["लोहंडीगुड़ा", "Lohandiguda", ...]
```

### 5. Location Enrichment

Adds LGD codes to existing location data:

```python
location = {
    "village": "मादर",
    "block": "लोहंडीगुड़ा",
    "district": "बस्तर",
    "state": "छत्तीसगढ़"
}

enriched = validator.enrich_with_lgd_data(location)

print(enriched)
# {
#     "village": "मादर",
#     "village_lgd_code": "234567",
#     "block": "लोहंडीगुड़ा",
#     "block_lgd_code": "3151",
#     "district": "बस्तर",
#     "district_lgd_code": "398",
#     "state": "छत्तीसगढ़",
#     "state_lgd_code": "22",
#     "validated_by_lgd": True,
#     "lgd_confidence": 0.95,
#     "lgd_match_details": {...}
# }
```

## Integration with HybridLocationValidator

The LGD validator is integrated into the hybrid validator:

```python
from app.services.location_validator import HybridLocationValidator

validator = HybridLocationValidator(db_session=db)

# Automatically uses LGD validation
result = validator.validate_and_enrich_location(
    location_text="मादर गांव, लोहंडीगुड़ा, बस्तर",
    enable_lgd_validation=True
)

print(result)
# {
#     "is_valid": True,
#     "lat": 19.1234,
#     "lng": 81.5678,
#     "admin_hierarchy": {
#         "village": "मादर",
#         "block": "लोहंडीगुड़ा",
#         "district": "बस्तर"
#     },
#     "lgd_codes": {
#         "village": "234567",
#         "block": "3151",
#         "district": "398"
#     },
#     "confidence": 0.92,
#     "source": "nominatim_+_lgd",
#     "validated_by_lgd": True,
#     "lgd_confidence": 0.95
# }
```

## Confidence Scoring

### Confidence Levels

| Score | Level | Description |
|-------|-------|-------------|
| 1.0 | Exact Match | Perfect match with LGD data |
| 0.9-0.99 | High Confidence | Very close match, minor variations |
| 0.7-0.89 | Medium Confidence | Fuzzy match, spelling variations |
| 0.6-0.69 | Low Confidence | Phonetic match or significant differences |
| < 0.6 | Very Low | Questionable match, manual verification needed |

### Confidence Calculation

```python
# Weighted combination:
# - 70% from string similarity ratio
# - 30% from inverse edit distance

confidence = (0.7 * similarity_ratio) + (0.3 * (1 - edit_distance/3))
```

## Fuzzy Matching Algorithms

### 1. Levenshtein Distance (Edit Distance)

Minimum number of single-character edits needed:

```python
distance = validator._levenshtein_distance("बस्तर", "बसतर")
# distance = 1 (missing '्')
```

### 2. Sequence Similarity

Ratio of matching characters:

```python
from difflib import SequenceMatcher

ratio = SequenceMatcher(None, "Bastar", "Baster").ratio()
# ratio = 0.833
```

### 3. Phonetic Matching

Simplified Soundex-like algorithm for Hindi/English:

```python
code1 = validator._phonetic_code("बस्तर")
code2 = validator._phonetic_code("bastar")
# Both produce similar codes: "bstr"
```

## Handling Hindi-English Transliteration

### Common Transliteration Patterns

| Hindi | English Variations |
|-------|-------------------|
| बस्तर | Bastar, Baster, Basthar |
| लोहंडीगुड़ा | Lohandiguda, Lohandguda, Lohandi Guda |
| मादर | Madar, Madur, Mader |
| छत्तीसगढ़ | Chhattisgarh, Chattisgarh, Chhatisgad |

### Handling Strategy

1. **Normalize text**: Remove diacritics, extra spaces
2. **Generate phonetic codes**: Convert to simplified sound representation
3. **Match phonetic codes**: Find similar-sounding names
4. **Score by similarity**: Combine phonetic + string similarity

## Edge Cases and Error Handling

### 1. Missing Data

```python
result = validator.validate_hierarchy(
    village="NewVillage2024",  # Not in LGD yet
    district="बस्तर"
)

# Result:
# {
#     "is_valid": False,
#     "issues": ["Village 'NewVillage2024' not found"],
#     "confidence": 0.0
# }
```

### 2. Multiple Villages with Same Name

```python
# Disambiguate using parent
matches = validator.fuzzy_match_location(
    name="मादर",
    level="village",
    parent_lgd_code="3151"  # Restrict to Lohandiguda block
)
```

### 3. Spelling Variations

```python
# Handles common spelling variations
result = validator.validate_hierarchy(
    village="Mader",  # Variation of "Madar"
    district="Bastar"
)

# Uses fuzzy matching to find correct name
# confidence will be 0.7-0.9 (not 1.0)
```

### 4. Database Unavailable

```python
# Validator uses mock data if database not connected
validator = LGDLocationValidator(db_session=None)

# Still functional with limited data
result = validator.validate_hierarchy(
    village="मादर",
    district="बस्तर"
)
```

## Performance Considerations

### Query Optimization

```python
# Limit results to improve performance
matches = validator.fuzzy_match_location(
    name="मादर",
    level="village",
    limit=3  # Only return top 3 matches
)
```

### Caching

```python
# Cache frequently validated locations
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_validate(village, district, state):
    return validator.validate_hierarchy(village, district, state)
```

### Batch Processing

```python
# Validate multiple locations efficiently
locations = [
    {"village": "मादर", "district": "बस्तर"},
    {"village": "जगदलपुर", "district": "बस्तर"}
]

results = []
for loc in locations:
    result = validator.validate_hierarchy(
        village=loc["village"],
        district=loc["district"]
    )
    results.append(result)
```

## Testing

### Unit Tests

```bash
# Run LGD validator tests
pytest tests/test_lgd_location_validator.py -v

# Run specific test
pytest tests/test_lgd_location_validator.py::TestLGDLocationValidator::test_validate_hierarchy_exact_match -v
```

### Test Coverage

```bash
# Generate coverage report
pytest tests/test_lgd_location_validator.py --cov=app.services.lgd_location_validator --cov-report=html
```

## Best Practices

### 1. Always Provide State

```python
# Good
result = validator.validate_hierarchy(
    village="मादर",
    state="छत्तीसगढ़"
)

# Less accurate
result = validator.validate_hierarchy(
    village="मादर"
    # No state - may match wrong village in different state
)
```

### 2. Use Parent Codes for Disambiguation

```python
# Good - specific to block
matches = validator.fuzzy_match_location(
    name="मादर",
    level="village",
    parent_lgd_code="3151"
)

# May return villages from other blocks
matches = validator.fuzzy_match_location(
    name="मादर",
    level="village"
)
```

### 3. Check Confidence Scores

```python
result = validator.validate_hierarchy(
    village="Madur",  # Misspelled
    district="Bastar"
)

if result["confidence"] < 0.7:
    # Ask user to confirm
    suggestions = validator.suggest_corrections("Madur", "village")
    print(f"Did you mean: {suggestions}")
```

### 4. Handle Validation Failures Gracefully

```python
result = validator.validate_hierarchy(
    village="UnknownVillage",
    district="बस्तर"
)

if not result["is_valid"]:
    # Log issues
    logger.warning(f"Validation failed: {result['issues']}")

    # Try fuzzy matching
    suggestions = validator.suggest_corrections(
        "UnknownVillage",
        "village"
    )

    if suggestions:
        print(f"Suggestions: {suggestions}")
```

## API Integration

### REST Endpoint Example

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/api/location/lgd/validate")
async def validate_with_lgd(
    village: str,
    district: str,
    state: str = "Chhattisgarh",
    db: Session = Depends(get_db)
):
    """Validate location against LGD data."""
    validator = LGDLocationValidator(db_session=db)

    result = validator.validate_hierarchy(
        village=village,
        district=district,
        state=state
    )

    return result

@router.get("/api/location/lgd/search")
async def search_lgd(
    query: str,
    level: str,
    parent_lgd_code: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search LGD database with autocomplete."""
    validator = LGDLocationValidator(db_session=db)

    matches = validator.fuzzy_match_location(
        name=query,
        level=level,
        parent_lgd_code=parent_lgd_code,
        limit=limit
    )

    return matches
```

## Future Enhancements

### 1. Machine Learning Integration

- Train model on user corrections
- Learn common misspelling patterns
- Improve phonetic matching accuracy

### 2. Real-time Updates

- Subscribe to LGD data updates
- Automatic quarterly refresh
- Alert on administrative changes

### 3. GPS Integration

- Combine GPS coordinates with LGD validation
- Verify location is within correct boundaries
- Detect GPS spoofing

### 4. Multi-language Support

- Support more Indian languages
- Handle regional dialects
- Improve transliteration accuracy

## Troubleshooting

### Issue: Low Confidence Scores

**Cause**: Input doesn't closely match LGD data

**Solution**:
```python
# Check suggestions
suggestions = validator.suggest_corrections(name, level)

# Try variations
for suggestion in suggestions:
    result = validator.validate_hierarchy(
        village=suggestion,
        district=district
    )
    if result["confidence"] > 0.8:
        break
```

### Issue: No Matches Found

**Cause**: Location not in database or significant misspelling

**Solution**:
```python
# Broaden search
matches = validator.fuzzy_match_location(
    name=name,
    level=level
    # Don't restrict by parent
)

# Check all matches
for match in matches:
    print(f"{match['name']} - {match['confidence']}")
```

### Issue: Multiple Matches

**Cause**: Common village name exists in multiple locations

**Solution**:
```python
# Use parent for disambiguation
matches = validator.fuzzy_match_location(
    name="मादर",
    level="village",
    parent_lgd_code=block_lgd_code  # Restrict to specific block
)
```

## Support

- **Documentation**: `/docs/LGD_INTEGRATION_PLAN.md`
- **Tests**: `/tests/test_lgd_location_validator.py`
- **Source**: `/app/services/lgd_location_validator.py`

For issues or questions, contact the development team.
