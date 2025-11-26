# Test Execution Guide - Authentication & Persistence

## 📋 Overview
This guide provides step-by-step instructions for executing all authentication and persistence tests.

---

## 🔧 Prerequisites

### Backend Setup
```bash
# Navigate to backend directory
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Create virtual environment if not exists
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-cov requests
```

### Environment Configuration
```bash
# Create .env file with test configuration
cat > .env.test << EOF
DEVELOPMENT_MODE=true
JWT_SECRET_KEY=test_secret_key_for_jwt_tokens
DATABASE_URL=sqlite:///./test_database.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081
EOF
```

### Start Backend Server
```bash
# Terminal 1: Start the backend server
uvicorn app.main:app --reload --port 8000

# Wait for message: "Application startup complete"
```

---

## 🧪 Test Suite 1: Backend API Tests

### Purpose
Validates OTP verification, JWT token generation, and authentication endpoints.

### Run Tests
```bash
# Run all backend tests
pytest tests/test_auth_persistence.py -v

# Run with coverage report
pytest tests/test_auth_persistence.py -v --cov=app --cov-report=html

# Run specific test class
pytest tests/test_auth_persistence.py::TestOTPVerification -v

# Run specific test
pytest tests/test_auth_persistence.py::TestOTPVerification::test_otp_verification_updates_phone_verified -v
```

### Expected Output
```
tests/test_auth_persistence.py::TestOTPVerification::test_otp_verification_updates_phone_verified PASSED
tests/test_auth_persistence.py::TestOTPVerification::test_otp_verification_records_timestamp PASSED
tests/test_auth_persistence.py::TestJWTTokens::test_jwt_includes_phone_verified_field PASSED
tests/test_auth_persistence.py::TestTokenValidation::test_verify_endpoint_accepts_valid_token PASSED
...

======================== X passed in Y.YYs ========================
```

### Troubleshooting
- **Import errors**: Ensure virtual environment is activated
- **Module not found**: Run `pip install -r requirements.txt`
- **Database errors**: Check DATABASE_URL in .env
- **Mock errors**: Install `pytest-mock`: `pip install pytest-mock`

---

## 📱 Test Suite 2: Mobile Integration Tests

### Purpose
Simulates complete mobile app authentication flow including token persistence and auto-login.

### Run Tests
```bash
# Ensure backend is running on http://localhost:8000

# Run mobile integration tests
pytest tests/integration/test_mobile_auth_flow.py -v -s

# Run specific test
pytest tests/integration/test_mobile_auth_flow.py::TestMobileAuthFlow::test_01_complete_login_flow -v -s
```

### Expected Output
```
============================================================
TEST 1: Complete Login Flow
============================================================

📞 Requesting OTP for +1234567890
📱 AsyncStorage.setItem: access_token
📱 AsyncStorage.setItem: phone_number
🔐 Token saved to AsyncStorage

✅ TEST 1 PASSED: Login flow complete
PASSED

============================================================
TEST 2: Auto-login After App Restart
============================================================
...
```

### Test Scenarios Covered
1. ✅ Complete login flow
2. ✅ Auto-login after restart
3. ✅ Logout clears tokens
4. ✅ Auto-login fails after logout
5. ✅ Chat requires authentication
6. ✅ Token persists across restarts
7. ✅ OTP re-verification
8. ✅ Storage isolation

### Troubleshooting
- **Connection refused**: Ensure backend is running
- **401 errors**: Check OTP value (default: "123456" in dev mode)
- **Timeout errors**: Increase timeout in test configuration

---

## 🐳 Test Suite 3: Docker Container Smoke Tests

### Purpose
Validates Docker deployment with quick health checks.

### Prerequisites
```bash
# Build Docker image
docker build -t boloo-backend:latest .

# Run container
docker run -d \
  --name boloo-test \
  -p 8000:8000 \
  -e DEVELOPMENT_MODE=true \
  -e JWT_SECRET_KEY=test_secret \
  boloo-backend:latest

# Check container is running
docker ps | grep boloo-test
```

### Run Tests
```bash
# Run smoke tests
pytest tests/smoke/test_docker_deployment.py -v -s

# Or run standalone
python tests/smoke/test_docker_deployment.py
```

### Expected Output
```
============================================================
🚀 DOCKER DEPLOYMENT SMOKE TESTS
============================================================

⏳ Waiting for service at http://localhost:8000...
✅ Service is ready (attempt 1)

🏥 Testing health endpoint...
✅ Health check passed: {'status': 'healthy'}

🗄️  Testing database connection...
✅ Database connection successful

📞 Testing OTP request for +1234567890...
✅ OTP request successful

✅ Testing OTP verification...
✅ OTP verification successful - token received

🔐 Testing token verification...
✅ Token verification successful

💬 Testing chat endpoint...
✅ Chat endpoint working correctly

============================================================
📊 TEST SUMMARY
============================================================
Total Tests: 6
✅ Passed: 6
❌ Failed: 0
Success Rate: 100.0%
```

### Cleanup
```bash
# Stop and remove container
docker stop boloo-test
docker rm boloo-test
```

### Troubleshooting
- **Service not available**: Check container logs `docker logs boloo-test`
- **Port conflicts**: Change port mapping or stop conflicting services
- **Database errors**: Check volume mounts and permissions

---

## 📊 Test Coverage Report

### Generate Coverage Report
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html  # macOS
# OR
xdg-open htmlcov/index.html  # Linux
# OR
start htmlcov/index.html  # Windows
```

### Coverage Targets
- **Overall:** >80%
- **Authentication modules:** >90%
- **Critical paths:** 100%

---

## 🚀 Complete Test Run

### Run All Tests Sequentially
```bash
#!/bin/bash
# save as run_all_tests.sh

echo "🧪 Starting Complete Test Suite"
echo "================================"

# Backend API Tests
echo "\n📦 Running Backend API Tests..."
pytest tests/test_auth_persistence.py -v
BACKEND_EXIT=$?

# Mobile Integration Tests
echo "\n📱 Running Mobile Integration Tests..."
pytest tests/integration/test_mobile_auth_flow.py -v -s
MOBILE_EXIT=$?

# Docker Smoke Tests
echo "\n🐳 Running Docker Smoke Tests..."
pytest tests/smoke/test_docker_deployment.py -v -s
DOCKER_EXIT=$?

# Summary
echo "\n================================"
echo "📊 Test Suite Summary"
echo "================================"
echo "Backend Tests: $([ $BACKEND_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Mobile Tests: $([ $MOBILE_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Docker Tests: $([ $DOCKER_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"

# Exit with error if any test failed
[ $BACKEND_EXIT -eq 0 ] && [ $MOBILE_EXIT -eq 0 ] && [ $DOCKER_EXIT -eq 0 ]
exit $?
```

### Make Executable and Run
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

---

## 🔍 Test Reporting

### Generate Test Report
```bash
# Install pytest-html
pip install pytest-html

# Generate HTML report
pytest tests/ -v --html=test_report.html --self-contained-html

# Open report
open test_report.html
```

### CI/CD Integration
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
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📝 Test Checklist

Before considering tests complete:

- [ ] All backend API tests pass
- [ ] All mobile integration tests pass
- [ ] All Docker smoke tests pass
- [ ] Code coverage >80%
- [ ] No flaky tests (run 3x to verify)
- [ ] Tests pass in CI/CD environment
- [ ] Test documentation updated
- [ ] Known issues documented

---

## 🆘 Getting Help

### Common Issues

**Tests fail with "ModuleNotFoundError"**
```bash
# Solution: Install missing dependencies
pip install -r requirements.txt
pytest --version  # Verify pytest is installed
```

**Tests fail with "Connection refused"**
```bash
# Solution: Ensure backend is running
lsof -i :8000  # Check what's using port 8000
uvicorn app.main:app --port 8000  # Start backend
```

**Tests timeout**
```bash
# Solution: Increase timeout or check server responsiveness
curl http://localhost:8000/health  # Manual health check
```

### Contact
- **Team:** Development Team
- **Documentation:** `/docs`
- **Issues:** Track in project issue tracker

---

**Last Updated:** 2025-11-24
**Version:** 1.0
