# Deployment Scripts - Boloo Application

**Version**: 1.0.0
**Last Updated**: 2025-11-23

---

## 📁 Files in This Directory

| Script | Size | Purpose | Runtime |
|--------|------|---------|---------|
| `validate-deployment.sh` | 14KB | Comprehensive deployment validation | 2-3 min |
| `smoke-tests.sh` | 12KB | Quick critical endpoint testing | 30 sec |
| `rollback.sh` | 16KB | Automated rollback system | 2-3 min |

---

## 🚀 Quick Usage Guide

### After Every Deployment

```bash
# 1. Quick smoke tests (30 seconds)
./smoke-tests.sh

# 2. Full validation (2-3 minutes)
./validate-deployment.sh

# 3. Rollback if needed
./rollback.sh
```

### Environment Variables

All scripts support these environment variables:

```bash
export BACKEND_URL="https://boloo-backend-api.azurewebsites.net"
export FRONTEND_URL="https://www.bultoo.com"
export RESOURCE_GROUP="boloo-production-rg"
export BACKEND_APP_NAME="boloo-backend-api"
export FRONTEND_APP_NAME="www.bultoo.com"
```

---

## 📊 validate-deployment.sh

### Purpose
Comprehensive post-deployment validation with health checks, endpoint testing, and error rate analysis.

### Usage
```bash
./validate-deployment.sh
```

### What It Checks

1. **Prerequisites**
   - Azure CLI installed
   - curl available
   - jq available (optional)

2. **Azure Authentication**
   - Logged into correct subscription

3. **Backend App Status**
   - App Service running
   - No deployment errors

4. **Health Endpoint**
   - `/health` returns 200
   - Database connection healthy
   - Redis connection healthy (if configured)

5. **Critical Endpoints**
   - `/v1/chat/start` - Chat functionality
   - `/api/dropdown/states` - State dropdown
   - `/api/dropdown/districts` - District dropdown
   - `/api/v1/docs` - API documentation

6. **CORS Headers**
   - Access-Control-Allow-Origin present
   - Access-Control-Allow-Methods correct
   - Access-Control-Allow-Headers correct

7. **Database Connectivity**
   - Can query LGD data
   - Returns expected results

8. **Environment Configuration**
   - DATABASE_URL configured
   - AZURE_OPENAI_ENDPOINT configured
   - AZURE_OPENAI_API_KEY configured
   - JWT_SECRET_KEY configured

9. **Error Rates**
   - Downloads recent logs
   - Analyzes error frequency
   - Alerts if >5% error rate

10. **Response Times**
    - Tests 5 requests
    - Calculates average
    - Warns if >2000ms

### Output Files

- **Log**: `/tmp/deployment-validation-YYYYMMDD-HHMMSS.log`
- **Metrics**: `/tmp/deployment-metrics-YYYYMMDD-HHMMSS.json`

### Exit Codes

- `0` - All checks passed ✅
- `1` - One or more checks failed ❌

### Example Output

```
═══════════════════════════════════════════════════════════
  DEPLOYMENT VALIDATION - Boloo Backend API
═══════════════════════════════════════════════════════════
Backend: https://boloo-backend-api.azurewebsites.net
Frontend: https://www.bultoo.com
Resource Group: boloo-production-rg
═══════════════════════════════════════════════════════════

[2025-11-23 20:00:00] Checking prerequisites...
[2025-11-23 20:00:00] ✅ Prerequisites check passed

[2025-11-23 20:00:01] Checking Azure authentication...
[2025-11-23 20:00:02] ✅ Authenticated to Azure subscription: Pay-As-You-Go

[2025-11-23 20:00:02] Checking backend app service status...
[2025-11-23 20:00:03] ✅ Backend app service is running

[2025-11-23 20:00:03] Testing health endpoint...
[2025-11-23 20:00:04] ✅ Health endpoint responding (HTTP 200)
[2025-11-23 20:00:04] ✅ Database connection: healthy

[... more checks ...]

═══════════════════════════════════════════════════════════
✅ VALIDATION PASSED - Deployment is healthy
Log file: /tmp/deployment-validation-20251123-200000.log
Metrics file: /tmp/deployment-metrics-20251123-200000.json
═══════════════════════════════════════════════════════════
```

---

## 🎯 smoke-tests.sh

### Purpose
Quick validation of critical user flows - designed to run in <1 minute.

### Usage
```bash
./smoke-tests.sh
```

### Tests Performed

1. **Health Check** - `/health` returns 200
2. **Chat Start** - Chat endpoint works, returns conversation_id
3. **States Dropdown** - Returns list of Indian states
4. **Districts Dropdown** - Returns districts for Maharashtra
5. **CORS Headers** - All CORS headers present
6. **Database Connectivity** - Can query database
7. **API Documentation** - Swagger UI accessible
8. **Frontend Availability** - Frontend loads
9. **Response Times** - Under 2 seconds
10. **End-to-End Flow** - Complete user journey works

### Output

```
═══════════════════════════════════════════════════════════
  SMOKE TESTS - Boloo Deployment
═══════════════════════════════════════════════════════════
Backend: https://boloo-backend-api.azurewebsites.net
Frontend: https://www.bultoo.com
Test User ID: 11111111-1111-4000-8111-000000000000
═══════════════════════════════════════════════════════════

[TEST] Health Check Endpoint
  ✅ PASS: Health endpoint returns 200 OK

[TEST] Chat Start Endpoint (/v1/chat/start)
  ✅ PASS: Chat start endpoint returns 200 OK
  ✅ PASS: Response contains conversation_id
  ✅ PASS: Response contains message

[TEST] States Dropdown Endpoint (/api/dropdown/states)
  ✅ PASS: States endpoint returns 200 OK
  ✅ PASS: Returned 36 states

[... 7 more tests ...]

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

### Custom Test User

```bash
# Test with custom user ID
TEST_USER_ID="your-user-id" ./smoke-tests.sh
```

---

## ⏮️ rollback.sh

### Purpose
Automated deployment rollback system with failure detection and incident reporting.

### Features

- 🔍 **Automatic Failure Detection**: Monitors deployment health
- 🔄 **Retry Logic**: 3 validation attempts with 30s delay
- ⏮️ **Smart Rollback**: Uses deployment slots or redeployment
- ✅ **Post-Rollback Validation**: Ensures rolled-back version works
- 📊 **Incident Reports**: Auto-generated Markdown reports
- 📧 **Notifications**: Email notification preparation

### Usage

```bash
# Automatic mode (default)
AUTO_ROLLBACK=true ./rollback.sh

# Manual mode
AUTO_ROLLBACK=false ./rollback.sh
```

### Rollback Triggers

The script will trigger rollback if:

1. Health check fails 3 times (30s between retries)
2. Smoke tests fail
3. Error rate exceeds 5%
4. Response time exceeds 2000ms

### Rollback Process

```
1. Detect Deployment Failure
   ├── Run validation
   ├── Retry 3 times (30s delay)
   └── If all fail → Trigger rollback

2. Find Previous Deployment
   ├── Query deployment history
   ├── Get last successful deployment
   └── Verify it exists

3. Perform Rollback
   ├── Use deployment slots (if available)
   ├── OR redeploy previous version
   └── Restart application

4. Validate Rollback
   ├── Wait 30 seconds
   ├── Run smoke tests
   └── Verify health

5. Generate Report
   ├── Create incident report
   ├── Save to /tmp/boloo-incidents/
   └── Prepare email notification

6. Notify Team
   └── Email to admin (if configured)
```

### Output Files

- **Rollback Log**: `/tmp/rollback-YYYYMMDD-HHMMSS.log`
- **Incident Report**: `/tmp/boloo-incidents/INC-YYYYMMDD-HHMMSS.md`

### Incident Report Example

```markdown
# Deployment Incident Report
**Incident ID**: INC-20251123-200000
**Timestamp**: 2025-11-23 20:00:00 UTC
**Severity**: Critical
**Status**: Resolved (Rolled Back)

---

## Summary
Automatic deployment rollback was triggered due to failed deployment validation.

## Incident Details

### Reason for Rollback
Health check failed 3 consecutive times. Smoke tests failed.

### Rollback Status
- **Automatic Rollback**: true
- **Rollback Success**: true
- **Timestamp**: 2025-11-23 20:05:00 UTC

[... detailed incident information ...]
```

### Exit Codes

- `0` - Rollback successful ✅
- `1` - Rollback failed ❌

---

## 🔧 Integration Examples

### GitHub Actions

```yaml
- name: Validate deployment
  run: ./scripts/deployment/validate-deployment.sh

- name: Rollback on failure
  if: failure()
  run: |
    AUTO_ROLLBACK=true ./scripts/deployment/rollback.sh
```

### Azure DevOps

```yaml
- script: |
    chmod +x scripts/deployment/smoke-tests.sh
    ./scripts/deployment/smoke-tests.sh
  displayName: 'Run smoke tests'

- script: |
    chmod +x scripts/deployment/rollback.sh
    AUTO_ROLLBACK=true ./scripts/deployment/rollback.sh
  condition: failed()
  displayName: 'Rollback on failure'
```

### Manual Deployment Script

```bash
#!/bin/bash
set -e

# Deploy
az webapp deployment source config-zip \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --src deploy.zip

# Wait
sleep 60

# Restart
az webapp restart \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

sleep 30

# Validate
cd scripts/deployment
./smoke-tests.sh || {
  echo "Smoke tests failed, triggering rollback..."
  AUTO_ROLLBACK=true ./rollback.sh
  exit 1
}

./validate-deployment.sh || {
  echo "Validation failed, triggering rollback..."
  AUTO_ROLLBACK=true ./rollback.sh
  exit 1
}

echo "✅ Deployment successful and validated"
```

---

## 🎓 Best Practices

### Before Deployment

1. ✅ Test in staging environment
2. ✅ Create database backup
3. ✅ Review recent changes
4. ✅ Notify team of deployment
5. ✅ Have rollback plan ready

### During Deployment

1. ✅ Monitor deployment logs
2. ✅ Wait for deployment to complete
3. ✅ Restart app service
4. ✅ Run smoke tests immediately
5. ✅ Run full validation

### After Deployment

1. ✅ Monitor for 30 minutes
2. ✅ Check error rates
3. ✅ Verify user flows
4. ✅ Review performance metrics
5. ✅ Document any issues

### If Issues Occur

1. 🚨 Check smoke tests output
2. 🚨 Review validation logs
3. 🚨 Trigger rollback if critical
4. 🚨 Investigate root cause
5. 🚨 Document in incident report

---

## 📞 Troubleshooting

### Scripts Won't Execute

```bash
# Make executable
chmod +x *.sh

# Check line endings (must be LF, not CRLF)
dos2unix *.sh  # If needed
```

### Azure CLI Not Authenticated

```bash
# Login to Azure
az login

# Verify authentication
az account show
```

### Validation Fails but Deployment is OK

```bash
# Run with verbose output
bash -x ./validate-deployment.sh

# Check specific endpoint manually
curl -v https://boloo-backend-api.azurewebsites.net/health
```

### Rollback Not Working

```bash
# Check deployment history
az webapp deployment list \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --output table

# Manual rollback
az webapp deployment slot swap \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --slot staging \
  --target-slot production
```

---

## 📚 Related Documentation

- **Complete Deployment Guide**: `/Users/diptendu/boloo app/boloo-app/docs/deployment/SAFE_DEPLOYMENT.md`
- **Quick Start**: `/Users/diptendu/boloo app/boloo-app/docs/deployment/DEPLOYMENT_SAFETY_SYSTEM.md`
- **Production Report**: `/Users/diptendu/boloo app/boloo-app/backend/PRODUCTION_DEPLOYMENT_REPORT.md`
- **Recovery Guide**: `/Users/diptendu/boloo app/boloo-app/docs/RECOVERY_CHECKPOINT.md`

---

## 🔗 Support

**DevOps Contact**: diptendudip@gmail.com

**Issues**: Create issue in repository

**Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade

---

**Version**: 1.0.0
**Last Updated**: 2025-11-23
**Maintained By**: DevOps Team
