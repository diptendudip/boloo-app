# Azure Settings Restoration - Quick Start Guide

**Last Updated:** 2025-11-24
**Status:** ✅ Scripts Ready - ⚠️ Manual Rotation Required

---

## 🚨 CRITICAL FINDINGS

After verification, here's what we discovered:

### ✅ GOOD NEWS
- All 31 Azure App Settings have **non-null values**
- Backend health endpoint is **responding (HTTP 200)**
- App Service is **running**
- Database and storage connections are **working**
- **AZURE_SPEECH_KEY has already been rotated** ✅

### ⚠️ URGENT ACTION NEEDED
- **AZURE_OPENAI_API_KEY still uses the exposed key** - MUST rotate immediately
- APP_ENV is set to "development" instead of "production" - Should update

---

## ⚡ QUICK FIX (5 Minutes)

### Step 1: Rotate AZURE_OPENAI_API_KEY

**Option A: Azure Portal (Recommended)**
1. Go to https://portal.azure.com
2. Navigate to: Cognitive Services → cgnet-openai
3. Click: Keys and Endpoint
4. Click: Regenerate Key 1
5. Copy the NEW key
6. Run this command:
```bash
az webapp config appsettings set \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --settings AZURE_OPENAI_API_KEY="<PASTE_NEW_KEY_HERE>"
```

**Option B: Azure CLI (Faster)**
```bash
# Regenerate and update in one go
NEW_OPENAI_KEY=$(az cognitiveservices account keys regenerate \
  --name cgnet-openai \
  --resource-group cgnet-mvp-rg \
  --key-name key1 \
  --query "key1" \
  --output tsv)

az webapp config appsettings set \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --settings AZURE_OPENAI_API_KEY="$NEW_OPENAI_KEY"
```

### Step 2: Fix APP_ENV to Production
```bash
az webapp config appsettings set \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --settings APP_ENV="production"
```

### Step 3: Restart and Verify
```bash
# Restart backend
az webapp restart \
  --resource-group boloo-production-rg \
  --name boloo-backend-api

# Wait 30 seconds, then test
sleep 30
curl https://boloo-backend-api.azurewebsites.net/health

# Run verification script
cd "/Users/diptendu/boloo app/boloo-app/backend/scripts"
./verify-azure-settings.sh
```

---

## 📋 Complete Scripts Available

### 1. Restoration Script
**File:** `restore-azure-settings.sh`
**Purpose:** Backup and restore all Azure app settings
**Usage:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend/scripts"
./restore-azure-settings.sh
```

**What it does:**
- ✅ Backs up current settings to JSON
- ✅ Generates new JWT_SECRET_KEY
- ✅ Restores all safe settings
- ✅ Creates rotation checklist
- ⚠️ Identifies settings needing manual rotation

### 2. Verification Script
**File:** `verify-azure-settings.sh`
**Purpose:** Verify all settings are correct and secure
**Usage:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend/scripts"
./verify-azure-settings.sh
```

**What it checks:**
- ✅ No null or empty values
- ✅ Critical settings exist
- ✅ Backend health endpoint
- ⚠️ Exposed keys rotated
- ✅ App Service status
- ✅ Environment configuration

---

## 📊 Current Status Summary

| Item | Status | Action |
|------|--------|--------|
| App Settings Count | ✅ 31/31 | None |
| Null Values | ✅ 0 | None |
| Backend Health | ✅ HTTP 200 | None |
| App Service | ✅ Running | None |
| AZURE_SPEECH_KEY | ✅ Rotated | None |
| AZURE_OPENAI_API_KEY | ⚠️ NOT rotated | **ROTATE NOW** |
| JWT_SECRET_KEY | ✅ Can rotate if needed | Optional (use script) |
| APP_ENV | ⚠️ development | **Change to production** |
| DATABASE_URL | ✅ Working | None |
| STORAGE | ✅ Working | None |

---

## 🎯 Priority Actions (In Order)

1. **CRITICAL:** Rotate AZURE_OPENAI_API_KEY (5 min)
2. **HIGH:** Update APP_ENV to "production" (1 min)
3. **MEDIUM:** Restart backend and verify (2 min)
4. **LOW:** Run full restoration script for documentation (5 min)
5. **FOLLOW-UP:** Remove .env from git history (20 min)

---

## 🔗 Full Documentation

- **Comprehensive Report:** `/Users/diptendu/boloo app/docs/AZURE_SETTINGS_RESTORE.md`
- **Immediate Actions:** `/Users/diptendu/boloo app/IMMEDIATE_ACTIONS_REQUIRED.md`
- **Restoration Script:** `/Users/diptendu/boloo app/boloo-app/backend/scripts/restore-azure-settings.sh`
- **Verification Script:** `/Users/diptendu/boloo app/boloo-app/backend/scripts/verify-azure-settings.sh`

---

## ✅ Success Checklist

After completing the rotation:

- [ ] AZURE_OPENAI_API_KEY rotated
- [ ] APP_ENV set to "production"
- [ ] Backend restarted
- [ ] Health endpoint returns HTTP 200
- [ ] Verification script shows all green ✅
- [ ] Test OpenAI integration working
- [ ] No errors in application logs
- [ ] .env removed from git history (see IMMEDIATE_ACTIONS_REQUIRED.md)

---

**Need Help?** See full documentation or contact: diptendudip@gmail.com
