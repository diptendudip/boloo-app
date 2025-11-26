# Production Deployment Package

## Package Contents

This deployment package is optimized for production with minimal size and maximum performance.

## Files Excluded (.dockerignore)
- Development files (tests/, docs/, examples/)
- IDE configurations (.vscode/, .idea/)
- Version control (.git/)
- Local data files (data/lgd/*.csv, *.7z)
- Python cache files (*.pyc, __pycache__)
- Logs and temporary files

## Package Size Optimization
- **Full Directory**: ~2.3GB
- **Deployment Package**: ~200-300MB (after .dockerignore)
- **Docker Image**: ~800MB-1GB (with system dependencies)

## Creating Deployment Package

### Option 1: Docker (Recommended)
```bash
# Build optimized image
docker build -t boloo-backend:production .

# Export image
docker save boloo-backend:production | gzip > deploy-prod.tar.gz
```

### Option 2: ZIP Archive
```bash
# Create deployment zip (respects .dockerignore)
cd /Users/diptendu/boloo\ app/boloo-app/backend
zip -r deploy-prod.zip . -x@.dockerignore -x "*.git*" -x "data/lgd/*"
```

### Option 3: Azure Deploy
```bash
# Direct deploy to Azure (no local package needed)
az webapp up --name boloo-backend --resource-group boloo-rg --runtime "PYTHON:3.11"
```

## Pre-Deployment Verification

### 1. Run Tests
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### 2. Security Scan
```bash
# Check for vulnerabilities
pip-audit

# Scan Docker image
trivy image boloo-backend:production
```

### 3. Environment Validation
```bash
# Verify all required env vars
python -c "from app.config import settings; print(settings.model_dump())"
```

### 4. Database Migration Dry-Run
```bash
alembic upgrade head --sql > migration.sql
# Review migration.sql before applying
```

## Post-Deployment Verification

### 1. Health Check
```bash
curl https://your-domain.azurewebsites.net/health
```

### 2. Load Test
```bash
# Install Apache Bench
brew install httpd  # macOS
apt-get install apache2-utils  # Linux

# Test 100 concurrent users
ab -n 1000 -c 100 https://your-domain.azurewebsites.net/api/v1/cases
```

### 3. Monitor Logs
```bash
# Azure CLI
az webapp log tail --name boloo-backend --resource-group boloo-rg

# Or via Azure Portal
# App Service → Log stream
```

## Rollback Procedure

### 1. Azure Deployment Slots
```bash
# Swap back to previous version
az webapp deployment slot swap --name boloo-backend --resource-group boloo-rg --slot staging --target-slot production
```

### 2. Database Rollback
```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision-id>
```

## Performance Benchmarks

### Expected Metrics (100 Users)
- **Requests/second**: 50-100
- **Average response time**: 100-200ms
- **p95 response time**: <500ms
- **Error rate**: <0.1%
- **Memory usage**: 2-3GB (2 workers)
- **CPU usage**: 40-60%

## Configuration Summary

### Dockerfile Optimizations
✅ Multi-stage build for smaller image
✅ Worker count: 2 (configurable via WEB_CONCURRENCY)
✅ Worker recycling: 1000 requests
✅ Graceful shutdown: 30 seconds
✅ Health checks: 30-second interval
✅ Timeout: 120 seconds for LLM calls

### Dependencies Optimized
✅ Production-only requirements
✅ No dev/test dependencies
✅ Pinned versions for stability
✅ Vector search disabled (memory intensive)

### Security Hardened
✅ No default secrets in production
✅ JWT validation enforced
✅ HTTPS required
✅ Rate limiting enabled
✅ Input sanitization

## Scaling Recommendations

### 100 Users (Current)
- **Tier**: B2 (3.5GB RAM)
- **Workers**: 2
- **Instances**: 1

### 200-500 Users
- **Tier**: B3 (7GB RAM)
- **Workers**: 4
- **Instances**: 1-2

### 500-1000 Users
- **Tier**: S1 (1.75GB RAM)
- **Workers**: 2
- **Instances**: 3-4 (with autoscaling)

### 1000+ Users
- **Tier**: P1V2 (3.5GB RAM)
- **Workers**: 3-4
- **Instances**: 4+ (autoscaling enabled)
- **Additional**: Azure CDN, Redis Premium, Database read replicas

## Contact
For deployment assistance: diptendudip@gmail.com
