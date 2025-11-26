# Migration 006 - Quick Deployment Guide

## TL;DR - 5 Minute Deployment

**What:** Add phone_number support to OTP table for chat authentication
**Impact:** Low risk, additive change, ~5 seconds downtime
**Rollback:** Simple, one command

---

## Pre-Flight Checklist

```bash
# 1. Backup database (CRITICAL)
pg_dump boloo_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Verify current migration
cd /Users/diptendu/boloo\ app/boloo-app/backend
alembic current
# Should show: 005_add_otp_verification_fields

# 3. Verify migration file exists
ls -l alembic/versions/006_add_phone_number_to_otp_table.py
```

---

## Deployment (3 Commands)

```bash
# 1. Apply migration
alembic upgrade head

# 2. Verify success
alembic current
# Should show: 006_add_phone_number_to_otp

# 3. Restart application
systemctl restart boloo-backend  # or your service command
```

---

## Quick Test

```bash
# Test phone OTP
curl -X POST http://localhost:8000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+911234567890"}'

# Should return: {"status": "success", "message": "OTP sent"}
```

---

## If Something Goes Wrong

```bash
# Rollback (instant)
alembic downgrade -1

# Restore backup (if needed)
psql boloo_db < backup_*.sql

# Restart service
systemctl restart boloo-backend
```

---

## What Changed?

**Database:**
- ✅ Added `otps.phone_number` VARCHAR(20) nullable
- ✅ Added index on `phone_number`
- ✅ Made `otps.email` nullable

**Model:**
- ✅ Updated `/Users/diptendu/boloo app/boloo-app/backend/app/models/otp.py`
- ✅ Added `phone_number` field
- ✅ Updated `__repr__()` and `to_dict()`

**Location Fields:**
- ℹ️ Already exist (migration 2324c72c4cf5)
- ℹ️ No changes needed

---

## Files Changed

1. **Migration:** `/Users/diptendu/boloo app/boloo-app/backend/alembic/versions/006_add_phone_number_to_otp_table.py`
2. **Model:** `/Users/diptendu/boloo app/boloo-app/backend/app/models/otp.py`

---

## Success Criteria

✅ Migration completes without errors
✅ Chat authentication works with phone
✅ Email authentication still works
✅ No errors in application logs

---

## Support

**Full Guide:** `/Users/diptendu/boloo app/boloo-app/backend/docs/MIGRATION_006_DEPLOYMENT_GUIDE.md`
**Test Report:** `/Users/diptendu/boloo app/boloo-app/backend/docs/MIGRATION_006_TEST_REPORT.md`

---

**Estimated Time:** 5 minutes
**Risk Level:** ✅ Low
**Tested:** ✅ Syntax validated
**Ready:** ✅ Yes
