-- LGD Integration Example Queries
-- These queries demonstrate common usage patterns for the LGD tables

-- ============================================================================
-- 1. HIERARCHICAL QUERIES
-- ============================================================================

-- Get all villages in a specific panchayat
SELECT
    lgd_code,
    name_en,
    name_hi,
    census_code
FROM lgd_admin_units
WHERE level = 'village'
    AND parent_lgd_code = '123456'  -- Panchayat LGD code
    AND is_active = true
ORDER BY name_en;

-- Get complete hierarchy for a village (recursively up to state)
WITH RECURSIVE hierarchy AS (
    -- Start with village
    SELECT
        lgd_code,
        name_en,
        name_hi,
        level,
        parent_lgd_code,
        1 as depth
    FROM lgd_admin_units
    WHERE lgd_code = '234567'  -- Village LGD code

    UNION ALL

    -- Recursively get parents
    SELECT
        p.lgd_code,
        p.name_en,
        p.name_hi,
        p.level,
        p.parent_lgd_code,
        h.depth + 1
    FROM lgd_admin_units p
    INNER JOIN hierarchy h ON p.lgd_code = h.parent_lgd_code
)
SELECT
    lgd_code,
    name_en,
    name_hi,
    level,
    depth
FROM hierarchy
ORDER BY depth DESC;

-- Get all children of a district (blocks, panchayats, villages)
SELECT
    level,
    COUNT(*) as count
FROM lgd_admin_units
WHERE parent_lgd_code = '398'  -- Bastar district code
    OR lgd_code IN (
        SELECT lgd_code FROM lgd_admin_units
        WHERE parent_lgd_code IN (
            SELECT lgd_code FROM lgd_admin_units
            WHERE parent_lgd_code = '398'
        )
    )
GROUP BY level;


-- ============================================================================
-- 2. NAME LOOKUPS & FUZZY MATCHING
-- ============================================================================

-- Search for villages by name (English)
SELECT
    lgd_code,
    name_en,
    name_hi,
    level,
    parent_lgd_code
FROM lgd_admin_units
WHERE name_en ILIKE '%madar%'
    AND level = 'village'
    AND is_active = true
ORDER BY name_en;

-- Search using aliases (handles spelling variations)
SELECT DISTINCT
    a.lgd_code,
    u.name_en,
    u.name_hi,
    u.level,
    a.alias,
    a.confidence
FROM lgd_name_aliases a
INNER JOIN lgd_admin_units u ON a.lgd_code = u.lgd_code
WHERE a.alias ILIKE '%baster%'  -- Common misspelling of Bastar
    AND u.is_active = true
ORDER BY a.confidence DESC, u.name_en;

-- Multi-language search (English OR Hindi)
SELECT
    lgd_code,
    name_en,
    name_hi,
    level
FROM lgd_admin_units
WHERE (name_en ILIKE '%बस्तर%' OR name_hi ILIKE '%बस्तर%')
    AND level = 'district'
    AND is_active = true;


-- ============================================================================
-- 3. VALIDATION QUERIES
-- ============================================================================

-- Validate village → panchayat → block → district hierarchy
SELECT
    v.lgd_code as village_code,
    v.name_en as village_name,
    p.lgd_code as panchayat_code,
    p.name_en as panchayat_name,
    b.lgd_code as block_code,
    b.name_en as block_name,
    d.lgd_code as district_code,
    d.name_en as district_name
FROM lgd_admin_units v
INNER JOIN lgd_admin_units p ON v.parent_lgd_code = p.lgd_code AND p.level = 'panchayat'
INNER JOIN lgd_admin_units b ON p.parent_lgd_code = b.lgd_code AND b.level = 'block'
INNER JOIN lgd_admin_units d ON b.parent_lgd_code = d.lgd_code AND d.level = 'district'
WHERE v.lgd_code = '234567'  -- Village code to validate
    AND v.level = 'village';

-- Check if a village belongs to a specific district (any path)
WITH RECURSIVE hierarchy AS (
    SELECT lgd_code, parent_lgd_code, level
    FROM lgd_admin_units
    WHERE lgd_code = '234567'  -- Village code

    UNION ALL

    SELECT p.lgd_code, p.parent_lgd_code, p.level
    FROM lgd_admin_units p
    INNER JOIN hierarchy h ON p.lgd_code = h.parent_lgd_code
)
SELECT EXISTS (
    SELECT 1 FROM hierarchy
    WHERE lgd_code = '398'  -- Expected district code
        AND level = 'district'
) as is_valid_hierarchy;


-- ============================================================================
-- 4. USER LOCATION ANALYTICS
-- ============================================================================

-- Count users by district (with LGD validation)
SELECT
    u.location_district_lgd_code,
    l.name_en as district_name,
    COUNT(*) as user_count,
    AVG(u.lgd_validation_confidence) as avg_confidence
FROM users u
INNER JOIN lgd_admin_units l ON u.location_district_lgd_code = l.lgd_code
WHERE u.lgd_validated = true
GROUP BY u.location_district_lgd_code, l.name_en
ORDER BY user_count DESC;

-- Find users with low validation confidence (may need re-validation)
SELECT
    id,
    phone,
    location_village,
    location_village_lgd_code,
    lgd_validation_confidence,
    lgd_validation_timestamp
FROM users
WHERE lgd_validated = true
    AND lgd_validation_confidence < 0.7
ORDER BY lgd_validation_confidence ASC
LIMIT 100;

-- Count users by village (top 10 villages)
SELECT
    v.name_en as village_name,
    v.name_hi as village_name_hi,
    b.name_en as block_name,
    d.name_en as district_name,
    COUNT(u.id) as user_count
FROM users u
INNER JOIN lgd_admin_units v ON u.location_village_lgd_code = v.lgd_code
INNER JOIN lgd_admin_units b ON v.parent_lgd_code = b.lgd_code
INNER JOIN lgd_admin_units d ON b.parent_lgd_code = d.lgd_code
WHERE u.lgd_validated = true
GROUP BY v.name_en, v.name_hi, b.name_en, d.name_en
ORDER BY user_count DESC
LIMIT 10;


-- ============================================================================
-- 5. CASE LOCATION ANALYTICS
-- ============================================================================

-- Count cases by district
SELECT
    c.location_district_lgd_code,
    l.name_en as district_name,
    COUNT(*) as case_count,
    COUNT(CASE WHEN c.status = 'open' THEN 1 END) as open_cases,
    COUNT(CASE WHEN c.status = 'closed' THEN 1 END) as closed_cases
FROM cases c
INNER JOIN lgd_admin_units l ON c.location_district_lgd_code = l.lgd_code
WHERE c.lgd_validated = true
GROUP BY c.location_district_lgd_code, l.name_en
ORDER BY case_count DESC;

-- Find cases and users in the same village
SELECT
    v.name_en as village_name,
    COUNT(DISTINCT u.id) as user_count,
    COUNT(DISTINCT c.id) as case_count
FROM lgd_admin_units v
LEFT JOIN users u ON u.location_village_lgd_code = v.lgd_code
LEFT JOIN cases c ON c.location_village_lgd_code = v.lgd_code
WHERE v.level = 'village'
    AND v.district_code = '398'  -- Bastar district
GROUP BY v.name_en
HAVING COUNT(DISTINCT c.id) > 0
ORDER BY case_count DESC;


-- ============================================================================
-- 6. DATA QUALITY CHECKS
-- ============================================================================

-- Find users with location names but no LGD codes (need validation)
SELECT
    id,
    phone,
    location_village,
    location_block,
    location_district,
    lgd_validated
FROM users
WHERE location_village IS NOT NULL
    AND location_village_lgd_code IS NULL
LIMIT 100;

-- Find orphaned aliases (aliases without valid parent unit)
SELECT
    a.id,
    a.lgd_code,
    a.alias,
    a.source
FROM lgd_name_aliases a
LEFT JOIN lgd_admin_units u ON a.lgd_code = u.lgd_code
WHERE u.lgd_code IS NULL;

-- Find invalid hierarchies (villages without proper parents)
SELECT
    v.lgd_code,
    v.name_en,
    v.parent_lgd_code,
    CASE
        WHEN p.lgd_code IS NULL THEN 'Missing parent'
        WHEN p.level NOT IN ('panchayat', 'block') THEN 'Invalid parent level'
        ELSE 'OK'
    END as issue
FROM lgd_admin_units v
LEFT JOIN lgd_admin_units p ON v.parent_lgd_code = p.lgd_code
WHERE v.level = 'village'
    AND (p.lgd_code IS NULL OR p.level NOT IN ('panchayat', 'block'));


-- ============================================================================
-- 7. AUTOCOMPLETE / SEARCH QUERIES (for API)
-- ============================================================================

-- Village autocomplete (with parent context)
SELECT
    v.lgd_code,
    v.name_en,
    v.name_hi,
    p.name_en as panchayat_name,
    b.name_en as block_name,
    d.name_en as district_name,
    -- Ranking by exact match first, then prefix match
    CASE
        WHEN v.name_en ILIKE 'madar' THEN 1
        WHEN v.name_en ILIKE 'madar%' THEN 2
        ELSE 3
    END as rank
FROM lgd_admin_units v
LEFT JOIN lgd_admin_units p ON v.parent_lgd_code = p.lgd_code
LEFT JOIN lgd_admin_units b ON p.parent_lgd_code = b.lgd_code
LEFT JOIN lgd_admin_units d ON b.parent_lgd_code = d.lgd_code
WHERE v.level = 'village'
    AND v.name_en ILIKE '%madar%'
    AND v.is_active = true
ORDER BY rank, v.name_en
LIMIT 10;

-- District dropdown (for state = Chhattisgarh)
SELECT
    lgd_code,
    name_en,
    name_hi,
    state_code
FROM lgd_admin_units
WHERE level = 'district'
    AND state_code = '22'  -- Chhattisgarh
    AND is_active = true
ORDER BY name_en;


-- ============================================================================
-- 8. PERFORMANCE MONITORING
-- ============================================================================

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND (tablename = 'lgd_admin_units' OR tablename = 'lgd_name_aliases')
ORDER BY idx_scan DESC;

-- Table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
    AND (tablename LIKE 'lgd_%' OR tablename IN ('users', 'cases'))
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Count records by level
SELECT
    level,
    COUNT(*) as count,
    COUNT(CASE WHEN is_active THEN 1 END) as active_count
FROM lgd_admin_units
GROUP BY level
ORDER BY
    CASE level
        WHEN 'state' THEN 1
        WHEN 'district' THEN 2
        WHEN 'block' THEN 3
        WHEN 'panchayat' THEN 4
        WHEN 'village' THEN 5
    END;


-- ============================================================================
-- 9. MAINTENANCE QUERIES
-- ============================================================================

-- Mark inactive admin units (e.g., after government reorganization)
UPDATE lgd_admin_units
SET is_active = false, updated_at = NOW()
WHERE lgd_code IN ('old_code_1', 'old_code_2');

-- Update timestamps (for records modified externally)
UPDATE lgd_admin_units
SET updated_at = NOW()
WHERE updated_at < '2025-01-01';

-- Add new alias (e.g., user reported a common misspelling)
INSERT INTO lgd_name_aliases (lgd_code, alias, language, source, confidence)
VALUES ('398', 'Baster', 'en', 'user_report', 0.8);

-- Re-validate all users in a district
UPDATE users u
SET
    lgd_validated = false,
    lgd_validation_confidence = NULL,
    lgd_validation_timestamp = NULL
WHERE location_district_lgd_code = '398';


-- ============================================================================
-- 10. REPORTING QUERIES
-- ============================================================================

-- Summary report: LGD coverage by state
SELECT
    state_code,
    MAX(CASE WHEN level = 'state' THEN name_en END) as state_name,
    COUNT(CASE WHEN level = 'district' THEN 1 END) as districts,
    COUNT(CASE WHEN level = 'block' THEN 1 END) as blocks,
    COUNT(CASE WHEN level = 'panchayat' THEN 1 END) as panchayats,
    COUNT(CASE WHEN level = 'village' THEN 1 END) as villages
FROM lgd_admin_units
WHERE is_active = true
GROUP BY state_code
ORDER BY state_name;

-- Validation quality report
SELECT
    'Users' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN lgd_validated THEN 1 END) as validated,
    ROUND(AVG(lgd_validation_confidence)::numeric, 3) as avg_confidence,
    COUNT(CASE WHEN lgd_validation_confidence >= 0.9 THEN 1 END) as high_confidence,
    COUNT(CASE WHEN lgd_validation_confidence < 0.7 THEN 1 END) as low_confidence
FROM users
WHERE location_village IS NOT NULL

UNION ALL

SELECT
    'Cases' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN lgd_validated THEN 1 END) as validated,
    ROUND(AVG(lgd_validation_confidence)::numeric, 3) as avg_confidence,
    COUNT(CASE WHEN lgd_validation_confidence >= 0.9 THEN 1 END) as high_confidence,
    COUNT(CASE WHEN lgd_validation_confidence < 0.7 THEN 1 END) as low_confidence
FROM cases
WHERE location_hierarchy IS NOT NULL;
