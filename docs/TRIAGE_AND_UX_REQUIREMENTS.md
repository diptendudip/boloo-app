# Boloo App - Triage & UX Requirements Specification

**Version**: 2.0
**Date**: October 27, 2025
**Status**: Requirements Defined | Implementation Pending

---

## 🎯 Vision

Transform Boloo from a basic grievance app into an **intelligent, respectful, uncertainty-killing** citizen engagement platform that automatically triages inputs, guides users with warmth, and provides crystal-clear next steps.

---

## 1️⃣ 3-Way TRIAGE (No Taps Needed)

### Objective
First 5-10 seconds of speech → automatically classify into Grievance, Community Story, or Personal with NO user input required (unless confidence is low).

### Requirements

#### R1.1: Automatic Classification
- **Trigger**: After 5-10s of audio OR when user stops talking (silence detection)
- **Action**: Backend sends audio + transcript to Claude API
- **Output**: Intent classification with confidence score (0.0-1.0)
  - `grievance` = routes to sarpanch/sachiv/district office
  - `community` = goes to public feed after moderation
  - `personal` = private diary (user-only)

#### R1.2: Confidence Bands
| Confidence | Action | User Experience |
|------------|--------|-----------------|
| **High (≥0.7)** | Auto-proceed | No interruption, shows subtle tag |
| **Medium (0.5-0.7)** | Confirm with 1 question | "यह शिकायत है या व्यक्तिगत नोट?" |
| **Low (<0.5)** | Show 3 chips | "कृपया चुनें: शिकायत \| समुदाय \| व्यक्तिगत" |

#### R1.3: User Override (Always Available)
- Small "Change" button always visible after classification
- Tapping shows 3 chips: Grievance 📢 | Community 📰 | Personal 📝
- One tap to switch, no confirmation needed

#### R1.4: Backend Implementation
**Endpoint**: `POST /v1/cases/triage`

**Request**:
```json
{
  "audio_url": "string",
  "transcript_text": "string",
  "location_hint": "string (optional)"
}
```

**Response**:
```json
{
  "intent": "grievance|community|personal",
  "confidence": 0.85,
  "reasoning": "User mentioned sarpanch and water supply issue",
  "suggested_issue_type": "water_supply" (if grievance)
}
```

#### R1.5: Grievance System Note
- Grievances route to entities (sarpanch/sachiv/district) immediately
- Backend tags will be built later, but database already prepared (from user's note)

---

## 2️⃣ UNCERTAINTY-KILLER UI ("Agla Kya Hoga?")

### Objective
After submitting, show a clear "What happens next" card with responsible office, time window, SLA clock, and escalation path. User should NEVER wonder "ab kya hoga?"

### Requirements

#### R2.1: Post-Submit Card (Immediate Display)
**Appears**: Immediately after case submission confirmation

**Card Content** (in Hindi):
```
┌──────────────────────────────────┐
│  ✅ आपकी शिकायत दर्ज हो गई      │
│                                   │
│  📍 जिम्मेदार दफ्तर:             │
│     ग्राम पंचायत रायपुर         │
│                                   │
│  ⏱️ अगला कदम:                    │
│     72 घंटे में पहली कार्यवाही  │
│                                   │
│  🔔 यदि 72h में जवाब नहीं आया:  │
│     → स्वतः BDO को भेजा जाएगा   │
│                                   │
│  📱 Case ID: #BL-2025-0042       │
└──────────────────────────────────┘
```

#### R2.2: Live SLA Clock
- Shows countdown: "72h 23m 14s remaining"
- Color changes:
  - Green: >50% time left
  - Yellow: 20-50% time left
  - Red: <20% time left
- Updates every minute

#### R2.3: Timeline with "Who Has the Ball"
**Visual**: Vertical timeline showing case journey

```
┌──────────────────────────────────┐
│  📍 अभी कहाँ है (WHERE NOW):     │
│                                   │
│  🔵 You → Submitted (2h ago)     │
│  ⚪ Moderator → Pending review   │
│  ⚪ Officer → Not yet received   │
└──────────────────────────────────┘
```

**States**:
- Filled circle (🔵) = completed
- Half-filled (◐) = in progress
- Empty (⚪) = pending
- Red (!!) = overdue/stuck

#### R2.4: Status Copy (Plain Hindi)
**Examples**:
- `"आपकी शिकायत मॉडरेटर के पास है"` (moderation)
- `"पंचायत ने आपकी शिकायत देखी"` (officer_accepted)
- `"काम शुरू हो गया है"` (in_progress)
- `"समस्या ठीक हो गई - कृपया confirm करें"` (resolved)

#### R2.5: Backend Implementation
**Endpoint**: `GET /v1/cases/{id}/next-steps`

**Response**:
```json
{
  "responsible_entity": {
    "name": "ग्राम पंचायत रायपुर",
    "type": "gram_panchayat"
  },
  "sla_window": "72h",
  "sla_due_at": "2025-10-30T14:30:00Z",
  "sla_remaining_seconds": 259200,
  "escalation_path": [
    {"rung": 1, "entity": "Gram Panchayat", "window": "72h"},
    {"rung": 2, "entity": "Block Development Officer", "window": "48h"},
    {"rung": 3, "entity": "District Office", "window": "24h"}
  ],
  "current_rung": 1,
  "who_has_ball": "moderator",
  "status_text_hi": "आपकी शिकायत मॉडरेटर के पास है"
}
```

---

## 3️⃣ FUNNY-YET-RESPECTFUL ASSISTANT TONE

### Objective
Make the assistant feel warm, helpful, and lightly humorous WITHOUT mocking the user's problem. Humor only in greetings/transitions, never in the actual problem.

### Requirements

#### R3.1: Tone Variants
**System should support 3 tone modes**:
1. `hi_formal` - Pure formal Hindi (for official summaries)
2. `hi_friendly` - Warm, slightly casual Hindi
3. `hi_cg_friendly` - Chhattisgarhi-flavored Hinglish

**User can select in settings** (default: `hi_friendly`)

#### R3.2: Microcopy Examples

**Greetings (Warm & Light)**:
| Context | hi_friendly | hi_cg_friendly |
|---------|-------------|----------------|
| App open | "नमस्ते! आज कैसी हैं?" | "का हो भई? सब ठीक?" |
| Recording start | "हाँ, बोलिये..." | "हां हां, बोलो ना..." |
| Recording done | "बढ़िया! अब आगे बढ़ते हैं" | "वाह! अब देखते हैं क्या हो सकता है" |

**Follow-ups (Only for Missing Slots)**:
| Context | hi_friendly | hi_cg_friendly |
|---------|-------------|----------------|
| Need location | "ये कहाँ हो रहा है?" | "ये कहाँ के बात हे?" |
| Need time | "ये कब से है?" | "ये कब से चालू हे भाई?" |
| Low confidence | "फिर से धीरे बताइये" | "अरे एक बार फेर बोल दो ना" |

**Acknowledgments (Respectful)**:
| Context | hi_friendly | hi_cg_friendly |
|---------|-------------|----------------|
| Submit success | "आपकी बात दर्ज हो गई" | "हो गया भई, लिख लिए हम" |
| Officer replied | "अधिकारी ने जवाब दिया है" | "देखो सा, ऑफिसर ने बोले हें" |

#### R3.3: Formal Mode (For Official Summaries)
When generating case summary for officers, **switch to pure formal Hindi**:
```
❌ "पानी नहीं आ रहा है भई, 15 दिन से"
✅ "नागरिक ने सूचित किया कि पिछले 15 दिनों से जल आपूर्ति बाधित है।"
```

#### R3.4: Backend Implementation
**Microcopy File**: `backend/app/assets/microcopy.json`

```json
{
  "hi_friendly": {
    "greeting_morning": "नमस्ते! आज कैसी हैं?",
    "recording_start": "हाँ, बोलिये...",
    "recording_done": "बढ़िया! अब आगे बढ़ते हैं",
    ...
  },
  "hi_cg_friendly": {
    "greeting_morning": "का हो भई? सब ठीक?",
    ...
  }
}
```

**Claude API Prompts**:
- Formal summary: `"Generate formal Hindi summary for government officials"`
- Friendly tone: `"Rephrase in warm, colloquial Hindi with light humor in transitions only"`

---

## 4️⃣ LANGUAGE HANDLING (Code-mix & Chhattisgarhi)

### Objective
Support Hindi ASR with Chhattisgarhi words, custom vocabulary (village/officer names), and graceful fallbacks on low confidence.

### Requirements

#### R4.1: Default UI Transcript
- **Display**: Hindi transcript in **Devanagari script** by default
- **Storage**: Keep raw English/mixed transcript for audit (`raw_transcript` field)
- **Switch**: User can toggle to see raw transcript if needed

#### R4.2: Azure Speech Configuration
**Model**: `hi-IN` (Hindi India)

**Custom Vocabulary**: Load from database
- All village names from Entities table (type=gram_panchayat)
- All officer names (sarpanch, sachiv, BDO, etc.)
- Common Chhattisgarhi words (e.g., "का हो", "हे", "बात" vs "बात")

**Implementation**:
```python
# backend/app/services/speech.py
def get_custom_vocabulary() -> List[str]:
    """Get custom vocab from Entities table"""
    entities = db.query(Entity).all()
    vocab = []
    for e in entities:
        vocab.append(e.name_hi)  # Hindi name
        vocab.append(e.name_en)  # English name
    vocab.extend([
        "सरपंच", "सचिव", "बीडीओ", "जिलाधीश",
        "ग्राम पंचायत", "नगर पंचायत", ...
    ])
    return vocab
```

#### R4.3: Low Confidence Retry
**Trigger**: If Azure Speech confidence < 0.6 for location/name

**Action**: Show reprompt in user's tone
```
hi_friendly: "फिर से धीरे बताइये - गाँव/मोहल्ले का नाम"
hi_cg_friendly: "अरे एक बार फेर बोल दो - कोन गांव हे?"
```

**Max Retries**: 2 attempts, then fallback to manual text input

#### R4.4: Offline Fallback
If internet is slow/unavailable:
1. Show: "इंटरनेट धीमा है - लिख कर बताएं?"
2. Offer text input field
3. Save audio locally, sync later
4. Use LLM on text instead of audio

---

## 5️⃣ DIRECTORY YOU CAN TRUST (And Fix)

### Objective
Allow moderators/officers to suggest corrections to entity data (phone numbers, names, escalation paths) with admin approval.

### Requirements

#### R5.1: Enhanced Entity Model
**Add 3 new fields to `entities` table**:
```sql
ALTER TABLE entities ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE entities ADD COLUMN suggested_updates JSONB;
ALTER TABLE entities ADD COLUMN last_verified_at TIMESTAMP;
```

**`suggested_updates` structure**:
```json
{
  "pending": [
    {
      "field": "contact_phone",
      "old_value": "0771-1234567",
      "new_value": "0771-7654321",
      "suggested_by": "user_uuid",
      "suggested_at": "2025-10-27T10:30:00Z",
      "reason": "Old number not working"
    }
  ],
  "history": [...]
}
```

#### R5.2: Correction Workflow
**Step 1**: Moderator/Officer submits correction
```
POST /v1/entities/{id}/suggest-correction
{
  "field": "contact_phone",
  "new_value": "0771-7654321",
  "reason": "Old number not working"
}
```

**Step 2**: Admin reviews in web console
- See all pending corrections
- Approve → create new version (old version retained)
- Reject → add to history with reason

**Step 3**: Version published
- `version` increments
- Routes updated immediately
- Old version kept for audit (separate `entity_versions` table)

#### R5.3: UI (Web Console - Moderator/Officer View)
**Button**: "Suggest Correction" on entity detail page

**Form Fields**:
- Field to correct (dropdown)
- New value (text input)
- Reason (text area)

---

## 6️⃣ PERSONAL ISSUES = RETENTION ENGINE

### Objective
Provide a private "My Diary" for personal notes that don't need official action, with reminders and one-tap conversion to grievance if needed later.

### Requirements

#### R6.1: Private Case Type
**Case Kind**: `kind=PERSONAL`
**Privacy**: `is_public=false` (never appears in public feed or admin dashboard)
**Access**: Only the user who created it can see it

#### R6.2: My Diary UI (Mobile)
**Location**: Separate tab in bottom navigation (Home | My Cases | My Diary)

**List View**:
```
┌──────────────────────────────────┐
│  📝 My Diary (Personal Notes)    │
│                                   │
│  ┌──────────────────────────┐   │
│  │ 🔔 Reminder in 2 days     │   │
│  │ School admission forms     │   │
│  │ Created 3 days ago         │   │
│  └──────────────────────────┘   │
│                                   │
│  ┌──────────────────────────┐   │
│  │ 📌 Note                   │   │
│  │ Ration card renewal       │   │
│  │ Created 1 week ago         │   │
│  └──────────────────────────┘   │
└──────────────────────────────────┘
```

#### R6.3: Reminder System
**Set Reminder**: When creating personal note
- "Do you want a reminder?" (optional)
- Date picker (e.g., "7 days from now")
- Stored in `reminder_at` field

**Notification**: Mobile push notification when `reminder_at` is reached
```
📝 Reminder: School admission forms
Tap to view your note
```

#### R6.4: Convert to Grievance (One Tap)
**Button**: "Convert to Grievance" on personal note detail

**Flow**:
1. User taps "Convert"
2. Confirmation: "यह शिकायत में बदलेगा - जारी रखें?"
3. If yes:
   - Update `kind=GRIEVANCE`
   - Update `can_convert_to_grievance=false`
   - Run triage/routing logic
   - Show "Agla Kya Hoga" card

#### R6.5: Backend Implementation
**Endpoint**: `GET /v1/cases/personal` (filter: `kind=PERSONAL`)

**Response**:
```json
{
  "cases": [
    {
      "id": "uuid",
      "title": "School admission forms",
      "note": "Need to submit by next month",
      "reminder_at": "2025-11-03T00:00:00Z",
      "can_convert_to_grievance": true,
      "created_at": "2025-10-24T10:00:00Z"
    }
  ]
}
```

---

## 7️⃣ CONVERSATION DESIGN (Minimal Slots)

### Objective
Extract only necessary information through natural conversation, showing progress visually, and asking only when confidence is low.

### Requirements

#### R7.1: Slot Schemas by Type

**Grievance Slots** (must-have):
- `location_text` (village/ward + district)
- `issue_type` (taxonomy key)
- `when_started` (date or "~15 din")
- `scope` (kitne log prabhavit)
- `prior_contact` (kis se baat hui)
- `evidence` (photo/video optional)
- `contact_phone` (from user profile)

**Community Story Slots**:
- `topic` (song/medicine/tradition/news)
- `where` (village/area)
- `who` (narrator/elders)
- `rights_ok` (consent - yes/no)
- `media` (1-3 photos/videos)

**Personal Slots**:
- `short_title` (user words)
- `note` (freeform text)
- `reminder_when` (optional date)
- `convertible` (can become grievance later? y/n)

#### R7.2: Slot Extraction Logic
**Tool**: Claude API with structured output

**Prompt Template**:
```
You are extracting slots from a citizen's voice grievance.
Transcript: "{transcript_text}"
Location hint: "{location_text}"

Required slots for GRIEVANCE:
- location_text (village + district)
- issue_type (from taxonomy list)
- when_started (date or duration)

Extract all available slots. For missing slots, set to null.

Output JSON:
{
  "location_text": "value or null",
  "issue_type": "value or null",
  ...
  "confidence": {
    "location_text": 0.0-1.0,
    "issue_type": 0.0-1.0,
    ...
  }
}
```

#### R7.3: Progress Chips UI
**Display**: Horizontal row of chips showing completion status

```
┌──────────────────────────────────┐
│  Location ✓  Issue ✓  When ✗    │
│  Scope ✗  Contact ✓  Photos ✗   │
└──────────────────────────────────┘
```

**Color coding**:
- Green checkmark (✓) = extracted with high confidence
- Red X (✗) = missing or low confidence
- Yellow (◐) = extracted but needs confirmation

#### R7.4: Minimal Follow-ups
**Rule**: Only ask for slots with confidence < 0.7

**Example Flow**:
```
User: "हमारे गांव में पानी नहीं आ रहा 15 दिन से"
     (Our village has no water for 15 days)

AI extracts:
- issue_type: "water_supply" (confidence: 0.95) ✓
- when_started: "15 दिन" (confidence: 0.90) ✓
- location_text: null (confidence: 0.0) ✗

AI asks: "कौन सा गाँव है?" (Which village?)
User: "रायपुर"

AI extracts:
- location_text: "रायपुर, रायपुर जिला" (confidence: 0.85) ✓

All required slots filled → Proceed to confirmation
```

#### R7.5: Live Transcript Display
**UI**: Big Devanagari text in real-time as user speaks

```
┌──────────────────────────────────┐
│  🎙️ Recording...                 │
│                                   │
│  हमारे गांव में पानी नहीं आ    │
│  रहा 15 दिन से...               │
│                                   │
│  [Big Hindi text, updated live]  │
└──────────────────────────────────┘
```

**Technical**: Use Azure Speech streaming API with 200ms latency

---

## 8️⃣ MINIMALISTIC UX (Reducing Uncertainty)

### Objective
Simplify the flow to: Talk → Triage → Confirm → See Next Steps. Minimize taps, show progress clearly, never leave user wondering.

### Requirements

#### R8.1: Home Screen
**Single Primary Action**: Big "🎙️ Mic" button (80% of screen focus)

**Optional Row**: Small "Categories" chips below mic (user can skip by just talking)

**Layout**:
```
┌──────────────────────────────────┐
│  Welcome to Boloo                 │
│  नागरिक शिकायत प्रणाली          │
│                                   │
│       ┌───────────┐              │
│       │           │              │
│       │     🎙️    │              │
│       │           │              │
│       └───────────┘              │
│       Tap to Report              │
│                                   │
│  [शिकायत] [समुदाय] [व्यक्तिगत] │ (optional)
│                                   │
│  📋 My Cases    📝 My Diary      │
└──────────────────────────────────┘
```

#### R8.2: Intake Flow (Chat + Live Transcript)
**Screen**: Full-screen chat interface (WhatsApp-like)

```
┌──────────────────────────────────┐
│  ← Back            🎙️ Recording  │
│                                   │
│  Bot: हाँ, बोलिये...             │
│                                   │
│  [Live Hindi Transcript]          │
│  हमारे गांव में पानी नहीं...    │
│                                   │
│  [Progress Chips]                 │
│  Location ✓  Issue ✓  When ✗    │
│                                   │
│  Bot: कौन सा गाँव है?            │
│                                   │
│  [Mic button to reply]            │
└──────────────────────────────────┘
```

#### R8.3: Confirm Screen (One Screen)
**Summary for Officials** (formal Hindi)
**Map Thumbnail** (if GPS available)
**Category Badge** (Grievance 📢 | Community 📰 | Personal 📝)

```
┌──────────────────────────────────┐
│  Confirm & Submit                 │
│                                   │
│  📢 Grievance                     │
│  Issue: Water Supply              │
│                                   │
│  Summary (for officers):          │
│  "नागरिक ने सूचित किया कि...    │
│                                   │
│  📍 Location: Raipur, Raipur      │
│  [Map thumbnail]                  │
│                                   │
│  🕐 Started: 15 days ago          │
│  👥 Affected: ~50 households      │
│                                   │
│  [पुष्टि करें और भेजें] (CTA)   │
└──────────────────────────────────┘
```

#### R8.4: After Submit
**Immediate Display**: "Agla Kya Hoga" card (from Requirement 2)

**No Loading**: Pre-calculate SLA + entity during confirmation step so card appears instantly

#### R8.5: My Cases (Compact List)
**Show**:
- Case title
- SLA timer (green/yellow/red)
- Last action pill ("Officer accepted 2h ago")
- "Who has ball" icon (👤 Citizen | 👮 Officer | 👨‍💼 Moderator)

```
┌──────────────────────────────────┐
│  My Cases                         │
│                                   │
│  ┌──────────────────────────┐   │
│  │ 🟢 72h 23m left          │   │
│  │ Water Supply Issue        │   │
│  │ 👨‍💼 Moderator reviewing  │   │
│  │ Updated 2h ago            │   │
│  └──────────────────────────┘   │
│                                   │
│  ┌──────────────────────────┐   │
│  │ 🔴 Overdue by 3h         │   │
│  │ Road Repair               │   │
│  │ 👮 Officer not responded │   │
│  │ Escalated to BDO          │   │
│  └──────────────────────────┘   │
└──────────────────────────────────┘
```

---

## 📋 Data & Platform Changes (Surgical Updates)

### Backend Changes Required

#### 1. Cases Table (ALREADY MOSTLY DONE ✅)
**Existing fields** (no change needed):
- `kind` enum (GRIEVANCE, COMMUNITY_STORY, PERSONAL) ✅
- `triage_intent` enum ✅
- `routing_confidence` float ✅
- `raw_transcript`, `hindi_transcript`, `formal_summary` ✅
- `can_convert_to_grievance` bool ✅
- `reminder_at` timestamp ✅
- `when_started`, `scope_affected`, `prior_contact` ✅
- `rights_consent` bool ✅

**No new fields needed!**

#### 2. Entities Table (NEEDS 3 NEW FIELDS)
**Add**:
```sql
ALTER TABLE entities ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE entities ADD COLUMN suggested_updates JSONB DEFAULT '{"pending":[],"history":[]}';
ALTER TABLE entities ADD COLUMN last_verified_at TIMESTAMP DEFAULT NOW();
```

#### 3. Users Table (NEEDS 1 NEW FIELD)
**Add**:
```sql
ALTER TABLE users ADD COLUMN locale_preference VARCHAR(20) DEFAULT 'hi_friendly';
```

#### 4. Consents Table (NEW TABLE)
**Create**:
```sql
CREATE TABLE consents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  grievance_public BOOLEAN DEFAULT FALSE,
  community_public BOOLEAN DEFAULT TRUE,
  personal_private BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. Audit Logs (ALREADY EXISTS ✅)
Keep all edits logged automatically.

---

## 🧪 Tests That Matter in the Field

### Test 1: ASR Fallback (Noisy Environment)
**Scenario**: User in crowded market, partial words captured

**Expected**:
- System detects low confidence on specific slots (e.g., village name)
- Asks to repeat ONLY missing slot: "गाँव का नाम फिर से बोलें"
- OR offers text fallback: "लिख कर बताएं?"

**Pass Criteria**: No full re-recording, only missing slot retry

---

### Test 2: Code-mix (Hindi + English + Chhattisgarhi)
**Scenario**: User says "हमारे village में पानी problem है का हो"

**Expected**:
- Hindi transcript: "हमारे गाँव में पानी की समस्या है"
- Formal summary: "नागरिक ने सूचित किया कि उनके गाँव में जल आपूर्ति बाधित है।"

**Pass Criteria**: Formal summary remains pure Hindi

---

### Test 3: Routing Confidence (Low Confidence Triggers Confirmation)
**Scenario**: User's description is vague → routing confidence = 0.6

**Expected**:
- System asks: "यह जल आपूर्ति की समस्या है?" (confirmation question)
- If user confirms → proceed
- If user says no → show taxonomy chips

**Pass Criteria**: No auto-routing without confirmation if confidence < 0.7

---

### Test 4: Offline (Record & Submit Later)
**Scenario**: User in area with no internet

**Expected**:
- "इंटरनेट धीमा है - ऑफलाइन रिकॉर्डिंग करें"
- Audio saved locally
- When online → auto-sync + process
- SLA start time = when online submission happened (not record time)

**Pass Criteria**: No data loss, clear SLA timing

---

### Test 5: Privacy (Personal Diary Never Public)
**Scenario**: User creates personal note

**Expected**:
- Entry visible ONLY in "My Diary" tab (not in "My Cases")
- Admin dashboard does NOT show personal entries
- Public feed does NOT show personal entries

**Pass Criteria**: Zero leakage of personal notes

---

## 📊 Success Metrics (How to Know It's Working)

### User Experience Metrics
- **Triage accuracy**: >85% correct auto-classification
- **Confidence overrides**: <10% of users manually change triage
- **Follow-up questions**: <2 average per case (minimal questioning)
- **Time to submit**: <3 minutes from start to finish
- **Uncertainty reduction**: "Agla Kya Hoga" card viewed by 100% after submit

### Engagement Metrics
- **Personal diary usage**: >30% of users create at least 1 personal note
- **Conversion rate**: 15-20% of personal notes convert to grievances
- **Repeat users**: >60% return within 7 days (retention engine working)

### System Metrics
- **ASR accuracy**: >90% for Hindi with custom vocabulary
- **Routing confidence**: Average >0.8 for grievances
- **SLA visibility**: 100% of cases show clear next steps

---

## 🚀 Implementation Priority (For Developers)

### Week 1 (Critical Foundation)
1. Triage API with Claude integration
2. "Agla Kya Hoga" API (next steps calculator)
3. Personal diary API endpoints
4. Mobile triage overlay UI

### Week 2 (Core UX)
5. Post-submit card with SLA clock
6. Timeline with "who has ball"
7. My Diary UI + reminders
8. Convert to grievance button

### Week 3 (Conversation Flow)
9. Slot extraction with Claude
10. Live transcript UI (Devanagari)
11. Progress chips UI
12. Minimal follow-up logic

### Week 4 (Language & Tone)
13. Tone engine (microcopy JSON)
14. Azure Speech integration (Hindi ASR)
15. Custom vocabulary loader
16. Formal summary generation

### Week 5 (Polish & Corrections)
17. Entity corrections workflow
18. Offline mode
19. ASR failure fallbacks
20. Testing + bug fixes

---

## 📖 Related Documents
- **Gap Analysis**: `docs/ANDROID_GAP_ANALYSIS.md`
- **Current Status**: `PROJECT_SUMMARY.md`
- **Development Phases**: `docs/DEVELOPMENT_PHASES.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

---

## 9️⃣ AI COACH ONBOARDING (First 5-6 Reports Only)

### Objective
Train new users how to effectively report issues on Boloo using an intelligent, conversational AI guide. After training complete (5-6 reports), system automatically switches to simple one-shot recording mode.

**Philosophy**: Minimalist, Steve Jobs-level elegance. AI Coach is a **temporary training wheel**, not a permanent feature.

### Requirements

#### R9.1: Training State Tracking

**User Training States**:
```sql
ALTER TABLE users ADD COLUMN training_reports_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN training_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN training_mode_enabled BOOLEAN DEFAULT TRUE;
```

**Logic**:
- New user installs app → `training_mode_enabled = TRUE`
- Each report submitted → `training_reports_count++`
- When `training_reports_count >= 5` → `training_completed = TRUE`, `training_mode_enabled = FALSE`
- User can manually toggle in Settings

#### R9.2: Dual-Mode Voice Recording Endpoint

**Modify Existing**: `POST /v1/transcription/transcribe-and-classify`

**Request** (Enhanced):
```json
{
  "audio": "file upload",
  "user_id": "uuid",
  "turn_number": 1,  // NEW: For multi-turn conversations
  "conversation_id": "uuid | null",  // NEW: Null for first turn
  "language": "hi-IN"
}
```

**Response** (Enhanced):
```json
{
  "success": true,
  "transcript": "हमारे इलाके में पानी की समस्या है",
  "transcript_confidence": 0.92,
  "intent": "grievance",
  "intent_confidence": 0.88,

  // NEW: Training Mode Fields
  "training_mode": true,
  "conversation_id": "conv-uuid",
  "completeness_analysis": {
    "collected_fields": ["issue_type", "description"],
    "missing_fields": [
      {
        "field": "location",
        "importance": "critical",
        "prompt_hi": "यह समस्या किस इलाके में है?",
        "prompt_en": "Which area has this problem?"
      },
      {
        "field": "duration",
        "importance": "high",
        "prompt_hi": "कब से यह समस्या है?",
        "prompt_en": "How long has this been happening?"
      }
    ],
    "completeness_score": 0.4,
    "is_complete": false
  },

  // Standard fields
  "triage_result": { /* existing */ }
}
```

#### R9.3: Minimalist UX Flow

**Mode 1: Training Mode (First 5-6 Reports)**

```
┌─────────────────────────────────┐
│  🎓 Training Mode (Report 1/5)  │  ← Subtle badge, top-right
│                                  │
│  [Tap mic → Record]              │
│                                  │
│  → Transcript shown              │
│  → AI analyzes completeness      │
│                                  │
│  If INCOMPLETE:                  │
│  ┌──────────────────────────┐  │
│  │ 📍 Missing: Location      │  │
│  │                           │  │
│  │ यह समस्या किस इलाके में  │  │
│  │ है?                       │  │
│  │                           │  │
│  │ [Tap to answer]  [Skip]  │  │
│  └──────────────────────────┘  │
│                                  │
│  → User records again            │
│  → Process repeats until complete│
│                                  │
│  If COMPLETE:                    │
│  ✅ "सभी जानकारी मिल गई!"      │
│  [Submit Report]                 │
└─────────────────────────────────┘
```

**Mode 2: Simple Mode (After Training)**

```
┌─────────────────────────────────┐
│  [No training badge]             │
│                                  │
│  [Tap mic → Record → Transcribe] │
│  → Shows transcript              │
│  → AI classifies                 │
│                                  │
│  ✅ [Submit] button immediately  │
│                                  │
│  💡 "Need help?" (small link)    │  ← If tapped, enables training mode for this report only
└─────────────────────────────────┘
```

**Minimalist Design Principles**:
- NO clutter
- NO unnecessary steps
- ONE primary action per screen
- Beautiful, large Hindi text
- Progress indicator (1/5, 2/5, etc.) very subtle

#### R9.4: Intelligent Completeness Analysis

**AI analyzes what's truly missing**:

```python
def analyze_completeness(transcript, intent, user_location_hint):
    """
    Determine what critical information is missing

    Returns only HIGH importance missing fields
    Skip MEDIUM/LOW importance for minimal UX
    """

    if intent == "grievance":
        required_fields = {
            "location": "critical",  # Only ask if GPS not available
            "issue_type": "critical",  # Usually auto-detected
            "duration": "high",  # "When did this start?"
        }
    elif intent == "community":
        required_fields = {
            "topic": "critical",
            "location": "high"
        }
    else:  # personal
        required_fields = {}  # No follow-ups for personal notes!

    # Extract what user already said
    extracted = extract_fields_from_transcript(transcript)

    # Only ask for CRITICAL missing fields
    missing = []
    for field, importance in required_fields.items():
        if field not in extracted and importance == "critical":
            missing.append(field)

    return {
        "is_complete": len(missing) == 0,
        "missing_fields": missing,
        "completeness_score": 1.0 - (len(missing) / len(required_fields))
    }
```

**Rule**: Ask maximum 2 follow-up questions. If still incomplete after 2 questions, proceed anyway.

#### R9.5: Settings Toggle

**Location**: Settings screen → "Training Mode"

```
┌─────────────────────────────────┐
│  Settings                        │
│                                  │
│  Language: हिंदी                │
│  Location: Raipur                │
│                                  │
│  ┌──────────────────────────┐  │
│  │ 🎓 Training Mode          │  │
│  │                           │  │
│  │ Guides you through        │  │
│  │ reporting              [◯]│  │  ← Toggle OFF after training
│  │                           │  │
│  │ Reports completed: 5/5    │  │
│  │ Training: Complete ✓      │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

**Toggle Logic**:
- Can enable even after training complete
- Useful for new report types (first grievance vs first community story)

#### R9.6: Backend State Management

**Conversations Table** (Minimal):
```sql
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    case_id UUID REFERENCES cases(id),
    turn_count INTEGER DEFAULT 1,
    is_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

**Conversation Turns Table**:
```sql
CREATE TABLE IF NOT EXISTS conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER,
    transcript TEXT,
    missing_fields JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Clean-up**: Delete conversations older than 24 hours automatically.

#### R9.7: First-Time User Flow (Onboarding)

**On First App Launch**:

```
┌─────────────────────────────────┐
│  Welcome to Boloo! 🙏           │
│                                  │
│  रिपोर्ट कैसे करें, सीखें?      │
│  Learn how to report issues?     │
│                                  │
│  [✓] Yes, guide me (Recommended) │
│  [ ] No, I know how to use this  │
│                                  │
│  [Continue]                      │
└─────────────────────────────────┘
```

**If "Yes, guide me"**:
- `training_mode_enabled = TRUE`
- Show 2-3 slide tutorial with beautiful illustrations
- Then proceed to mic button

**If "No"**:
- `training_mode_enabled = FALSE`
- Skip directly to mic button

#### R9.8: Graduation Celebration

**After 5th Successful Report**:

```
┌─────────────────────────────────┐
│  🎉 बधाई हो!                    │
│     Congratulations!             │
│                                  │
│  You've completed training!      │
│  आप सीख गए!                     │
│                                  │
│  From now on, reporting will be  │
│  faster and simpler.             │
│                                  │
│  💡 Tip: You can re-enable      │
│  training mode anytime in        │
│  Settings.                       │
│                                  │
│  [Awesome! 🎊]                  │
└─────────────────────────────────┘
```

**After this**:
- `training_completed = TRUE`
- `training_mode_enabled = FALSE`
- Future reports use simple one-shot mode

#### R9.9: Performance & Cost

**Training Mode** (Multi-turn):
- Average 2-3 turns per report
- Cost: $0.045 per conversation (see Azure AI Integration doc)
- Duration: ~2-3 minutes

**Simple Mode** (One-shot):
- Single recording
- Cost: $0.01 per report
- Duration: ~30 seconds

**Estimated Monthly Cost** (1000 active users):
- Training phase (first 5-6 reports): $45 × 6 = $270
- Post-training (ongoing): $10/month
- **Average over time**: ~$15-20/month (most users trained)

---

## 10️⃣ PHOTO UPLOAD & FEED SYSTEM (New Features)

### Objective
Allow users to attach photos to reports and view community stories in a simple RSS-style feed.

### Requirements

#### R10.1: Photo Storage Setup

**Storage Solution**: MinIO (S3-compatible)

**Configuration**:
```python
# backend/app/config.py
MINIO_ENDPOINT: str = "localhost:9000"
MINIO_ACCESS_KEY: str = ""
MINIO_SECRET_KEY: str = ""
MINIO_BUCKET_NAME: str = "boloo-media"
MINIO_USE_SSL: bool = False
```

**Database Schema**:
```sql
CREATE TABLE IF NOT EXISTS media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    file_type VARCHAR(50),  -- image/jpeg, image/png, video/mp4
    file_size INTEGER,
    storage_url TEXT,
    thumbnail_url TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_media_case ON media(case_id);
```

#### R10.2: Photo Upload UI (Mobile)

**Simple UI**:
```
┌─────────────────────────────────┐
│  Add Photo (Optional)            │
│                                  │
│  ┌────────┐ ┌────────┐          │
│  │ 📷     │ │ 🖼️     │          │
│  │ Camera │ │ Gallery│          │
│  └────────┘ └────────┘          │
│                                  │
│  Max 3 photos                    │
│                                  │
│  [Skip]         [Continue]       │
└─────────────────────────────────┘
```

**API Endpoint**:
```
POST /v1/cases/{case_id}/photos
Content-Type: multipart/form-data

photo: file upload (max 5MB)
```

#### R10.3: Feed System (RSS-Based)

**Feed Types**:
1. **Community Feed** - Public community stories (after moderation)
2. **My Reports** - User's own grievances
3. **Local Feed** - Stories from user's area (within 5km)

**Simple List UI**:
```
┌─────────────────────────────────┐
│  Community Feed                  │
│                                  │
│  ┌──────────────────────────┐  │
│  │ 📷 Water Supply Fixed    │  │
│  │ Ward 23, Raipur          │  │
│  │ 2 hours ago              │  │
│  │ 👍 12  💬 3              │  │
│  └──────────────────────────┘  │
│                                  │
│  ┌──────────────────────────┐  │
│  │ 🎉 Community Event       │  │
│  │ Tomorrow at 5 PM         │  │
│  │ Village Square           │  │
│  │ 👍 8  💬 1               │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

**API Endpoint**:
```
GET /v1/feed?type=community&limit=20&offset=0

Response:
{
  "items": [
    {
      "id": "uuid",
      "title": "Water Supply Fixed",
      "summary": "...",
      "location": "Ward 23, Raipur",
      "photos": ["url1", "url2"],
      "created_at": "2025-10-28T10:00:00Z",
      "likes_count": 12,
      "comments_count": 3
    }
  ]
}
```

#### R10.4: Moderation Queue (Later Phase)

**Note**: Will be implemented after app trial using open-source CMS.

**Placeholder**:
- All community stories go to moderation queue
- Admin approves/rejects
- Approved stories appear in feed

---

**Document Owner**: Development Team
**Last Updated**: October 28, 2025 (Added AI Coach Onboarding + Feed System)
**Next Review**: After Phase 2A completion
