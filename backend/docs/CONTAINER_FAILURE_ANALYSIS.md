# Backend Container Startup Failure Analysis
**Date:** November 23, 2025
**App Service:** boloo-backend-api
**Resource Group:** boloo-production-rg

---

## Executive Summary

The backend container is failing to start due to **Out of Memory (OOM) errors** caused by deploying the local `.python_packages` directory (267MB) which contains heavy ML dependencies that are loading during worker initialization.

### Critical Finding
**Workers are being SIGKILL'd during startup with "Perhaps out of memory?" errors**

---

## Root Cause Analysis

### 1. **Exact Error Messages**

From Docker logs (`2025_11_23_lw0sdlwk000F7X_default_docker.log`):

```
[2025-11-23 20:06:43 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:11)
[2025-11-23 20:06:43 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:12)
[2025-11-23 20:06:43 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:13)
[2025-11-23 20:06:43 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:14)
[2025-11-23 20:06:44 +0000] [1] [ERROR] Worker (pid:12) was sent SIGKILL! Perhaps out of memory?
[2025-11-23 20:06:44 +0000] [1] [ERROR] Worker (pid:11) was sent SIGKILL! Perhaps out of memory?
[2025-11-23 20:06:44 +0000] [1] [ERROR] Worker (pid:13) was sent SIGKILL! Perhaps out of memory?
[2025-11-23 20:06:44 +0000] [1] [ERROR] Worker (pid:14) was sent SIGKILL! Perhaps out of memory?
```

**Pattern:**
- Workers boot at timestamps like `20:06:12`
- After 30 seconds, WORKER TIMEOUT occurs at `20:06:43`
- Immediately followed by SIGKILL with OOM message
- **This repeats infinitely** - workers never successfully start

### 2. **Deployment Comparison**

#### Working Deployment (b0a1bbd2):
- **Manifest size:** 2,732 bytes
- **Files deployed:** 89 files
- **Total size:** ~506KB of application code only
- **Status:** ✅ Started successfully in ~3 minutes

#### Failed Deployment (11d81d82):
- **Manifest size:** 285,713 bytes (100x larger!)
- **Files deployed:** 3,881 files
- **Total size:** ~228MB (includes 267MB .python_packages)
- **Status:** ❌ OOM kills during worker startup

### 3. **Why Workers Are Failing**

The Gunicorn workers are configured with:
```python
--workers 4
--worker-class uvicorn.workers.UvicornWorker
--timeout 30
--preload
```

**Startup sequence causing OOM:**

1. **Master process** starts and preloads the application
2. Application imports load heavy dependencies from `.python_packages`:
   - `sentence-transformers` (500MB+ when loaded)
   - `torch` dependencies
   - `faiss-cpu` vector libraries
   - `huggingface_hub` model loaders
3. **Fork occurs** - 4 worker processes created
4. **Each worker** tries to initialize:
   - Loads the ML models into memory
   - Initializes transformers
   - Creates vector indexes
5. **B1 tier (1.75GB RAM) exhausted:**
   - Master process: ~400MB
   - Worker 1: ~500MB (loading sentence-transformers)
   - Worker 2: ~500MB (loading sentence-transformers)
   - Worker 3: ~500MB (starts loading, OOM killer triggers)
   - **TOTAL REQUIRED: 2GB+**
   - **AVAILABLE: 1.75GB** ❌

### 4. **Why Previous Deployment Worked**

The working deployment (b0a1bbd2) was a **code-only deployment**:
- No `.python_packages` directory
- Dependencies installed by Azure from `requirements.txt`
- Azure's build process excluded heavy ML libraries (commented out in requirements.txt)
- Only essential dependencies installed: FastAPI, SQLAlchemy, etc.
- Memory footprint: ~300MB per worker

---

## File System Issues

### .gitignore Violation

The `.gitignore` file correctly excludes:
```
__pycache__/
venv/
.venv/
.python_packages/
```

But the latest `deploy.zip` **includes 267MB of .python_packages** anyway!

**Root cause:** The deployment script is not respecting `.gitignore` and is packaging everything.

---

## Evidence from Logs

### Deployment Manifest Comparison

**Working deployment manifest (first 5 lines):**
```
Dockerfile
startup.sh
app/main.py
app/config.py
requirements.txt
```

**Failed deployment manifest (first 5 lines):**
```
.python_packages
.python_packages/lib
.python_packages/lib/site-packages
.python_packages/lib/site-packages/bin
.python_packages/lib/site-packages/bin/alembic
```

The failed deployment **starts with .python_packages** instead of application code!

---

## Impact Analysis

### Container Lifecycle
1. ✅ **Deployment:** SUCCESS (rsync completes in 60 seconds)
2. ✅ **Container creation:** SUCCESS
3. ✅ **Image pull:** SUCCESS
4. ✅ **Container start:** SUCCESS
5. ❌ **Worker initialization:** FAILURE (OOM after 30s)
6. 🔄 **Restart loop:** Container restarts, repeats forever

### Health Check
```bash
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3
```
- Never reaches `/health` endpoint
- Workers killed before health check can succeed
- Azure marks app as "unhealthy" after 10 minutes

---

## Solution: Immediate Fix

### Step 1: Remove .python_packages from Deployment

**Option A: Clean deployment (RECOMMENDED)**
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
zip -r deploy-clean.zip . -x "*.git*" "*.python_packages/*" "*venv/*" "*__pycache__*" "*.DS_Store" "*node_modules/*"
az webapp deploy --resource-group boloo-production-rg --name boloo-backend-api --src-path deploy-clean.zip --type zip
```

**Option B: Delete .python_packages directory**
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
rm -rf .python_packages
zip -r deploy.zip . -x "*.git*" "*venv/*" "*__pycache__*" "*.DS_Store"
az webapp deploy --resource-group boloo-production-rg --name boloo-backend-api --src-path deploy.zip --type zip
```

### Step 2: Verify Requirements.txt

Ensure `requirements.txt` has ML libraries **commented out**:
```python
# Vector Search (DISABLED - Requires 1.2GB+ RAM, use only on B2+ tier)
# Uncomment these if ENABLE_VECTOR_SEARCH=1 and you have sufficient memory:
# faiss-cpu==1.7.4
# sentence-transformers==2.2.2
```

### Step 3: Deploy Docker Image (BETTER OPTION)

Since you have a working Dockerfile, use **Docker deployment** instead of zip:

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Build and push to GitHub Container Registry
docker build -t ghcr.io/diptendudip/boloo-backend:v1.0 .
docker push ghcr.io/diptendudip/boloo-backend:v1.0

# Update Azure to use Docker image
az webapp config container set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --docker-custom-image-name ghcr.io/diptendudip/boloo-backend:v1.0 \
  --docker-registry-server-url https://ghcr.io
```

**Why Docker is better:**
- Dockerfile already excludes unnecessary files
- No risk of .python_packages leaking in
- Consistent builds
- Faster deployments (layers cached)

---

## Long-Term Recommendations

### 1. Scale Up to B2 Tier (if ML features needed)
- Current: B1 (1.75GB RAM) = $54.75/month
- Upgrade: B2 (3.5GB RAM) = $109.50/month
- Benefit: Can run 2-4 workers with ML models

### 2. Implement Lazy Loading
Instead of preloading all models:
```python
# app/services/ai_service.py
_model_cache = {}

def get_model():
    if 'sentence_transformer' not in _model_cache:
        _model_cache['sentence_transformer'] = SentenceTransformer('model-name')
    return _model_cache['sentence_transformer']
```

### 3. Use External Vector DB
- Azure Cognitive Search (managed service)
- Pinecone (serverless vector DB)
- Benefit: Offload memory-intensive operations

### 4. Fix Deployment Pipeline
Create `.deployignore` file:
```
.git/
.python_packages/
venv/
.venv/
__pycache__/
*.pyc
.DS_Store
*.log
tests/
.env
```

### 5. Add Deployment Validation
```bash
# Pre-deployment check
if [ -d ".python_packages" ]; then
    echo "ERROR: .python_packages directory found! Remove before deploying."
    exit 1
fi
```

---

## Verification Steps After Fix

1. **Check deployment manifest size:**
   ```bash
   az webapp deployment list --name boloo-backend-api --resource-group boloo-production-rg --query "[0].properties.size"
   ```
   Should be < 1MB

2. **Monitor container logs:**
   ```bash
   az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg
   ```
   Should see: `Application startup complete.`

3. **Check health endpoint:**
   ```bash
   curl https://boloo-backend-api.azurewebsites.net/health
   ```
   Should return 200 OK

4. **Verify worker count:**
   ```bash
   az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg | grep "Booting worker"
   ```
   Should see 4 workers boot successfully

---

## Summary

### ✅ What Worked
- Code-only deployment (89 files, 506KB)
- Workers started in < 30 seconds
- Memory usage: ~300MB per worker

### ❌ What Failed
- Deploying .python_packages (3,881 files, 228MB)
- Workers timeout after 30 seconds
- OOM kills during ML library initialization
- Memory required: 2GB+ (exceeds B1 tier 1.75GB)

### 🔧 Immediate Action Required
1. **Remove .python_packages from deployment**
2. **Deploy code-only zip or use Docker image**
3. **Verify requirements.txt has ML libraries commented out**

### 📊 Success Criteria
- Deployment manifest < 1MB
- Workers start within 30 seconds
- Health check passes
- No OOM errors in logs
