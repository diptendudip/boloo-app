# Quick Deployment Guide

## First-Time Setup (One-Time)

### 1. Configure GitHub Secrets

Go to GitHub Repository → Settings → Secrets → Actions

Add these secrets:

```bash
# Azure Service Principal (get from Azure CLI)
AZURE_CREDENTIALS=$(az ad sp create-for-rbac \
  --name "boloo-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/boloo-production-rg \
  --sdk-auth)
```

Copy the JSON output to `AZURE_CREDENTIALS` secret.

### 2. Configure Azure App Service

```bash
# Set Docker registry credentials
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

### 3. Configure Environment Variables

```bash
# Create .env.production file
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production

# Deploy environment variables to Azure
./scripts/configure-azure-env.sh production
```

## Regular Deployments

### Automated Deployment (Recommended)

1. **Commit and push to main branch:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **GitHub Actions automatically:**
   - Builds Docker image
   - Pushes to GHCR
   - Deploys to Azure
   - Runs health checks

3. **Monitor deployment:**
   - Check GitHub Actions tab
   - View logs in Azure Portal

### Manual Deployment

```bash
# Deploy with auto-generated version
./scripts/deploy-docker.sh

# Deploy with specific version
./scripts/deploy-docker.sh v1.2.3
```

## Quick Commands

### View Logs
```bash
# Real-time logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Download logs
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

### Health Check
```bash
# Quick health check
curl https://boloo-backend-api.azurewebsites.net/health

# Full deployment test
./scripts/test-deployment.sh
```

### Restart App
```bash
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

### Rollback
```bash
# Interactive rollback
./scripts/rollback-deployment.sh

# Rollback to specific version
./scripts/rollback-deployment.sh v1.2.2

# Rollback to previous
./scripts/rollback-deployment.sh previous
```

## Troubleshooting

### Deployment Failed

1. **Check GitHub Actions logs**
2. **Check Azure App Service logs:**
   ```bash
   az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg
   ```
3. **Verify environment variables:**
   ```bash
   az webapp config appsettings list \
     --name boloo-backend-api \
     --resource-group boloo-production-rg
   ```

### App Not Starting

1. **Check container logs:**
   ```bash
   az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg
   ```

2. **Verify Docker image:**
   ```bash
   # Check current image
   az webapp config container show \
     --name boloo-backend-api \
     --resource-group boloo-production-rg
   ```

3. **Test locally:**
   ```bash
   docker pull ghcr.io/diptendudip/boloo-backend:latest
   docker run -p 8000:8000 ghcr.io/diptendudip/boloo-backend:latest
   ```

### Health Check Failing

1. **Wait 60 seconds** (startup time)
2. **Check database connection**
3. **Verify environment variables**
4. **Check application logs**

## Emergency Procedures

### Quick Rollback
```bash
./scripts/rollback-deployment.sh previous
```

### Stop Traffic
```bash
az webapp stop \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

### Start Traffic
```bash
az webapp start \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

## URLs

- **Production API:** https://boloo-backend-api.azurewebsites.net
- **Health Check:** https://boloo-backend-api.azurewebsites.net/health
- **API Docs:** https://boloo-backend-api.azurewebsites.net/docs
- **OpenAPI:** https://boloo-backend-api.azurewebsites.net/openapi.json
- **Azure Portal:** https://portal.azure.com
- **GitHub Actions:** https://github.com/YOUR_USERNAME/boloo-app/actions

## Key Files

- `.github/workflows/deploy-docker.yml` - Main deployment workflow
- `.github/workflows/docker-cleanup.yml` - Image cleanup workflow
- `scripts/deploy-docker.sh` - Manual deployment script
- `scripts/configure-azure-env.sh` - Environment configuration
- `scripts/rollback-deployment.sh` - Rollback script
- `scripts/test-deployment.sh` - Deployment testing
- `.env.production` - Production environment variables
- `Dockerfile` - Container configuration

## Support Contacts

- **DevOps Team:** devops@boloo.app
- **On-Call:** +1-XXX-XXX-XXXX
- **Slack:** #backend-deployments
