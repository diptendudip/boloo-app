# Deployment Safety System - Quick Start Guide

**Created**: 2025-11-23
**Version**: 1.0.0
**Status**: Production Ready ✅

---

## 📋 Overview

A comprehensive automated deployment safety system with validation and rollback capabilities for the Boloo application on Azure.

### System Components

```
📁 scripts/deployment/
├── validate-deployment.sh    (14KB) - Comprehensive deployment validation
├── smoke-tests.sh            (12KB) - Quick critical endpoint tests
└── rollback.sh               (16KB) - Automated rollback system

📁 docs/deployment/
└── SAFE_DEPLOYMENT.md        (25KB) - Complete deployment guide
```

---

## 🚀 Quick Start

### 1. Post-Deployment Validation

After deploying to Azure, immediately run:

```bash
cd "/Users/diptendu/boloo app/boloo-app/scripts/deployment"

# Quick smoke tests (30 seconds)
./smoke-tests.sh

# Full validation suite (2-3 minutes)
./validate-deployment.sh
```

### 2. Automated Rollback (if validation fails)

```bash
# Automatic rollback on failure
AUTO_ROLLBACK=true ./rollback.sh

# Manual rollback trigger
./rollback.sh
```

---

## 🎯 What Each Script Does

### validate-deployment.sh

**Purpose**: Comprehensive post-deployment validation

**Checks Performed** (10 total):
1. ✅ Prerequisites (Azure CLI, curl, jq)
2. ✅ Azure authentication
3. ✅ Backend app service status
4. ✅ Health endpoint (/health)
5. ✅ Critical endpoints (chat, dropdowns, docs)
6. ✅ CORS headers
7. ✅ Database connectivity
8. ✅ Environment configuration
9. ✅ Error rates (last 100 log entries)
10. ✅ Response times (5 iterations)

**Usage**:
```bash
./validate-deployment.sh

# With custom URLs
BACKEND_URL="https://your-backend.azurewebsites.net" \
FRONTEND_URL="https://your-frontend.com" \
./validate-deployment.sh
```

**Output**:
- Console log with colored status
- Log file: `/tmp/deployment-validation-YYYYMMDD-HHMMSS.log`
- Metrics file: `/tmp/deployment-metrics-YYYYMMDD-HHMMSS.json`

**Exit Codes**:
- `0` - All validations passed ✅
- `1` - One or more validations failed ❌

---

### smoke-tests.sh

**Purpose**: Quick validation of critical user flows

**Tests Performed** (10 total):
1. Health Check
2. Chat Start Endpoint
3. States Dropdown
4. Districts Dropdown
5. CORS Headers
6. Database Connectivity
7. API Documentation
8. Frontend Availability
9. Response Time Performance
10. End-to-End User Flow

**Usage**:
```bash
./smoke-tests.sh

# With custom configuration
BACKEND_URL="https://your-backend.azurewebsites.net" \
FRONTEND_URL="https://your-frontend.com" \
TEST_USER_ID="your-test-user-id" \
./smoke-tests.sh
```

**Output**:
```
═══════════════════════════════════════════════════════════
  SMOKE TESTS - Boloo Deployment
═══════════════════════════════════════════════════════════

[TEST] Health Check Endpoint
  ✅ PASS: Health endpoint returns 200 OK

[TEST] Chat Start Endpoint (/v1/chat/start)
  ✅ PASS: Chat start endpoint returns 200 OK
  ✅ PASS: Response contains conversation_id
  ✅ PASS: Response contains message

[... more tests ...]

═══════════════════════════════════════════════════════════
  TEST RESULTS
═══════════════════════════════════════════════════════════
Tests Run: 10
Tests Passed: 10
Tests Failed: 0
Pass Rate: 100.0%
═══════════════════════════════════════════════════════════

✅ ALL SMOKE TESTS PASSED
```

**Exit Codes**:
- `0` - All tests passed ✅
- `1` - One or more tests failed ❌

---

### rollback.sh

**Purpose**: Automated deployment rollback system

**Features**:
- 🔍 Automatic failure detection
- 🔄 Multiple validation retries (3 attempts)
- ⏮️ Automatic rollback to previous version
- ✅ Post-rollback validation
- 📊 Incident report generation
- 📧 Email notification preparation

**Trigger Conditions**:
- Health check fails 3 times (with 30s retry delay)
- Smoke tests fail
- Error rate exceeds 5%
- Response time exceeds 2 seconds

**Usage**:
```bash
# Automatic mode (default)
AUTO_ROLLBACK=true ./rollback.sh

# Manual mode (for testing)
AUTO_ROLLBACK=false ./rollback.sh
```

**Rollback Process**:
1. Detect deployment failure
2. Retry validation 3 times (30s delay between retries)
3. Get previous successful deployment
4. Perform rollback (slot swap or redeployment)
5. Restart application
6. Validate rolled-back deployment
7. Generate incident report
8. Send notifications

**Output**:
- Console log with rollback progress
- Rollback log: `/tmp/rollback-YYYYMMDD-HHMMSS.log`
- Incident report: `/tmp/boloo-incidents/INC-YYYYMMDD-HHMMSS.md`

**Exit Codes**:
- `0` - Rollback successful and validated ✅
- `1` - Rollback failed or validation failed ❌

---

## 📖 Complete Documentation

For detailed deployment procedures, see:
**`/Users/diptendu/boloo app/boloo-app/docs/deployment/SAFE_DEPLOYMENT.md`**

Includes:
- Pre-deployment checklist
- Step-by-step deployment process
- Post-deployment validation procedures
- Manual rollback procedures
- Incident response plan
- Monitoring and alerting setup
- Common issues and solutions
- Best practices

---

## 🔧 Integration with CI/CD

### GitHub Actions Example

```yaml
name: Production Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Azure
        run: |
          # Your deployment commands
          az webapp deployment source config-zip ...

      - name: Wait for deployment
        run: sleep 60

      - name: Run smoke tests
        run: |
          chmod +x scripts/deployment/smoke-tests.sh
          ./scripts/deployment/smoke-tests.sh

      - name: Run validation
        run: |
          chmod +x scripts/deployment/validate-deployment.sh
          ./scripts/deployment/validate-deployment.sh

      - name: Rollback on failure
        if: failure()
        run: |
          chmod +x scripts/deployment/rollback.sh
          AUTO_ROLLBACK=true ./scripts/deployment/rollback.sh
```

---

## 🎯 Recommended Workflow

### Every Deployment

```bash
# 1. Deploy to Azure
cd "/Users/diptendu/boloo app/boloo-app/backend"
az webapp deployment source config-zip \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --src deploy.zip

# 2. Wait for deployment to complete
sleep 60

# 3. Restart app service (ensure clean state)
az webapp restart \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# 4. Wait for app to be ready
sleep 30

# 5. Run smoke tests
cd "/Users/diptendu/boloo app/boloo-app/scripts/deployment"
./smoke-tests.sh

# 6. If smoke tests pass, run full validation
./validate-deployment.sh

# 7. If validation fails, automatic rollback will trigger
# (if AUTO_ROLLBACK=true in rollback.sh)
```

### Emergency Rollback

```bash
cd "/Users/diptendu/boloo app/boloo-app/scripts/deployment"

# Immediate rollback
./rollback.sh

# Verify rollback success
./smoke-tests.sh
```

---

## 📊 Monitoring Integration

### Key Metrics Tracked

1. **Availability**
   - Health check status
   - HTTP status codes
   - Service uptime

2. **Performance**
   - Response time (p95, p99)
   - Throughput (requests/second)
   - Database query time

3. **Errors**
   - Error rate
   - Exception count
   - Failed requests by endpoint

4. **Resources**
   - CPU usage
   - Memory usage
   - Database connections

### Alert Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | >5% | Trigger rollback |
| Response Time | >2000ms | Warning |
| Health Check | 3 consecutive failures | Trigger rollback |
| CPU Usage | >80% | Scale up alert |
| Memory Usage | >85% | Scale up alert |

---

## 🚨 Recent Issue Context

Based on `PRODUCTION_DEPLOYMENT_REPORT.md` and `RECOVERY_CHECKPOINT.md`:

### Issue Encountered
- **Problem**: Backend deployed but may not have restarted properly
- **Symptom**: HTTP 500 errors on `/v1/chat/start` endpoint
- **Root Cause**: Pydantic validation error - deployed code missing updated helper functions
- **Solution**: Always restart app service after deployment + run validation scripts

### Prevention Measures (Implemented)

1. ✅ **Automated Validation**: `validate-deployment.sh` checks all critical endpoints
2. ✅ **Smoke Tests**: Quick tests for user-facing features
3. ✅ **Automatic Rollback**: Detects failures and rolls back automatically
4. ✅ **Incident Reports**: Auto-generated for all rollback events
5. ✅ **Deployment Guide**: Step-by-step procedures with restart steps

---

## 🎓 Best Practices

### ✅ DO

1. **Always run smoke tests after deployment**
2. **Wait 30 seconds after restart before testing**
3. **Monitor logs during and after deployment**
4. **Keep rollback plan ready**
5. **Document all deployment changes**

### ❌ DON'T

1. **Don't skip validation steps**
2. **Don't deploy without testing in staging first**
3. **Don't ignore failed smoke tests**
4. **Don't deploy during peak hours**
5. **Don't leave deployments unmonitored**

---

## 📞 Support

**DevOps Contact**: diptendudip@gmail.com

**Incident Response**: See `SAFE_DEPLOYMENT.md` Section 6

**Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade

---

## 🔗 Quick Links

- **Validation Script**: `/Users/diptendu/boloo app/boloo-app/scripts/deployment/validate-deployment.sh`
- **Smoke Tests**: `/Users/diptendu/boloo app/boloo-app/scripts/deployment/smoke-tests.sh`
- **Rollback Script**: `/Users/diptendu/boloo app/boloo-app/scripts/deployment/rollback.sh`
- **Full Documentation**: `/Users/diptendu/boloo app/boloo-app/docs/deployment/SAFE_DEPLOYMENT.md`
- **Production Report**: `/Users/diptendu/boloo app/boloo-app/backend/PRODUCTION_DEPLOYMENT_REPORT.md`
- **Recovery Guide**: `/Users/diptendu/boloo app/boloo-app/docs/RECOVERY_CHECKPOINT.md`

---

**System Status**: ✅ Production Ready
**Last Updated**: 2025-11-23
**Version**: 1.0.0
