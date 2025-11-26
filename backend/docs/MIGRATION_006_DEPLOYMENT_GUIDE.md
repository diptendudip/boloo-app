# Migration 006: Add Phone Number to OTP Table - Deployment Guide

## Overview

**Migration ID:** `006_add_phone_number_to_otp`
**Date:** 2025-11-24
**Revises:** `005_add_otp_verification_fields`

This migration fixes the chat interface issue by adding phone number support to the OTP authentication system.

## Problem Statement

The chat interface requires phone-based OTP authentication, but the current OTP table only supports email-based OTP. This causes errors when users try to authenticate via phone.

## Changes Made

### 1. Database Schema Changes

**Table:** `otps`

| Column | Type | Change | Description |
|--------|------|--------|-------------|
| `phone_number` | VARCHAR(20) | **ADDED** | Phone number for OTP (nullable) |
| `email` | VARCHAR(255) | **MODIFIED** | Changed from NOT NULL to nullable |

**Indexes Added:**
- `ix_otps_phone_number` on `otps.phone_number`

### 2. Model Changes

**File:** `/Users/diptendu/boloo app/boloo-app/backend/app/models/otp.py`

- Added `phone_number` field (nullable, indexed)
- Made `email` field nullable
- Updated `__repr__()` to use phone_number or email
- Updated `to_dict()` to include phone_number

### 3. Location Fields Status

**IMPORTANT:** User location fields (`location_state`, `location_district`, `location_block`, `location_panchayat`, `location_village`, `location_street`) were **ALREADY ADDED** in migration `2324c72c4cf5_add_hierarchical_location_to_user_and_`.

The User model already has all required location fields. No additional migration needed.

## Migration Files

1. **Migration:** `/Users/diptendu/boloo app/boloo-app/backend/alembic/versions/006_add_phone_number_to_otp_table.py`
2. **Updated Model:** `/Users/diptendu/boloo app/boloo-app/backend/app/models/otp.py`

## Pre-Deployment Checklist

- [ ] Backup production database
- [ ] Verify all pending migrations are applied: `alembic current`
- [ ] Review migration SQL: `alembic upgrade head --sql`
- [ ] Ensure no active OTP operations during deployment
- [ ] Test rollback procedure in staging

## Deployment Steps

### Step 1: Backup Database

```bash
# Production backup
pg_dump -h <host> -U <user> -d boloo_db > backup_pre_migration_006_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Verify Current State

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Check current migration
alembic current

# Expected output: 005_add_otp_verification_fields
```

### Step 3: Review Migration SQL (Optional)

```bash
# Generate SQL without applying
alembic upgrade head --sql > migration_006_review.sql

# Review the SQL
cat migration_006_review.sql
```

### Step 4: Apply Migration

```bash
# Apply migration
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 005_add_otp_verification_fields -> 006_add_phone_number_to_otp, add phone_number to otp table
```

### Step 5: Verify Migration

```bash
# Verify current version
alembic current

# Expected output: 006_add_phone_number_to_otp

# Verify table structure
psql -h <host> -U <user> -d boloo_db -c "\d otps"

# Verify indexes
psql -h <host> -U <user> -d boloo_db -c "\di+ ix_otps_phone_number"
```

### Step 6: Test OTP Functionality

```bash
# Restart application
systemctl restart boloo-backend  # or your service name

# Test phone-based OTP
curl -X POST http://localhost:8000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+911234567890"}'

# Test email-based OTP (should still work)
curl -X POST http://localhost:8000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Rollback Procedure

If issues occur, rollback using:

```bash
# Rollback one version
alembic downgrade -1

# Verify rollback
alembic current

# Expected output: 005_add_otp_verification_fields

# Restore from backup if needed
psql -h <host> -U <user> -d boloo_db < backup_pre_migration_006_*.sql
```

## Database Impact Analysis

### Performance Impact
- **Minimal:** Adding nullable column and index
- **Estimated Downtime:** < 5 seconds
- **Lock Type:** Brief ACCESS EXCLUSIVE lock during ALTER TABLE

### Storage Impact
- **Per Row:** ~24 bytes (20 bytes VARCHAR + 4 bytes overhead)
- **Index Size:** ~8 bytes per row + overhead
- **Total Estimated:** For 100k OTP records: ~3.2 MB

### Query Performance
- **Positive:** New index speeds up phone_number lookups
- **Neutral:** No impact on existing email-based queries

## Compatibility Notes

### Application Code Changes Required

**Before deployment, ensure these code changes are deployed:**

1. **OTP Creation Service** - Support both email and phone_number:
```python
# Update OTP creation logic
otp = OTP(
    phone_number=phone_number if phone_number else None,
    email=email if email else None,
    otp_code=OTP.generate_code(),
    expires_at=datetime.utcnow() + timedelta(minutes=10)
)
```

2. **OTP Verification Service** - Check by phone or email:
```python
# Update OTP verification query
otp = db.query(OTP).filter(
    (OTP.phone_number == phone_number) | (OTP.email == email),
    OTP.otp_code == otp_code,
    OTP.is_used == False
).first()
```

### Backward Compatibility
- ✅ Existing email-based OTP flows continue to work
- ✅ Both email and phone_number are nullable
- ✅ Downgrade safely removes phone_number support

## Validation Tests

### Unit Tests Required

```python
# test_otp_model.py
def test_otp_with_phone_number():
    """Test OTP creation with phone number"""
    otp = OTP(
        phone_number="+911234567890",
        otp_code="123456",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    assert otp.phone_number == "+911234567890"
    assert otp.email is None
    assert str(otp) == "<OTP +911234567890 - 123456>"

def test_otp_with_email():
    """Test OTP creation with email (backward compatibility)"""
    otp = OTP(
        email="test@example.com",
        otp_code="123456",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    assert otp.email == "test@example.com"
    assert otp.phone_number is None
    assert str(otp) == "<OTP test@example.com - 123456>"

def test_otp_to_dict_includes_phone():
    """Test OTP to_dict includes phone_number"""
    otp = OTP(
        phone_number="+911234567890",
        otp_code="123456",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    otp_dict = otp.to_dict()
    assert "phone_number" in otp_dict
    assert otp_dict["phone_number"] == "+911234567890"
```

### Integration Tests Required

```python
# test_otp_flow.py
async def test_phone_otp_flow():
    """Test complete phone-based OTP flow"""
    # Send OTP
    response = await client.post("/api/auth/send-otp",
        json={"phone_number": "+911234567890"})
    assert response.status_code == 200

    # Verify OTP exists in DB
    otp = db.query(OTP).filter(
        OTP.phone_number == "+911234567890",
        OTP.is_used == False
    ).first()
    assert otp is not None

    # Verify OTP
    response = await client.post("/api/auth/verify-otp",
        json={"phone_number": "+911234567890", "otp_code": otp.otp_code})
    assert response.status_code == 200
```

## Monitoring

### Key Metrics to Watch

1. **OTP Creation Rate**
   - Monitor phone vs email OTP creation
   - Alert if phone OTP creation fails

2. **Database Performance**
   - Index usage on `ix_otps_phone_number`
   - Query execution time for OTP lookups

3. **Error Rates**
   - Track OTP validation failures
   - Monitor constraint violations

### Recommended Alerts

```yaml
alerts:
  - name: OTP Phone Number Errors
    condition: otp_creation_error_rate > 5%
    action: page_oncall

  - name: OTP Index Not Used
    condition: ix_otps_phone_number_usage < 1%
    action: investigate_queries
```

## Expected Results

### Success Criteria

✅ Migration applies without errors
✅ Both phone and email OTP creation works
✅ Chat interface authentication succeeds
✅ Existing email-based flows unaffected
✅ No performance degradation
✅ Rollback tested successfully

### Known Issues

None anticipated. The change is additive and backward compatible.

## Support Contacts

- **Database Team:** DBA team contact
- **Backend Team:** Backend engineers
- **On-Call:** Production support rotation

## Appendix A: SQL Commands

### Manual Upgrade (if needed)

```sql
-- Add phone_number column
ALTER TABLE otps ADD COLUMN phone_number VARCHAR(20);

-- Create index
CREATE INDEX ix_otps_phone_number ON otps(phone_number);

-- Make email nullable
ALTER TABLE otps ALTER COLUMN email DROP NOT NULL;
```

### Manual Downgrade (if needed)

```sql
-- Make email NOT NULL again
ALTER TABLE otps ALTER COLUMN email SET NOT NULL;

-- Drop index
DROP INDEX IF EXISTS ix_otps_phone_number;

-- Drop column
ALTER TABLE otps DROP COLUMN phone_number;
```

### Verification Queries

```sql
-- Check table structure
\d otps

-- Check indexes
\di+ ix_otps_phone_number

-- Sample phone-based OTP records
SELECT id, phone_number, email, otp_code, created_at
FROM otps
WHERE phone_number IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;

-- Count phone vs email OTPs
SELECT
    COUNT(*) FILTER (WHERE phone_number IS NOT NULL) as phone_otps,
    COUNT(*) FILTER (WHERE email IS NOT NULL) as email_otps,
    COUNT(*) as total_otps
FROM otps;
```

## Appendix B: Environment-Specific Notes

### Development
```bash
# Local database migration
cd backend
alembic upgrade head
```

### Staging
```bash
# Connect to staging DB
export DATABASE_URL="postgresql://user:pass@staging-db:5432/boloo_staging"
alembic upgrade head
```

### Production
```bash
# Use production credentials
export DATABASE_URL="postgresql://user:pass@prod-db:5432/boloo_prod"

# Apply with confirmation
alembic upgrade head

# Monitor logs
tail -f /var/log/boloo/backend.log
```

## Timeline

- **Development:** Complete ✅
- **Testing:** Pending local DB setup
- **Staging Deployment:** TBD
- **Production Deployment:** TBD
- **Estimated Duration:** 10-15 minutes total

---

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Author:** Backend Development Team
