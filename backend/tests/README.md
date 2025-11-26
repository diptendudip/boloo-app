# 🧪 Authentication & Persistence Test Suite

Comprehensive test suite for validating login persistence and OTP verification features.

---

## 🚀 Quick Start

```bash
# Run all tests
./run_all_tests.sh

# Run specific suite
pytest test_auth_persistence.py -v
pytest integration/test_mobile_auth_flow.py -v -s
pytest smoke/test_docker_deployment.py -v -s
```

---

## 📁 Test Structure

```
tests/
├── README.md                           # This file
├── requirements.txt                    # Test dependencies
├── run_all_tests.sh                    # Automated test runner
├── test_auth_persistence.py            # Backend API tests
├── integration/
│   └── test_mobile_auth_flow.py       # Mobile integration tests
└── smoke/
    └── test_docker_deployment.py       # Docker smoke tests
```

---

## 🎯 Test Suites

### 1. Backend API Tests (`test_auth_persistence.py`)

**Purpose:** Validate backend authentication endpoints and JWT functionality

**Test Classes:**
- `TestOTPVerification` - OTP verification logic
- `TestJWTTokens` - JWT token generation
- `TestTokenValidation` - Token validation endpoints
- `TestAuthPersistence` - State persistence
- `TestSecurityFeatures` - Security validation

**Run:**
```bash
pytest test_auth_persistence.py -v
pytest test_auth_persistence.py --cov=app
```

**Coverage:** 20+ test cases

---

### 2. Mobile Integration Tests (`integration/test_mobile_auth_flow.py`)

**Purpose:** Simulate complete mobile app authentication flow

**Features:**
- MockAsyncStorage for React Native storage simulation
- MobileAuthClient for app behavior simulation
- End-to-end flow testing

**Test Scenarios:**
1. Complete login flow
2. Auto-login after restart
3. Logout clears tokens
4. Auto-login fails after logout
5. Chat requires authentication
6. Token persistence across restarts
7. OTP re-verification
8. Storage isolation

**Run:**
```bash
pytest integration/test_mobile_auth_flow.py -v -s
```

**Coverage:** 8 integration test scenarios

---

### 3. Docker Smoke Tests (`smoke/test_docker_deployment.py`)

**Purpose:** Quick validation of Docker deployment

**Checks:**
- Service availability
- Health endpoint
- Database connectivity
- Authentication endpoints
- Chat endpoint with auth

**Run:**
```bash
# Start Docker container first
docker run -d -p 8000:8000 --name boloo-test boloo-backend:latest

# Run tests
pytest smoke/test_docker_deployment.py -v -s

# Or run standalone
python smoke/test_docker_deployment.py
```

**Coverage:** 6 smoke test checks

---

## 🔧 Setup

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### Environment
```bash
# Create test environment file (optional)
cat > ../.env.test << EOF
DEVELOPMENT_MODE=true
JWT_SECRET_KEY=test_secret_key
DATABASE_URL=sqlite:///./test_database.db
EOF
```

---

## 📊 Test Execution

### Run All Tests
```bash
# Automated runner with colorful output
./run_all_tests.sh

# Skip Docker tests
./run_all_tests.sh --skip-docker
```

### Run with Coverage
```bash
pytest . --cov=app --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests
```bash
# Single test class
pytest test_auth_persistence.py::TestOTPVerification -v

# Single test method
pytest test_auth_persistence.py::TestOTPVerification::test_otp_verification_updates_phone_verified -v

# With debugging output
pytest integration/test_mobile_auth_flow.py -v -s --tb=long
```

---

## ✅ Expected Results

### All Tests Pass
```
============================================================
🧪 AUTHENTICATION & PERSISTENCE TEST SUITE
============================================================

📦 Backend API Tests: PASSED (20 tests)
📱 Mobile Integration Tests: PASSED (8 tests)
🐳 Docker Smoke Tests: PASSED (6 tests)

============================================================
🎉 ALL TESTS PASSED
✅ System is ready for production
============================================================
```

### Coverage Report
```
Name                          Stmts   Miss  Cover
-------------------------------------------------
app/__init__.py                  12      0   100%
app/auth.py                      89      5    94%
app/main.py                     123     12    90%
app/database.py                  45      3    93%
-------------------------------------------------
TOTAL                           269     20    93%
```

---

## 🐛 Troubleshooting

### Backend Not Running
```bash
# Error: Connection refused
# Solution: Start backend
uvicorn app.main:app --reload --port 8000
```

### Missing Dependencies
```bash
# Error: ModuleNotFoundError
# Solution: Install dependencies
pip install -r requirements.txt
```

### Tests Timeout
```bash
# Error: Request timeout
# Solution: Check backend health
curl http://localhost:8000/health

# Increase timeout in tests (edit test files)
```

### Docker Tests Fail
```bash
# Error: Service not available
# Solution: Build and run container
docker build -t boloo-backend:latest ..
docker run -d -p 8000:8000 --name boloo-test \
  -e DEVELOPMENT_MODE=true \
  boloo-backend:latest

# Check logs
docker logs boloo-test
```

---

## 📚 Documentation

### Full Guides
- **Test Execution Guide:** `/docs/test_execution_guide.md`
- **Production Readiness:** `/docs/production_readiness_checklist.md`
- **Quick Reference:** `/docs/test_quick_reference.md`
- **Test Summary:** `/docs/TEST_SUMMARY.md`

### Test Files
- **Backend Tests:** `test_auth_persistence.py`
- **Mobile Tests:** `integration/test_mobile_auth_flow.py`
- **Docker Tests:** `smoke/test_docker_deployment.py`

---

## 🎯 What's Tested

### Authentication
- [x] OTP request and verification
- [x] JWT token generation with claims
- [x] Token validation and expiration
- [x] Phone verification status tracking
- [x] Secure authentication flow

### Persistence
- [x] Token storage in AsyncStorage
- [x] Auto-login on app restart
- [x] Session persistence across restarts
- [x] Secure logout and cleanup
- [x] Multiple login/logout cycles

### Security
- [x] JWT signature validation
- [x] Token expiration enforcement
- [x] Invalid token rejection
- [x] OTP reuse prevention
- [x] Payload tampering detection

### API Endpoints
- [x] `/auth/request-otp`
- [x] `/auth/verify-otp`
- [x] `/auth/verify`
- [x] `/chat` (with authentication)
- [x] `/health`
- [x] `/health/db`

---

## 📈 Test Metrics

| Suite | Tests | Duration | Coverage |
|-------|-------|----------|----------|
| Backend API | 20+ | ~5s | >90% |
| Mobile Integration | 8 | ~30s | >85% |
| Docker Smoke | 6 | ~15s | N/A |
| **Total** | **45+** | **~50s** | **>80%** |

---

## 🔍 Test Details

### Backend API Tests

```python
# Example: Test OTP verification
def test_otp_verification_updates_phone_verified(self, mock_db):
    """Verify that OTP verification sets phone_verified to True"""
    # Test implementation validates database update
```

**Classes:**
- `TestOTPVerification` (5 tests)
- `TestJWTTokens` (3 tests)
- `TestTokenValidation` (6 tests)
- `TestAuthPersistence` (3 tests)
- `TestSecurityFeatures` (4 tests)

### Mobile Integration Tests

```python
# Example: Test auto-login
def test_02_auto_login_after_restart(self, client, test_phone, test_otp):
    """Test that auto-login works after app restart"""
    # Simulates complete mobile app flow
```

**Scenarios:**
1. Complete login flow
2. Auto-login after restart
3. Logout clears tokens
4. Auto-login fails after logout
5. Chat requires auth
6. Token persistence
7. OTP re-verification
8. Storage isolation

### Docker Smoke Tests

```python
# Example: Test health endpoint
def test_health_endpoint(self) -> Dict:
    """Validate service health check"""
    # Quick deployment validation
```

**Checks:**
- Service availability
- Health endpoints
- Database connectivity
- API endpoints
- Authentication flow

---

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run tests
        run: cd tests && ./run_all_tests.sh
```

---

## 💡 Tips

### Running Specific Tests
```bash
# Run tests matching a pattern
pytest -k "otp" -v

# Run tests in a specific file
pytest test_auth_persistence.py -v

# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Debugging
```bash
# Run with detailed traceback
pytest --tb=long

# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest -l
```

### Coverage
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Show missing lines
pytest --cov=app --cov-report=term-missing

# Coverage with branch checking
pytest --cov=app --cov-branch
```

---

## 🆘 Need Help?

1. **Check the guides:**
   - Full guide: `/docs/test_execution_guide.md`
   - Quick ref: `/docs/test_quick_reference.md`

2. **Common issues:**
   - See troubleshooting section above
   - Check backend logs: `docker logs boloo-test`

3. **Contact:**
   - Development team
   - Project documentation

---

**Last Updated:** 2025-11-24
**Version:** 1.0
**Status:** ✅ Complete and Ready

