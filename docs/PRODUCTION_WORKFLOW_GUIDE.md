# Production Workflow Guide - Boloo MVP

**Complete guide for maintaining, testing, and deploying Boloo to production**

---

## 📋 Table of Contents

1. [Development Workflow (Offline → Test → Live)](#development-workflow)
2. [Secrets Management (Never Expose Keys)](#secrets-management)
3. [Custom Domain Setup (bultoo.com)](#custom-domain-setup)
4. [Moderator Frontend](#moderator-frontend)
5. [GitHub Workflow (Safe Code Pushing)](#github-workflow)
6. [Bug Fix Workflow](#bug-fix-workflow)
7. [UI/UX Changes Workflow](#uiux-changes-workflow)

---

## 1. Development Workflow (Offline → Test → Live)

### Three-Environment Strategy

```
LOCAL (Your Mac) → STAGING (Azure Staging Slot) → PRODUCTION (Azure Live)
```

### Setup Process

#### A. **Local Development (Offline Testing)**

**Backend:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Use local .env file
cp .env.example .env.local
# Edit .env.local with LOCAL database and test credentials

# Run locally
python -m uvicorn app.main:app --reload --port 8000
```

**Mobile App:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"

# Point to local backend
# Edit app.json: "apiUrl": "http://192.168.1.205:8000"

# Run locally
npx expo start
```

**Moderator Web:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/web"

# Use local environment
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000

# Run locally
npm run dev  # Runs on http://localhost:3000
```

#### B. **Staging Environment (Test Before Live)**

Create a **staging slot** on Azure:

```bash
# Create staging slot
az webapp deployment slot create \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --slot staging

# Deploy to staging first
az webapp deployment source config-zip \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot staging \
  --src backend-deploy.zip

# Test staging URL
curl https://boloo-backend-app-staging.azurewebsites.net/health
```

**Staging URLs:**
- Backend: `https://boloo-backend-app-staging.azurewebsites.net`
- Web: Deploy to separate staging app or Vercel preview

#### C. **Production Deployment (Go Live)**

Only after thorough staging tests:

```bash
# Swap staging to production (zero-downtime)
az webapp deployment slot swap \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot staging \
  --target-slot production

# Instant rollback if issues found
az webapp deployment slot swap \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot production \
  --target-slot staging
```

---

## 2. Secrets Management (Never Expose Keys)

### **CRITICAL RULE: Never commit .env files to GitHub!**

### A. **.gitignore Configuration**

Create/update `.gitignore` in project root:

```bash
# CRITICAL: Never commit these files
.env
.env.local
.env.production
*.env

# Backend secrets
backend/.env
backend/.env.*

# Mobile app secrets
mobile/.env
mobile/.env.*

# Web frontend secrets
web/.env.local
web/.env.production

# Azure credentials
azure-credentials.json
```

### B. **Environment Variable Strategy**

**File Structure:**
```
boloo-app/
├── .env.example          # ✅ Commit this (no real values)
├── .env                  # ❌ NEVER commit
├── .env.local            # ❌ NEVER commit
├── .env.production       # ❌ NEVER commit
├── backend/
│   ├── .env.example      # ✅ Commit
│   ├── .env.local        # ❌ NEVER commit
│   └── .env.production   # ❌ NEVER commit
├── mobile/
│   ├── .env.example      # ✅ Commit
│   └── .env.local        # ❌ NEVER commit
└── web/
    ├── .env.example      # ✅ Commit
    ├── .env.local        # ❌ NEVER commit
    └── .env.production   # ❌ NEVER commit
```

**Example `.env.example`:**
```bash
# Backend .env.example
APP_NAME=Boloo
DATABASE_URL=postgresql://user:password@localhost:5432/boloo
AZURE_OPENAI_API_KEY=<your-azure-openai-key>
AZURE_SPEECH_KEY=<your-azure-speech-key>
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
```

### C. **Storing Production Secrets**

**Option 1: Azure App Settings (Recommended)**
```bash
# Store secrets in Azure (never in code)
az webapp config appsettings set \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --settings \
    AZURE_OPENAI_API_KEY="<real-key>" \
    TWILIO_AUTH_TOKEN="<real-token>"
```

**Option 2: GitHub Secrets (for CI/CD)**
1. Go to GitHub repo → Settings → Secrets → Actions
2. Add secrets:
   - `AZURE_OPENAI_API_KEY`
   - `TWILIO_AUTH_TOKEN`
   - `DATABASE_URL`
   - etc.

### D. **VSCode Secret Storage**

Your Twilio credentials in VSCode are safe! To access:

1. **Check if stored in `.env` file** (don't commit this)
2. **Or use VSCode Settings Sync** (encrypted, synced to your Microsoft account)

To find Twilio credentials:
```bash
# Search for Twilio in your .env files (careful not to expose)
grep -r "TWILIO" "/Users/diptendu/boloo app/boloo-app" --include="*.env*" | grep -v ".example"
```

---

## 3. Custom Domain Setup (bultoo.com)

### A. **Configure Domain DNS**

In your domain registrar (GoDaddy, Namecheap, etc.):

**For Backend API (api.bultoo.com):**
```
Type    Name    Value                                     TTL
CNAME   api     boloo-backend-app.azurewebsites.net      300
TXT     asuid   <get-from-azure>                          300
```

**For Moderator Web (admin.bultoo.com or bultoo.com):**
```
Type    Name    Value                                     TTL
CNAME   admin   boloo-web-app.azurewebsites.net          300
A       @       <azure-app-ip-address>                    300
```

**For Mobile App (if using web version: app.bultoo.com):**
```
Type    Name    Value                                     TTL
CNAME   app     boloo-mobile-web.azurewebsites.net       300
```

### B. **Azure Custom Domain Configuration**

**Backend API:**
```bash
# Get domain verification ID
az webapp show \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --query "customDomainVerificationId" -o tsv

# Add custom domain
az webapp config hostname add \
  --webapp-name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --hostname api.bultoo.com

# Enable HTTPS (free SSL certificate)
az webapp config ssl bind \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --certificate-thumbprint auto \
  --ssl-type SNI \
  --hostname api.bultoo.com
```

**Moderator Web:**
```bash
# Same process for web app
az webapp config hostname add \
  --webapp-name boloo-web-app \
  --resource-group cgnet-mvp-rg \
  --hostname admin.bultoo.com

az webapp config ssl bind \
  --name boloo-web-app \
  --resource-group cgnet-mvp-rg \
  --certificate-thumbprint auto \
  --ssl-type SNI \
  --hostname admin.bultoo.com
```

### C. **Update Mobile App API URLs**

After domain setup:

**Edit `mobile/app.json`:**
```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://api.bultoo.com"
    }
  }
}
```

**Rebuild app:**
```bash
cd mobile
eas build --platform android --profile production
```

---

## 4. Moderator Frontend

### **Location:** `/Users/diptendu/boloo app/boloo-app/web`

This is a **Next.js** application with admin panels for:

- **Cases Management** (`/app/cases/page.tsx`)
- **User Management** (`/app/users/page.tsx`)
- **Entities Management** (`/app/entities/page.tsx`)
- **Taxonomies** (`/app/taxonomies/page.tsx`)
- **Analytics** (`/app/analytics/page.tsx`)
- **Monitoring** (`/app/monitoring/page.tsx`)
- **Settings** (`/app/settings/page.tsx`)

### Running Locally

```bash
cd "/Users/diptendu/boloo app/boloo-app/web"

# Install dependencies (if not done)
npm install

# Create local environment
cp .env.example .env.local

# Edit .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev

# Access at http://localhost:3000
```

### Deploying to Azure

**Option 1: Azure Static Web Apps (Free Tier)**
```bash
az staticwebapp create \
  --name boloo-admin-web \
  --resource-group cgnet-mvp-rg \
  --location southindia \
  --source . \
  --branch main \
  --app-location "web" \
  --output-location "out"
```

**Option 2: Vercel (Recommended for Next.js)**
```bash
cd web
npm install -g vercel
vercel login
vercel --prod
```

**Option 3: Azure App Service (Container)**
```bash
# Build Docker image
cd web
docker build -t boloo-web .

# Push to Azure Container Registry
az acr create --name bolooregistry --resource-group cgnet-mvp-rg --sku Basic
az acr build --registry bolooregistry --image boloo-web:latest .

# Deploy to App Service
az webapp create \
  --name boloo-web-app \
  --resource-group cgnet-mvp-rg \
  --plan boloo-backend-plan \
  --deployment-container-image-name bolooregistry.azurecr.io/boloo-web:latest
```

---

## 5. GitHub Workflow (Safe Code Pushing)

### A. **First-Time Setup**

```bash
cd "/Users/diptendu/boloo app/boloo-app"

# Initialize git (if not done)
git init

# Create comprehensive .gitignore
cat > .gitignore <<EOF
# CRITICAL: Never commit secrets
.env
.env.*
!.env.example
*.env

# Local development
.vscode/
.idea/
.DS_Store

# Python
__pycache__/
*.pyc
*.pyo
venv/
.pytest_cache/

# Node.js
node_modules/
.next/
out/
build/
dist/

# Mobile
.expo/
.expo-shared/
*.apk
*.ipa

# Database
*.db
*.sqlite

# Logs
*.log
logs/

# Azure
azure-credentials.json
.azure/
EOF

# Add all files (secrets excluded by .gitignore)
git add .

# Commit
git commit -m "Initial commit - Boloo MVP"

# Create GitHub repo and push
gh repo create boloo-mvp --private --source=. --remote=origin
git push -u origin main
```

### B. **Daily Development Workflow**

```bash
# 1. Create feature branch
git checkout -b fix/audio-upload-bug

# 2. Make changes locally
# Edit files...

# 3. Test locally first
cd backend && python -m pytest
cd ../mobile && npm test

# 4. Commit changes
git add .
git commit -m "Fix: Audio upload timeout issue"

# 5. Push to GitHub
git push origin fix/audio-upload-bug

# 6. Create Pull Request
gh pr create --title "Fix audio upload timeout" --body "Fixes issue #123"

# 7. After review, merge to main
gh pr merge --squash
```

### C. **GitHub Actions for CI/CD**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: boloo-backend-app
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: backend/

  deploy-web:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Vercel
        run: |
          cd web
          npm install
          npm run build
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## 6. Bug Fix Workflow

### **Scenario: Production Bug Found**

**Example: Audio upload failing on live app**

#### Step 1: **Reproduce Locally**

```bash
# 1. Pull latest production code
git checkout main
git pull origin main

# 2. Use production-like environment
cd backend
cp .env.production .env.local
# Edit .env.local to use staging database (not production!)

# 3. Reproduce bug locally
python -m uvicorn app.main:app --reload

# 4. Check logs
tail -f logs/app.log
```

#### Step 2: **Fix and Test Offline**

```bash
# 1. Create bug fix branch
git checkout -b hotfix/audio-upload-fix

# 2. Make changes
# Edit backend/app/routers/uploads.py

# 3. Test locally
python -m pytest tests/test_uploads.py
curl -X POST http://localhost:8000/api/uploads/audio -F "file=@test.m4a"

# 4. Verify fix works
# Test multiple scenarios
```

#### Step 3: **Deploy to Staging**

```bash
# 1. Commit changes
git add .
git commit -m "Hotfix: Fix audio upload timeout (increase to 60s)"

# 2. Push to GitHub
git push origin hotfix/audio-upload-fix

# 3. Create PR for review
gh pr create --title "Hotfix: Audio upload timeout" --body "Fixes production bug #456"

# 4. Deploy to staging
az webapp deployment source config-zip \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot staging \
  --src backend-deploy.zip

# 5. Test on staging
curl https://boloo-backend-app-staging.azurewebsites.net/api/uploads/audio
```

#### Step 4: **Deploy to Production**

```bash
# 1. After staging tests pass, merge PR
gh pr merge --squash

# 2. Swap staging to production (zero downtime)
az webapp deployment slot swap \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot staging \
  --target-slot production

# 3. Monitor production
az webapp log tail --name boloo-backend-app --resource-group cgnet-mvp-rg

# 4. If issues, instant rollback
az webapp deployment slot swap \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot production \
  --target-slot staging
```

---

## 7. UI/UX Changes Workflow

### **Example: Change button color in mobile app**

#### Mobile App Changes

```bash
# 1. Local development
cd "/Users/diptendu/boloo app/boloo-app/mobile"

# 2. Make UI changes
# Edit src/components/ChatInterface.tsx
# Change button color, text, etc.

# 3. Test on emulator/device
npx expo start
# Press 'a' for Android or 'i' for iOS

# 4. See changes in real-time (hot reload)
```

#### Web App Changes

```bash
# 1. Local development
cd "/Users/diptendu/boloo app/boloo-app/web"

# 2. Make UI changes
# Edit app/cases/page.tsx
# Change styles in components/

# 3. Test locally
npm run dev
# Open http://localhost:3000

# 4. See changes in real-time (hot reload)
```

#### Deploy UI Changes

**Mobile:**
```bash
# After testing, build new APK
cd mobile
eas build --platform android --profile production

# Download and distribute APK
```

**Web:**
```bash
# Commit and push
git add web/
git commit -m "UI: Update case list styling"
git push origin main

# Auto-deploy via GitHub Actions or manual:
cd web
vercel --prod
```

---

## 8. Quick Reference Commands

### Check Production Status
```bash
# Backend health
curl https://api.bultoo.com/health

# Database connection
az postgres flexible-server show --name boloo-db-server --resource-group cgnet-mvp-rg

# View logs
az webapp log tail --name boloo-backend-app --resource-group cgnet-mvp-rg
```

### Emergency Rollback
```bash
# Swap back to previous version
az webapp deployment slot swap \
  --resource-group cgnet-mvp-rg \
  --name boloo-backend-app \
  --slot production \
  --target-slot staging
```

### Update Secrets
```bash
# Update environment variable on Azure
az webapp config appsettings set \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --settings NEW_SECRET_KEY="new-value"
```

---

## 9. Cost Monitoring

### Set Budget Alerts
```bash
# Create budget alert
az consumption budget create \
  --budget-name boloo-monthly-budget \
  --amount 5000 \
  --time-grain Monthly \
  --start-date "$(date +%Y-%m-01)" \
  --end-date "2026-12-31" \
  --resource-group cgnet-mvp-rg \
  --notifications \
    email="diptendudip@gmail.com" \
    threshold=80 \
    operator=GreaterThan
```

### Check Costs
```bash
# View current month costs
az consumption usage list \
  --start-date "$(date +%Y-%m-01)" \
  --end-date "$(date +%Y-%m-%d)"
```

---

## Summary

✅ **Local → Staging → Production** workflow
✅ **Never commit secrets** (use .gitignore + Azure App Settings)
✅ **Custom domain** setup for api.bultoo.com
✅ **Moderator frontend** at `/web` folder
✅ **GitHub workflow** with CI/CD
✅ **Bug fix process** with rollback capability
✅ **UI/UX changes** with hot reload

**Next immediate steps:**
1. Setup .gitignore to protect secrets
2. Create staging slot on Azure
3. Configure custom domain (bultoo.com)
4. Deploy moderator web frontend
5. Test full workflow

---

**Generated:** November 20, 2025
