# LGD Integration Database Migration

## Migration Details

**Migration ID**: `6f8cc5330bbf`
**File**: `/Users/diptendu/boloo app/boloo-app/backend/alembic/versions/6f8cc5330bbf_add_lgd_integration_tables.py`
**Created**: 2025-11-17 16:12:06
**Revises**: `2324c72c4cf5`

## Overview

This migration implements the database schema for Local Government Directory (LGD) integration, enabling validation of administrative boundaries against authoritative government data from https://lgdirectory.gov.in.

## Changes Summary

### New Tables Created

#### 1. `lgd_admin_units`
Central table storing all LGD administrative units (states, districts, blocks, panchayats, villages).

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `lgd_code` (VARCHAR(20), UNIQUE, NOT NULL) - Official LGD identifier
- `name_en` (VARCHAR(255), NOT NULL) - English name
- `name_hi` (VARCHAR(255)) - Hindi name
- `name_local` (VARCHAR(255)) - Local language name
- `level` (VARCHAR(20), NOT NULL) - Administrative level: state/district/block/panchayat/village
- `parent_lgd_code` (VARCHAR(20), FK) - Parent unit's LGD code
- `state_code` (VARCHAR(5)) - State identifier
- `district_code` (VARCHAR(5)) - District identifier
- `census_code` (VARCHAR(20)) - Census 2011 code
- `is_active` (BOOLEAN, DEFAULT true)
- `created_at` (TIMESTAMP, DEFAULT now())
- `updated_at` (TIMESTAMP, DEFAULT now())

**Indexes:**
- `idx_lgd_name_en` - Fast name lookups (English)
- `idx_lgd_name_hi` - Fast name lookups (Hindi)
- `idx_lgd_level` - Filter by administrative level
- `idx_lgd_parent` - Hierarchical queries
- `idx_lgd_state_code` - State-level filtering
- `idx_lgd_district_code` - District-level filtering
- `idx_lgd_is_active` - Active/inactive filtering
- `idx_lgd_level_parent` (COMPOSITE) - Efficient child lookups

**Self-Referential Foreign Key:**
- `parent_lgd_code` → `lgd_admin_units.lgd_code` (ON DELETE SET NULL)

---

#### 2. `lgd_name_aliases`
Stores name variations and aliases for fuzzy matching (handles spelling variations, transliterations).

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `lgd_code` (VARCHAR(20), NOT NULL, FK) - Reference to lgd_admin_units
- `alias` (VARCHAR(255), NOT NULL) - Alternative name/spelling
- `language` (VARCHAR(10)) - Language code: en/hi/local
- `source` (VARCHAR(50)) - Data source: lgd/census/osm/user_report
- `confidence` (FLOAT, DEFAULT 1.0) - Match confidence score

**Indexes:**
- `idx_alias_name` - Fast alias lookups
- `idx_alias_lgd_code` - Reverse lookup to admin units
- `idx_alias_language` - Language-based filtering
- `idx_alias_name_lang` (COMPOSITE) - Combined name + language queries

**Foreign Key:**
- `lgd_code` → `lgd_admin_units.lgd_code` (ON DELETE CASCADE)

---

### Existing Table Modifications

#### `users` Table - Added LGD Columns

**Location LGD Codes:**
- `location_village_lgd_code` (VARCHAR(20))
- `location_panchayat_lgd_code` (VARCHAR(20))
- `location_block_lgd_code` (VARCHAR(20))
- `location_district_lgd_code` (VARCHAR(20))
- `location_state_lgd_code` (VARCHAR(20))

**Validation Metadata:**
- `lgd_validated` (BOOLEAN, DEFAULT false) - Whether location is LGD-validated
- `lgd_validation_confidence` (FLOAT) - Validation confidence score (0-1)
- `lgd_validation_timestamp` (TIMESTAMP) - When validation occurred

**Indexes:**
- `ix_users_village_lgd` - Fast village lookups
- `ix_users_block_lgd` - Fast block lookups
- `ix_users_district_lgd` - Fast district lookups

**Foreign Keys:**
- All 5 LGD code columns reference `lgd_admin_units.lgd_code` (ON DELETE SET NULL)

---

#### `cases` Table - Added LGD Columns

**Location LGD Codes:**
- `location_village_lgd_code` (VARCHAR(20))
- `location_block_lgd_code` (VARCHAR(20))
- `location_district_lgd_code` (VARCHAR(20))

**Validation Metadata:**
- `lgd_validated` (BOOLEAN, DEFAULT false)
- `lgd_validation_confidence` (FLOAT)

**Indexes:**
- `ix_cases_village_lgd` - Fast village lookups
- `ix_cases_block_lgd` - Fast block lookups
- `ix_cases_district_lgd` - Fast district lookups

**Foreign Keys:**
- All 3 LGD code columns reference `lgd_admin_units.lgd_code` (ON DELETE SET NULL)

---

## Performance Optimizations

### Query Patterns Supported

1. **Hierarchical Queries** (Fast with `idx_lgd_level_parent`):
   ```sql
   SELECT * FROM lgd_admin_units
   WHERE level = 'village' AND parent_lgd_code = '3151';
   ```

2. **Name Lookups** (Fast with `idx_lgd_name_en`, `idx_lgd_name_hi`):
   ```sql
   SELECT * FROM lgd_admin_units
   WHERE name_en LIKE 'Bastar%';
   ```

3. **Fuzzy Matching** (Fast with `idx_alias_name_lang`):
   ```sql
   SELECT * FROM lgd_name_aliases
   WHERE alias ILIKE '%madar%' AND language = 'hi';
   ```

4. **User Location Aggregation** (Fast with `ix_users_district_lgd`):
   ```sql
   SELECT location_district_lgd_code, COUNT(*)
   FROM users
   WHERE lgd_validated = true
   GROUP BY location_district_lgd_code;
   ```

---

## Running the Migration

### Apply Migration
```bash
cd backend
alembic upgrade head
```

### Verify Migration
```bash
alembic current
# Should show: 6f8cc5330bbf (head)
```

### Rollback (if needed)
```bash
alembic downgrade -1
```

---

## Post-Migration Steps

### 1. Import LGD Data
After running the migration, populate the tables:

```bash
# Download Chhattisgarh LGD data
python -m app.scripts.lgd_importer --state "Chhattisgarh"

# Or import from local file
python -m app.scripts.lgd_importer --file data/chhattisgarh_lgd.csv
```

### 2. Build Aliases
Generate name aliases for fuzzy matching:

```bash
python -m app.scripts.lgd_alias_builder --state "Chhattisgarh"
```

### 3. Validate Existing Data (Optional)
Backfill LGD codes for existing users/cases:

```bash
python -m app.scripts.backfill_lgd_codes --table users --limit 1000
python -m app.scripts.backfill_lgd_codes --table cases --limit 1000
```

---

## Integration with Existing Code

### Location Validator Enhancement
The existing `HybridLocationValidator` will now:
1. Geocode location (Mappls/Nominatim)
2. **Validate against LGD data** (new)
3. Store LGD codes in user/case records
4. Return confidence score combining both sources

### Expected Accuracy Improvement
- **Before**: 70-85% (geocoding only)
- **After**: 95%+ (geocoding + LGD validation)

---

## Data Model Relationships

```
lgd_admin_units (self-referential tree)
    ├─ Chhattisgarh (state, lgd_code: "22")
    │   └─ Bastar (district, parent: "22")
    │       └─ Lohandiguda (block, parent: district_code)
    │           └─ Madar GP (panchayat, parent: block_code)
    │               └─ Madar Village (village, parent: panchayat_code)
    │
    └─ lgd_name_aliases (1:many)
        ├─ "बस्तर" (alias for Bastar, language: hi)
        ├─ "Baster" (alias for Bastar, language: en)
        └─ "बस्‍तर" (alias for Bastar, language: hi, source: user_report)

users
    ├─ location_village_lgd_code → lgd_admin_units.lgd_code
    ├─ location_panchayat_lgd_code → lgd_admin_units.lgd_code
    ├─ location_block_lgd_code → lgd_admin_units.lgd_code
    ├─ location_district_lgd_code → lgd_admin_units.lgd_code
    └─ location_state_lgd_code → lgd_admin_units.lgd_code

cases
    ├─ location_village_lgd_code → lgd_admin_units.lgd_code
    ├─ location_block_lgd_code → lgd_admin_units.lgd_code
    └─ location_district_lgd_code → lgd_admin_units.lgd_code
```

---

## Storage Requirements

### Estimated Sizes (Chhattisgarh)

- **lgd_admin_units**: ~20,000 rows
  - 1 state + 28 districts + ~150 blocks + ~5,000 panchayats + ~15,000 villages
  - Size: ~5 MB (with indexes: ~15 MB)

- **lgd_name_aliases**: ~50,000 rows
  - ~2-3 aliases per admin unit
  - Size: ~10 MB (with indexes: ~20 MB)

- **users** (additional columns): +8 columns per row
  - Size: Negligible (~20 bytes per user)

- **cases** (additional columns): +5 columns per row
  - Size: Negligible (~15 bytes per case)

**Total Additional Storage**: ~35-40 MB for Chhattisgarh data

---

## Security Considerations

1. **Foreign Key Constraints**: Prevent orphaned LGD codes
2. **ON DELETE SET NULL**: Graceful handling of deleted admin units
3. **ON DELETE CASCADE**: Aliases automatically removed with parent unit
4. **Indexes**: Prevent full table scans on large datasets
5. **Validation Flags**: Track data quality (`lgd_validated`, `confidence`)

---

## Maintenance

### Quarterly LGD Data Updates
LGD data is updated quarterly by the government. Schedule:

```bash
# Cron job to check for updates (every 3 months)
0 0 1 */3 * cd /app && python -m app.scripts.lgd_update_checker
```

### Manual Update Process
```bash
# 1. Download latest data
python -m app.scripts.lgd_importer --state "Chhattisgarh" --force-update

# 2. Merge with existing data (preserves user-reported aliases)
python -m app.scripts.lgd_merge --strategy smart

# 3. Re-validate existing records
python -m app.scripts.revalidate_lgd --table users --where "lgd_validated = true"
```

---

## Troubleshooting

### Migration Fails: Foreign Key Error
**Issue**: Existing users/cases have location data that doesn't match LGD codes.

**Solution**: Migration uses nullable columns with `ON DELETE SET NULL`, so this shouldn't happen. If it does:
```bash
# Set all LGD codes to NULL first
alembic downgrade -1
# Fix data manually
# Re-run migration
alembic upgrade head
```

### Slow Queries After Migration
**Issue**: Missing indexes or table statistics outdated.

**Solution**:
```sql
-- Re-analyze tables
ANALYZE lgd_admin_units;
ANALYZE lgd_name_aliases;
ANALYZE users;
ANALYZE cases;

-- Check index usage
SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'public';
```

---

## References

- **LGD Integration Plan**: `/Users/diptendu/boloo app/boloo-app/docs/LGD_INTEGRATION_PLAN.md`
- **LGD Portal**: https://lgdirectory.gov.in/
- **Open Data Portal**: https://data.gov.in/
- **Alembic Docs**: https://alembic.sqlalchemy.org/

---

## Next Steps

1. ✅ Migration created (this file)
2. ⏭️ Run migration: `alembic upgrade head`
3. ⏭️ Import Chhattisgarh LGD data
4. ⏭️ Implement `LGDLocationValidator` service
5. ⏭️ Create API endpoints for LGD search
6. ⏭️ Update mobile app to display LGD codes
7. ⏭️ Integrate with Smart Chat location confirmation
