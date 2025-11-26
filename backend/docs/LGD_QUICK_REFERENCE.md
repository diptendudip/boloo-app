# LGD Validator - Quick Reference

## Import

```python
from app.services.lgd_location_validator import LGDLocationValidator
```

## Basic Usage

### 1. Initialize Validator

```python
# With database (production)
validator = LGDLocationValidator(db_session=db)

# Without database (testing)
validator = LGDLocationValidator(db_session=None)
```

### 2. Validate Hierarchy

```python
result = validator.validate_hierarchy(
    village="मादर",
    block="लोहंडीगुड़ा",
    district="बस्तर",
    state="छत्तीसगढ़"
)

# Check result
if result["is_valid"]:
    print(f"✅ Valid location - Confidence: {result['confidence']}")
    print(f"LGD Codes: {result['lgd_codes']}")
else:
    print(f"❌ Invalid - Issues: {result['issues']}")
```

### 3. Fuzzy Match

```python
matches = validator.fuzzy_match_location(
    name="Bastar",
    level="district",
    limit=3
)

for match in matches:
    print(f"{match['name']} - {match['confidence']:.2f}")
```

### 4. Get Suggestions

```python
suggestions = validator.suggest_corrections(
    name="Baster",
    level="district"
)

print(f"Did you mean: {', '.join(suggestions)}")
```

### 5. Enrich Location

```python
location = {
    "village": "मादर",
    "district": "बस्तर"
}

enriched = validator.enrich_with_lgd_data(location)

print(f"Village LGD Code: {enriched.get('village_lgd_code')}")
print(f"Confidence: {enriched.get('lgd_confidence')}")
```

## Integration with HybridValidator

```python
from app.services.location_validator import HybridLocationValidator

validator = HybridLocationValidator(db_session=db)

result = validator.validate_and_enrich_location(
    location_text="मादर, बस्तर",
    enable_lgd_validation=True
)

print(f"GPS: ({result['lat']}, {result['lng']})")
print(f"LGD Codes: {result['lgd_codes']}")
print(f"Confidence: {result['confidence']}")
```

## Response Structure

### validate_hierarchy()

```python
{
    "is_valid": bool,
    "lgd_codes": {
        "state": "22",
        "district": "398",
        "block": "3151",
        "panchayat": "123456",
        "village": "234567"
    },
    "standardized_names": {
        "state": "छत्तीसगढ़",
        "district": "बस्तर",
        "block": "लोहंडीगुड़ा",
        "panchayat": "मादर ग्राम पंचायत",
        "village": "मादर"
    },
    "confidence": 0.95,
    "issues": [],
    "match_details": {
        "village_match_type": "exact|fuzzy|phonetic",
        "village_match_confidence": 0.95
    }
}
```

### fuzzy_match_location()

```python
[
    {
        "lgd_code": "398",
        "name": "बस्तर",
        "name_en": "Bastar",
        "match_type": "exact|fuzzy|phonetic",
        "confidence": 0.85,
        "edit_distance": 1,
        "similarity_ratio": 0.87
    }
]
```

## Confidence Levels

| Score | Level | Action |
|-------|-------|--------|
| 1.0 | Exact | Accept automatically |
| 0.9-0.99 | High | Accept with notification |
| 0.7-0.89 | Medium | Ask user to confirm |
| 0.6-0.69 | Low | Show suggestions |
| < 0.6 | Very Low | Request manual entry |

## Common Patterns

### Check if location exists

```python
result = validator.validate_hierarchy(
    village=village_name,
    district=district_name
)

exists = result["is_valid"] and result["confidence"] >= 0.7
```

### Handle misspellings

```python
result = validator.validate_hierarchy(
    village=user_input,
    district=district
)

if not result["is_valid"] or result["confidence"] < 0.7:
    suggestions = validator.suggest_corrections(
        user_input,
        "village"
    )
    # Show suggestions to user
```

### Search with autocomplete

```python
matches = validator.fuzzy_match_location(
    name=partial_input,
    level="village",
    parent_lgd_code=block_code,
    limit=10
)

# Return matches for autocomplete dropdown
```

### Validate full hierarchy

```python
result = validator.validate_hierarchy(
    village=form_data["village"],
    panchayat=form_data.get("panchayat"),
    block=form_data["block"],
    district=form_data["district"],
    state=form_data.get("state", "Chhattisgarh")
)

if not result["is_valid"]:
    # Show which fields are incorrect
    for issue in result["issues"]:
        print(f"Error: {issue}")
```

## Tips

### 1. Always provide state for accuracy

```python
# ✅ Good
result = validator.validate_hierarchy(
    village="मादर",
    state="छत्तीसगढ़"
)

# ❌ Less accurate
result = validator.validate_hierarchy(
    village="मादर"
)
```

### 2. Use parent codes for disambiguation

```python
# Multiple villages named "मादर"
matches = validator.fuzzy_match_location(
    name="मादर",
    level="village",
    parent_lgd_code=block_lgd_code  # Narrow to specific block
)
```

### 3. Check confidence before accepting

```python
result = validator.validate_hierarchy(...)

if result["confidence"] < 0.7:
    # Ask user to verify
    suggestions = validator.suggest_corrections(...)
```

### 4. Handle validation failures gracefully

```python
try:
    result = validator.validate_hierarchy(...)

    if not result["is_valid"]:
        # Show user-friendly error
        if result["issues"]:
            error = result["issues"][0]
        else:
            error = "Location not found in database"

except Exception as e:
    # Log error but don't crash
    logger.error(f"Validation error: {e}")
    # Fall back to basic validation
```

## Testing

### Run tests

```bash
# All tests
pytest tests/test_lgd_location_validator.py -v

# Specific test
pytest tests/test_lgd_location_validator.py::TestLGDLocationValidator::test_validate_hierarchy_exact_match -v

# With coverage
pytest tests/test_lgd_location_validator.py --cov=app.services.lgd_location_validator
```

### Run demo

```bash
python3 examples/lgd_validator_demo.py
```

## Troubleshooting

### Low confidence scores

**Problem**: Getting confidence < 0.7

**Solutions**:
1. Check spelling
2. Try suggestions: `validator.suggest_corrections()`
3. Try fuzzy matching: `validator.fuzzy_match_location()`
4. Check if location exists in database

### No matches found

**Problem**: `fuzzy_match_location()` returns empty list

**Solutions**:
1. Verify level is correct ("village", "district", etc.)
2. Remove parent filter temporarily
3. Try different spelling variations
4. Check if location is in database

### Validation always fails

**Problem**: `is_valid` always False

**Solutions**:
1. Check database connection
2. Verify LGD data is imported
3. Check for typos in input
4. Try with mock data first

## Files

- **Service**: `app/services/lgd_location_validator.py`
- **Tests**: `tests/test_lgd_location_validator.py`
- **Demo**: `examples/lgd_validator_demo.py`
- **Docs**: `docs/LGD_VALIDATOR_USAGE.md`
- **Plan**: `docs/LGD_INTEGRATION_PLAN.md`

## API Endpoints (Future)

```python
# Validate location
POST /api/location/lgd/validate
Body: {"village": "मादर", "district": "बस्तर"}

# Search with autocomplete
GET /api/location/lgd/search?query=Baster&level=district&limit=10

# Get hierarchy
GET /api/location/lgd/hierarchy/398

# Enrich location
POST /api/location/lgd/enrich
Body: {"village": "मादर", "district": "बस्तर"}
```

## Need Help?

1. Check: `docs/LGD_VALIDATOR_USAGE.md`
2. Run: `python3 examples/lgd_validator_demo.py`
3. Test: `pytest tests/test_lgd_location_validator.py -v`
4. Contact: Development team
