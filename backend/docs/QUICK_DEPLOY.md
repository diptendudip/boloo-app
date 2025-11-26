# Quick Docker Deployment - TL;DR

## 🚀 3-Step Deployment

### Step 1: Build
```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend/
./scripts/build-docker.sh
```

### Step 2: Test
```bash
./scripts/test-docker.sh
```

### Step 3: Push
```bash
# First time only - authenticate
export CR_PAT=ghp_YOUR_GITHUB_PERSONAL_ACCESS_TOKEN
echo $CR_PAT | docker login ghcr.io -u diptendudip --password-stdin

# Push
./scripts/push-docker.sh
```

## 🔄 Deploy to Azure

```bash
# Update Azure App Service
az webapp config container set \
  --name boloo-backend \
  --resource-group boloo-rg \
  --docker-custom-image-name ghcr.io/diptendudip/boloo-backend:latest \
  --docker-registry-server-url https://ghcr.io \
  --docker-registry-server-user diptendudip \
  --docker-registry-server-password $CR_PAT

# Restart
az webapp restart --name boloo-backend --resource-group boloo-rg

# Monitor
az webapp log tail --name boloo-backend --resource-group boloo-rg
```

## ✅ Verify

```bash
curl https://boloo-backend.azurewebsites.net/health
```

## 📋 What's Included

✅ Chat fixes with `bool()` wrappers
✅ Location confirmation validation
✅ Production-ready Gunicorn config
✅ Health checks every 30s
✅ 2 workers for optimal performance
✅ Automatic worker recycling

## 🐛 Common Issues

**Build fails?**
```bash
# Ensure Docker is running
docker info
```

**Test fails?**
```bash
# Check .env file exists
ls -la .env

# View logs
docker logs boloo-backend-test
```

**Push fails?**
```bash
# Re-authenticate
echo $CR_PAT | docker login ghcr.io -u diptendudip --password-stdin
```

**Azure shows old version?**
```bash
# Force restart
az webapp restart --name boloo-backend --resource-group boloo-rg
```

---

**Full documentation:** See [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
