# Android App Development - Gap Analysis & Phase-wise Update

**Date**: October 27, 2025
**Status**: Backend 70% Ready | Mobile App 40% Complete | Critical UX Features Missing

---

## 📊 Executive Summary

### What You Have Now
- ✅ Backend API with **triage-ready data models** (kind, triage_intent, routing_confidence)
- ✅ Mobile app with basic OTP auth + voice recording
- ✅ Web console with monitoring dashboard
- ✅ Database seeded with 131 Chhattisgarh entities

### What Your Updated Plan Requires
- **3-way triage system** (Grievance/Community/Personal)
- **"Agla Kya Hoga" uncertainty-killer UI** with SLA tracking
- **Funny-yet-respectful Chhattisgarhi/Hinglish tone**
- **Personal diary feature** (My Diary with nudges)
- **Minimalistic conversation-driven UX**
- **Hindi transcript by default** with Chhattisgarhi custom vocabulary

### Critical Finding 🎯
**Backend database models ALREADY SUPPORT your new plan!** The `Case` model has all the triage fields (kind, triage_intent, routing_confidence, can_convert_to_grievance, etc.). **Only UI/UX and conversation flow need to be built.**

---

## 🔍 Detailed Gap Analysis: 8-Point Plan vs Current State

### 1️⃣ **3-Way TRIAGE (Grievance/Community/Personal)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Backend Model** | ✅ Has `kind` enum (GRIEVANCE, COMMUNITY_STORY, PERSONAL) | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `triage_intent` enum | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `routing_confidence` float | ✅ Matches | **READY** |
| **Backend API** | ❌ No triage endpoint | ❌ Needs `POST /v1/cases/triage` | **MISSING** |
| **Mobile UI** | ❌ No triage selection | ❌ Needs triage overlay after 5-10s | **MISSING** |
| **Mobile UI** | ❌ No override chips | ❌ Needs 3 chips (Grievance/Community/Personal) | **MISSING** |
| **LLM Integration** | ❌ No Claude API for triage | ❌ Needs intent classification | **MISSING** |

**Gap**: Backend ready, but NO triage logic, NO API endpoint, NO mobile UI.

---

### 2️⃣ **"Agla Kya Hoga?" Uncertainty-Killer UI**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Backend Model** | ✅ Has `sla_due_at` field | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `entity_id` (responsible office) | ✅ Matches | **READY** |
| **Backend API** | ❌ No "what happens next" endpoint | ❌ Needs `GET /v1/cases/{id}/next-steps` | **MISSING** |
| **Mobile UI** | ❌ No "Agla Kya Hoga" card | ❌ Needs card after submit | **MISSING** |
| **Mobile UI** | ❌ No SLA clock visualization | ❌ Needs live timer (72h → BDO) | **MISSING** |
| **Mobile UI** | ❌ No "who has the ball" indicator | ❌ Needs timeline showing Citizen/Mod/Officer | **MISSING** |
| **Backend Logic** | ❌ No escalation calculation | ❌ Needs SLA → next rung logic | **MISSING** |

**Gap**: Models exist but NO API to calculate next steps, NO mobile UI to display.

---

### 3️⃣ **Funny-yet-Respectful Assistant Tone (Chhattisgarhi/Hinglish)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Mobile UI** | ✅ Has Hindi/English toggle | ⚠️ Needs Chhattisgarhi variant | **PARTIAL** |
| **Tone System** | ❌ No microcopy engine | ❌ Needs warm/humorous lines for greetings | **MISSING** |
| **Tone System** | ❌ No formal mode switch | ❌ Needs formal Hindi for official summary | **MISSING** |
| **Backend Model** | ✅ Has `formal_summary` field | ✅ Matches | **READY** |
| **LLM Integration** | ❌ No tone prompts | ❌ Needs Claude prompts with tone variants | **MISSING** |
| **Mobile UI** | ❌ No dynamic assistant messages | ❌ Needs contextual humor | **MISSING** |

**Gap**: Backend field exists, but NO tone engine, NO UI microcopy system.

---

### 4️⃣ **Language Handling (Code-mix & Chhattisgarhi)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Backend Model** | ✅ Has `hindi_transcript` field | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `raw_transcript` field | ✅ Matches (for audit) | **READY** |
| **ASR Integration** | ❌ No Azure Speech setup | ❌ Needs Hindi ASR with custom vocab | **MISSING** |
| **Mobile UI** | ✅ Shows English transcript | ❌ Needs Hindi (Devanagari) by default | **NEEDS UPDATE** |
| **Backend Config** | ❌ No custom vocabulary list | ❌ Needs village/officer names from Entities | **MISSING** |
| **Mobile UX** | ❌ No low-confidence retry | ❌ Needs "धीमे बोल दीजिए" reprompt | **MISSING** |

**Gap**: Models ready, but NO Azure Speech integration, NO custom vocabulary, NO Hindi-first UI.

---

### 5️⃣ **Trustworthy Directory (With Corrections)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Backend Model** | ⚠️ Entity model exists | ❌ Needs `version` field | **NEEDS UPDATE** |
| **Backend Model** | ❌ No correction proposals | ❌ Needs `suggested_updates` JSON field | **MISSING** |
| **Backend Model** | ❌ No verification tracking | ❌ Needs `last_verified_at` timestamp | **MISSING** |
| **Backend API** | ❌ No correction endpoint | ❌ Needs `POST /v1/entities/{id}/suggest-correction` | **MISSING** |
| **Web Console** | ❌ No admin approval UI | ❌ Needs correction review interface | **MISSING** |
| **Backend Logic** | ❌ No versioning logic | ❌ Needs old version retention | **MISSING** |

**Gap**: Entity model needs 3 new fields + correction workflow.

---

### 6️⃣ **Personal Issues = Retention Engine (My Diary)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Backend Model** | ✅ Has `kind=PERSONAL` enum | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `can_convert_to_grievance` bool | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `reminder_at` datetime | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `is_public=false` (privacy) | ✅ Matches | **READY** |
| **Backend API** | ❌ No personal diary endpoint | ❌ Needs `GET /v1/cases/personal` | **MISSING** |
| **Mobile UI** | ❌ No "My Diary" section | ❌ Needs private case list | **MISSING** |
| **Mobile UI** | ❌ No reminder UI | ❌ Needs nudge notifications | **MISSING** |
| **Mobile UI** | ❌ No "Convert to grievance" button | ❌ Needs one-tap conversion | **MISSING** |

**Gap**: Backend FULLY ready, but NO API routes, NO mobile UI for personal diary.

---

### 7️⃣ **Conversation Design (Minimal Slots)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Backend Model** | ✅ Has slot fields (when_started, scope_affected, prior_contact) | ✅ Matches | **READY** |
| **Backend Model** | ✅ Has `rights_consent` bool | ✅ Matches | **READY** |
| **LLM Integration** | ❌ No slot extraction logic | ❌ Needs Claude API for missing-slot detection | **MISSING** |
| **Mobile UI** | ❌ No live transcript overlay | ❌ Needs big Devanagari live transcript | **MISSING** |
| **Mobile UI** | ❌ No progress chips | ❌ Needs (Location ✓, Issue ✓, When ✗...) | **MISSING** |
| **Mobile UX** | ❌ No minimal follow-ups | ❌ Needs only ask for missing slots | **MISSING** |

**Gap**: Backend slots ready, but NO LLM extraction, NO conversation UI.

---

### 8️⃣ **Minimalistic UX (Reducing Uncertainty)**

| Component | Current State | Updated Plan Requirement | Status |
|-----------|---------------|--------------------------|--------|
| **Home Screen** | ✅ Has single Mic button | ✅ Matches | **READY** |
| **Issue Selection** | ⚠️ Separate screen | ❌ Should be optional row | **NEEDS REDESIGN** |
| **Intake Flow** | ❌ No chat UI | ❌ Needs chat + live transcript | **MISSING** |
| **Confirm Screen** | ❌ Not built yet | ❌ Needs summary for officials + map | **MISSING** |
| **After Submit** | ❌ No post-submit card | ❌ Needs "Agla Kya Hoga" card | **MISSING** |
| **My Cases** | ⚠️ Placeholder screen | ❌ Needs SLA timers + "who has ball" | **NEEDS REBUILD** |

**Gap**: Flow exists but needs major UX overhaul to minimize taps and uncertainty.

---

## 📈 Phase-wise Implementation Status

### **Phase 1: MVP (Original Plan)**
| Feature | Original Plan Status | Reality |
|---------|---------------------|---------|
| Database schema | ✅ Complete | ✅ Enhanced with triage fields |
| Backend API (basic) | ✅ Complete | ✅ Basic CRUD working |
| Mobile OTP auth | ✅ Complete | ✅ Working |
| Voice recording | ✅ Complete | ✅ Working |
| Web console | ✅ Complete | ✅ Working |
| **Overall Phase 1** | **85% Complete** | **Basic flow works, but UX outdated** |

---

### **Phase 2: Your Updated Plan (Current Priority)**
| Category | Feature | Backend | Mobile | Priority |
|----------|---------|---------|--------|----------|
| **Triage** | 3-way classification API | ❌ | ❌ | 🔴 CRITICAL |
| **Triage** | Mobile triage UI overlay | ✅ | ❌ | 🔴 CRITICAL |
| **Triage** | Override chips (3 buttons) | ✅ | ❌ | 🔴 CRITICAL |
| **UX** | "Agla Kya Hoga" API | ❌ | ❌ | 🔴 CRITICAL |
| **UX** | SLA clock + escalation card | ✅ | ❌ | 🔴 CRITICAL |
| **UX** | Timeline with "who has ball" | ✅ | ❌ | 🔴 CRITICAL |
| **Tone** | Microcopy engine (Chhattisgarhi) | ❌ | ❌ | 🟡 HIGH |
| **Tone** | Formal summary generation | ⚠️ | ⚠️ | 🟡 HIGH |
| **Language** | Azure Speech (Hindi ASR) | ❌ | ❌ | 🟡 HIGH |
| **Language** | Custom vocabulary (villages) | ❌ | ❌ | 🟡 HIGH |
| **Language** | Hindi transcript UI (default) | ✅ | ❌ | 🟡 HIGH |
| **Directory** | Entity versioning + corrections | ❌ | ❌ | 🟢 MEDIUM |
| **Personal** | Personal diary API | ✅ | ❌ | 🔴 CRITICAL |
| **Personal** | My Diary UI + reminders | ✅ | ❌ | 🔴 CRITICAL |
| **Personal** | Convert to grievance button | ✅ | ❌ | 🔴 CRITICAL |
| **Conversation** | Slot extraction (Claude API) | ⚠️ | ❌ | 🟡 HIGH |
| **Conversation** | Live transcript + progress chips | ✅ | ❌ | 🟡 HIGH |
| **Conversation** | Minimal follow-up logic | ❌ | ❌ | 🟡 HIGH |

---

## 🎯 What Needs to Be Built (Priority Order)

### 🔴 **CRITICAL (Must Build First - 2-3 weeks)**

#### 1. Backend APIs (4-5 days)
- [ ] `POST /v1/cases/triage` - Classify intent with Claude API
- [ ] `GET /v1/cases/{id}/next-steps` - Calculate SLA + escalation
- [ ] `GET /v1/cases/personal` - Personal diary list
- [ ] `POST /v1/cases/{id}/convert-to-grievance` - One-tap conversion
- [ ] `POST /v1/entities/{id}/suggest-correction` - Entity corrections

#### 2. Mobile Triage Flow (3-4 days)
- [ ] Triage overlay after 5-10s of speech
- [ ] 3 override chips (Grievance/Community/Personal)
- [ ] Confidence-based confirmation (if <0.7)
- [ ] Auto-proceed on high confidence

#### 3. Mobile "Agla Kya Hoga" Card (2-3 days)
- [ ] Post-submit card with:
  - Responsible entity name
  - Expected time window (e.g., "72h")
  - SLA clock (live countdown)
  - Escalation rung (e.g., "then BDO")
- [ ] Timeline view with "who has the ball"
- [ ] Status copy in plain Hindi

#### 4. Personal Diary Feature (3-4 days)
- [ ] "My Diary" tab (separate from My Cases)
- [ ] Private case list (kind=PERSONAL)
- [ ] Reminder UI with notifications
- [ ] "Convert to Grievance" button (one tap)
- [ ] Never show in public/admin feeds

---

### 🟡 **HIGH (Important UX - 1-2 weeks)**

#### 5. Conversation UX Overhaul (4-5 days)
- [ ] Chat-style interface (WhatsApp-like)
- [ ] Big Devanagari live transcript
- [ ] Progress chips (Location ✓, Issue ✓, When ✗)
- [ ] One-line assistant bubbles (warm tone)
- [ ] Only ask for missing slots

#### 6. Tone Engine (2-3 days)
- [ ] Microcopy JSON file (Hindi/Chhattisgarhi variants)
- [ ] Greetings with light humor
- [ ] Formal mode for official summaries
- [ ] Claude API prompts with tone config

#### 7. Language Enhancement (3-4 days)
- [ ] Azure Speech integration (Hindi ASR)
- [ ] Custom vocabulary from Entities table
- [ ] Low-confidence retry logic ("धीमे बोल दीजिए")
- [ ] Hindi transcript by default (Devanagari)

---

### 🟢 **MEDIUM (Can Come Later - 1 week)**

#### 8. Entity Directory Improvements (2-3 days)
- [ ] Add `version`, `suggested_updates`, `last_verified_at` fields
- [ ] Correction submission workflow
- [ ] Admin approval interface (web console)
- [ ] Old version retention

#### 9. Offline & Edge Cases (3-4 days)
- [ ] Offline recording + queue
- [ ] Poor network fallback (text mode)
- [ ] ASR failure → manual text input

---

## 📐 Updated Development Phases

### **Phase 2A: Triage & UX Foundation** (2 weeks)
**Goal**: Get 3-way triage + uncertainty-killer UI working

**Week 1**:
1. Build triage API with Claude integration
2. Create mobile triage overlay UI
3. Build "Agla Kya Hoga" API

**Week 2**:
4. Create post-submit card with SLA clock
5. Build timeline with "who has ball"
6. Personal diary API + mobile UI

**Deliverable**: Users can record → triage auto-classifies → see next steps immediately

---

### **Phase 2B: Conversation & Tone** (1.5 weeks)
**Goal**: Make conversation feel natural and respectful

**Week 3**:
1. Slot extraction with Claude API
2. Chat-style UI with live transcript
3. Progress chips UI

**Week 4**:
4. Tone engine with Chhattisgarhi microcopy
5. Formal summary generation
6. Hindi ASR with custom vocabulary

**Deliverable**: Natural conversation flow with minimal questions in warm Hindi tone

---

### **Phase 2C: Polish & Edge Cases** (1 week)
**Goal**: Handle all edge cases gracefully

**Week 5**:
1. Entity corrections workflow
2. Offline mode
3. ASR failure fallbacks
4. Testing + bug fixes

**Deliverable**: Production-ready app with all 8 improvements

---

## 🚨 Critical Insights for You

### 1. **Backend is 70% Ready!**
The database models ALREADY have all the fields you need (kind, triage_intent, routing_confidence, etc.). This is HUGE - it means someone already understood your vision and prepped the backend. **You only need to build APIs and UI.**

### 2. **Mobile App is 40% Complete**
Basic OTP + voice recording works, but the UX doesn't match your updated plan. **Major UI redesign needed** (triage overlay, chat interface, SLA cards).

### 3. **No LLM Integration Yet**
The Claude API is NOT integrated. **This is the biggest missing piece** - without it, triage, slot extraction, and tone won't work.

### 4. **No Azure Speech Yet**
Voice recording works, but there's no STT (speech-to-text). **Azure Speech integration is critical** for Hindi ASR with custom vocabulary.

### 5. **Personal Diary is a Game-Changer**
The backend is 100% ready for this (all fields exist). **This is the easiest quick win** - just build the API routes and mobile UI.

---

## ✅ Recommended Action Plan

### **Option 1: Build Everything (4-6 weeks total)**
Follow Phase 2A → 2B → 2C sequentially. This gives you a fully production-ready app with all 8 improvements.

### **Option 2: Quick Wins First (2 weeks + iterate)**
1. **Week 1**: Personal Diary feature (backend ready, easy UI)
2. **Week 2**: Triage API + mobile overlay
3. **Week 3+**: Iterate based on user feedback

### **Option 3: I Help You Prioritize (Ask Me)**
Tell me:
- What's your deadline?
- What features are MUST-HAVE vs nice-to-have?
- Do you have Claude API + Azure Speech keys?
- Should we focus on citizen app or web console first?

---

## 🎯 Next Steps (Choose One)

**A)** "Start with Phase 2A - build triage + uncertainty-killer UI"
**B)** "Focus on quick wins - personal diary + basic improvements"
**C)** "Help me prioritize - here's my deadline and constraints"
**D)** "Show me detailed technical implementation for [specific feature]"

What would you like to do?
