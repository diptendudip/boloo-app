# OTP Verification State Tracking - Deployment Steps

## 🚀 Step-by-Step Deployment Guide

### Prerequisites
- PostgreSQL database running
- Backend server stopped
- Database backup created (recommended)

### Step 1: Apply Database Migration

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Check current migration status
alembic current

# Run the migration
alembic upgrade head

# Verify migration applied
alembic current
# Should show: 005_add_otp_verification_fields (head)
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade add_conversation_metadata -> 005_add_otp_verification_fields
INFO  [alembic.runtime.migration] Adding columns phone_verified, phone_verified_at, last_otp_verified_at
INFO  [alembic.runtime.migration] Creating index ix_users_phone_verified
```

### Step 2: Verify Database Schema

```bash
psql -U boloo -d boloo -c "\d users"
```

**Look for these columns:**
```
phone_verified           | boolean                     | not null default false
phone_verified_at        | timestamp without time zone |
last_otp_verified_at     | timestamp without time zone |
```

### Step 3: Check Existing Users

```sql
-- All users should have phone_verified = false initially
SELECT
  id,
  phone,
  phone_verified,
  phone_verified_at,
  created_at
FROM users
LIMIT 5;
```

### Step 4: Restart Backend Server

```bash
# If using uvicorn directly
uvicorn app.main:app --reload

# If using systemd
sudo systemctl restart boloo-backend

# If using docker
docker-compose restart backend
```

### Step 5: Test OTP Flow

```bash
# Run automated test
./scripts/test_otp_verification.sh

# Or test manually
export API_URL=http://localhost:8000

# Request OTP
curl -X POST $API_URL/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'

# Verify OTP (use OTP from development response)
curl -X POST $API_URL/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "otp_code": "123456"}'
```

### Step 6: Verify Token Endpoint

```bash
# Get token from Step 5 response
TOKEN="your_access_token_here"

# Test verification endpoint
curl -X GET $API_URL/auth/verify \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
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

### Step 7: (Optional) Enable Middleware for Production

**Edit `/Users/diptendu/boloo app/boloo-app/backend/app/main.py`:**

```python
from app.middleware.otp_verification import OTPVerificationMiddleware

# Add after CORS and other middleware
app.add_middleware(
    OTPVerificationMiddleware,
    enforce_in_production=True  # Only enforces when APP_ENV=production
)
```

**Restart server after adding middleware.**

### Step 8: Test Middleware (Production Mode Only)

```bash
# Set production mode
export APP_ENV=production

# Restart server
uvicorn app.main:app --reload

# Try to access protected endpoint with unverified token
# Should return 403
curl -X GET http://localhost:8000/cases/my-cases \
  -H "Authorization: Bearer UNVERIFIED_TOKEN"
```

**Expected Response (403):**
```json
{
  "detail": "Phone verification required. Please verify your phone number via OTP.",
  "error_code": "OTP_VERIFICATION_REQUIRED",
  "phone_verified": false
}
```

### Step 9: Monitor Logs

```bash
# Check server logs for errors
tail -f logs/app.log

# Check for security events
tail -f logs/security.log
```

### Step 10: Update Mobile App (Frontend)

**Update your mobile app to:**

1. Check token verification status on launch:
```javascript
const response = await fetch('/auth/verify', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();

if (!data.phone_verified) {
  // Show OTP verification screen
}
```

2. Handle 403 errors:
```javascript
if (response.status === 403) {
  const error = await response.json();
  if (error.error_code === 'OTP_VERIFICATION_REQUIRED') {
    // Redirect to OTP verification
  }
}
```

## 🔄 Rollback Procedure

If you need to rollback the changes:

```bash
# Rollback migration
alembic downgrade -1

# Verify rollback
alembic current
# Should show: add_conversation_metadata

# Restart server
uvicorn app.main:app --reload
```

## ✅ Post-Deployment Checklist

- [ ] Migration applied successfully
- [ ] Database schema updated
- [ ] Server restarted without errors
- [ ] OTP flow tested and working
- [ ] Token verification endpoint working
- [ ] JWT tokens include `phone_verified` field
- [ ] Middleware enabled (if production)
- [ ] Mobile app updated
- [ ] Monitoring configured
- [ ] Documentation updated

## 📊 Monitoring Queries

### Verification Rate
```sql
SELECT
  COUNT(*) FILTER (WHERE phone_verified = true) * 100.0 / COUNT(*) as verification_percentage,
  COUNT(*) FILTER (WHERE phone_verified = true) as verified_users,
  COUNT(*) FILTER (WHERE phone_verified = false) as unverified_users
FROM users;
```

### Recent Verifications
```sql
SELECT
  phone,
  phone_verified_at,
  last_otp_verified_at,
  AGE(NOW(), phone_verified_at) as time_since_verification
FROM users
WHERE phone_verified = true
ORDER BY phone_verified_at DESC
LIMIT 20;
```

### Verification by Day
```sql
SELECT
  DATE(phone_verified_at) as verification_date,
  COUNT(*) as verifications
FROM users
WHERE phone_verified = true
GROUP BY DATE(phone_verified_at)
ORDER BY verification_date DESC;
```

## 🐛 Troubleshooting

### Issue: Migration Fails

**Error:** "column already exists"

**Solution:**
```bash
# Check if columns exist
psql -U boloo -d boloo -c "\d users" | grep phone_verified

# If columns exist, mark migration as applied
alembic stamp 005_add_otp_verification_fields
```

### Issue: OTP Not Updating Verification Status

**Check:**
1. Is migration applied? `alembic current`
2. Is server using latest code? `git status`
3. Are database changes committed? Check logs

**Debug:**
```sql
-- Check user after OTP verification
SELECT phone_verified, phone_verified_at
FROM users
WHERE phone = '+919876543210';
```

### Issue: Middleware Blocking All Requests

**Solutions:**
```bash
# Option 1: Disable production enforcement
export APP_ENV=development

# Option 2: Check bypass paths in middleware
# /auth/* should always bypass

# Option 3: Temporarily disable middleware
# Comment out in main.py and restart
```

### Issue: JWT Token Missing phone_verified

**Cause:** Old tokens generated before update

**Solution:**
- Users must login again to get new tokens
- Or manually issue new tokens for testing

## 📝 Configuration Reference

### Environment Variables

| Variable | Default | Production | Description |
|----------|---------|------------|-------------|
| `APP_ENV` | `development` | `production` | Environment mode |
| `JWT_SECRET_KEY` | (dev key) | (secure key) | Token signing key |
| `JWT_EXPIRATION_HOURS` | `24` | `24` | Token expiry time |
| `DATABASE_URL` | (local) | (prod URL) | Database connection |

### Middleware Configuration

```python
# In app/main.py
app.add_middleware(
    OTPVerificationMiddleware,
    enforce_in_production=True  # Only enforce in production
)
```

## 🔒 Security Considerations

1. **JWT Tokens:**
   - Include `phone_verified` status
   - Expire after 24 hours
   - Signed with secure secret key

2. **Database:**
   - `phone_verified` defaults to `false`
   - Indexed for performance
   - Nullable timestamps

3. **Middleware:**
   - Only enforces in production
   - Bypasses auth endpoints
   - Returns clear error messages

4. **Backward Compatibility:**
   - Existing users start unverified
   - No breaking API changes
   - Graceful degradation

## 📞 Support Contacts

**Technical Issues:**
- Check logs: `tail -f logs/app.log`
- Review documentation: `docs/OTP_VERIFICATION_API.md`
- Run tests: `./scripts/test_otp_verification.sh`

**Emergency Rollback:**
```bash
alembic downgrade -1
sudo systemctl restart boloo-backend
```

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ Migration shows as applied: `alembic current`
2. ✅ Database has new columns: `\d users`
3. ✅ OTP verification sets `phone_verified = true`
4. ✅ JWT tokens include `phone_verified` field
5. ✅ `/auth/verify` endpoint returns verification status
6. ✅ Middleware enforces verification (in production)
7. ✅ Mobile app handles verification states
8. ✅ No errors in server logs

---

**Deployment completed successfully!** 🎊

For detailed API documentation, see `docs/OTP_VERIFICATION_API.md`
For quick start guide, see `docs/QUICK_START_OTP_VERIFICATION.md`
