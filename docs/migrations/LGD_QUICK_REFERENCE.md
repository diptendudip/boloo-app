# LGD Integration Quick Reference Card

## Table Structure Cheat Sheet

### `lgd_admin_units` - Main LGD Data
```sql
lgd_code (PK, unique)     -- "398" (Bastar district)
name_en                    -- "Bastar"
name_hi                    -- "बस्तर"
level                      -- state/district/block/panchayat/village
parent_lgd_code (FK)       -- Parent unit's code
state_code, district_code  -- Quick state/district lookup
is_active                  -- false = deprecated unit
```

### `lgd_name_aliases` - Fuzzy Matching
```sql
lgd_code (FK)  -- References lgd_admin_units
alias          -- "Baster", "बस्‍तर" (variations)
language       -- en/hi/local
source         -- lgd/census/osm/user_report
confidence     -- 0.0-1.0
```

### `users` - LGD Columns Added
```sql
location_village_lgd_code
location_panchayat_lgd_code
location_block_lgd_code
location_district_lgd_code
location_state_lgd_code
lgd_validated             -- true/false
lgd_validation_confidence -- 0.0-1.0
lgd_validation_timestamp
```

### `cases` - LGD Columns Added
```sql
location_village_lgd_code
location_block_lgd_code
location_district_lgd_code
lgd_validated
lgd_validation_confidence
```

---

## Common Queries

### 1. Find Village by Name
```sql
SELECT lgd_code, name_en, name_hi, parent_lgd_code
FROM lgd_admin_units
WHERE name_en ILIKE '%madar%' AND level = 'village';
```

### 2. Get Full Hierarchy (Village → State)
```sql
WITH RECURSIVE hierarchy AS (
    SELECT lgd_code, name_en, level, parent_lgd_code, 1 as depth
    FROM lgd_admin_units WHERE lgd_code = '234567'  -- Village
    UNION ALL
    SELECT p.lgd_code, p.name_en, p.level, p.parent_lgd_code, h.depth + 1
    FROM lgd_admin_units p
    JOIN hierarchy h ON p.lgd_code = h.parent_lgd_code
)
SELECT * FROM hierarchy ORDER BY depth DESC;
```

### 3. Fuzzy Search with Aliases
```sql
SELECT DISTINCT u.lgd_code, u.name_en, a.alias, a.confidence
FROM lgd_name_aliases a
JOIN lgd_admin_units u ON a.lgd_code = u.lgd_code
WHERE a.alias ILIKE '%baster%'  -- Misspelling
ORDER BY a.confidence DESC;
```

### 4. Validate User Location
```sql
SELECT
    u.id,
    u.location_village,
    v.name_en as official_village_name,
    u.lgd_validation_confidence
FROM users u
JOIN lgd_admin_units v ON u.location_village_lgd_code = v.lgd_code
WHERE u.id = 123;
```

### 5. Count Users by District
```sql
SELECT
    d.name_en,
    COUNT(*) as user_count
FROM users u
JOIN lgd_admin_units d ON u.location_district_lgd_code = d.lgd_code
WHERE u.lgd_validated = true
GROUP BY d.name_en
ORDER BY user_count DESC;
```

---

## Python Integration Examples

### Check if Village Exists
```python
from app.models import LGDAdminUnit

village = db.query(LGDAdminUnit).filter(
    LGDAdminUnit.name_en.ilike("%madar%"),
    LGDAdminUnit.level == "village",
    LGDAdminUnit.is_active == True
).first()

if village:
    print(f"Found: {village.name_en} (LGD: {village.lgd_code})")
```

### Get Hierarchy
```python
def get_hierarchy(lgd_code: str, db: Session) -> List[LGDAdminUnit]:
    """Get full hierarchy from village to state"""
    units = []
    current = db.query(LGDAdminUnit).filter_by(lgd_code=lgd_code).first()

    while current:
        units.append(current)
        if current.parent_lgd_code:
            current = db.query(LGDAdminUnit).filter_by(
                lgd_code=current.parent_lgd_code
            ).first()
        else:
            break

    return units
```

### Validate and Store LGD Codes
```python
def validate_and_store_lgd(user: User, location_data: dict, db: Session):
    """Validate location against LGD and store codes"""
    validator = LGDLocationValidator(db)

    result = validator.validate_hierarchy(
        village=location_data.get("village"),
        block=location_data.get("block"),
        district=location_data.get("district"),
        state="Chhattisgarh"
    )

    if result["is_valid"]:
        user.location_village_lgd_code = result["lgd_codes"]["village"]
        user.location_block_lgd_code = result["lgd_codes"]["block"]
        user.location_district_lgd_code = result["lgd_codes"]["district"]
        user.lgd_validated = True
        user.lgd_validation_confidence = result["confidence"]
        user.lgd_validation_timestamp = datetime.utcnow()
        db.commit()

    return result
```

### Fuzzy Search
```python
def search_location(query: str, level: str, db: Session):
    """Search with fuzzy matching"""
    # Direct match
    direct = db.query(LGDAdminUnit).filter(
        LGDAdminUnit.name_en.ilike(f"%{query}%"),
        LGDAdminUnit.level == level,
        LGDAdminUnit.is_active == True
    ).all()

    # Alias match
    alias = db.query(LGDAdminUnit).join(LGDNameAlias).filter(
        LGDNameAlias.alias.ilike(f"%{query}%"),
        LGDAdminUnit.level == level,
        LGDAdminUnit.is_active == True
    ).all()

    # Combine and deduplicate
    results = {u.lgd_code: u for u in direct + alias}
    return list(results.values())
```

---

## API Endpoint Examples

### GET /api/location/lgd/search
```bash
curl "http://localhost:8000/api/location/lgd/search?query=madar&level=village&limit=10"
```

**Response:**
```json
[
  {
    "lgd_code": "234567",
    "name_en": "Madar",
    "name_hi": "मादर",
    "level": "village",
    "parent_lgd_code": "123456",
    "hierarchy": {
      "panchayat": "Madar GP",
      "block": "Lohandiguda",
      "district": "Bastar"
    }
  }
]
```

### GET /api/location/lgd/hierarchy/{lgd_code}
```bash
curl "http://localhost:8000/api/location/lgd/hierarchy/234567"
```

**Response:**
```json
{
  "village": {"lgd_code": "234567", "name_en": "Madar"},
  "panchayat": {"lgd_code": "123456", "name_en": "Madar GP"},
  "block": {"lgd_code": "3151", "name_en": "Lohandiguda"},
  "district": {"lgd_code": "398", "name_en": "Bastar"},
  "state": {"lgd_code": "22", "name_en": "Chhattisgarh"}
}
```

### POST /api/location/lgd/validate
```bash
curl -X POST "http://localhost:8000/api/location/lgd/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "village": "Madar",
    "block": "Lohandiguda",
    "district": "Bastar",
    "state": "Chhattisgarh"
  }'
```

**Response:**
```json
{
  "is_valid": true,
  "lgd_codes": {
    "village": "234567",
    "panchayat": "123456",
    "block": "3151",
    "district": "398",
    "state": "22"
  },
  "standardized_names": {
    "village": "मादर",
    "panchayat": "मादर ग्राम पंचायत",
    "block": "लोहंडीगुड़ा",
    "district": "बस्तर",
    "state": "छत्तीसगढ़"
  },
  "confidence": 0.98,
  "issues": []
}
```

---

## Migration Commands

### Apply Migration
```bash
cd backend
alembic upgrade head
```

### Check Status
```bash
alembic current
alembic history --verbose
```

### Rollback
```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade 2324c72c4cf5  # Rollback to specific version
```

### Validate Migration
```bash
python -m py_compile alembic/versions/6f8cc5330bbf_*.py
alembic check
```

---

## Import Commands

### Import LGD Data
```bash
# Download and import Chhattisgarh data
python -m app.scripts.lgd_importer --state "Chhattisgarh"

# Import from local file
python -m app.scripts.lgd_importer --file data/chhattisgarh.csv

# Import specific district
python -m app.scripts.lgd_importer --state "Chhattisgarh" --district "Bastar"
```

### Build Aliases
```bash
# Generate aliases for fuzzy matching
python -m app.scripts.lgd_alias_builder --state "Chhattisgarh"

# Add manual aliases
python -m app.scripts.lgd_alias_builder --add-alias \
  --lgd-code "398" \
  --alias "Baster" \
  --language "en" \
  --source "user_report"
```

### Backfill Existing Data
```bash
# Validate and add LGD codes to existing users
python -m app.scripts.backfill_lgd_codes --table users --limit 1000

# Dry run (preview only)
python -m app.scripts.backfill_lgd_codes --table users --dry-run
```

---

## Index Usage Monitoring

### Check Index Performance
```sql
-- Most used indexes
SELECT
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('lgd_admin_units', 'lgd_name_aliases', 'users', 'cases')
ORDER BY idx_scan DESC;

-- Unused indexes (candidates for removal)
SELECT indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND tablename IN ('lgd_admin_units', 'lgd_name_aliases');
```

### Reanalyze Tables
```sql
ANALYZE lgd_admin_units;
ANALYZE lgd_name_aliases;
ANALYZE users;
ANALYZE cases;
```

---

## Troubleshooting

### Problem: Slow queries
**Solution:**
```sql
-- Check missing indexes
EXPLAIN ANALYZE
SELECT * FROM lgd_admin_units WHERE name_en ILIKE '%madar%';

-- Rebuild statistics
ANALYZE lgd_admin_units;
VACUUM ANALYZE lgd_admin_units;
```

### Problem: Foreign key constraint violation
**Solution:**
```sql
-- Find invalid references
SELECT DISTINCT location_village_lgd_code
FROM users
WHERE location_village_lgd_code IS NOT NULL
  AND location_village_lgd_code NOT IN (SELECT lgd_code FROM lgd_admin_units);

-- Fix by setting to NULL or correcting code
UPDATE users
SET location_village_lgd_code = NULL
WHERE location_village_lgd_code NOT IN (SELECT lgd_code FROM lgd_admin_units);
```

### Problem: Low validation confidence
**Solution:**
```python
# Re-validate with fresh data
from app.services.lgd_location_validator import LGDLocationValidator

validator = LGDLocationValidator(db)
result = validator.validate_hierarchy(
    village=user.location_village,
    block=user.location_block,
    district=user.location_district
)

# Update user with new confidence score
user.lgd_validation_confidence = result["confidence"]
```

---

## Performance Tips

1. **Always filter by `is_active = true`** to skip deprecated units
2. **Use composite indexes** for `(level, parent_lgd_code)` queries
3. **Cache common lookups** (e.g., district list) in Redis
4. **Batch imports** in transactions of 1000-5000 records
5. **Use ILIKE for case-insensitive** searches (faster than LOWER())
6. **Index foreign keys** for join performance (already done in migration)

---

## Key Files

- **Migration**: `backend/alembic/versions/6f8cc5330bbf_add_lgd_integration_tables.py`
- **Models**: `backend/app/models/lgd.py` (to be created)
- **Validator**: `backend/app/services/lgd_location_validator.py` (to be created)
- **Importer**: `backend/app/scripts/lgd_importer.py` (to be created)
- **API Router**: `backend/app/routers/location.py` (to be extended)
- **Documentation**: `docs/LGD_INTEGRATION_PLAN.md`
- **Example Queries**: `docs/migrations/lgd_example_queries.sql`

---

## Support

- **Issues**: Check `docs/migrations/LGD_MIGRATION_README.md`
- **Examples**: `docs/migrations/lgd_example_queries.sql`
- **Plan**: `docs/LGD_INTEGRATION_PLAN.md`
- **LGD Portal**: https://lgdirectory.gov.in/
