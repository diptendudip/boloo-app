# OTP Phone Number Column Fix - Implementation Summary

## Problem Statement

The MSG91 service was trying to use the `phone_number` column when creating OTP records, but the OTP model in `/app/models/otp.py` only had an `email` column. This caused a mismatch between the service and the data model.

## Solution Implemented

### 1. Updated OTP Model (`/app/models/otp.py`)

**Changes Made:**
- Added `phone_number = Column(String(20), nullable=True, index=True)`
- Made `email` column nullable to support both email and phone-based OTP
- Updated `__repr__` method to display either phone_number or email
- Updated `to_dict()` method to include phone_number field

**Before:**
```python
class OTP(Base):
    __tablename__ = "otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**After:**
```python
class OTP(Base):
    __tablename__ = "otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=True, index=True)  # Made nullable
    phone_number = Column(String(20), nullable=True, index=True)  # Added
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. MSG91 Service Verification (`/app/services/msg91_service.py`)

**Verified OTP Record Creation:**

The MSG91 service correctly creates OTP records with `phone_number` in THREE places:

1. **send_otp() method** (lines 131-136):
```python
otp_record = OTP(
    phone_number=full_number,  # ✅ Uses phone_number
    otp_code=otp_code,
    expires_at=expires_at,
    is_used=False
)
```

2. **_resend_voice_otp() method** (lines 346-351):
```python
otp_record = OTP(
    phone_number=full_number,  # ✅ Uses phone_number
    otp_code=otp_code,
    expires_at=expires_at,
    is_used=False
)
```

3. **verify_otp() method** (lines 241-246):
```python
otp_record = db.query(OTP).filter(
    OTP.phone_number == full_number,  # ✅ Queries by phone_number
    OTP.otp_code == otp_code,
    OTP.is_used == False,
    OTP.expires_at > datetime.utcnow()
).first()
```

**Verdict:** ✅ MSG91 service is correctly implemented and uses phone_number throughout.

### 3. Fixed Test Mocks (`/tests/test_otp_verification.py`)

**Issue Found:**
The test mock was using `email=phone_number` which was incorrect.

**Fixed:**
```python
# Before (line 315)
otp = OTP(
    email=phone_number,  # ❌ Wrong
    otp_code=otp_code,
    expires_at=datetime.utcnow() + timedelta(minutes=5)
)

# After (line 315)
otp = OTP(
    phone_number=phone_number,  # ✅ Correct
    otp_code=otp_code,
    expires_at=datetime.utcnow() + timedelta(minutes=5)
)
```

### 4. Created Comprehensive Test Suite (`/tests/test_otp_phone.py`)

**Test Coverage:**

#### A. OTP Model Tests (7 tests)
1. ✅ `test_otp_with_phone_number` - Create OTP with phone number
2. ✅ `test_otp_with_email` - Create OTP with email (backward compatibility)
3. ✅ `test_otp_with_both_phone_and_email` - Both fields supported
4. ✅ `test_otp_repr_with_phone` - String representation with phone
5. ✅ `test_otp_repr_with_email` - String representation with email
6. ✅ `test_otp_to_dict_includes_phone` - Dictionary serialization
7. ✅ `test_otp_query_by_phone_number` - Database queries

#### B. MSG91 Service Integration Tests (4 tests)
1. ✅ `test_send_otp_creates_phone_record` - Send OTP creates phone record
2. ✅ `test_verify_otp_with_phone_number` - Verification works with phone
3. ✅ `test_resend_otp_creates_new_phone_record` - Resend creates new record
4. ✅ `test_voice_otp_creates_phone_record` - Voice OTP uses phone number

#### C. OTP Validation Tests (2 tests)
1. ✅ `test_is_valid_with_phone_number` - Validation logic works
2. ✅ `test_generate_code_format` - OTP code generation

**Total Tests:** 13 comprehensive tests covering all aspects of phone_number integration.

## Database Schema Change

**Migration Required:**

Since we added a new `phone_number` column and made `email` nullable, a database migration is needed:

```sql
-- Add phone_number column
ALTER TABLE otps ADD COLUMN phone_number VARCHAR(20);

-- Make email nullable (if not already)
ALTER TABLE otps ALTER COLUMN email DROP NOT NULL;

-- Add index for performance
CREATE INDEX idx_otps_phone_number ON otps(phone_number);
```

**Alembic Migration:**
```bash
cd backend
alembic revision --autogenerate -m "Add phone_number to OTP model"
alembic upgrade head
```

## Files Modified

1. ✅ `/app/models/otp.py` - Added phone_number column, updated methods
2. ✅ `/tests/test_otp_verification.py` - Fixed mock to use phone_number
3. ✅ `/tests/test_otp_phone.py` - NEW: Comprehensive test suite (13 tests)
4. ✅ `/docs/OTP_PHONE_NUMBER_FIX.md` - THIS FILE: Implementation summary

## Verification Checklist

- [x] OTP model has `phone_number` column
- [x] OTP model has `email` column (nullable for backward compatibility)
- [x] Both columns are indexed for query performance
- [x] `__repr__` method handles both phone and email
- [x] `to_dict()` method includes phone_number
- [x] MSG91 service uses phone_number for OTP creation (3 locations)
- [x] MSG91 service queries OTP by phone_number
- [x] Test mocks fixed to use phone_number
- [x] Comprehensive test suite created (13 tests)
- [x] Backward compatibility maintained (email still works)

## Backward Compatibility

The implementation maintains **100% backward compatibility**:

1. **Email-based OTP** still works (email column is nullable, not removed)
2. **Phone-based OTP** now works (new phone_number column)
3. **Both can coexist** in the same record if needed
4. **Existing code** using email continues to function

## Testing

Run the test suite to verify:

```bash
# Run OTP phone number tests
pytest tests/test_otp_phone.py -v

# Run all OTP-related tests
pytest tests/test_otp*.py -v

# Run MSG91 integration tests
pytest tests/test_msg91*.py -v
```

## Production Deployment

1. **Create database migration:**
   ```bash
   alembic revision --autogenerate -m "Add phone_number to OTP model"
   ```

2. **Review migration file** to ensure it adds:
   - `phone_number VARCHAR(20)` column
   - Makes `email` nullable
   - Adds index on `phone_number`

3. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

4. **Verify in production:**
   - Test SMS OTP sending
   - Test OTP verification
   - Test OTP resend
   - Check database records have phone_number

## Summary

✅ **Problem:** MSG91 service couldn't use phone_number column (didn't exist)
✅ **Solution:** Added phone_number to OTP model, made email nullable
✅ **Testing:** Created 13 comprehensive tests
✅ **Verification:** All MSG91 service code uses phone_number correctly
✅ **Compatibility:** Email-based OTP still works (backward compatible)
✅ **Database:** Migration required (add phone_number column)

**Status:** ✅ COMPLETE - Ready for database migration and deployment
