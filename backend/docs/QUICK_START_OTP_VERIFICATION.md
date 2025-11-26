# Quick Start: OTP Verification State Tracking

## 🚀 5-Minute Setup

### 1. Run Database Migration

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade add_conversation_metadata -> 005_add_otp_verification_fields
```

### 2. Restart Backend Server

```bash
# Stop current server (Ctrl+C)
# Start server
uvicorn app.main:app --reload
```

### 3. Test OTP Flow

```bash
# Run automated test script
./scripts/test_otp_verification.sh

# Or test manually:
curl -X POST http://localhost:8000/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "otp_code": "123456"}'
```

## 📋 What Changed?

### Database (User Table)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `phone_verified` | boolean | `false` | Phone verified via OTP |
| `phone_verified_at` | timestamp | `null` | First verification time |
| `last_otp_verified_at` | timestamp | `null` | Latest OTP verification |

### JWT Token Payload

**Before:**
```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "type": "access"
}
```

**After:**
```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "type": "access",
  "phone_verified": true,
  "phone_number": "+919876543210"
}
```

### New API Endpoint

**GET /auth/verify**
```bash
curl -X GET http://localhost:8000/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "valid": true,
  "user_id": "uuid",
  "phone_verified": true,
  "phone_number": "+919876543210",
  "phone_verified_at": "2025-11-24T19:00:00Z",
  "last_otp_verified_at": "2025-11-24T19:00:00Z"
}
```

## 🔒 Production Mode

### Enable OTP Middleware

**Option 1: Add to `app/main.py`**
```python
from app.middleware.otp_verification import OTPVerificationMiddleware

# Add after other middleware
app.add_middleware(
    OTPVerificationMiddleware,
    enforce_in_production=True  # Only enforces in production
)
```

**Option 2: Set environment variable**
```bash
export APP_ENV=production
```

### What Happens in Production?

- ✅ Users must verify OTP before accessing protected endpoints
- ✅ `/auth/*` endpoints remain accessible (no lockout)
- ✅ Returns 403 with clear error message if not verified
- ✅ Middleware automatically bypassed in development mode

## 🧪 Testing Commands

### Check Migration Status
```bash
alembic current
# Should show: 005_add_otp_verification_fields
```

### Check Database Schema
```bash
psql -U boloo -d boloo -c "\d users"
# Should show: phone_verified, phone_verified_at, last_otp_verified_at
```

### Verify User State
```sql
SELECT phone, phone_verified, phone_verified_at
FROM users
WHERE phone = '+919876543210';
```

### Decode JWT Token
```bash
# Install jq if not present
# brew install jq  # macOS
# sudo apt-get install jq  # Linux

TOKEN="your_jwt_token"
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq
```

### Test Middleware (Production Mode)
```bash
export APP_ENV=production

# Should return 403 for unverified users
curl -X GET http://localhost:8000/cases/my-cases \
  -H "Authorization: Bearer UNVERIFIED_USER_TOKEN"
```

## 📱 Mobile App Integration

### Check Token on Launch
```javascript
async function initializeApp() {
  const token = await AsyncStorage.getItem('authToken');

  const response = await fetch('http://api.boloo.com/auth/verify', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();

  if (!data.valid) {
    // Token invalid - go to login
    navigation.navigate('Login');
  } else if (!data.phone_verified) {
    // Phone not verified - show OTP screen
    navigation.navigate('VerifyOTP');
  } else {
    // All good - proceed to app
    navigation.navigate('Home');
  }
}
```

### Handle 403 OTP Required
```javascript
// In API client
async function apiRequest(url, options) {
  const response = await fetch(url, options);

  if (response.status === 403) {
    const error = await response.json();

    if (error.error_code === 'OTP_VERIFICATION_REQUIRED') {
      // Show OTP verification modal
      showOTPModal();
    }
  }

  return response;
}
```

## 🔍 Troubleshooting

### Migration Error: "column already exists"
```bash
# Check if migration already ran
alembic current

# If needed, mark migration as run without executing
alembic stamp 005_add_otp_verification_fields
```

### Users Not Verified After OTP
**Check:**
1. Database updated? `SELECT phone_verified FROM users;`
2. Token regenerated? Old tokens don't have `phone_verified`
3. User logged in again? Verification happens on `/auth/otp/verify`

### Middleware Blocking Everything
**Solutions:**
```bash
# Option 1: Disable production enforcement
export APP_ENV=development

# Option 2: Modify middleware
# Set enforce_in_production=False in main.py
```

### Can't Access /auth/verify
**Check:**
1. Server running? `curl http://localhost:8000/health`
2. Token format? Must be `Authorization: Bearer <token>`
3. Route registered? Check `http://localhost:8000/docs`

## 📚 Related Files

| File | Purpose |
|------|---------|
| `app/models/user.py` | User model with OTP fields |
| `app/routers/auth.py` | OTP endpoints + JWT generation |
| `app/middleware/otp_verification.py` | Production middleware |
| `alembic/versions/005_*.py` | Database migration |
| `tests/test_otp_verification.py` | Unit tests |
| `scripts/test_otp_verification.sh` | Integration test |
| `docs/OTP_VERIFICATION_API.md` | Full documentation |

## ⚡ Common Tasks

### Reset User Verification
```sql
UPDATE users
SET phone_verified = false,
    phone_verified_at = NULL,
    last_otp_verified_at = NULL
WHERE phone = '+919876543210';
```

### Manually Verify User
```sql
UPDATE users
SET phone_verified = true,
    phone_verified_at = NOW(),
    last_otp_verified_at = NOW()
WHERE phone = '+919876543210';
```

### Check All Unverified Users
```sql
SELECT phone, created_at
FROM users
WHERE phone_verified = false
ORDER BY created_at DESC;
```

### Generate New Token for Testing
```python
from app.routers.auth import create_access_token

token = create_access_token(
    user_id="your-user-uuid",
    phone_number="+919876543210",
    phone_verified=True
)
print(token)
```

## 🎯 Next Steps

1. ✅ Run migration: `alembic upgrade head`
2. ✅ Test OTP flow: `./scripts/test_otp_verification.sh`
3. ✅ Update mobile app to check `phone_verified`
4. ✅ Add middleware to `main.py` (when ready for production)
5. ✅ Monitor security logs for verification attempts
6. ✅ Update user documentation

## 🆘 Support

**Issues?**
- Check logs: `tail -f logs/app.log`
- Enable debug: `export DEBUG=true`
- View security logs: `cat logs/security.log`

**Questions?**
- Full docs: `docs/OTP_VERIFICATION_API.md`
- API reference: `http://localhost:8000/docs`
