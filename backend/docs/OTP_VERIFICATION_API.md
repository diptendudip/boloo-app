# OTP Verification State Tracking - API Documentation

## Overview

This document describes the OTP verification state tracking system added to the Boloo backend API. The system tracks which users have verified their phone numbers via OTP and includes this status in JWT tokens for frontend validation.

## Database Schema Changes

### User Model Updates

Three new fields added to the `users` table:

```python
phone_verified: bool = False              # Whether phone is verified
phone_verified_at: datetime | None        # First verification timestamp
last_otp_verified_at: datetime | None     # Most recent OTP verification
```

### Migration

**File:** `alembic/versions/005_add_otp_verification_fields.py`

**Run migration:**
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

## API Changes

### 1. Enhanced JWT Token Payload

JWT tokens now include OTP verification status:

```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "type": "access",
  "phone_verified": true,
  "phone_number": "+919876543210"
}
```

### 2. Updated `/auth/otp/verify` Endpoint

**Endpoint:** `POST /auth/otp/verify`

**Behavior Changes:**
- After successful OTP verification, sets:
  - `user.phone_verified = True`
  - `user.phone_verified_at = current_timestamp`
  - `user.last_otp_verified_at = current_timestamp`
- Returns JWT token with `phone_verified: true`

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "phone": "+919876543210",
    "phone_verified": true,
    "phone_verified_at": "2025-11-24T19:00:00.000Z",
    "last_otp_verified_at": "2025-11-24T19:00:00.000Z",
    ...
  }
}
```

### 3. New `/auth/verify` Endpoint

**Endpoint:** `GET /auth/verify`

**Purpose:** Verify JWT token validity and check OTP verification status

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (Success - 200):**
```json
{
  "valid": true,
  "user_id": "user-uuid",
  "phone_verified": true,
  "phone_number": "+919876543210",
  "phone_verified_at": "2025-11-24T19:00:00.000Z",
  "last_otp_verified_at": "2025-11-24T19:00:00.000Z"
}
```

**Response (Invalid Token - 401):**
```json
{
  "detail": "Invalid or expired token"
}
```

**Response (User Not Found - 401):**
```json
{
  "detail": "User not found or inactive"
}
```

### 4. Updated User Response

All endpoints returning user objects now include:

```json
{
  "id": "uuid",
  "phone": "+919876543210",
  "phone_verified": true,
  "phone_verified_at": "2025-11-24T19:00:00.000Z",
  "last_otp_verified_at": "2025-11-24T19:00:00.000Z",
  ...
}
```

## Middleware: OTP Verification Check

**File:** `app/middleware/otp_verification.py`

### Purpose

Enforces OTP verification for protected endpoints in production mode.

### Configuration

```python
from app.middleware.otp_verification import OTPVerificationMiddleware

# Add to main.py
app.add_middleware(
    OTPVerificationMiddleware,
    enforce_in_production=True  # Only enforce in production
)
```

### Bypass Rules

The following paths **bypass** OTP verification check:

**Exact matches:**
- `/auth/otp/request`
- `/auth/otp/verify`
- `/auth/otp/resend`
- `/auth/verify`
- `/auth/profile`
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`

**Path prefixes:**
- `/auth/*`
- `/static/*`
- `/public/*`

### Behavior

**Development Mode:**
- Middleware is bypassed (no enforcement)

**Production Mode:**
- Checks JWT token for `phone_verified: true`
- Returns 403 if phone not verified

**Response (403 Forbidden):**
```json
{
  "detail": "Phone verification required. Please verify your phone number via OTP.",
  "error_code": "OTP_VERIFICATION_REQUIRED",
  "phone_verified": false
}
```

## Testing Guide

### 1. Setup Database

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Run migration
alembic upgrade head

# Verify migration
alembic current
```

### 2. Test OTP Flow

**Step 1: Request OTP**
```bash
curl -X POST http://localhost:8000/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'
```

**Step 2: Verify OTP**
```bash
curl -X POST http://localhost:8000/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp_code": "123456"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "phone_verified": true,
    "phone_verified_at": "2025-11-24T19:00:00.000Z",
    ...
  }
}
```

### 3. Verify Token

```bash
TOKEN="your_jwt_token_here"

curl -X GET http://localhost:8000/auth/verify \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "valid": true,
  "user_id": "uuid",
  "phone_verified": true,
  "phone_number": "+919876543210",
  "phone_verified_at": "2025-11-24T19:00:00.000Z",
  "last_otp_verified_at": "2025-11-24T19:00:00.000Z"
}
```

### 4. Test Middleware (Production)

**Set production mode:**
```bash
export APP_ENV=production
```

**Access protected endpoint without phone verification:**
```bash
# This should return 403 if phone_verified is false
curl -X GET http://localhost:8000/cases/my-cases \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Check Database State

```sql
-- Connect to PostgreSQL
psql -U boloo -d boloo

-- Check user verification status
SELECT
  id,
  phone,
  phone_verified,
  phone_verified_at,
  last_otp_verified_at,
  created_at
FROM users
ORDER BY created_at DESC
LIMIT 10;
```

### 6. Decode JWT Token (for debugging)

```python
import jwt
import json

token = "your_jwt_token_here"
secret = "dev_secret_key_change_in_production"

decoded = jwt.decode(token, secret, algorithms=["HS256"])
print(json.dumps(decoded, indent=2))
```

**Expected payload:**
```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "type": "access",
  "phone_verified": true,
  "phone_number": "+919876543210"
}
```

## Integration with Frontend

### 1. Check Token on App Launch

```javascript
async function checkAuthStatus() {
  const token = await getStoredToken();

  const response = await fetch('/auth/verify', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();

  if (!data.valid) {
    // Redirect to login
  } else if (!data.phone_verified) {
    // Show OTP verification screen
  } else {
    // Proceed to main app
  }
}
```

### 2. Handle 403 OTP Required Error

```javascript
async function apiRequest(url, options) {
  const response = await fetch(url, options);

  if (response.status === 403) {
    const error = await response.json();

    if (error.error_code === 'OTP_VERIFICATION_REQUIRED') {
      // Show OTP verification dialog
      showOTPVerification();
    }
  }

  return response;
}
```

### 3. Decode JWT to Check Verification

```javascript
function decodeJWT(token) {
  const base64Url = token.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(
    atob(base64).split('').map(c =>
      '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    ).join('')
  );

  return JSON.parse(jsonPayload);
}

const payload = decodeJWT(token);
console.log('Phone verified:', payload.phone_verified);
```

## Production Deployment Checklist

- [ ] Run database migration: `alembic upgrade head`
- [ ] Set `APP_ENV=production` environment variable
- [ ] Configure secure `JWT_SECRET_KEY` (32+ characters)
- [ ] Enable SSL for database connection
- [ ] Test OTP flow in production environment
- [ ] Verify middleware enforcement
- [ ] Monitor security logs for failed verification attempts
- [ ] Update mobile app to handle OTP verification states
- [ ] Test 403 error handling in frontend
- [ ] Document OTP verification flow for users

## Security Considerations

1. **JWT Payload:**
   - `phone_verified` status is in token (no DB lookup needed)
   - Token expiration: 24 hours (configurable)

2. **Middleware:**
   - Only enforced in production (`APP_ENV=production`)
   - Bypasses auth endpoints to prevent lockout
   - Gracefully handles invalid tokens

3. **Database:**
   - `phone_verified` defaults to `false` for new users
   - Indexed for performance
   - Nullable timestamps (NULL = not verified)

4. **Backward Compatibility:**
   - Existing users start with `phone_verified=false`
   - Must verify OTP on next login
   - No breaking changes to existing API

## Troubleshooting

### Issue: Migration fails with "column already exists"

**Solution:**
```bash
# Check current migration state
alembic current

# Rollback and rerun
alembic downgrade -1
alembic upgrade head
```

### Issue: JWT tokens missing phone_verified field

**Solution:**
- Ensure `create_access_token()` is updated
- Users must login again to get new tokens
- Old tokens will be rejected by middleware

### Issue: Middleware blocking all requests

**Solution:**
```python
# Check environment mode
echo $APP_ENV  # Should be "development" for testing

# Or bypass middleware
app.add_middleware(
    OTPVerificationMiddleware,
    enforce_in_production=False  # Disable enforcement
)
```

### Issue: Cannot access /auth/verify endpoint

**Solution:**
- Check if endpoint is registered in router
- Verify bearer token format: `Authorization: Bearer <token>`
- Check server logs for errors

## API Endpoints Summary

| Endpoint | Method | Auth Required | OTP Verified Required | Purpose |
|----------|--------|---------------|----------------------|---------|
| `/auth/otp/request` | POST | No | No | Request OTP |
| `/auth/otp/verify` | POST | No | No | Verify OTP & login |
| `/auth/otp/resend` | POST | No | No | Resend OTP |
| `/auth/verify` | GET | Yes | No | Check token status |
| `/auth/profile` | PUT | Yes | No | Update profile |
| `/cases/*` | * | Yes | **Yes (Prod)** | Protected endpoints |

## Support

For issues or questions:
- Check server logs: `tail -f logs/app.log`
- Enable debug mode: `DEBUG=True` in `.env`
- Review security logs: Check `app/logs/security.log`
