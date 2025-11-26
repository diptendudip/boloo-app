# Test Quick Reference Guide

## 🚀 Quick Start

### Run All Tests
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
./tests/run_all_tests.sh
```

### Run Individual Test Suites
```bash
# Backend API tests only
pytest tests/test_auth_persistence.py -v

# Mobile integration tests only
pytest tests/integration/test_mobile_auth_flow.py -v -s

# Docker smoke tests only
pytest tests/smoke/test_docker_deployment.py -v -s
```

---

## 📋 Test Files Overview

| File | Purpose | Duration | Dependencies |
|------|---------|----------|--------------|
| `tests/test_auth_persistence.py` | Backend API validation | ~5s | Backend running |
| `tests/integration/test_mobile_auth_flow.py` | End-to-end auth flow | ~30s | Backend running |
| `tests/smoke/test_docker_deployment.py` | Docker deployment check | ~15s | Docker container |

---

## 🎯 Common Commands

### Setup
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests
```bash
# Single test class
pytest tests/test_auth_persistence.py::TestOTPVerification -v

# Single test method
pytest tests/test_auth_persistence.py::TestOTPVerification::test_otp_verification_updates_phone_verified -v
```

### Debug Mode
```bash
# Show print statements and detailed errors
pytest tests/integration/test_mobile_auth_flow.py -v -s --tb=long
```

---

## 🔍 What Each Test Suite Validates

### 1. Backend API Tests (`test_auth_persistence.py`)
- ✅ OTP verification updates `phone_verified` field
- ✅ JWT tokens include `phone_verified` claim
- ✅ Token validation works correctly
- ✅ Expired tokens are rejected
- ✅ Invalid tokens return 401
- ✅ OTP verification timestamp recorded
- ✅ Security features (signature validation, tampering detection)

### 2. Mobile Integration Tests (`test_mobile_auth_flow.py`)
- ✅ Complete login flow (OTP request → verification → token storage)
- ✅ Auto-login after app restart
- ✅ Logout clears all tokens and data
- ✅ Auto-login fails after logout
- ✅ Chat endpoint requires authentication
- ✅ Token persists across multiple app restarts
- ✅ OTP re-verification flow
- ✅ Storage isolation across login/logout cycles

### 3. Docker Smoke Tests (`test_docker_deployment.py`)
- ✅ Health endpoint responds
- ✅ Database connection works
- ✅ OTP request endpoint functional
- ✅ OTP verification endpoint functional
- ✅ Token verification endpoint functional
- ✅ Chat endpoint works with authenticated user

---

## 🐛 Troubleshooting

### "Connection refused" Error
```bash
# Check if backend is running
lsof -i :8000

# Start backend if not running
uvicorn app.main:app --reload --port 8000
```

### "ModuleNotFoundError"
```bash
# Install missing dependencies
pip install -r tests/requirements.txt
pip install -r requirements.txt
```

### Tests Timeout
```bash
# Check backend health manually
curl http://localhost:8000/health

# Increase timeout in tests (edit test files)
```

### Docker Tests Fail
```bash
# Build and run Docker container
docker build -t boloo-backend:latest .
docker run -d -p 8000:8000 --name boloo-test boloo-backend:latest

# Check logs
docker logs boloo-test
```

---

## 📊 Expected Results

### ✅ All Tests Pass
```
======================== 45 passed in 12.34s ========================
✅ Backend API Tests: PASSED
✅ Mobile Integration Tests: PASSED
✅ Docker Smoke Tests: PASSED
🎉 ALL TESTS PASSED
```

### Coverage Target
- Overall: >80%
- Auth modules: >90%
- Critical paths: 100%

---

## 🎯 Pre-Deployment Checklist

Before deploying to production:

1. ✅ Run `./tests/run_all_tests.sh` - all tests pass
2. ✅ Check coverage: `pytest --cov=app --cov-report=term`
3. ✅ Review production readiness checklist: `docs/production_readiness_checklist.md`
4. ✅ Verify Docker image builds: `docker build -t boloo-backend .`
5. ✅ Run security scan: `bandit -r app/`

---

## 📞 Support

- **Full Guide:** `docs/test_execution_guide.md`
- **Production Checklist:** `docs/production_readiness_checklist.md`
- **Test Runner:** `tests/run_all_tests.sh`

---

**Last Updated:** 2025-11-24
