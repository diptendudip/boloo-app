# CI/CD Setup Guide - Boloo Backend

## Overview

This document describes the automated CI/CD pipeline for deploying the Boloo Backend to Azure App Service using Docker containers.

## Architecture

```
GitHub Repository → GitHub Actions → GHCR → Azure App Service
                    ↓
              Build Docker Image
                    ↓
              Push to Registry
                    ↓
              Deploy to Azure
                    ↓
              Health Check
```

## Components

### 1. GitHub Actions Workflow

**File:** `.github/workflows/deploy-docker.yml`

**Triggers:**
- Push to `main` branch (backend changes only)
- Manual workflow dispatch

**Jobs:**
1. **build-and-push**: Builds Docker image and pushes to GHCR
2. **deploy-to-azure**: Deploys to Azure App Service
3. **tag-release**: Creates version tags

**Features:**
- Multi-stage Docker build with caching
- Semantic versioning (SHA, timestamp, latest)
- Automated health checks
- Smoke tests
- Deployment summaries

### 2. Manual Deployment Script

**File:** `scripts/deploy-docker.sh`

**Usage:**
```bash
# Deploy with auto-generated version
./scripts/deploy-docker.sh

# Deploy with specific version
./scripts/deploy-docker.sh v1.0.0

# Deploy to specific environment
./scripts/deploy-docker.sh v1.0.0 staging
```

**Features:**
- Prerequisites validation
- Docker build and tag
- Multi-registry push
- Azure deployment
- Health checks
- Smoke tests
- Deployment metadata

### 3. Environment Configuration Script

**File:** `scripts/configure-azure-env.sh`

**Usage:**
```bash
# Configure production environment
./scripts/configure-azure-env.sh production

# Configure staging environment
./scripts/configure-azure-env.sh staging
```

**Configures:**
- Application settings
- Database connections
- JWT/security settings
- CORS configuration
- Redis cache
- Azure Storage
- Third-party integrations
- Logging
- Health check monitoring

### 4. Rollback Script

**File:** `scripts/rollback-deployment.sh`

**Usage:**
```bash
# Interactive rollback
./scripts/rollback-deployment.sh

# Rollback to specific version
./scripts/rollback-deployment.sh v1.0.0

# Rollback to previous version
./scripts/rollback-deployment.sh previous
```

**Features:**
- Lists available versions
- Creates backup before rollback
- Confirms before execution
- Health validation
- Rollback metadata tracking

## Setup Instructions

### 1. GitHub Secrets

Configure the following secrets in your GitHub repository:

#### Required Secrets:
- `AZURE_CREDENTIALS`: Azure service principal credentials
  ```json
  {
    "clientId": "<client-id>",
    "clientSecret": "<client-secret>",
    "subscriptionId": "<subscription-id>",
    "tenantId": "<tenant-id>"
  }
  ```

#### Optional Secrets (for environment configuration):
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: JWT signing key
- `OPENAI_API_KEY`: OpenAI API key
- `SENDGRID_API_KEY`: SendGrid API key
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage connection

### 2. Azure Service Principal

Create Azure service principal for GitHub Actions:

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "boloo-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/boloo-production-rg \
  --sdk-auth

# Copy the output JSON to AZURE_CREDENTIALS secret
```

### 3. GitHub Container Registry Access

Configure App Service to access GHCR:

```bash
# Set registry credentials
az webapp config container set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --docker-registry-server-url https://ghcr.io \
  --docker-registry-server-user <github-username> \
  --docker-registry-server-password <github-token>
```

### 4. Enable Continuous Deployment

```bash
# Enable webhook for continuous deployment
az webapp deployment container config \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --enable-cd true
```

### 5. Make Scripts Executable

```bash
chmod +x scripts/deploy-docker.sh
chmod +x scripts/configure-azure-env.sh
chmod +x scripts/rollback-deployment.sh
```

## Environment Variables

### Required Variables

Create `.env.production` file:

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/boloo_db

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=https://boloo.app,https://www.boloo.app
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=*

# Application
ENVIRONMENT=production
LOG_LEVEL=info
```

### Optional Variables

```env
# Redis Cache
REDIS_URL=redis://host:6379
REDIS_SSL=true
CACHE_TTL=300

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER=uploads

# Email
SENDGRID_API_KEY=SG.xxx
EMAIL_FROM=noreply@boloo.app

# SMS
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890

# AI
OPENAI_API_KEY=sk-xxx
```

## Deployment Workflow

### Automated Deployment (GitHub Actions)

1. Push changes to `main` branch
2. GitHub Actions triggers automatically
3. Docker image built and pushed to GHCR
4. Azure App Service pulls new image
5. Health checks validate deployment
6. Smoke tests ensure functionality

### Manual Deployment

1. Build and push locally:
   ```bash
   ./scripts/deploy-docker.sh v1.0.0 production
   ```

2. Configure environment:
   ```bash
   ./scripts/configure-azure-env.sh production
   ```

3. Monitor deployment:
   ```bash
   az webapp log tail \
     --name boloo-backend-api \
     --resource-group boloo-production-rg
   ```

### Rollback Procedure

1. List available versions:
   ```bash
   ./scripts/rollback-deployment.sh
   ```

2. Select version to rollback to

3. Confirm rollback

4. Validate health checks

## Image Tagging Strategy

Images are tagged with multiple versions:

- `latest`: Latest stable build
- `main-{sha}`: Branch and commit SHA
- `{YYYYMMDD-HHmmss}`: Timestamp
- `production`: Environment tag

**Example:**
```
ghcr.io/diptendudip/boloo-backend:latest
ghcr.io/diptendudip/boloo-backend:main-abc123
ghcr.io/diptendudip/boloo-backend:20250124-143022
ghcr.io/diptendudip/boloo-backend:production
```

## Image Retention Policy

Keep last 5 stable images for quick rollback:

```bash
# List all images
docker images ghcr.io/diptendudip/boloo-backend

# Clean old images (keep last 5)
docker images ghcr.io/diptendudip/boloo-backend --format "{{.Tag}}" | \
  tail -n +6 | \
  xargs -I {} docker rmi ghcr.io/diptendudip/boloo-backend:{}
```

## Monitoring and Logging

### View Live Logs

```bash
# Stream application logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Download logs
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --log-file logs.zip
```

### Health Check Endpoint

**URL:** `https://boloo-backend-api.azurewebsites.net/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-24T14:30:22Z"
}
```

### Metrics

Monitor in Azure Portal:
- CPU usage
- Memory usage
- Response time
- Request count
- Error rate

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. Verify Azure credentials
3. Check Docker image exists in GHCR
4. Validate environment variables

### Health Check Fails

1. Check application logs:
   ```bash
   az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg
   ```

2. Verify database connectivity
3. Check environment variables
4. Validate Docker image

### Rollback Required

1. Identify last working version
2. Run rollback script:
   ```bash
   ./scripts/rollback-deployment.sh previous
   ```

3. Monitor health checks
4. Investigate root cause

## Best Practices

1. **Always test locally before pushing**
   ```bash
   docker build -t boloo-backend:test .
   docker run -p 8000:8000 boloo-backend:test
   ```

2. **Use environment-specific configurations**
   - `.env.production` for production
   - `.env.staging` for staging
   - `.env.development` for local

3. **Monitor deployments**
   - Watch GitHub Actions logs
   - Check Azure App Service metrics
   - Review application logs

4. **Keep rollback images**
   - Maintain last 5 stable versions
   - Tag with semantic versions
   - Document deployment history

5. **Security**
   - Never commit secrets
   - Use Azure Key Vault for sensitive data
   - Rotate credentials regularly
   - Review access permissions

## Support

For issues or questions:
- Check Azure Portal for service health
- Review GitHub Actions logs
- Check application logs
- Contact DevOps team

## Related Documentation

- [Dockerfile Configuration](../Dockerfile)
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Docker Documentation](https://docs.docker.com/)
