# 🎯 Boloo Mobile Web Hosting Recommendations

**Date:** November 22, 2025
**Platform:** Boloo Citizen Grievance Reporting Platform

---

## 📊 Business Context Analysis

### What Boloo Is
- **Purpose**: Government-backed citizen grievance reporting platform for Chhattisgarh
- **Target Users**: Rural Indian citizens (Hindi-first, voice-optimized)
- **Data Type**: Sensitive citizen data (grievances, phone numbers, locations, voice recordings)
- **Compliance**: Government data sovereignty requirements - **MUST store in India**

### Critical Requirements
1. ✅ **Data Sovereignty**: All citizen data MUST remain in India
2. ✅ **Privacy-First**: Personal diary entries must be 100% private
3. ✅ **Government Compliance**: Audit logging, SLA tracking
4. ✅ **Accessibility**: Fast load times for rural 4G users
5. ✅ **Cost Efficiency**: Minimize infrastructure costs

---

## 🗂️ Current Architecture

### What's Already in Central India ✅
| Component | Service | Data Type | Location |
|-----------|---------|-----------|----------|
| **Backend API** | Azure App Service (B1) | Business logic | Central India ✅ |
| **Database** | PostgreSQL Flexible Server | User data, cases, profiles | Central India ✅ |
| **Audio Storage** | Azure Blob Storage | Voice recordings | Central India ✅ |
| **Azure OpenAI** | GPT-4o-mini | AI processing | Central India ✅ |
| **Azure Speech** | Speech-to-Text | Voice transcription | Central India ✅ |

### What's Currently in US ❌
| Component | Service | Data Type | Location |
|-----------|---------|-----------|----------|
| **Mobile Web App** | Azure Static Web Apps (Free) | HTML, JavaScript, CSS (NO user data) | Central US ❌ |

---

## 🔍 Data Flow Analysis

### Mobile Web App (Static Files)
```javascript
web-build/
├── index.html          // 5 KB - App shell
├── _expo/
│   └── static/
│       └── js/
│           └── bundle.js  // 1.8 MB - React Native Web code
└── assets/             // 100 KB - Fonts, icons
```

**Total Size**: ~1.86 MB
**Contains**: ZERO user data, just application code
**Purpose**: Loads once, then runs in browser

### User Data Flow (API Calls)
```
User in India
    ↓
Mobile Web App (downloads once from US)
    ↓
ALL API CALLS → Backend in Central India ✅
    ├─ User authentication
    ├─ Grievance submission
    ├─ Voice transcription
    ├─ Case tracking
    └─ Feed/social features
    ↓
Database in Central India ✅
```

**Key Insight**:
- Static files downloaded **ONCE** (slow if from US)
- API calls happen **CONSTANTLY** (already fast - India to India)

---

## 🎯 Recommended Solution: Host on Existing Backend (Option 3)

### Why This Is Best for Boloo

**For Government Compliance:**
- ✅ **100% India hosting** - satisfies data sovereignty requirements
- ✅ **Simplified audits** - everything in one infrastructure
- ✅ **Single jurisdiction** - no cross-border data concerns
- ✅ **Fewer attack vectors** - one domain, one certificate, one security perimeter

**For Performance:**
- ✅ **Fast loads for Indian users** - Central India to India (~50-100ms)
- ✅ **Already optimized region** - same as your API
- ✅ **No additional CDN needed** - local hosting is fast enough

**For Cost:**
- ✅ **₹0 additional cost** - already paying for B1 App Service (₹1,380/month)
- ✅ **Save ₹750/month** vs Azure Storage Static Website upgrade
- ✅ **No bandwidth charges** - included in App Service plan

**For Operations:**
- ✅ **Single deployment** - one CI/CD pipeline
- ✅ **One domain** - `boloo-backend-api.azurewebsites.net` serves both API and web
- ✅ **Shared SSL** - one certificate to manage
- ✅ **Easier troubleshooting** - all logs in one place

---

## 📋 Implementation: Host Mobile Web on Backend

### Option A: Serve from `/mobile` path (Recommended)

```
URL Structure:
- https://boloo-backend-api.azurewebsites.net/          → API (existing)
- https://boloo-backend-api.azurewebsites.net/mobile/   → Mobile web app (new)
- https://boloo-backend-api.azurewebsites.net/docs      → API docs (existing)
```

**How to implement:**

1. **Build mobile web** (already done):
```bash
cd mobile
npx expo export --platform web
# Creates: mobile/web-build/
```

2. **Copy to backend static folder**:
```bash
# Create static folder in backend
mkdir -p backend/static/mobile

# Copy web build
cp -r mobile/web-build/* backend/static/mobile/
```

3. **Update FastAPI to serve static files** (`backend/app/main.py`):
```python
from fastapi.staticfiles import StaticFiles

# Mount static files
app.mount("/mobile", StaticFiles(directory="static/mobile", html=True), name="mobile")
```

4. **Deploy to Azure**:
```bash
# Existing deployment command works
# Azure deploys both API + static files
```

**Pros:**
- ✅ Simple path separation
- ✅ API remains at root
- ✅ Easy to understand

**Cons:**
- ⚠️ Slightly longer URL

---

### Option B: Separate subdomain (Production-ready)

```
URL Structure:
- https://api.boloo.gov.in/       → Backend API
- https://app.boloo.gov.in/       → Mobile web app
- https://admin.boloo.gov.in/     → Admin dashboard
```

**Requires:**
- Custom domain registration
- DNS configuration
- SSL certificate setup

**Best for:** Production launch with custom domain

---

## 🚀 Quick Migration Guide

### Step 1: Build Mobile Web
```bash
cd mobile
npx expo export --platform web --output-dir dist
```

### Step 2: Add Static File Serving to Backend
```python
# backend/app/main.py
from fastapi.staticfiles import StaticFiles
import os

# Mount static files for mobile web
static_path = os.path.join(os.path.dirname(__file__), "..", "static", "mobile")
if os.path.exists(static_path):
    app.mount("/mobile", StaticFiles(directory=static_path, html=True), name="mobile")
```

### Step 3: Update Deployment Script
```bash
# Add to your deployment workflow
- name: Build mobile web
  run: |
    cd mobile
    npm install
    npx expo export --platform web

- name: Copy to backend static
  run: |
    mkdir -p backend/static/mobile
    cp -r mobile/dist/* backend/static/mobile/

- name: Deploy backend with static files
  run: |
    cd backend
    zip -r deploy.zip . -x "*.git*" -x "node_modules/*"
    az webapp deployment source config-zip \
      --resource-group boloo-production-rg \
      --name boloo-backend-api \
      --src deploy.zip
```

### Step 4: Test
```bash
# Mobile web app
https://boloo-backend-api.azurewebsites.net/mobile/

# API still works
https://boloo-backend-api.azurewebsites.net/api/dropdown/states
```

---

## 📊 Cost Comparison

| Option | Monthly Cost | Location | Setup Complexity |
|--------|--------------|----------|------------------|
| **Current (Static Web Apps Free)** | ₹0 | Central US ❌ | Already done |
| **Option 1: Azure Storage** | ₹40 | Central India ✅ | Medium |
| **Option 2: App Service** | ₹1,500 | Central India ✅ | High |
| **Option 3: Existing Backend** | **₹0** | **Central India** ✅ | **Low** |

**Winner**: Option 3 - same cost as current, but in India!

---

## ⚡ Performance Comparison

### Current Setup (US Hosting)
```
User in India → Static files from US (3-5 sec first load) ❌
               ↓
            API calls to India (200-500ms) ✅
```

### Recommended Setup (Backend Hosting)
```
User in India → Static files from India (1-2 sec first load) ✅
               ↓
            API calls to India (200-500ms) ✅
```

**Improvement**: 2-3x faster first load for Indian users!

---

## 🛡️ Security & Compliance Benefits

### Single Security Perimeter
- One domain to secure
- One SSL certificate
- One firewall configuration
- One WAF policy
- One DDoS protection

### Audit Trail
- All access logs in one place
- Single Azure resource for compliance review
- Simplified government audit process

### Data Residency
- 100% India hosting
- No cross-border data transfer
- Meets local data protection requirements

---

## 📈 Scalability Path

### Today (Testing Phase)
- B1 App Service: Serves both API + Mobile Web
- Handles 100-1,000 concurrent users

### Growth (1,000-10,000 users)
- Scale up to B2/B3
- Add Azure Front Door for caching
- Static files cached at edge

### Production (10,000+ users)
- Separate App Service for web (optional)
- Azure CDN for static files
- Load balancer for API

**Note**: Can start simple, scale later!

---

## ✅ Implementation Checklist

- [ ] Build mobile web locally (`npx expo export --platform web`)
- [ ] Test build locally with `python -m http.server` in `web-build/`
- [ ] Create `backend/static/mobile/` directory
- [ ] Copy web build to backend static folder
- [ ] Update `backend/app/main.py` to mount static files
- [ ] Test locally: `http://localhost:8000/mobile/`
- [ ] Update API base URL in mobile app if path changes
- [ ] Deploy to Azure (same process as before)
- [ ] Test production: `https://boloo-backend-api.azurewebsites.net/mobile/`
- [ ] Update documentation with new URL
- [ ] Delete old Static Web App (optional, save free tier)

---

## 🎯 Final Recommendation

**Use Option 3: Host on Existing Backend**

**Reasoning:**
1. **Government compliance** - 100% India hosting
2. **Zero additional cost** - already paying for backend
3. **Better performance** - faster for Indian users
4. **Simpler architecture** - one less moving part
5. **Easier to audit** - everything in one place
6. **Production-ready** - can scale when needed

**Next Steps:**
1. Implement static file serving in FastAPI
2. Deploy mobile web to backend
3. Test at `/mobile` path
4. Share new URL with friends for testing
5. Plan for custom domain before production launch

---

**This approach gives you the best of all worlds: compliance, performance, and cost efficiency!** 🎉
