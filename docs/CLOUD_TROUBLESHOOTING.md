# Boloo App - Cloud Deployment Troubleshooting Guide

**Last Updated:** November 22, 2025
**Environment:** Azure Production

---

## 📋 Table of Contents

1. [Common Deployment Issues](#common-deployment-issues)
2. [How to Check Logs](#how-to-check-logs)
3. [How to Restart Services](#how-to-restart-services)
4. [How to Rollback Deployments](#how-to-rollback-deployments)
5. [Database Connection Issues](#database-connection-issues)
6. [SSL Certificate Issues](#ssl-certificate-issues)
7. [Performance Issues](#performance-issues)
8. [Emergency Procedures](#emergency-procedures)

---

## 🚨 Common Deployment Issues

### Issue 1: Backend API Returns 404 on All Endpoints

**Status:** 🔴 **ACTIVE ISSUE**

**Symptoms:**
- `curl https://boloo-backend-api.azurewebsites.net/api/v1/cases` returns 404
- `/docs` endpoint not accessible
- Default Gunicorn page shows instead of FastAPI app

**Root Cause:**
```
No framework detected; using default app from /opt/defaultsite
Application is running default Gunicorn app, not FastAPI
```

**Diagnostic Commands:**
```bash
# Check application status
az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "{state:state,defaultHostName:defaultHostName}"

# View recent logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "framework\|error"

# Check startup command
az webapp config show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "appCommandLine"
```

**Solution:**
```bash
# Set correct startup command
az webapp config set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --startup-file "gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120"

# Restart application
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Wait 30 seconds and test
sleep 30
curl https://boloo-backend-api.azurewebsites.net/health
```

**Verification:**
```bash
# Should return FastAPI response, not default page
curl https://boloo-backend-api.azurewebsites.net/docs

# Check logs for successful startup
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "uvicorn\|fastapi"
```

---

### Issue 2: Virtual Environment Not Detected

**Symptoms:**
```
WARNING: Could not find virtual environment directory /home/site/wwwroot/antenv.
WARNING: Could not find package directory /home/site/wwwroot/__oryx_packages__.
```

**Root Cause:**
Oryx build system not creating Python virtual environment properly.

**Solution:**

**Option A: Configure Oryx build (Recommended)**
```bash
# Add oryx-manifest.toml to backend directory
cat > "/Users/diptendu/boloo app/boloo-app/backend/oryx-manifest.toml" << 'EOF'
[build]
platformName = "python"
platformVersion = "3.11"
virtualEnvironmentPath = "/tmp/8dc5d7e"

[run]
command = "gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
EOF

# Enable build during deployment
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Redeploy
cd "/Users/diptendu/boloo app/boloo-app/backend"
az webapp deployment source config-zip \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --src backend.zip
```

**Option B: Use custom Docker container**
```bash
# Build and push Docker image
cd "/Users/diptendu/boloo app/boloo-app/backend"
az acr build \
  --registry YOUR_REGISTRY \
  --image boloo-backend:latest \
  --file Dockerfile \
  .

# Update app to use container
az webapp config container set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --docker-custom-image-name YOUR_REGISTRY.azurecr.io/boloo-backend:latest
```

---

### Issue 3: Database Connection Timeout

**Symptoms:**
- `psycopg2.OperationalError: timeout expired`
- `could not connect to server`
- Intermittent 500 errors on API

**Diagnostic:**
```bash
# Test database connectivity
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "state"

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --name boloo-database \
  --resource-group boloo-production-rg \
  -o table

# Check connection from App Service
az webapp ssh --name boloo-backend-api --resource-group boloo-production-rg
# In SSH session:
$ psql "postgresql://booloadmin:PASSWORD@boloo-database.postgres.database.azure.com/flexibleserverdb?sslmode=require"
```

**Solution:**
```bash
# 1. Verify database is running
az postgres flexible-server start \
  --name boloo-database \
  --resource-group boloo-production-rg

# 2. Add App Service outbound IPs to firewall
APP_IPS=$(az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "outboundIpAddresses" -o tsv | tr ',' '\n')

for IP in $APP_IPS; do
  az postgres flexible-server firewall-rule create \
    --name boloo-database \
    --resource-group boloo-production-rg \
    --rule-name "AppService-$IP" \
    --start-ip-address "$IP" \
    --end-ip-address "$IP"
done

# 3. Verify DATABASE_URL is correct
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "[?name=='DATABASE_URL']"

# 4. Increase connection pool settings
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings \
    SQLALCHEMY_POOL_SIZE=5 \
    SQLALCHEMY_MAX_OVERFLOW=10 \
    SQLALCHEMY_POOL_TIMEOUT=30
```

---

### Issue 4: Static Web App Not Loading (404)

**Symptoms:**
- Web application shows 404 or blank page
- JavaScript not loading
- Routes not working

**Diagnostic:**
```bash
# Check deployment status
az staticwebapp show \
  --name boloo-web-admin \
  --resource-group boloo-production-rg \
  --query "{name:name,defaultHostname:defaultHostname,repositoryUrl:repositoryUrl}"

# Check GitHub Actions deployment
gh run list --limit 5
gh run view --log
```

**Solution:**

**If deployment failed:**
```bash
# Trigger manual deployment
cd "/Users/diptendu/boloo app/boloo-app"
git add .
git commit -m "Trigger deployment"
git push origin main

# Monitor deployment
gh run watch
```

**If routes not working:**
```bash
# Verify staticwebapp.config.json exists
cat "/Users/diptendu/boloo app/boloo-app/web/staticwebapp.config.json"

# Should include navigationFallback
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/_next/*", "/api/*", "/*.{css,scss,js,png,jpg,gif,svg}"]
  }
}

# Redeploy if missing
```

---

### Issue 5: Environment Variables Not Applied

**Symptoms:**
- App can't connect to Azure services
- "Configuration value not found" errors
- API keys showing as undefined

**Diagnostic:**
```bash
# List all app settings
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  -o table

# Check specific variable
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "[?name=='AZURE_OPENAI_API_KEY'].{Name:name,Value:value}"
```

**Solution:**
```bash
# Set missing environment variables
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://cgnet-openai.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
    # ... add other variables

# Restart to apply
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Verify in logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "environment\|config"
```

---

## 📜 How to Check Logs

### Backend API Logs

**Live streaming (real-time):**
```bash
# All logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Filter for errors
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "error\|exception\|traceback"

# Filter for specific keyword
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "database\|openai"
```

**Download log archives:**
```bash
# Download all logs as ZIP
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --log-file boloo-logs-$(date +%Y%m%d-%H%M).zip

# Extract and view
unzip boloo-logs-*.zip
ls -lh LogFiles/

# View docker logs
cat LogFiles/*_docker.log

# View application logs
cat LogFiles/Application/diagnostics-*.txt
```

**Via Kudu console:**
```bash
# Access Kudu
open https://boloo-backend-api.scm.azurewebsites.net

# Navigate to:
Debug console → CMD → LogFiles
- Application/
- kudu/
- docker logs
```

**Via Azure Portal:**
```bash
# Portal log viewer
1. Go to Azure Portal
2. Navigate to boloo-backend-api
3. Left menu → "Logs" or "Log stream"
4. Real-time view of logs
```

### Web Application Logs

**GitHub Actions logs:**
```bash
# List recent workflow runs
gh run list --limit 10

# View specific run
gh run view <RUN_ID>

# View failed run logs
gh run view <RUN_ID> --log-failed

# Download logs
gh run download <RUN_ID>
```

**Static Web App diagnostics:**
```bash
# Check deployment status
az staticwebapp show \
  --name boloo-web-admin \
  --resource-group boloo-production-rg

# No direct logs, check GitHub Actions
```

### Database Logs

**PostgreSQL logs:**
```bash
# List server logs
az postgres flexible-server server-logs list \
  --resource-group boloo-production-rg \
  --server-name boloo-database

# Download specific log
az postgres flexible-server server-logs download \
  --resource-group boloo-production-rg \
  --server-name boloo-database \
  --name LOG_FILE_NAME
```

---

## 🔄 How to Restart Services

### Restart Backend API

**Standard restart:**
```bash
# Graceful restart
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Wait for restart (30-60 seconds)
sleep 45

# Verify
curl https://boloo-backend-api.azurewebsites.net/health
```

**Force restart (if hung):**
```bash
# Stop application
az webapp stop \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Wait 10 seconds
sleep 10

# Start application
az webapp start \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Verify
az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "state"
```

### Restart Database

**⚠️ WARNING: This causes downtime!**
```bash
# Restart PostgreSQL server
az postgres flexible-server restart \
  --name boloo-database \
  --resource-group boloo-production-rg

# Takes 2-5 minutes
# Monitor status
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "state"
```

### Restart Static Web App

**No direct restart needed - redeploy:**
```bash
# Trigger redeployment via GitHub Actions
cd "/Users/diptendu/boloo app/boloo-app"
git commit --allow-empty -m "Trigger redeploy"
git push origin main

# Monitor deployment
gh run watch
```

---

## ⏪ How to Rollback Deployments

### Rollback Backend API

**Method 1: Swap deployment slots (if configured)**
```bash
# List deployment slots
az webapp deployment slot list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Swap staging to production
az webapp deployment slot swap \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --slot staging \
  --target-slot production
```

**Method 2: Redeploy previous version**
```bash
# List deployment history
az webapp deployment list-publishing-credentials \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Get previous deployment
cd "/Users/diptendu/boloo app/boloo-app/backend"
git log --oneline -10

# Checkout previous commit
git checkout <PREVIOUS_COMMIT_HASH>

# Create deployment package
zip -r backend-rollback.zip . -x "*.git*" "*.pyc" "__pycache__/*"

# Deploy
az webapp deployment source config-zip \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --src backend-rollback.zip

# Return to main
git checkout main
```

### Rollback Web Application

**Via GitHub:**
```bash
# Find working commit
cd "/Users/diptendu/boloo app/boloo-app"
git log --oneline web/ -10

# Revert to previous commit
git revert <BAD_COMMIT_HASH>
git push origin main

# Or hard reset (use with caution)
git reset --hard <GOOD_COMMIT_HASH>
git push --force origin main

# Automatic deployment triggers
gh run watch
```

**Quick rollback:**
```bash
# Revert last commit
git revert HEAD
git push origin main
```

### Rollback Database Migrations

**⚠️ CRITICAL: Test in staging first!**
```bash
# SSH into app service
az webapp ssh --name boloo-backend-api --resource-group boloo-production-rg

# In SSH session:
$ cd /home/site/wwwroot
$ source antenv/bin/activate  # if venv exists
$ alembic current  # Check current migration
$ alembic downgrade -1  # Rollback one migration
$ alembic history  # Verify

# Exit SSH
$ exit

# Restart app
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

---

## 🗄️ Database Connection Issues

### Symptom: "Could not connect to server"

**Diagnostic steps:**
```bash
# 1. Check database status
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "{state:state,fullyQualifiedDomainName:fullyQualifiedDomainName}"

# 2. Test connectivity from local machine
psql "postgresql://booloadmin:YOUR_PASSWORD@boloo-database.postgres.database.azure.com/flexibleserverdb?sslmode=require"

# 3. Check firewall rules
az postgres flexible-server firewall-rule list \
  --name boloo-database \
  --resource-group boloo-production-rg \
  -o table

# 4. Get App Service outbound IPs
az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "{outboundIpAddresses:outboundIpAddresses,possibleOutboundIpAddresses:possibleOutboundIpAddresses}"
```

**Solution:**
```bash
# Add App Service IPs to database firewall
# Get all possible IPs
IPS=$(az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "possibleOutboundIpAddresses" -o tsv | tr ',' '\n')

# Add firewall rules
for IP in $IPS; do
  echo "Adding $IP to firewall"
  az postgres flexible-server firewall-rule create \
    --name boloo-database \
    --resource-group boloo-production-rg \
    --rule-name "AppService-$(echo $IP | tr '.' '-')" \
    --start-ip-address "$IP" \
    --end-ip-address "$IP"
done

# Verify
az postgres flexible-server firewall-rule list \
  --name boloo-database \
  --resource-group boloo-production-rg \
  -o table
```

### Symptom: "SSL connection required"

**Solution:**
```bash
# Verify DATABASE_URL includes sslmode=require
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "[?name=='DATABASE_URL'].value" -o tsv

# Should end with: ?sslmode=require

# If missing, update
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings DATABASE_URL="postgresql://booloadmin:PASSWORD@boloo-database.postgres.database.azure.com/flexibleserverdb?sslmode=require"
```

### Symptom: "Too many connections"

**Diagnostic:**
```bash
# Check current connections
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "storage"

# Connect and check
psql "postgresql://..." -c "SELECT count(*) FROM pg_stat_activity;"
```

**Solution:**
```bash
# Increase max connections (requires restart)
az postgres flexible-server parameter set \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --name max_connections \
  --value 100

# Configure connection pooling in app
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings \
    SQLALCHEMY_POOL_SIZE=5 \
    SQLALCHEMY_MAX_OVERFLOW=10 \
    SQLALCHEMY_POOL_PRE_PING=true \
    SQLALCHEMY_POOL_RECYCLE=3600

# Restart both
az postgres flexible-server restart --name boloo-database --resource-group boloo-production-rg
az webapp restart --name boloo-backend-api --resource-group boloo-production-rg
```

---

## 🔒 SSL Certificate Issues

### Issue: Certificate Expired or Invalid

**Symptoms:**
- Browser shows "Not Secure"
- SSL handshake errors
- Certificate warning

**For Azure-managed certificates (automatic renewal):**
```bash
# Check certificate status
az webapp config ssl list \
  --resource-group boloo-production-rg

# Force renewal (if needed)
az webapp config ssl bind \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --certificate-thumbprint AUTO \
  --ssl-type SNI

# Verify HTTPS enforcement
az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "httpsOnly"

# If false, enable
az webapp update \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --set httpsOnly=true
```

### Issue: Mixed Content (HTTP/HTTPS)

**Web app loading HTTP resources:**
```bash
# Check staticwebapp.config.json
cat "/Users/diptendu/boloo app/boloo-app/web/staticwebapp.config.json"

# Should have HSTS header
{
  "globalHeaders": {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
  }
}

# Update and redeploy if missing
```

---

## ⚡ Performance Issues

### Symptom: Slow Response Times (> 5 seconds)

**Diagnostic:**
```bash
# Check response time metrics
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric HttpResponseTime \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M \
  --aggregation Average,Maximum

# Check CPU usage
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric CpuTime \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M \
  --aggregation Total

# Check memory
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric MemoryWorkingSet \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M \
  --aggregation Average
```

**Solutions:**

**1. Scale up (vertical scaling):**
```bash
# Upgrade to B2 (double resources)
az appservice plan update \
  --name boloo-backend-plan \
  --resource-group boloo-production-rg \
  --sku B2

# Costs: ~₹2,100/month (was ₹1,050)
```

**2. Scale out (horizontal scaling):**
```bash
# Add more instances
az appservice plan update \
  --name boloo-backend-plan \
  --resource-group boloo-production-rg \
  --number-of-workers 2

# Costs: 2x current plan cost
```

**3. Optimize application:**
```bash
# Increase Gunicorn workers
az webapp config set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --startup-file "gunicorn app.main:app --workers 8 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120 --worker-tmp-dir /dev/shm"

# Enable application-level caching
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings \
    ENABLE_CACHE=true \
    CACHE_TTL=300
```

### Symptom: High Memory Usage

**Diagnostic:**
```bash
# Check memory consumption
az webapp ssh --name boloo-backend-api --resource-group boloo-production-rg

# In SSH:
$ free -h
$ top
$ ps aux --sort=-%mem | head -10
```

**Solution:**
```bash
# Restart to clear memory leaks
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Monitor for leaks
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "memory\|oom"
```

### Symptom: Cold Start Delays

**Azure App Service sleeps after inactivity (Basic tier)**

**Solutions:**

**1. Enable Always On (requires Standard tier or higher):**
```bash
# Upgrade to S1
az appservice plan update \
  --name boloo-backend-plan \
  --resource-group boloo-production-rg \
  --sku S1

# Enable Always On
az webapp config set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --always-on true

# Cost: ~₹5,000/month
```

**2. Keep-alive ping (Free alternative):**
```bash
# Set up external monitoring that pings every 5 minutes
# Use UptimeRobot or similar service
# Prevents app from sleeping
```

---

## 🆘 Emergency Procedures

### 🔥 Emergency: Complete Outage

**Immediate actions (5 minutes):**
```bash
# 1. Check all services
az resource list \
  --resource-group boloo-production-rg \
  --query "[].{Name:name, Type:type, State:properties.state}" \
  -o table

# 2. Restart backend
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# 3. Check database
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "state"

# 4. View recent errors
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i "critical\|error" \
  | tail -50
```

**Escalation (if not resolved in 10 minutes):**
```bash
# 1. Create support ticket
az support tickets create \
  --ticket-name "boloo-outage-$(date +%Y%m%d-%H%M)" \
  --title "Boloo Production Outage" \
  --severity moderate \
  --contact-email diptendudip@gmail.com

# 2. Check Azure status
open https://status.azure.com

# 3. Notify stakeholders
# Send email to team about outage
```

### 🔥 Emergency: Database Corruption

**⚠️ DO NOT proceed without backup!**
```bash
# 1. Immediately stop writes
az webapp stop \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# 2. Create backup
az postgres flexible-server backup create \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --backup-name emergency-$(date +%Y%m%d-%H%M)

# 3. Restore from latest backup
az postgres flexible-server restore \
  --name boloo-database-restored \
  --resource-group boloo-production-rg \
  --source-server boloo-database \
  --restore-point-in-time "2025-11-22T10:00:00Z"

# 4. Update DATABASE_URL to point to restored server
# 5. Restart backend app
```

### 🔥 Emergency: Security Breach

**Immediate lockdown:**
```bash
# 1. Rotate all secrets
# Generate new JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 32)

az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings JWT_SECRET_KEY="$NEW_JWT_SECRET"

# 2. Lock down database
az postgres flexible-server firewall-rule delete-all \
  --name boloo-database \
  --resource-group boloo-production-rg

# 3. Enable diagnostic logging
az webapp log config \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --application-logging filesystem \
  --level verbose

# 4. Review access logs
az monitor activity-log list \
  --resource-group boloo-production-rg \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  -o table

# 5. Create incident report
```

---

## 📞 Support Escalation

### Tier 1: Self-Service (< 30 min)
- Check this troubleshooting guide
- View logs via CLI or Portal
- Restart services
- Check Azure status page

### Tier 2: Community Support (< 2 hours)
- Azure Forums: https://docs.microsoft.com/answers/
- Stack Overflow: Tag `azure` + `fastapi`
- GitHub Issues: https://github.com/diptendudip/boloo-app/issues

### Tier 3: Azure Support (< 24 hours)
```bash
# Create support ticket
az support tickets create \
  --ticket-name "boloo-issue-$(date +%Y%m%d)" \
  --title "Production Issue Description" \
  --severity minimal \
  --contact-email diptendudip@gmail.com \
  --problem-classification "/Azure/App Service"
```

### Emergency Contact
**Technical Owner:** Diptendu
**Email:** diptendudip@gmail.com
**Azure Subscription:** 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc

---

## ✅ Quick Troubleshooting Checklist

Before opening a support ticket, verify:

- [ ] Azure services status page checked
- [ ] Resource group resources are all "Running"
- [ ] Recent logs reviewed for errors
- [ ] Service restart attempted
- [ ] Environment variables verified
- [ ] Database connectivity tested
- [ ] Firewall rules checked
- [ ] Recent deployments reviewed
- [ ] Metrics checked for anomalies
- [ ] Cost budget not exceeded

---

**Guide Last Updated:** November 22, 2025
**Maintained By:** DevOps Team
**Next Review:** December 22, 2025
