# MVP Corrected Plan - Audio INCLUDED

**IMPORTANT:** Audio upload is PART of MVP, not optional!

---

## 🎯 CORRECTED MVP SCOPE

### **MUST HAVE (All Required for MVP):**
✅ Text-based grievance submission
✅ **Audio recording and upload** ← KEEPING THIS
✅ Real AI conversations (Azure OpenAI)
✅ Audio transcription (Azure Speech)
✅ Case tracking ("My Cases")
✅ Entity routing to authorities
✅ SLA tracking
✅ Privacy enforcement

### **REMOVED FROM PLAN:**
❌ ~~Disable audio~~ - BAD IDEA, audio stays!

---

## 🚨 ACTUAL MVP BLOCKERS (Corrected)

### **BLOCKER #1: conversation_service.py (CRITICAL)**
**Status:** 🔴 Mock implementation
**Fix:** Replace with Azure OpenAI
**Time:** 30 minutes
**Priority:** P0

### **BLOCKER #2: Azure Speech Credentials (CRITICAL)**
**Status:** 🔴 NOT CONFIGURED
**File:** `backend/.env`
**Missing:**
- `AZURE_SPEECH_KEY=<your-key>`
- `AZURE_SPEECH_REGION=<your-region>`

**Impact:** Audio transcription falls back to dummy mode
**Fix Required:**
1. Get Azure Speech credentials from Azure Portal
2. Add to `.env` file
3. Test transcription

**Time:** 15 minutes (if credentials available)

### **BLOCKER #3: expo-av Deprecation (MEDIUM)**
**Status:** 🟡 Still using deprecated package
**Files:**
- `mobile/src/components/ChatInterface.tsx`
- `mobile/src/utils/AudioCompressor.ts`

**Fix:** Replace with expo-audio
**Time:** 30 minutes

### **BLOCKER #4: next_steps.py (LOW)**
**Status:** 🟡 Verify dummy data not used
**Time:** 10 minutes

---

## 📋 PARALLEL EXECUTION (CORRECTED)

### **Track 1: Backend AI Fixes** (CRITICAL - 45 min)
```bash
# Task 1.1: Fix conversation_service.py (30 min)
# - Replace mock with Azure OpenAI
# - Use gpt-4o-mini

# Task 1.2: Get Azure Speech credentials (15 min)
# - Check Azure Portal for Speech resource
# - Add AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to .env
# - Test transcription works
```

### **Track 2: Mobile Audio Updates** (HIGH - 30 min)
```bash
# Task 2.1: Replace expo-av with expo-audio (30 min)
# - Install expo-audio@~14.0.0
# - Update ChatInterface.tsx
# - Update AudioCompressor.ts
# - Test audio recording still works
```

### **Track 3: Testing** (After Tracks 1-2)
```bash
# Task 3.1: Test audio → transcription → AI conversation (30 min)
# - Record audio in mobile app
# - Upload to backend
# - Verify transcription works (Azure Speech)
# - Verify conversation works (Azure OpenAI)
# - Check case creation
```

---

## ✅ CORRECTED SUCCESS CRITERIA

**MVP is ready when:**
- ✅ User can submit grievance via TEXT
- ✅ User can submit grievance via AUDIO (with transcription)
- ✅ AI has natural conversation (not mock)
- ✅ Case created and visible in "My Cases"
- ✅ Case routed to correct authority
- ✅ User sees "What happens next" with SLA

---

## 🚨 CRITICAL DECISION NEEDED

**Do you have Azure Speech credentials?**

**Option A:** YES - I have Azure Speech credentials
- ✅ Add to .env file
- ✅ Test transcription
- ✅ Launch full MVP with audio

**Option B:** NO - Need to create Azure Speech resource
- Create Speech resource in Azure Portal (5 min)
- Get credentials
- Add to .env
- ✅ Launch full MVP with audio

**Option C:** Use different transcription service
- Configure alternative (OpenAI Whisper?)
- Update transcription_service.py
- Test and launch

**Which option applies to you?**

---

*Created: Nov 19, 2025*
*Correction: Audio is PART of MVP, not optional*
*Next: Configure Azure Speech credentials*
