# CI/CD Pipeline - Boloo Backend

## 🚀 Automated Docker Deployment to Azure

Complete CI/CD solution for deploying Boloo Backend to Azure App Service using GitHub Actions and Docker.

---

## 📦 What's Included

### GitHub Actions Workflows
- **deploy-docker.yml** - Main deployment pipeline
- **docker-cleanup.yml** - Image retention management

### Deployment Scripts
- **deploy-docker.sh** - Manual deployment with versioning
- **configure-azure-env.sh** - Environment configuration
- **rollback-deployment.sh** - Quick rollback capability
- **test-deployment.sh** - Deployment validation

### Documentation
- **CI-CD-SETUP.md** - Complete setup guide
- **QUICK-DEPLOY-GUIDE.md** - Quick reference
- **DEPLOYMENT-CHECKLIST.md** - Pre-deployment checklist
- **CI-CD-COMPLETE.md** - Implementation summary

---

## ⚡ Quick Start

### 1️⃣ First-Time Setup (5 minutes)

**A. Configure GitHub Secrets:**
```bash
# Create Azure service principal
az ad sp create-for-rbac \
  --name "boloo-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/boloo-production-rg \
  --sdk-auth

# Copy output to GitHub → Settings → Secrets → Actions → AZURE_CREDENTIALS
```

**B. Configure Azure App Service:**
```bash
# Set container registry credentials
az webapp config container set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --docker-registry-server-url https://ghcr.io \
  --docker-registry-server-user YOUR_GITHUB_USERNAME \
  --docker-registry-server-password YOUR_GITHUB_TOKEN

# Enable continuous deployment
az webapp deployment container config \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --enable-cd true
```

**C. Configure Environment Variables:**
```bash
# Create production environment file
cp .env.production.example .env.production

# Edit with your values
nano .env.production

# Deploy to Azure
./scripts/configure-azure-env.sh production
```

### 2️⃣ Deploy (30 seconds)

**Option A - Automated (Recommended):**
```bash
git add .
git commit -m "Your changes"
git push origin main
# ✨ GitHub Actions automatically builds, tests, and deploys
```

**Option B - Manual:**
```bash
./scripts/deploy-docker.sh v1.0.0
```

### 3️⃣ Verify (1 minute)

```bash
# Run comprehensive tests
./scripts/test-deployment.sh

# Quick health check
curl https://boloo-backend-api.azurewebsites.net/health
```

### 4️⃣ Rollback (If needed)

```bash
# Interactive rollback
./scripts/rollback-deployment.sh

# Or rollback to previous version
./scripts/rollback-deployment.sh previous
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│ Developer       │
│ Push to main    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ GitHub Actions              │
│ ┌─────────────────────────┐ │
│ │ 1. Checkout code        │ │
│ │ 2. Build Docker image   │ │
│ │ 3. Run tests            │ │
│ │ 4. Push to GHCR         │ │
│ │ 5. Deploy to Azure      │ │
│ │ 6. Health checks        │ │
│ │ 7. Smoke tests          │ │
│ └─────────────────────────┘ │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ GitHub Container Registry   │
│ ghcr.io/.../boloo-backend   │
│ - latest                    │
│ - main-{sha}                │
│ - {timestamp}               │
│ - production                │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Azure App Service           │
│ boloo-backend-api           │
│ - Auto-pull new images      │
│ - Health monitoring         │
│ - Auto-scaling              │
│ - Log streaming             │
└─────────────────────────────┘
```

---

## 📋 File Structure

```
backend/
├── .github/
│   └── workflows/
│       ├── deploy-docker.yml       # Main CI/CD pipeline
│       └── docker-cleanup.yml      # Image cleanup
│
├── scripts/
│   ├── deploy-docker.sh           # Manual deployment
│   ├── configure-azure-env.sh     # Environment setup
│   ├── rollback-deployment.sh     # Rollback tool
│   └── test-deployment.sh         # Testing tool
│
├── docs/
│   ├── CI-CD-SETUP.md            # Complete guide
│   ├── QUICK-DEPLOY-GUIDE.md     # Quick reference
│   ├── DEPLOYMENT-CHECKLIST.md   # Checklist
│   └── CI-CD-COMPLETE.md         # Summary
│
├── .env.production.example        # Environment template
├── Dockerfile                     # Container config
└── README-CICD.md                # This file
```

---

## 🎯 Features

### Automated Deployment
✅ Trigger on push to main branch  
✅ Docker build with layer caching  
✅ Multi-tag versioning (SHA, timestamp, latest)  
✅ Push to GitHub Container Registry  
✅ Deploy to Azure App Service  
✅ Automated health checks  
✅ Smoke tests  
✅ Deployment summaries  

### Manual Deployment
✅ Version control and tagging  
✅ Prerequisites validation  
✅ Multi-environment support  
✅ Health validation  
✅ Deployment metadata tracking  

### Environment Management
✅ Database configuration  
✅ JWT/security settings  
✅ CORS configuration  
✅ Redis cache setup  
✅ Azure Storage integration  
✅ Third-party API keys  
✅ Logging and monitoring  

### Rollback & Recovery
✅ Interactive version selection  
✅ Automatic backup before rollback  
✅ Health validation  
✅ Rollback metadata tracking  
✅ Keep last 5 versions for quick rollback  

### Monitoring & Testing
✅ Real-time health checks  
✅ 8 automated smoke tests  
✅ Response time monitoring  
✅ Security headers validation  
✅ CORS verification  
✅ JSON response validation  

---

## 🔧 Common Commands

### Deployment
```bash
# Automated deployment
git push origin main

# Manual deployment
./scripts/deploy-docker.sh v1.0.0

# Deploy to staging
./scripts/deploy-docker.sh v1.0.0 staging
```

### Configuration
```bash
# Configure production environment
./scripts/configure-azure-env.sh production

# Update environment variables
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings KEY=VALUE
```

### Monitoring
```bash
# Real-time logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Download logs
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Health check
curl https://boloo-backend-api.azurewebsites.net/health
```

### Testing
```bash
# Run deployment tests
./scripts/test-deployment.sh

# Test specific URL
./scripts/test-deployment.sh https://boloo-backend-api.azurewebsites.net
```

### Rollback
```bash
# Interactive rollback
./scripts/rollback-deployment.sh

# Rollback to specific version
./scripts/rollback-deployment.sh v1.2.3

# Rollback to previous
./scripts/rollback-deployment.sh previous
```

### Maintenance
```bash
# Restart app
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# View current image
az webapp config container show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# List available images
docker images ghcr.io/diptendudip/boloo-backend
```

---

## 🚨 Troubleshooting

### Deployment Failed

**1. Check GitHub Actions logs:**
- Go to Actions tab in GitHub
- Find failed workflow
- Review error messages

**2. Check Azure logs:**
```bash
az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg
```

**3. Verify secrets:**
- GitHub: Settings → Secrets → Actions
- Azure: Portal → App Service → Configuration

### Health Check Failing

**1. Wait for startup (60 seconds)**

**2. Check application logs:**
```bash
az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg
```

**3. Verify environment variables:**
```bash
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

**4. Test database connection:**
```bash
# Check DATABASE_URL is set correctly
```

### Container Won't Start

**1. Test image locally:**
```bash
docker pull ghcr.io/diptendudip/boloo-backend:latest
docker run -p 8000:8000 ghcr.io/diptendudip/boloo-backend:latest
```

**2. Check Dockerfile:**
```bash
# Verify Dockerfile builds successfully
docker build -t test-build .
```

**3. Verify registry access:**
```bash
az webapp config container show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

---

## 📊 Monitoring

### Key Metrics
- **CPU Usage:** < 70%
- **Memory Usage:** < 80%
- **Response Time:** < 500ms
- **Error Rate:** < 1%
- **Uptime:** > 99.9%

### Alerts
Set up alerts in Azure for:
- High CPU/Memory usage
- Application errors
- Failed health checks
- Slow response times

### Logs
```bash
# Stream logs
az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg

# Download logs
az webapp log download --name boloo-backend-api --resource-group boloo-production-rg
```

---

## 🔐 Security

### Secrets Management
- ✅ GitHub Secrets for CI/CD credentials
- ✅ Azure Key Vault for sensitive data
- ✅ Environment variables for configuration
- ✅ No hardcoded secrets in code

### Container Security
- ✅ Multi-stage builds
- ✅ Minimal base image (Python 3.11-slim)
- ✅ Non-root user
- ✅ Security scanning

### Network Security
- ✅ HTTPS only
- ✅ CORS properly configured
- ✅ Security headers enabled
- ✅ Rate limiting configured

---

## 📚 Documentation

- **[CI-CD-SETUP.md](docs/CI-CD-SETUP.md)** - Complete setup guide with architecture details
- **[QUICK-DEPLOY-GUIDE.md](docs/QUICK-DEPLOY-GUIDE.md)** - Quick reference for common tasks
- **[DEPLOYMENT-CHECKLIST.md](docs/DEPLOYMENT-CHECKLIST.md)** - Pre-deployment checklist
- **[CI-CD-COMPLETE.md](docs/CI-CD-COMPLETE.md)** - Implementation summary

---

## 🎓 Best Practices

1. **Always test locally before pushing**
2. **Use automated deployment for consistency**
3. **Monitor deployments in real-time**
4. **Keep rollback images available**
5. **Document changes in commit messages**
6. **Review logs after deployment**
7. **Test rollback procedures regularly**
8. **Rotate secrets periodically**
9. **Keep dependencies updated**
10. **Monitor resource usage**

---

## 🆘 Support

### Quick Links
- **GitHub Actions:** [View Workflows](https://github.com/YOUR_USERNAME/boloo-app/actions)
- **Azure Portal:** [App Service](https://portal.azure.com)
- **Container Registry:** [GHCR Packages](https://github.com/YOUR_USERNAME/boloo-backend/pkgs/container/boloo-backend)

### Contact
- **DevOps Team:** devops@boloo.app
- **On-Call:** +1-XXX-XXX-XXXX
- **Slack:** #backend-deployments

---

## ✅ Status

**Implementation:** Complete ✓  
**Testing:** Verified ✓  
**Documentation:** Complete ✓  
**Production Ready:** Yes ✓  

**Created:** 2025-01-24  
**Last Updated:** 2025-01-24  
**Version:** 1.0.0  

---

**Happy Deploying! 🚀**
