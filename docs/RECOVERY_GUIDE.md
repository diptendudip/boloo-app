# Boloo App - Crash Recovery Guide

## Table of Contents
1. [Quick Recovery](#quick-recovery)
2. [Full System Reset](#full-system-reset)
3. [Common Issues](#common-issues)
4. [Verification Steps](#verification-steps)
5. [Troubleshooting](#troubleshooting)

---

## Quick Recovery

If VS Code or Claude Flow crashes, use this script for quick recovery:

```bash
cd "/Users/diptendu/boloo app/boloo-app"
./START_PROJECT.sh
```

### What This Script Does:
1. ✅ Checks if services are already running
2. ✅ Starts Docker services (PostgreSQL, Redis, MinIO)
3. ✅ Verifies Python virtual environment exists
4. ✅ Installs missing dependencies automatically
5. ✅ Starts backend (port 8000) and mobile (port 8081) with PM2
6. ✅ Tests backend connectivity

---

## Full System Reset

⚠️ **WARNING**: This will delete ALL local data and rebuild from scratch!

Use this **ONLY** when START_PROJECT.sh fails:

```bash
cd "/Users/diptendu/boloo app/boloo-app"
./FULL_RESET.sh
```

### What This Script Does:
1. 🛑 Stops all PM2 processes
2. 🗑️ Deletes Python virtual environment
3. 🐳 Rebuilds all Docker containers
4. 📦 Reinstalls all dependencies from scratch
5. 🗄️ Resets database (data loss!)
6. 🚀 Restarts all services

**You will be prompted for confirmation before any destructive actions.**

---

## Common Issues

### Issue 1: "Backend not responding"

**Symptoms:**
- Mobile app shows "Network Error"
- Cannot reach http://localhost:8000

**Solution:**
```bash
# Check if backend is running
pm2 status

# If not running, start it
cd "/Users/diptendu/boloo app/boloo-app/backend"
pm2 start "venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000" --name boloo-backend

# Check logs for errors
pm2 logs boloo-backend
```

### Issue 2: "ModuleNotFoundError" in Python

**Symptoms:**
- Backend crashes with `ModuleNotFoundError: No module named 'xxx'`
- Import errors in logs

**Solution:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
source venv/bin/activate
pip install <missing-package>

# Or reinstall all dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic python-jose passlib bcrypt python-multipart openai anthropic jsonschema azure-ai-formrecognizer redis python-dotenv pyjwt "numpy<2" faiss-cpu sentence-transformers scipy geoalchemy2 phonenumbers email-validator aiofiles aiosmtplib azure-cognitiveservices-speech azure-storage-blob pillow python-magic libmagic pydantic-settings uvloop rapidfuzz pydub

# Restart backend
pm2 restart boloo-backend
```

### Issue 3: "NumPy version incompatibility"

**Symptoms:**
- Error: `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`

**Solution:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
source venv/bin/activate
pip install "numpy<2" --force-reinstall
pm2 restart boloo-backend
```

### Issue 4: "Docker services not running"

**Symptoms:**
- PostgreSQL connection errors
- Redis connection errors

**Solution:**
```bash
cd "/Users/diptendu/boloo app/boloo-app"
docker-compose up -d

# Verify services are running
docker ps

# Check PostgreSQL
docker exec boloo-postgres pg_isready -U postgres

# Check Redis
docker exec boloo-redis redis-cli ping
```

### Issue 5: "Mobile Expo not responding"

**Symptoms:**
- QR code not showing
- Metro bundler not starting

**Solution:**
```bash
# Check if running
pm2 status

# Restart mobile
cd "/Users/diptendu/boloo app/boloo-app/mobile"
pm2 restart boloo-mobile

# Or start fresh
pm2 delete boloo-mobile
pm2 start "npx expo start" --name boloo-mobile

# Check logs
pm2 logs boloo-mobile
```

### Issue 6: "Port already in use"

**Symptoms:**
- Error: `EADDRINUSE: address already in use :::8000`

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Or for port 8081 (Expo)
lsof -ti:8081 | xargs kill -9

# Restart services
pm2 restart all
```

---

## Verification Steps

After recovery, verify everything is working:

### 1. Check PM2 Status
```bash
pm2 status
```
**Expected:**
- ✅ boloo-backend: online
- ✅ boloo-mobile: online

### 2. Check Backend Health
```bash
curl http://localhost:8000/v1/monitoring/health
```
**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T..."
}
```

### 3. Check Docker Services
```bash
docker ps
```
**Expected:**
- ✅ boloo-postgres: running
- ✅ boloo-redis: running
- ✅ boloo-minio: running

### 4. Test API Endpoints
```bash
# Test states endpoint
curl http://192.168.1.205:8000/api/dropdown/states

# Should return list of 36 states
```

### 5. Test Mobile Connection
- Open Expo Go app on your phone
- Scan QR code from terminal
- Navigate to "Update Address" screen
- Verify states dropdown loads (should show 36 states)

---

## Troubleshooting

### VS Code Crash Recovery Checklist

If VS Code crashes again, follow this checklist:

- [ ] Check if PM2 processes are still running: `pm2 status`
- [ ] Check if Docker services are running: `docker ps`
- [ ] Verify backend health: `curl http://localhost:8000/v1/monitoring/health`
- [ ] Check logs for errors: `pm2 logs`
- [ ] If issues persist, run: `./START_PROJECT.sh`
- [ ] If still broken, run: `./FULL_RESET.sh` (last resort)

### Python Virtual Environment Issues

If the Python venv gets corrupted:

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Delete corrupted venv
rm -rf venv __pycache__ .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Create fresh venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip wheel setuptools
# ... (install all packages as shown in Issue 2)
```

### PM2 Configuration Backup

PM2 saves your process configuration automatically. To manually save:

```bash
# Save current PM2 configuration
pm2 save

# Restore after system restart
pm2 resurrect
```

---

## File Locations

**Recovery Scripts:**
- Quick Recovery: `/Users/diptendu/boloo app/boloo-app/START_PROJECT.sh`
- Full Reset: `/Users/diptendu/boloo app/boloo-app/FULL_RESET.sh`

**Logs:**
- PM2 logs: `~/.pm2/logs/`
- Backend logs: `pm2 logs boloo-backend`
- Mobile logs: `pm2 logs boloo-mobile`

**Configuration:**
- PM2 config: `~/.pm2/dump.pm2`
- Docker Compose: `/Users/diptendu/boloo app/boloo-app/docker-compose.yml`
- Backend env: `/Users/diptendu/boloo app/boloo-app/backend/.env`

---

## Emergency Contacts & Resources

**Documentation:**
- This guide: `/Users/diptendu/boloo app/boloo-app/docs/RECOVERY_GUIDE.md`
- Backend README: `/Users/diptendu/boloo app/boloo-app/backend/README.md`
- Mobile README: `/Users/diptendu/boloo app/boloo-app/mobile/README.md`

**Useful Commands:**
```bash
# View all PM2 logs in real-time
pm2 logs

# Restart all services
pm2 restart all

# Stop all services
pm2 stop all

# Delete all PM2 processes
pm2 delete all

# Check backend port
lsof -i:8000

# Check mobile port
lsof -i:8081

# Docker compose commands
docker-compose up -d
docker-compose down
docker-compose logs -f
```

---

**Remember:** The quickest recovery path is usually:
1. Try `pm2 restart all`
2. If that fails, try `./START_PROJECT.sh`
3. Only use `./FULL_RESET.sh` as a last resort

---

## Lessons Learned from Nov 24, 2025 Recovery

### 🚨 Critical Issues Discovered

#### 1. Exposed API Keys
**Problem:** Production Azure API keys found in backend/.env file
**Impact:** Security risk - unauthorized access to Azure services
**Root Cause:** Keys copied to local environment for testing

**Prevention:**
```bash
# NEVER do this:
echo "AZURE_OPENAI_API_KEY=actual-key" >> .env

# ALWAYS use Azure Key Vault or app settings:
az webapp config appsettings set \
  --name app-name \
  --settings AZURE_OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=...)"
```

**Recovery Actions:**
1. Rotate all exposed keys immediately
2. Remove from local .env files
3. Verify .env in .gitignore
4. Check Git history for commits
5. If found in Git, consider all keys compromised

#### 2. Azure App Settings Lost
**Problem:** All Azure environment variables NULL or incorrect
**Impact:** Production application completely non-functional
**Root Cause:** Unknown - possible manual deletion or deployment issue

**Prevention:**
- Backup app settings before changes:
  ```bash
  az webapp config appsettings list \
    --name app-name \
    --resource-group rg-name \
    --output json > appsettings-backup-$(date +%Y%m%d).json
  ```
- Use Infrastructure as Code (Terraform/ARM templates)
- Enable Azure DevOps change tracking
- Set up config monitoring alerts

**Recovery Actions:**
1. Restore from backup if available
2. Manually reconfigure all settings
3. Document all settings in secure location
4. Test each service connection
5. Restart application

#### 3. Deployment Without Verification
**Problem:** Backend deployed but chat functionality not tested
**Impact:** Production bugs not caught immediately
**Root Cause:** No automated testing in deployment pipeline

**Prevention:**
- Add smoke tests to deployment pipeline
- Implement health check endpoints
- Use staging environment for testing
- Automated integration tests
- Deployment gates in Azure DevOps

**Recovery Actions:**
1. Run comprehensive endpoint tests
2. Check application logs
3. Monitor error rates
4. Test critical user flows
5. Redeploy if needed

### 🛡️ Security Best Practices

1. **Never Store Secrets Locally**
   - Use Azure Key Vault
   - Use managed identities
   - Use environment-specific app settings
   - Keep .env.example with dummy values only

2. **Regular Security Audits**
   - Check for exposed credentials
   - Review access controls
   - Monitor for suspicious activity
   - Rotate keys quarterly
   - Enable Azure Security Center

3. **Configuration Management**
   - Backup all settings before changes
   - Use version control for infrastructure
   - Document all configuration
   - Use separate dev/staging/prod configs
   - Never use dev secrets in production

4. **Monitoring & Alerts**
   - Set up Azure Monitor alerts
   - Enable Application Insights
   - Track configuration changes
   - Monitor error rates
   - Set up cost alerts

### 📋 New Recovery Checklist

**Immediate Actions (First 5 minutes):**
- [ ] Run `./QUICK_RECOVERY.sh` for system health check
- [ ] Check Azure app status
- [ ] Review recent deployment logs
- [ ] Test critical API endpoints
- [ ] Check for security issues

**P0 - Critical (Next 2 hours):**
- [ ] Rotate any exposed API keys
- [ ] Restore missing environment variables
- [ ] Fix critical functionality issues
- [ ] Verify database connectivity
- [ ] Test end-to-end user flow

**P1 - High (Next 24 hours):**
- [ ] Complete security audit
- [ ] Set up monitoring alerts
- [ ] Update documentation
- [ ] Run comprehensive tests
- [ ] Deploy to staging first

**P2 - Medium (Next week):**
- [ ] Implement Infrastructure as Code
- [ ] Set up automated testing
- [ ] Configure backup systems
- [ ] Review disaster recovery plan
- [ ] Update team runbooks

### 🚀 Quick Recovery Script

**New Tool:** `/Users/diptendu/boloo app/boloo-app/QUICK_RECOVERY.sh`

```bash
# Run comprehensive system check
cd "/Users/diptendu/boloo app/boloo-app"
./QUICK_RECOVERY.sh
```

**Features:**
- Checks Azure service status
- Tests critical API endpoints
- Audits environment variables
- Scans for security issues
- Provides recovery commands
- Links to documentation

**Use Cases:**
- After any crash or failure
- Before major deployments
- After configuration changes
- During security audits
- Weekly health checks

### 📚 Enhanced Documentation

**New Documents Created:**
1. `/docs/RECOVERY_SUMMARY_NOV24.md`
   - Comprehensive recovery status
   - Priority action plan with P0/P1/P2 tasks
   - Security issues and fixes
   - System health overview
   - Lessons learned

2. `/boloo-app/QUICK_RECOVERY.sh`
   - Automated system health check
   - Security scanning
   - Recovery commands
   - Documentation links

**Updated Documents:**
- This file (RECOVERY_GUIDE.md)
- Enhanced with lessons learned
- Added security best practices
- Improved recovery workflows

### 🎯 Success Metrics

**Before Nov 24 Recovery:**
- Manual checks only
- No automated health monitoring
- Security issues undetected
- Configuration not backed up
- Recovery time: 2-4 hours

**After Nov 24 Recovery:**
- Automated health checks (`QUICK_RECOVERY.sh`)
- Security scanning built-in
- Configuration backup procedures
- Clear priority-based recovery
- Recovery time: 30-60 minutes

---

**Remember:** The quickest recovery path is now:
1. Run `./QUICK_RECOVERY.sh` first
2. Review `/docs/RECOVERY_SUMMARY_NOV24.md`
3. Follow P0 priority tasks
4. Use `./START_PROJECT.sh` for local services
5. Only use `./FULL_RESET.sh` as absolute last resort

---

*Last Updated: Nov 24, 2025 - Added Nov 24 Recovery Lessons*
*Version: 2.1*
