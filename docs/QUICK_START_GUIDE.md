# Quick Start Guide - All Your Questions Answered

## ✅ Your Questions - Quick Answers

### 1. **"How do we do maintenance if there's a bug in live system?"**

**Answer:** Use the 3-tier workflow:

```
LOCAL (test fix) → STAGING (verify) → PRODUCTION (deploy)
```

**Steps:**
1. Reproduce bug locally on your Mac
2. Fix and test offline
3. Deploy to Azure staging slot first
4. Test on staging
5. Swap staging → production (instant, zero downtime)
6. If issues, instant rollback

**See full details:** `docs/PRODUCTION_WORKFLOW_GUIDE.md` Section 6

---

### 2. **"How to push code to GitHub without exposing keys?"**

**Answer:** Use `.gitignore` to never commit secrets:

```bash
# Already created at root: .gitignore
# This protects all .env files automatically

# Safe to commit:
.env.example          ✅ (no real values)
requirements.txt      ✅
source code          ✅

# NEVER committed:
.env                  ❌ (real secrets)
.env.production       ❌
backend/.env          ❌
```

**Your Twilio credentials in VSCode are safe** - they're in `.env` files which are protected.

**See full details:** `docs/PRODUCTION_WORKFLOW_GUIDE.md` Section 2

---

### 3. **"How to host on bultoo.com?"**

**Answer:** Configure custom domain in your domain registrar + Azure:

**DNS Setup (in GoDaddy/Namecheap):**
```
Type    Name    Value
CNAME   api     boloo-backend-app.azurewebsites.net
CNAME   admin   boloo-web-app.azurewebsites.net
```

**Azure Setup:**
```bash
az webapp config hostname add \
  --webapp-name boloo-backend-app \
  --hostname api.bultoo.com

# Auto-enable free HTTPS/SSL
az webapp config ssl bind \
  --name boloo-backend-app \
  --certificate-thumbprint auto \
  --hostname api.bultoo.com
```

**Result:**
- Backend API: `https://api.bultoo.com`
- Admin Panel: `https://admin.bultoo.com`

**See full details:** `docs/PRODUCTION_WORKFLOW_GUIDE.md` Section 3

---

### 4. **"Where is the moderator frontend?"**

**Answer:** Located at `/Users/diptendu/boloo app/boloo-app/web`

**What it has:**
- Cases management
- User management
- Analytics dashboard
- Monitoring
- Settings
- Entities & Taxonomies

**To run locally:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/web"
npm install
npm run dev
# Opens at http://localhost:3000
```

**To deploy:**
- Option 1: Vercel (easiest for Next.js)
- Option 2: Azure Static Web Apps
- Option 3: Azure App Service

**See full details:** `docs/PRODUCTION_WORKFLOW_GUIDE.md` Section 4

---

### 5. **"How to make changes offline and push to live in future?"**

**Answer:** Standard Git workflow:

```bash
# 1. Make changes locally
cd "/Users/diptendu/boloo app/boloo-app/mobile"
# Edit ChatInterface.tsx...

# 2. Test with hot reload
npx expo start  # See changes instantly

# 3. When satisfied, commit
git add src/components/ChatInterface.tsx
git commit -m "UI: Change button color to blue"

# 4. Push to GitHub (secrets protected by .gitignore)
git push origin main

# 5. Deploy to staging first
az webapp deployment source config-zip \
  --name boloo-backend-app \
  --slot staging \
  --src backend-deploy.zip

# 6. Test staging

# 7. Swap to production
az webapp deployment slot swap \
  --name boloo-backend-app \
  --slot staging \
  --target-slot production
```

**See full details:** `docs/PRODUCTION_WORKFLOW_GUIDE.md` Sections 5, 6, 7

---

### 6. **"UI/UX tweaks needed in the app"**

**Answer:** Easy with hot reload!

**For Mobile App:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"

# Edit any file, e.g.:
# - src/components/ChatInterface.tsx (chat UI)
# - src/screens/HomeScreen.tsx (home page)
# - app.json (colors, icons, splash screen)

npx expo start
# Changes appear instantly on device/emulator
```

**For Web Admin:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/web"

# Edit any file, e.g.:
# - app/cases/page.tsx (cases page)
# - components/Navigation.tsx (navigation)

npm run dev
# Changes appear instantly at localhost:3000
```

**After testing, build for production:**
```bash
# Mobile
eas build --platform android

# Web
npm run build
vercel --prod
```

**See full details:** `docs/PRODUCTION_WORKFLOW_GUIDE.md` Section 7

---

## 🚀 Immediate Next Steps

### Step 1: Protect Your Secrets (Done!)
✅ Created `.gitignore` in project root
✅ Your Twilio credentials are safe in `.env` files

### Step 2: Push Code to GitHub Safely
```bash
cd "/Users/diptendu/boloo app/boloo-app"

# Initialize git (if not done)
git init

# Add all files (secrets excluded by .gitignore)
git add .
git commit -m "Initial commit - Boloo MVP"

# Create private GitHub repo
gh repo create boloo-mvp --private --source=. --remote=origin
git push -u origin main
```

### Step 3: Create Azure Staging Slot
```bash
# For testing before production
az webapp deployment slot create \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --slot staging
```

### Step 4: Deploy Moderator Frontend
```bash
cd "/Users/diptendu/boloo app/boloo-app/web"

# Option A: Vercel (Recommended)
npm install -g vercel
vercel login
vercel --prod

# Or Option B: Azure Static Web App
az staticwebapp create \
  --name boloo-admin \
  --resource-group cgnet-mvp-rg \
  --location southindia
```

### Step 5: Setup Custom Domain (bultoo.com)
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Add DNS records (CNAME for api.bultoo.com)
3. Configure in Azure (commands in workflow guide)
4. Enable free SSL (automatic)

### Step 6: Configure Twilio
Your credentials are already saved in VSCode. I need:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

Then I'll add them to Azure securely.

---

## 📁 Project Structure

```
boloo-app/
├── backend/              # FastAPI Python backend
│   ├── app/
│   ├── .env             # ❌ Never commit (protected)
│   └── .env.example     # ✅ Safe to commit
├── mobile/              # React Native Expo app
│   ├── src/
│   ├── app.json
│   └── .env             # ❌ Never commit
├── web/                 # Next.js moderator frontend
│   ├── app/
│   ├── components/
│   └── .env.local       # ❌ Never commit
└── docs/                # All documentation
    ├── PRODUCTION_WORKFLOW_GUIDE.md  # Full guide
    ├── AZURE_DEPLOYMENT_SUCCESS.md   # Deployment details
    └── QUICK_START_GUIDE.md          # This file
```

---

## 💡 Pro Tips

1. **Always test locally first** - Fast iteration with hot reload
2. **Use staging before production** - Zero-risk testing
3. **Never commit .env files** - .gitignore protects you
4. **Instant rollback available** - Swap slots if issues
5. **Custom domain with free SSL** - Professional URLs
6. **Monitor costs** - Set Azure budget alerts

---

## 🆘 Common Tasks

### Update API URL in mobile app
```bash
# Edit mobile/app.json
"apiUrl": "https://api.bultoo.com"

# Rebuild
eas build --platform android
```

### View production logs
```bash
az webapp log tail \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg
```

### Rollback production instantly
```bash
az webapp deployment slot swap \
  --name boloo-backend-app \
  --slot production \
  --target-slot staging
```

### Update environment variable
```bash
az webapp config appsettings set \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --settings NEW_VAR="value"
```

---

**For complete details, see:** `docs/PRODUCTION_WORKFLOW_GUIDE.md`

**Generated:** November 20, 2025
