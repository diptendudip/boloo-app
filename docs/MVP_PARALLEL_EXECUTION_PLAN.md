# MVP Parallel Execution Plan - Budget-Conscious Approach

**Created:** Nov 19, 2025
**Azure Budget:** 17,000 INR (~$200 USD) - **INCLUDES OpenAI Credits**
**Strategy:** Fix everything locally FIRST, deploy to Azure LAST

---

## 🚨 CRITICAL: Azure Cost Management

### Your Budget Reality

**Total Credits:** 17,000 INR (~$200 USD)
**Includes:** OpenAI API calls for LLM
**Current Usage:** Unknown (need to check)
**Risk:** Can burn through credits FAST if not careful

### Azure Service Costs (Monthly Estimates)

| Service | Tier | Monthly Cost (INR) | Usage |
|---------|------|-------------------|-------|
| **App Service** | F1 Free | ₹0 | 60 CPU min/day limit |
| **App Service** | B1 Basic | ₹1,050 | Recommended for production |
| **PostgreSQL** | B1ms Burstable | ₹990 | 1vCore, 2GB RAM |
| **Storage** | Standard LRS | ₹150-300 | 100GB storage |
| **CDN** | Standard | ₹0-500 | First 10GB free |
| **OpenAI GPT-4o-mini** | Per token | Variable | **This eats your credits!** |
| | | | |
| **MINIMUM MONTHLY** | | **₹2,190** | Using F1 free tier |
| **RECOMMENDED MONTHLY** | | **₹3,000-4,000** | Using B1 tier |

### OpenAI Cost Reality

**gpt-4o-mini pricing:**
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**Real usage (conservative estimate):**
- 100 conversations/day
- ~500 tokens per conversation
- **Monthly:** ~1.5M tokens = **₹500-1,000**

### Budget Breakdown Strategy

**Safe Allocation:**
- **Infrastructure:** ₹3,000/month (App Service, DB, Storage)
- **OpenAI:** ₹2,000/month (conservative)
- **Buffer:** ₹1,000/month (unexpected costs)
- **Total:** ₹6,000/month

**Your 17k INR lasts:** ~2.5 months if careful

### 🚨 DANGER ZONES (Avoid These)

| Service | Cost | Why Dangerous |
|---------|------|---------------|
| **Premium App Service** | ₹8,000+/mo | 8x more expensive |
| **General Purpose PostgreSQL** | ₹6,000+/mo | 6x more expensive |
| **Azure Cognitive Search** | ₹3,000+/mo | Not needed for MVP |
| **Application Insights** | ₹500+/mo | Use basic logging instead |
| **Excessive OpenAI calls** | Variable | No retry loops! |
| **Multiple environments** | 2-3x cost | Dev locally, prod only |

### Cost Control Measures

```bash
# 1. Set spending limits IMMEDIATELY after deployment
az consumption budget create \
  --budget-name boloo-monthly-limit \
  --amount 6000 \
  --category cost \
  --time-grain monthly \
  --start-date 2025-11-01 \
  --end-date 2026-06-30

# 2. Set alerts at 50%, 80%, 100%
# 3. Monitor daily with:
az consumption usage list --start-date 2025-11-01 --end-date 2025-11-30
```

---

## 📋 DOCUMENTATION AUDIT

### ✅ COMPLETE & READY (No Work Needed)

| Document | Lines | Status | Notes |
|----------|-------|--------|-------|
| **AZURE_DEPLOYMENT_GUIDE.md** | 600 | ✅ Ready | Complete Azure setup |
| **DOMAIN_SETUP.md** | 547 | ✅ Ready | GoDaddy → Azure DNS |
| **APK_BUILD_GUIDE.md** | 795 | ✅ Ready | EAS Build complete |
| **CI_CD_PIPELINE.md** | 831 | ✅ Ready | GitHub Actions |
| **PERFORMANCE_OPTIMIZATION.md** | 744 | ✅ Ready | Mobile optimization plan |
| **RECOVERY_GUIDE.md** | 331 | ✅ Ready | Crash recovery |
| **CRASH_RECOVERY_SYSTEM.md** | - | ✅ Ready | Auto-checkpoint system |
| **MVP_SETUP.md** | 154 | ✅ Ready | First-time setup |
| **START_HERE.md** | 154 | ✅ Ready | Quick start guide |

**Total Documentation:** 4,156+ lines, 9 complete guides

### ⚠️ NEEDS IMPLEMENTATION (Pre-Azure Work)

| Component | Status | Time | Priority |
|-----------|--------|------|----------|
| **conversation_service.py** | 🔴 Mock | 30 min | CRITICAL |
| **transcription_service.py** | 🟡 Fallback | 15 min | MEDIUM |
| **next_steps.py** | 🟡 Verify | 10 min | LOW |
| **expo-av → expo-audio** | 🟡 Deprecated | 30 min | HIGH |
| **Hermes engine** | ⏸️ Optional | 5 min | MEDIUM |
| **APK build test** | ⏸️ Not done | 30 min | HIGH |

**Total Pre-Work:** 2 hours (critical path: 55 minutes)

---

## 🚀 PARALLEL EXECUTION PLAN (4 Tracks)

### **Track 1: Backend MVP Fixes** (CRITICAL - 55 min)
**Owner:** Backend specialist
**Blocks:** MVP launch

```bash
# Task 1.1: Fix conversation_service.py (30 min)
cd backend/app/services
# Replace mock with real Azure OpenAI
# Use gpt-4o-mini deployment
# Test natural conversation flow

# Task 1.2: Audio strategy decision (10 min)
# Decision: Text-only MVP (fastest path)
# Remove/disable audio upload for now
# Add "Coming soon" message

# Task 1.3: Verify next_steps.py (10 min)
# Check if dummy function is used
# Ensure real data in production
# Test endpoint

# Task 1.4: End-to-end test (5 min)
curl localhost:8000/v1/cases
# Test full conversation flow
```

### **Track 2: Mobile Performance** (MEDIUM - 65 min)
**Owner:** Mobile specialist
**Can run parallel to Track 1**

```bash
# Task 2.1: Replace expo-av (30 min)
cd mobile
npm install expo-audio@~14.0.0
npm uninstall expo-av
# Update VoiceRecordScreen.tsx imports
# Update app.json dependencies

# Task 2.2: Enable Hermes (5 min)
# Edit app.json: "android": { "jsEngine": "hermes" }

# Task 2.3: Code splitting setup (30 min)
# Implement React.lazy for screens
# Test bundle size reduction
```

### **Track 3: Testing & QA** (HIGH - 45 min)
**Owner:** QA specialist
**Starts after Track 1 completes**

```bash
# Task 3.1: Backend API testing (15 min)
# Test all endpoints
# Verify conversation flow
# Check entity routing

# Task 3.2: Mobile app testing (20 min)
# Test on Android device
# Verify performance improvements
# Check offline mode

# Task 3.3: APK build test (10 min)
eas build --platform android --profile preview
# Verify APK size
# Test on device
```

### **Track 4: Azure Deployment** (LAST - 2-3 hours)
**Owner:** DevOps specialist
**Only starts when Tracks 1-3 are 100% complete**

```bash
# Phase 1: Azure setup (60 min)
# Follow AZURE_DEPLOYMENT_GUIDE.md
# Create resource group
# Setup PostgreSQL (B1ms tier ONLY)
# Setup App Service (B1 tier ONLY)
# Configure environment variables

# Phase 2: Domain & SSL (30 min)
# Follow DOMAIN_SETUP.md
# Configure DNS
# Setup free SSL certificate

# Phase 3: Deploy & test (30 min)
# Deploy backend
# Run migrations
# Health check
# Test production API

# Phase 4: Monitor & optimize (30 min)
# Setup budget alerts
# Configure logging
# Monitor first hour
```

---

## 🎯 EXECUTION TIMELINE

### **Day 1: Pre-Deployment (Local Work Only)**

**Morning (2 hours):**
- ✅ Track 1: Backend MVP fixes (55 min)
- ✅ Track 2: Mobile performance (65 min in parallel)
- ✅ Break & sync (10 min)

**Afternoon (2 hours):**
- ✅ Track 3: Testing & QA (45 min)
- ✅ Fix any issues found (30 min buffer)
- ✅ Final verification (15 min)
- ✅ Document results (15 min)

**Evening (DECISION POINT):**
```
IF all tests pass:
  ✅ Proceed to Azure deployment
ELSE:
  ⚠️ Fix issues, retest tomorrow
```

### **Day 2: Deployment (If Day 1 succeeds)**

**Morning (3 hours):**
- ✅ Azure resource creation (60 min)
- ✅ Backend deployment (60 min)
- ✅ Testing & verification (60 min)

**Afternoon (2 hours):**
- ✅ Domain setup (30 min)
- ✅ APK build & distribution (60 min)
- ✅ Final smoke tests (30 min)

**Evening:**
- 🎉 MVP LAUNCHED

---

## 🔍 PRE-FLIGHT CHECKLIST (Before Azure)

### **Backend Checklist:**
- [ ] conversation_service.py uses real Azure OpenAI
- [ ] No mock/dummy implementations
- [ ] All tests pass
- [ ] Database migrations tested
- [ ] Environment variables documented
- [ ] Health endpoint working
- [ ] API docs accessible

### **Mobile Checklist:**
- [ ] expo-audio installed and working
- [ ] Deprecated packages removed
- [ ] Hermes enabled (optional)
- [ ] APK builds successfully
- [ ] App installs and runs on device
- [ ] No crashes or errors
- [ ] Offline mode works

### **Cost Checklist:**
- [ ] Budget alerts configured
- [ ] Only B1 tier services planned
- [ ] No premium features enabled
- [ ] OpenAI retry logic tested (no infinite loops!)
- [ ] Monitoring dashboard ready
- [ ] Cost calculator verified

---

## 💰 AZURE COST CALCULATOR (Pre-Deployment)

### **Estimated Monthly Costs:**

```
Infrastructure:
├─ App Service (B1)        : ₹1,050
├─ PostgreSQL (B1ms)       : ₹990
├─ Storage (Standard 100GB): ₹200
├─ Bandwidth (10GB)        : ₹0 (free tier)
└─ Subtotal                : ₹2,240/month

OpenAI (Conservative):
├─ 100 conversations/day
├─ 3,000/month total
├─ ~1.5M tokens/month
└─ Cost                    : ₹500-1,000/month

TOTAL MONTHLY              : ₹2,740-3,240
Budget Duration (17k INR)  : 5-6 months
```

### **Aggressive Usage (Danger Zone):**

```
Infrastructure:
├─ App Service (B1)        : ₹1,050
├─ PostgreSQL (B1ms)       : ₹990
├─ Storage (Standard 100GB): ₹200
└─ Subtotal                : ₹2,240/month

OpenAI (High usage):
├─ 500 conversations/day
├─ 15,000/month total
├─ ~7.5M tokens/month
└─ Cost                    : ₹2,500-5,000/month

TOTAL MONTHLY              : ₹4,740-7,240
Budget Duration (17k INR)  : 2-3 months ⚠️
```

### **Cost Optimization Strategies:**

1. **Use F1 Free Tier for initial testing** (saves ₹1,050/month)
2. **Text-only MVP** (no Azure Speech costs)
3. **Lazy load models** (reduce OpenAI calls)
4. **Cache common responses** (reduce redundant API calls)
5. **Rate limiting** (prevent abuse)
6. **Monitor daily** (catch issues early)

---

## 🚨 RISK MITIGATION

### **High-Risk Scenarios:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| **OpenAI retry loops** | Burn entire budget in hours | Add circuit breaker, max retries = 3 |
| **Unexpected traffic spike** | ₹10k+ in one day | Rate limiting, budget alerts |
| **Premium tier accidental** | 8x cost increase | Template validation, reviews |
| **Forgot to shutdown dev env** | 2x costs | Single environment only |
| **No monitoring** | Surprise bills | Daily check mandatory |

### **Safety Net Commands:**

```bash
# 1. Emergency shutdown (if costs spike)
az webapp stop --name bultoo-api --resource-group bultoo-rg

# 2. Check current spending
az consumption usage list --start-date $(date -d '1 month ago' +%Y-%m-%d)

# 3. Delete everything (nuclear option)
az group delete --name bultoo-rg --yes --no-wait
```

---

## ✅ SUCCESS CRITERIA

### **Pre-Deployment:**
- ✅ All 3 MVP blockers fixed
- ✅ Mobile app builds successfully
- ✅ All tests pass locally
- ✅ Performance targets met
- ✅ Documentation complete

### **Post-Deployment:**
- ✅ Backend responding on Azure
- ✅ Database connected and working
- ✅ Mobile app connects to production API
- ✅ Budget alerts configured
- ✅ First 10 test cases successful
- ✅ Daily cost < ₹200

---

## 📊 CURRENT STATUS

### **What's Ready:**
- ✅ 9 comprehensive guides (4,156+ lines)
- ✅ Database with 9-state data
- ✅ All services running locally
- ✅ Crash recovery system

### **What Needs Work:**
- ⏸️ 3 MVP blockers (55 min)
- ⏸️ Mobile performance (65 min)
- ⏸️ Testing & QA (45 min)
- ⏸️ Azure deployment (3 hours)

### **Total Time to MVP:**
- **Local work:** 3-4 hours
- **Azure deployment:** 3 hours
- **Total:** 6-7 hours to production

---

## 🚀 RECOMMENDED IMMEDIATE ACTION

**START WITH LOCAL WORK (ZERO COST):**

```bash
# 1. Fix MVP blockers NOW (saves time and money)
cd backend
# Fix conversation_service.py
# Disable audio for MVP
# Test everything locally

# 2. Optimize mobile app (runs in parallel)
cd mobile
# Replace expo-av
# Enable Hermes
# Build and test APK

# 3. ONLY THEN deploy to Azure
# When everything works perfectly locally
# No debugging in cloud = no wasted credits
```

**AZURE IS THE LAST STEP, NOT THE FIRST!**

---

*Created: Nov 19, 2025*
*Budget: 17,000 INR (~$200 USD)*
*Strategy: Fix local first, deploy last*
*Estimated timeline: 6-7 hours to production MVP*
