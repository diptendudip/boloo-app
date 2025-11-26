# Docker Deployment Guide - Boloo Backend

## Overview

This guide covers building, testing, and deploying the boloo-backend Docker container with the latest chat fixes to GitHub Container Registry (ghcr.io).

## 🔧 Chat Fixes Included

The Docker image includes the following fixes:

1. **Location Confirmation Fix** (`app/utils/location_confirmation.py`)
   - Added `bool()` wrappers to `has_meaningful_location()`
   - Prevents `None` propagation in boolean comparisons
   - Line 244: `return bool(has_district and has_village_or_block)`

2. **Chat Router Fix** (`app/routers/chat.py`)
   - Added `bool()` wrappers for `has_profile_location`
   - Line 554: `has_profile_location = bool(profile_location and has_meaningful_location(profile_location))`
   - Line 619: `profile_location_available=bool(has_profile_location)`
   - Line 1410: `bool(extracted_data.get('location'))`

## 📋 Prerequisites

1. **Docker Desktop** installed and running
2. **GitHub Personal Access Token** (PAT) with permissions:
   - `write:packages`
   - `read:packages`
   - `delete:packages` (optional)
3. **Environment variables** configured in `.env` file

## 🚀 Quick Start

### 1. Build the Docker Image

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend/
./scripts/build-docker.sh
```

**What it does:**
- Verifies all required files exist
- Confirms chat fixes are present
- Builds Docker image with multi-stage optimization
- Tags with both `:latest` and timestamped version (`:vYYYYMMDD-HHMMSS`)
- Runs quick validation test
- Shows image size and details

**Expected output:**
```
✅ BUILD SUCCESSFUL
📌 Image Tags:
   • ghcr.io/diptendudip/boloo-backend:latest
   • ghcr.io/diptendudip/boloo-backend:v20251124-120530
```

**Build time:** ~3-5 minutes (first build), ~1-2 minutes (cached builds)

### 2. Test Locally

```bash
./scripts/test-docker.sh
```

**What it does:**
- Starts container on port 8001 (to avoid conflicts)
- Waits for service to be ready (max 60s)
- Runs comprehensive tests:
  - Health check endpoint
  - API documentation accessibility
  - Root endpoint validation
  - Resource usage monitoring
- Shows container logs
- Provides manual testing URLs

**Tests performed:**
1. ✅ Health check: `GET http://localhost:8001/health`
2. ✅ API docs: `GET http://localhost:8001/docs`
3. ✅ Root endpoint: `GET http://localhost:8001/`
4. ✅ Resource usage: CPU/Memory stats

**Manual testing:**
```bash
# Test chat endpoint with location
curl -X POST http://localhost:8001/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "हाँ",
    "language": "hi"
  }'
```

### 3. Push to GitHub Container Registry

```bash
./scripts/push-docker.sh
```

**Prerequisites:**
```bash
# 1. Create GitHub Personal Access Token at:
# https://github.com/settings/tokens/new
# Select: write:packages, read:packages

# 2. Set environment variable
export CR_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Login to GitHub Container Registry
echo $CR_PAT | docker login ghcr.io -u diptendudip --password-stdin

# 4. Run push script
./scripts/push-docker.sh
```

**What it does:**
- Verifies Docker authentication
- Pushes all image tags to ghcr.io
- Validates push success
- Provides GitHub package URL

**Expected output:**
```
✅ PUSH SUCCESSFUL
📦 Pushed Images:
   • ghcr.io/diptendudip/boloo-backend:latest
   • ghcr.io/diptendudip/boloo-backend:v20251124-120530

🔗 View on GitHub:
   https://github.com/diptendudip/boloo-backend/pkgs/container/boloo-backend
```

## 📦 Dockerfile Details

### Base Image
- **Python 3.11 Slim** - Minimal Debian-based Python image
- Size: ~150MB (base), ~800MB (with dependencies)

### System Dependencies
```dockerfile
gcc, g++              # C/C++ compilers for Python packages
libpq-dev            # PostgreSQL development libraries
libgdal-dev, gdal-bin # GIS/spatial data processing
ffmpeg               # Audio processing for voice features
curl                 # Health checks
```

### Python Dependencies
From `requirements.txt`:
- **FastAPI** 0.104.1 - Web framework
- **Uvicorn** 0.24.0 - ASGI server
- **Gunicorn** 21.2.0 - Process manager
- **SQLAlchemy** 2.0.23 - Database ORM
- **Anthropic** 0.9.0 - Claude API client
- And 20+ more packages

### Production Configuration

```dockerfile
ENV PYTHONUNBUFFERED=1              # Real-time logging
ENV PYTHONDONTWRITEBYTECODE=1       # No .pyc files
ENV PORT=8000                        # API port
ENV WEB_CONCURRENCY=2                # Worker processes
ENV WORKERS=2                        # Gunicorn workers
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV MAX_REQUESTS=1000                # Worker recycling
ENV MAX_REQUESTS_JITTER=50           # Random jitter
ENV TIMEOUT=120                      # Request timeout
ENV GRACEFUL_TIMEOUT=30              # Shutdown grace period
ENV KEEP_ALIVE=5                     # Connection keep-alive
```

### Gunicorn Command
```bash
gunicorn app.main:app \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## 🔄 Deployment to Azure

### Option 1: Azure Container Registry (ACR)

```bash
# 1. Tag for ACR
docker tag ghcr.io/diptendudip/boloo-backend:latest \
  bolooregistry.azurecr.io/boloo-backend:latest

# 2. Login to ACR
az acr login --name bolooregistry

# 3. Push to ACR
docker push bolooregistry.azurecr.io/boloo-backend:latest

# 4. Update App Service
az webapp config container set \
  --name boloo-backend \
  --resource-group boloo-rg \
  --docker-custom-image-name bolooregistry.azurecr.io/boloo-backend:latest

# 5. Restart App Service
az webapp restart --name boloo-backend --resource-group boloo-rg
```

### Option 2: GitHub Container Registry (ghcr.io)

```bash
# 1. Configure Azure App Service to use ghcr.io
az webapp config container set \
  --name boloo-backend \
  --resource-group boloo-rg \
  --docker-custom-image-name ghcr.io/diptendudip/boloo-backend:latest \
  --docker-registry-server-url https://ghcr.io \
  --docker-registry-server-user diptendudip \
  --docker-registry-server-password $CR_PAT

# 2. Restart App Service
az webapp restart --name boloo-backend --resource-group boloo-rg

# 3. Monitor deployment
az webapp log tail --name boloo-backend --resource-group boloo-rg
```

### Option 3: Continuous Deployment

Set up webhook for automatic deployment:

```bash
# 1. Get webhook URL
WEBHOOK_URL=$(az webapp deployment container config \
  --name boloo-backend \
  --resource-group boloo-rg \
  --enable-cd true \
  --query CI_CD_URL -o tsv)

# 2. Configure GitHub webhook
# GitHub → Settings → Webhooks → Add webhook
# Payload URL: $WEBHOOK_URL
# Content type: application/json
# Events: Package published
```

## 🔍 Verification

### 1. Check Container Logs
```bash
# Azure
az webapp log tail --name boloo-backend --resource-group boloo-rg

# Docker (local)
docker logs -f boloo-backend-test
```

### 2. Test Endpoints
```bash
# Health check
curl https://boloo-backend.azurewebsites.net/health

# API documentation
curl https://boloo-backend.azurewebsites.net/docs

# Chat endpoint (requires auth)
curl -X POST https://boloo-backend.azurewebsites.net/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "हाँ", "language": "hi"}'
```

### 3. Monitor Performance
```bash
# Container metrics
az monitor metrics list \
  --resource boloo-backend \
  --resource-group boloo-rg \
  --metric-names "CpuPercentage,MemoryPercentage"

# HTTP metrics
az monitor metrics list \
  --resource boloo-backend \
  --resource-group boloo-rg \
  --metric-names "Requests,Http2xx,Http4xx,Http5xx"
```

## 📊 Image Optimization

### Current Image Size
```bash
docker images ghcr.io/diptendudip/boloo-backend
# REPOSITORY                              TAG       SIZE
# ghcr.io/diptendudip/boloo-backend      latest    ~800MB
```

### Size Breakdown
- Base image (python:3.11-slim): ~150MB
- System dependencies: ~200MB
- Python packages: ~400MB
- Application code: ~50MB

### Further Optimization (Optional)

1. **Multi-stage build with Alpine** (reduces to ~500MB)
2. **Remove development dependencies** (saves ~100MB)
3. **Use slim packages** (e.g., `libpq` instead of `libpq-dev`)

## 🐛 Troubleshooting

### Build fails with "requirements.txt not found"
```bash
# Ensure you're in the backend directory
cd /Users/diptendu/boloo\ app/boloo-app/backend/
./scripts/build-docker.sh
```

### Container starts but health check fails
```bash
# Check logs
docker logs boloo-backend-test

# Common issues:
# 1. Missing environment variables (.env file)
# 2. Database connection error (check DATABASE_URL)
# 3. API keys not set (ANTHROPIC_API_KEY, AZURE_SPEECH_KEY)
```

### Push to ghcr.io fails with "authentication required"
```bash
# Re-login to GitHub Container Registry
export CR_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
echo $CR_PAT | docker login ghcr.io -u diptendudip --password-stdin

# Verify login
docker info | grep ghcr.io
```

### Azure deployment shows old version
```bash
# Force pull latest image
az webapp config container set \
  --name boloo-backend \
  --resource-group boloo-rg \
  --docker-custom-image-name ghcr.io/diptendudip/boloo-backend:latest

# Clear cache and restart
az webapp restart --name boloo-backend --resource-group boloo-rg

# Monitor logs
az webapp log tail --name boloo-backend --resource-group boloo-rg
```

## 📝 Version History

### v20251124 - Chat Fixes
- ✅ Added `bool()` wrappers to prevent `None` propagation
- ✅ Fixed location confirmation validation
- ✅ Improved type safety in chat router
- ✅ Enhanced error handling

### Previous Versions
- v20251123 - Production optimization (2 workers, resource limits)
- v20251122 - Added health monitoring
- v20251121 - Initial production Dockerfile

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/configure-custom-container)

## 🔐 Security Checklist

- [ ] Environment variables secured (not in Dockerfile)
- [ ] GitHub PAT stored securely (GitHub Secrets or Azure Key Vault)
- [ ] Container runs as non-root user (optional enhancement)
- [ ] Secrets rotation policy in place
- [ ] Image vulnerability scanning enabled
- [ ] HTTPS enforced in production
- [ ] Rate limiting configured
- [ ] Security headers enabled

## 📞 Support

For issues or questions:
1. Check logs: `docker logs <container-id>`
2. Review troubleshooting section above
3. Check Azure diagnostics: `az webapp log tail`
4. Contact DevOps team

---

**Last Updated:** 2025-11-24
**Maintainer:** Backend Development Team
**Docker Image:** ghcr.io/diptendudip/boloo-backend:latest
