# Safe Deployment Guide - Boloo Application

**Version**: 1.0.0
**Last Updated**: 2025-11-23
**Target Environment**: Azure Production

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Process](#deployment-process)
4. [Post-Deployment Validation](#post-deployment-validation)
5. [Rollback Procedures](#rollback-procedures)
6. [Incident Response Plan](#incident-response-plan)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Overview

This guide provides comprehensive procedures for safely deploying the Boloo application to Azure production environment with automated validation and rollback capabilities.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 DEPLOYMENT PIPELINE                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Pre-Deployment Validation                           │
│     ├── Code Review                                     │
│     ├── Automated Tests                                 │
│     └── Security Scan                                   │
│                                                          │
│  2. Staging Deployment                                  │
│     ├── Deploy to Staging                               │
│     ├── Smoke Tests                                     │
│     └── Integration Tests                               │
│                                                          │
│  3. Production Deployment                               │
│     ├── Deploy Backend                                  │
│     ├── Deploy Frontend                                 │
│     └── Database Migrations                             │
│                                                          │
│  4. Post-Deployment Validation                          │
│     ├── Health Checks                                   │
│     ├── Smoke Tests                                     │
│     ├── Performance Validation                          │
│     └── Error Rate Monitoring                           │
│                                                          │
│  5. Automatic Rollback (if validation fails)            │
│     ├── Detect Failures                                 │
│     ├── Trigger Rollback                                │
│     ├── Validate Rollback                               │
│     └── Generate Incident Report                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Deployment Tools

| Tool | Purpose | Location |
|------|---------|----------|
| `validate-deployment.sh` | Comprehensive deployment validation | `scripts/deployment/` |
| `smoke-tests.sh` | Quick critical endpoint testing | `scripts/deployment/` |
| `rollback.sh` | Automated rollback system | `scripts/deployment/` |

---

## Pre-Deployment Checklist

### 1. Code Quality Validation

- [ ] All tests passing locally
- [ ] Code review completed and approved
- [ ] No console.log or debugging code
- [ ] All TODOs addressed or documented
- [ ] Dependencies updated and tested

```bash
# Run local tests
cd backend
python -m pytest tests/ -v

cd ../frontend
npm test
```

### 2. Environment Preparation

- [ ] Environment variables configured in Azure
- [ ] Secrets rotated (if needed)
- [ ] Database backup completed
- [ ] Deployment slots configured (if using)

```bash
# Verify environment variables
az webapp config appsettings list \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --query "[].{name:name}" -o table
```

### 3. Database Preparation

- [ ] Database migrations tested in staging
- [ ] Rollback migrations prepared
- [ ] Data backup completed
- [ ] Migration plan documented

```bash
# Create database backup
az postgres server backup create \
  --resource-group boloo-production-rg \
  --server-name boloo-db \
  --name pre-deployment-$(date +%Y%m%d-%H%M%S)
```

### 4. Communication

- [ ] Stakeholders notified of deployment window
- [ ] Maintenance window scheduled (if needed)
- [ ] Support team on standby
- [ ] Rollback plan communicated

### 5. Monitoring Setup

- [ ] Monitoring dashboards ready
- [ ] Alerts configured
- [ ] Log aggregation active
- [ ] Performance baselines recorded

---

## Deployment Process

### Step 1: Pre-Deployment Validation

```bash
# Navigate to backend directory
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Run production readiness check
./scripts/verify-production-ready.sh

# Build and test Docker image locally
docker build -t boloo-backend:test .
docker run -p 8000:8000 boloo-backend:test

# Test locally
curl http://localhost:8000/health
```

### Step 2: Deploy to Staging (Recommended)

```bash
# Deploy to staging slot
az webapp deployment slot create \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --slot staging

# Deploy to staging
az webapp deployment source config-zip \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --slot staging \
  --src deploy.zip

# Wait for deployment to complete
sleep 60

# Run smoke tests against staging
BACKEND_URL="https://boloo-backend-api-staging.azurewebsites.net" \
  ./scripts/deployment/smoke-tests.sh
```

### Step 3: Production Deployment

```bash
# Option A: Slot Swap (Zero-Downtime)
az webapp deployment slot swap \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --slot staging \
  --target-slot production

# Option B: Direct Deployment
az webapp deployment source config-zip \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --src deploy.zip

# Wait for deployment to complete
sleep 60

# Restart app service to ensure clean state
az webapp restart \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# Wait for app to be ready
sleep 30
```

### Step 4: Database Migrations (if needed)

```bash
# SSH into app service
az webapp ssh \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# Run migrations
alembic upgrade head

# Verify migration
alembic current

# Exit SSH
exit
```

### Step 5: Frontend Deployment

```bash
# Navigate to frontend
cd "../mobile-web"

# Build production bundle
npm run build

# Deploy to Azure Static Web Apps
az staticwebapp deploy \
  --name www.bultoo.com \
  --resource-group boloo-production-rg \
  --source ./build
```

---

## Post-Deployment Validation

### Automated Validation

Run the comprehensive validation script:

```bash
cd "/Users/diptendu/boloo app/boloo-app/scripts/deployment"

# Run full validation suite
./validate-deployment.sh
```

This script performs:
1. ✅ Prerequisites check
2. ✅ Azure authentication
3. ✅ Backend app status
4. ✅ Health endpoint test
5. ✅ Critical endpoints test
6. ✅ CORS headers validation
7. ✅ Database connectivity
8. ✅ Environment configuration
9. ✅ Error rate analysis
10. ✅ Response time check

### Manual Validation Steps

#### 1. Health Check

```bash
# Backend health
curl -i https://boloo-backend-api.azurewebsites.net/health

# Expected: HTTP 200 with JSON response
# {
#   "status": "healthy",
#   "database": "healthy",
#   "redis": "healthy"
# }
```

#### 2. API Documentation

```bash
# Verify Swagger UI accessible
curl -i https://boloo-backend-api.azurewebsites.net/api/v1/docs

# Expected: HTTP 200 with HTML
```

#### 3. Critical User Flows

**Test Chat Start:**
```bash
curl -v -X POST "https://boloo-backend-api.azurewebsites.net/v1/chat/start?user_id=11111111-1111-4000-8111-000000000000&language=hi" \
  -H "Origin: https://www.bultoo.com" \
  -H "Content-Type: application/json"

# Expected: HTTP 200 with conversation_id and message
```

**Test Address Dropdowns:**
```bash
# States
curl -i "https://boloo-backend-api.azurewebsites.net/api/dropdown/states" \
  -H "Origin: https://www.bultoo.com"

# Expected: HTTP 200 with array of states

# Districts
curl -i "https://boloo-backend-api.azurewebsites.net/api/dropdown/districts?stateCode=MH" \
  -H "Origin: https://www.bultoo.com"

# Expected: HTTP 200 with array of districts
```

#### 4. CORS Validation

```bash
curl -i -X OPTIONS "https://boloo-backend-api.azurewebsites.net/v1/chat/start" \
  -H "Origin: https://www.bultoo.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

# Expected headers:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization
```

#### 5. Frontend Validation

```bash
# Frontend loads
curl -i https://www.bultoo.com

# Expected: HTTP 200 with HTML
```

#### 6. End-to-End Test

1. Open https://www.bultoo.com in browser
2. Select State → District → Sub-District → Village
3. Click "Start Chat"
4. Verify chat loads and responds
5. Check browser console for errors

### Performance Validation

```bash
# Load test (requires Apache Bench)
ab -n 100 -c 10 https://boloo-backend-api.azurewebsites.net/api/dropdown/states

# Expected:
# - Requests per second: >50
# - Time per request (mean): <200ms
# - Failed requests: 0
```

### Monitoring Validation

```bash
# Check Azure Application Insights
az monitor app-insights metrics show \
  --resource-group boloo-production-rg \
  --app boloo-backend-api \
  --metric requests/duration \
  --aggregation avg

# View recent logs
az webapp log tail \
  --resource-group boloo-production-rg \
  --name boloo-backend-api
```

---

## Rollback Procedures

### Automatic Rollback

The automated rollback system (`rollback.sh`) continuously monitors deployment health and automatically rolls back on failures.

**Features:**
- ✅ Automatic failure detection
- ✅ Multiple validation retries
- ✅ Automatic rollback to previous version
- ✅ Post-rollback validation
- ✅ Incident report generation
- ✅ Email notifications

**Trigger Conditions:**
- Health check fails 3 times in a row
- Smoke tests fail
- Error rate exceeds 5%
- Response time exceeds 2 seconds

**Usage:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/scripts/deployment"

# Manual rollback trigger
./rollback.sh

# Automatic rollback (runs on deployment validation failure)
AUTO_ROLLBACK=true ./rollback.sh
```

### Manual Rollback

#### Quick Rollback (Deployment Slots)

```bash
# Swap back to previous slot
az webapp deployment slot swap \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --slot production \
  --target-slot staging
```

#### Rollback to Specific Version

```bash
# List recent deployments
az webapp deployment list \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --output table

# Note the deployment ID of the version to rollback to
# Example: abcd1234

# Redeploy specific version
az webapp deployment source sync \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# Restart app
az webapp restart \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# Wait and validate
sleep 30
./scripts/deployment/smoke-tests.sh
```

#### Database Rollback

```bash
# Rollback database migrations
az webapp ssh \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# Inside SSH session
alembic downgrade -1  # Go back one migration
# or
alembic downgrade <revision>  # Go back to specific revision

# Verify
alembic current
exit
```

#### Full System Rollback

```bash
# 1. Rollback backend
az webapp deployment slot swap \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --slot production \
  --target-slot staging

# 2. Rollback database (if needed)
# SSH and run: alembic downgrade -1

# 3. Rollback frontend
az staticwebapp deploy \
  --name www.bultoo.com \
  --resource-group boloo-production-rg \
  --source ./build-previous  # Previous build artifacts

# 4. Validate
./scripts/deployment/validate-deployment.sh
```

---

## Incident Response Plan

### Severity Levels

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **P0 - Critical** | Complete service outage | Immediate | All hands |
| **P1 - High** | Major feature broken | <15 minutes | DevOps + Engineering |
| **P2 - Medium** | Minor feature broken | <1 hour | DevOps |
| **P3 - Low** | Non-critical issue | <4 hours | Engineering |

### Incident Response Workflow

```
┌──────────────────────────────────────────────┐
│         INCIDENT DETECTED                     │
│  (Monitoring alert or user report)            │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│    1. ASSESS SEVERITY                         │
│    - Check service status                     │
│    - Determine user impact                    │
│    - Classify severity level                  │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│    2. IMMEDIATE RESPONSE                      │
│    - Alert on-call team                       │
│    - Start incident log                       │
│    - Begin investigation                      │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│    3. MITIGATION                              │
│    - Automatic rollback (if configured)       │
│    - Manual rollback (if needed)              │
│    - Service restoration                      │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│    4. VALIDATION                              │
│    - Run smoke tests                          │
│    - Verify service health                    │
│    - Monitor error rates                      │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│    5. POST-INCIDENT                           │
│    - Generate incident report                 │
│    - Root cause analysis                      │
│    - Preventive measures                      │
│    - Documentation update                     │
└──────────────────────────────────────────────┘
```

### Contact Information

**DevOps Team:**
- Email: diptendudip@gmail.com
- Escalation: (Configure on-call rotation)

**Azure Support:**
- Portal: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
- Phone: (Based on subscription tier)

### Incident Communication Template

```
Subject: [P{severity}] Boloo Production Incident - {Brief Description}

INCIDENT DETAILS
================
Severity: P{0-3}
Status: {Investigating/Mitigating/Resolved}
Started: {timestamp}
Duration: {duration}
Impact: {description of user impact}

CURRENT STATUS
==============
{What's happening right now}

ACTIONS TAKEN
=============
1. {action 1}
2. {action 2}
3. {action 3}

NEXT STEPS
==========
1. {next action 1}
2. {next action 2}

ETA: {estimated resolution time}

Will provide updates every {interval}.
```

---

## Monitoring and Alerting

### Key Metrics to Monitor

#### 1. Availability Metrics
- **Health Check Status**: 99.9% uptime target
- **HTTP Status Codes**: <0.1% 5xx errors
- **Service Uptime**: Continuous monitoring

#### 2. Performance Metrics
- **Response Time (p95)**: <200ms target
- **Response Time (p99)**: <500ms target
- **Throughput**: Requests per second
- **Database Query Time**: <50ms average

#### 3. Error Metrics
- **Error Rate**: <0.1% target
- **Exception Count**: Track by type
- **Failed Requests**: By endpoint

#### 4. Resource Metrics
- **CPU Usage**: <70% average
- **Memory Usage**: <80% average
- **Database Connections**: <80% of pool
- **Disk I/O**: Monitor for bottlenecks

### Azure Monitor Alerts

#### Create Alert Rules

```bash
# High error rate alert
az monitor metrics alert create \
  --name "high-error-rate" \
  --resource-group boloo-production-rg \
  --scopes "/subscriptions/{sub-id}/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --condition "count requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action email diptendudip@gmail.com

# High response time alert
az monitor metrics alert create \
  --name "high-response-time" \
  --resource-group boloo-production-rg \
  --scopes "/subscriptions/{sub-id}/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --condition "avg requests/duration > 2000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action email diptendudip@gmail.com
```

### Application Insights Dashboard

Key widgets to include:
1. **Availability**: Health check results over time
2. **Failed Requests**: Chart of HTTP 5xx errors
3. **Response Time**: p50, p95, p99 percentiles
4. **Server Exceptions**: Exception count by type
5. **Database Performance**: Query duration trends

---

## Common Issues and Solutions

### Issue 1: Backend Returns HTTP 500

**Symptoms:**
- API returns 500 Internal Server Error
- Health check fails
- Application logs show exceptions

**Diagnosis:**
```bash
# Check recent logs
az webapp log tail --resource-group boloo-production-rg --name boloo-backend-api

# Look for Python tracebacks or error messages
```

**Solutions:**
1. **Pydantic Validation Error:**
   ```bash
   # Check if code is properly deployed
   # Restart app service
   az webapp restart --resource-group boloo-production-rg --name boloo-backend-api
   ```

2. **Database Connection Error:**
   ```bash
   # Verify DATABASE_URL is set correctly
   az webapp config appsettings list \
     --resource-group boloo-production-rg \
     --name boloo-backend-api \
     --query "[?name=='DATABASE_URL']"
   ```

3. **Missing Dependencies:**
   ```bash
   # SSH into app and check
   az webapp ssh --resource-group boloo-production-rg --name boloo-backend-api
   pip list
   ```

### Issue 2: CORS Errors

**Symptoms:**
- Frontend shows CORS errors in console
- Preflight OPTIONS requests fail
- "Access-Control-Allow-Origin" header missing

**Diagnosis:**
```bash
# Test CORS headers
curl -i -X OPTIONS "https://boloo-backend-api.azurewebsites.net/v1/chat/start" \
  -H "Origin: https://www.bultoo.com" \
  -H "Access-Control-Request-Method: POST"
```

**Solutions:**
1. **Remove Azure CORS Configuration:**
   ```bash
   # Let FastAPI handle CORS
   az webapp cors remove --resource-group boloo-production-rg \
     --name boloo-backend-api --allowed-origins *
   ```

2. **Update ALLOWED_ORIGINS Environment Variable:**
   ```bash
   az webapp config appsettings set \
     --resource-group boloo-production-rg \
     --name boloo-backend-api \
     --settings ALLOWED_ORIGINS="https://www.bultoo.com,https://bultoo.com"
   ```

3. **Restart App:**
   ```bash
   az webapp restart --resource-group boloo-production-rg --name boloo-backend-api
   ```

### Issue 3: Deployment Doesn't Restart App

**Symptoms:**
- New code deployed but old code still running
- Changes not reflected in production
- Deployment shows success but no changes

**Solutions:**
1. **Manual Restart:**
   ```bash
   az webapp restart --resource-group boloo-production-rg --name boloo-backend-api

   # Wait for restart
   sleep 30

   # Verify
   curl https://boloo-backend-api.azurewebsites.net/health
   ```

2. **Stop and Start:**
   ```bash
   # Full stop/start cycle
   az webapp stop --resource-group boloo-production-rg --name boloo-backend-api
   sleep 10
   az webapp start --resource-group boloo-production-rg --name boloo-backend-api
   sleep 30
   ```

3. **Check Auto-Heal Settings:**
   ```bash
   # Configure auto-heal to restart on high error rate
   # Done in Azure Portal > App Service > Auto-heal
   ```

### Issue 4: Slow Response Times

**Symptoms:**
- API responses take >2 seconds
- Timeouts on frontend
- Users report slow loading

**Diagnosis:**
```bash
# Measure response time
time curl https://boloo-backend-api.azurewebsites.net/api/dropdown/states

# Check database performance
# Look for slow queries in Application Insights
```

**Solutions:**
1. **Scale Up App Service:**
   ```bash
   az appservice plan update \
     --resource-group boloo-production-rg \
     --name boloo-app-service-plan \
     --sku B2
   ```

2. **Add Database Indexes:**
   ```sql
   -- SSH into app, connect to database
   -- Add indexes on frequently queried columns
   CREATE INDEX idx_lgd_state_code ON lgd_data(state_code);
   CREATE INDEX idx_lgd_district_code ON lgd_data(district_code);
   ```

3. **Enable Caching:**
   ```python
   # Add Redis caching for dropdown data
   # Update app/api/dropdown.py
   ```

### Issue 5: Database Migration Failures

**Symptoms:**
- Alembic migration fails
- Database schema out of sync
- Application can't connect to database

**Solutions:**
1. **Check Current Migration Status:**
   ```bash
   az webapp ssh --resource-group boloo-production-rg --name boloo-backend-api
   alembic current
   alembic history
   ```

2. **Manually Fix Migration:**
   ```bash
   # Mark current schema as migrated
   alembic stamp head

   # Or rollback and retry
   alembic downgrade -1
   alembic upgrade head
   ```

3. **Restore from Backup (if needed):**
   ```bash
   az postgres server restore \
     --resource-group boloo-production-rg \
     --name boloo-db \
     --restore-point-in-time "2025-11-23T19:00:00Z" \
     --source-server boloo-db
   ```

---

## Best Practices

### ✅ DO

1. **Always test in staging first**
2. **Run smoke tests after deployment**
3. **Monitor for 30 minutes post-deployment**
4. **Keep rollback plan ready**
5. **Document all changes**
6. **Use deployment slots for zero-downtime**
7. **Create database backups before migrations**
8. **Run validation scripts automatically**
9. **Set up proper monitoring and alerts**
10. **Communicate with stakeholders**

### ❌ DON'T

1. **Don't deploy directly to production without testing**
2. **Don't skip validation steps**
3. **Don't deploy during peak hours (unless emergency)**
4. **Don't modify database directly in production**
5. **Don't commit secrets to version control**
6. **Don't skip database backups**
7. **Don't ignore warning signs in monitoring**
8. **Don't deploy without rollback plan**
9. **Don't make multiple changes at once**
10. **Don't leave deployments unmonitored**

---

## Appendix

### A. Quick Reference Commands

```bash
# Check deployment status
az webapp deployment list --resource-group boloo-production-rg --name boloo-backend-api --output table

# Restart backend
az webapp restart --resource-group boloo-production-rg --name boloo-backend-api

# View logs
az webapp log tail --resource-group boloo-production-rg --name boloo-backend-api

# Test health
curl https://boloo-backend-api.azurewebsites.net/health

# Run smoke tests
./scripts/deployment/smoke-tests.sh

# Run full validation
./scripts/deployment/validate-deployment.sh

# Trigger rollback
./scripts/deployment/rollback.sh
```

### B. Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint |
| `AZURE_OPENAI_API_KEY` | Yes | Azure OpenAI API key |
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `AZURE_SPEECH_KEY` | Yes | Azure Speech API key |
| `ALLOWED_ORIGINS` | Yes | CORS allowed origins |
| `REDIS_URL` | No | Redis connection string |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

### C. Support Resources

- **Azure Documentation**: https://docs.microsoft.com/en-us/azure/
- **Boloo Backend Docs**: `/Users/diptendu/boloo app/boloo-app/backend/docs/`
- **Deployment Reports**: `/Users/diptendu/boloo app/boloo-app/backend/PRODUCTION_DEPLOYMENT_REPORT.md`
- **Recovery Guide**: `/Users/diptendu/boloo app/boloo-app/docs/RECOVERY_CHECKPOINT.md`

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-23
**Maintained By**: DevOps Team
**Contact**: diptendudip@gmail.com
