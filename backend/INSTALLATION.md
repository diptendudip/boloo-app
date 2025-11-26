# Security Fixes - Installation Guide

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**New dependency added:**
- `slowapi>=0.1.9` - Rate limiting middleware

### 2. Verify Installation
```bash
python scripts/verify_security_fixes.py
```

**Expected output:**
```
============================================================
SECURITY FIXES VERIFICATION
============================================================
Environment: development
Production: False

1️⃣  HTTPS Enforcement & HSTS Headers
✅ HTTPSRedirectMiddleware imported successfully
✅ SecurityHeadersMiddleware imported successfully
...

Checks Passed: 7/7 (100%)

✅ ALL SECURITY FIXES VERIFIED!
Status: PRODUCTION READY
```

### 3. Run Tests
```bash
pytest tests/test_security_fixes.py -v
```

### 4. Set Environment Variables (Production)
```bash
export APP_ENV=production
export DATABASE_SSL_MODE=require
export DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

### 5. Deploy

That's it! All security fixes are now active.

---

## Detailed Installation

### Dependencies

The following package was added to `requirements.txt`:

```txt
# Rate Limiting
slowapi>=0.1.9
```

Install with:
```bash
pip install slowapi
```

### Environment Variables

#### Required for Production
```bash
APP_ENV=production
DATABASE_SSL_MODE=require  # or verify-ca, verify-full
```

#### Optional (Secure Defaults)
```bash
ALLOWED_ORIGINS=https://your-domain.com
JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

### Verification Checklist

After installation, verify:

- [ ] `slowapi` is installed: `pip show slowapi`
- [ ] Security middleware imported without errors
- [ ] All tests pass: `pytest tests/test_security_fixes.py -v`
- [ ] Verification script passes: `python scripts/verify_security_fixes.py`

---

## Troubleshooting

### Error: "No module named 'slowapi'"
**Solution:**
```bash
pip install slowapi
```

### Error: "Database SSL must be enabled in production"
**Solution:**
```bash
export DATABASE_SSL_MODE=require
# or
export DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

### Error: "Dev bypass attempted in production"
**Solution:** This is correct! Dev bypass is now blocked in production. Use proper JWT authentication.

---

## Files Created/Modified

### New Files (6)
1. `app/middleware/security.py` - HTTPS & security headers
2. `app/middleware/rate_limit.py` - Rate limiting
3. `app/middleware/__init__.py` - Package init
4. `app/utils/security_logger.py` - Security logging
5. `tests/test_security_fixes.py` - Security tests
6. `scripts/verify_security_fixes.py` - Verification script

### Modified Files (5)
1. `requirements.txt` - Added slowapi
2. `app/config.py` - SSL enforcement
3. `app/main.py` - Security middleware
4. `app/routers/auth.py` - Rate limiting & logging
5. `app/utils/auth.py` - Dev bypass blocking (already had it)

---

## Next Steps

1. **Install:** `pip install -r requirements.txt`
2. **Verify:** `python scripts/verify_security_fixes.py`
3. **Test:** `pytest tests/test_security_fixes.py -v`
4. **Deploy:** Set environment variables and deploy

For detailed documentation, see:
- `IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `SECURITY_FIXES.md` - Technical documentation
