# Boloo App - Implementation Roadmap v2.0

**Based on**: Updated 8-point improvement plan (Oct 27, 2025)
**Timeline**: 4-6 weeks for complete implementation
**Status**: Roadmap defined, implementation pending

---

## 📋 Quick Reference

| Phase | Duration | Focus | Priority |
|-------|----------|-------|----------|
| **Phase 2A** | 2 weeks | Triage + Uncertainty-Killer UI | 🔴 CRITICAL |
| **Phase 2B** | 1.5 weeks | Conversation + Tone Engine | 🟡 HIGH |
| **Phase 2C** | 1 week | Polish + Edge Cases | 🟢 MEDIUM |
| **Phase 2D** | 2-3 weeks | AI Coach Onboarding System | 🟡 HIGH |
| **Phase 2E** | 1 week | Photo Upload & Storage | 🟢 MEDIUM |
| **Phase 2F** | 1-2 weeks | Feed System (Community Stories) | 🟢 MEDIUM |
| **Phase 2G** | 1 week | Moderation Queue | 🟢 LOW (post-trial) |
| **Total** | 8.5-10.5 weeks | Full v2.0 + AI Coach + Feed | - |

---

## 🔴 Phase 2A: Triage & Uncertainty-Killer UI (2 Weeks)

### Goal
Get 3-way triage working + show users exactly what happens next (no more uncertainty!)

### Week 1: Triage System

#### Day 1-2: Backend Triage API
**Task**: Build Claude API integration for intent classification
- [ ] Create `POST /v1/cases/triage` endpoint
- [ ] Integrate Claude API with prompt template
- [ ] Return intent (grievance/community/personal) + confidence
- [ ] Add suggested_issue_type if grievance detected
- [ ] Write unit tests

**Files**:
- `backend/app/routers/triage.py` (new)
- `backend/app/services/claude.py` (new)
- `backend/app/prompts/triage.py` (new - prompt templates)

**Acceptance**:
- API returns `{"intent": "grievance", "confidence": 0.85}`
- High confidence (≥0.7) → auto-proceed
- Low confidence (<0.7) → requires confirmation

---

#### Day 3-4: Mobile Triage Overlay UI
**Task**: Auto-classify after 5-10s, show chips on low confidence
- [ ] Create triage overlay component
- [ ] Call triage API when recording stops
- [ ] Show loading: "विश्लेषण हो रहा है..."
- [ ] Display result with confidence badge
- [ ] 3 override chips (Grievance/Community/Personal)
- [ ] User can tap to change, no confirmation needed

**Files**:
- `mobile/src/components/TriageOverlay.tsx` (new)
- `mobile/src/screens/VoiceRecordScreen.tsx` (update)
- `mobile/src/services/triage.ts` (new)

**Acceptance**:
- Overlay appears automatically after recording
- High confidence → proceeds without taps
- Low confidence → shows 3 chips to select

---

#### Day 5: Testing & Bug Fixes
- [ ] Test all 3 triage paths (grievance/community/personal)
- [ ] Test confidence bands (high/medium/low)
- [ ] Test override flow
- [ ] Fix any UI/API issues

---

### Week 2: "Agla Kya Hoga" System

#### Day 1-2: Next Steps API
**Task**: Calculate SLA, entity, escalation path
- [ ] Create `GET /v1/cases/{id}/next-steps` endpoint
- [ ] Calculate responsible entity from location + issue_type
- [ ] Determine SLA window (72h for GP, 48h for BDO, etc.)
- [ ] Build escalation ladder (rung 1 → rung 2 → rung 3)
- [ ] Return Hindi status text ("आपकी शिकायत...")

**Files**:
- `backend/app/routers/cases.py` (update)
- `backend/app/services/sla.py` (new)
- `backend/app/services/routing.py` (update)

**Acceptance**:
- API returns full next-steps object
- SLA due_at calculated correctly
- Escalation path includes all rungs
- Hindi status text matches case state

---

#### Day 3-4: Mobile "Agla Kya Hoga" Card
**Task**: Post-submit card with SLA clock + timeline
- [ ] Create post-submit screen with card
- [ ] Display responsible entity name
- [ ] Show live SLA countdown (updates every minute)
- [ ] Color-code timer (green/yellow/red)
- [ ] Display escalation rung ("72h, then BDO")
- [ ] Timeline view with "who has ball" indicator

**Files**:
- `mobile/src/screens/CaseSubmittedScreen.tsx` (new)
- `mobile/src/components/SLAClockCard.tsx` (new)
- `mobile/src/components/CaseTimeline.tsx` (new)
- `mobile/src/hooks/useSLATimer.ts` (new - countdown logic)

**Acceptance**:
- Card appears immediately after submit
- SLA clock counts down in real-time
- Timeline shows current state clearly
- Hindi text is respectful and clear

---

#### Day 5: Personal Diary Feature
**Task**: Build private notes with reminders
- [ ] Create `GET /v1/cases/personal` endpoint
- [ ] Create `POST /v1/cases/{id}/convert-to-grievance` endpoint
- [ ] Build "My Diary" tab in mobile app
- [ ] Personal note creation flow
- [ ] Reminder date picker
- [ ] "Convert to Grievance" button
- [ ] Push notification for reminders

**Files**:
- `backend/app/routers/cases.py` (update)
- `mobile/src/screens/MyDiaryScreen.tsx` (new)
- `mobile/src/screens/PersonalNoteDetailScreen.tsx` (new)
- `mobile/src/services/notifications.ts` (update)

**Acceptance**:
- Personal notes never appear in public/admin views
- Reminders trigger notifications
- Convert button works in one tap
- Privacy is 100% enforced

---

### Phase 2A Deliverable
✅ Users can record → auto-triage classifies → see clear next steps
✅ Personal diary feature working for retention
✅ No more "ab kya hoga?" uncertainty

---

## 🟡 Phase 2B: Conversation & Tone Engine (1.5 Weeks)

### Goal
Make conversations feel natural, warm, and respectful with minimal questions

### Week 3: Slot Extraction & Conversation UX

#### Day 1-2: Claude Slot Extraction
**Task**: Extract structured data from voice transcript
- [ ] Create slot extraction prompts for Claude API
- [ ] Build `POST /v1/cases/extract-slots` endpoint
- [ ] Define schemas for all 3 case types (grievance/community/personal)
- [ ] Return confidence scores per slot
- [ ] Identify missing slots (confidence < 0.7)

**Files**:
- `backend/app/services/claude.py` (update)
- `backend/app/prompts/slot_extraction.py` (new)
- `backend/app/schemas/slots.py` (new)

**Acceptance**:
- API extracts all available slots from transcript
- Confidence scores are accurate
- Missing slots clearly identified
- Schema validates output

---

#### Day 3-4: Chat UI with Live Transcript
**Task**: Replace simple recording screen with chat interface
- [ ] Build chat-style UI (WhatsApp-like bubbles)
- [ ] Display live Hindi transcript (big Devanagari text)
- [ ] Azure Speech streaming integration (200ms latency)
- [ ] Assistant bubbles with one-line messages
- [ ] Progress chips showing slot completion
- [ ] Follow-up questions only for missing slots

**Files**:
- `mobile/src/screens/ConversationScreen.tsx` (new - replaces VoiceRecordScreen)
- `mobile/src/components/LiveTranscript.tsx` (new)
- `mobile/src/components/ProgressChips.tsx` (new)
- `mobile/src/components/ChatBubble.tsx` (new)
- `mobile/src/services/azureSpeech.ts` (new)

**Acceptance**:
- Live transcript updates in real-time
- Assistant asks max 2 follow-up questions
- Progress chips show visual feedback
- UX feels conversational, not interrogative

---

#### Day 5: Testing Conversation Flow
- [ ] Test grievance flow (all required slots)
- [ ] Test community story flow
- [ ] Test personal note flow
- [ ] Test minimal follow-ups logic
- [ ] Test low-confidence retry behavior

---

### Week 4: Tone Engine & Language

#### Day 1-2: Tone Engine & Microcopy
**Task**: Add warm, respectful Hindi/Chhattisgarhi tone
- [ ] Create microcopy JSON file (hi_friendly, hi_cg_friendly, hi_formal)
- [ ] Build microcopy loader service
- [ ] User settings for tone preference
- [ ] Claude prompts for tone switching
- [ ] Formal summary generation for officers
- [ ] Conversational warmth for citizens

**Files**:
- `backend/app/assets/microcopy.json` (new)
- `backend/app/services/microcopy.py` (new)
- `mobile/src/constants/microcopy.ts` (new)
- `mobile/src/context/LanguageContext.tsx` (update)

**Acceptance**:
- Greetings use light humor ("का हो भई?")
- Follow-ups are warm, not robotic
- Official summaries remain formal
- Tone never mocks user's problem

---

#### Day 3-4: Azure Speech Integration
**Task**: Hindi ASR with custom vocabulary
- [ ] Set up Azure Speech resource
- [ ] Configure `hi-IN` model
- [ ] Load custom vocabulary from Entities table
- [ ] Add Chhattisgarhi common words
- [ ] Implement low-confidence retry logic
- [ ] Fallback to text input on failure

**Files**:
- `backend/app/services/azureSpeech.py` (new)
- `backend/app/services/vocabulary.py` (new - builds from Entities)
- `mobile/src/services/azureSpeech.ts` (update)

**Acceptance**:
- Hindi ASR accuracy >90%
- Village names recognized correctly
- Low confidence triggers "धीरे बोलें" reprompt
- Offline fallback works gracefully

---

#### Day 5: Integration Testing
- [ ] Test Hindi ASR with real audio samples
- [ ] Test code-mix (Hindi + English + Chhattisgarhi)
- [ ] Test tone variations across flows
- [ ] Test formal summary generation
- [ ] Fix any translation/tone issues

---

### Phase 2B Deliverable
✅ Natural conversation flow with minimal questions
✅ Warm, respectful tone (Chhattisgarhi-friendly)
✅ Hindi ASR with custom vocabulary working
✅ Chat UI feels like talking to a helpful friend

---

## 🟢 Phase 2C: Polish & Edge Cases (1 Week)

### Goal
Handle all edge cases gracefully, add entity corrections, finalize for production

### Week 5: Final Polish

#### Day 1-2: Entity Directory Corrections
**Task**: Let moderators/officers suggest entity updates
- [ ] Add 3 new fields to entities table (version, suggested_updates, last_verified_at)
- [ ] Create `POST /v1/entities/{id}/suggest-correction` endpoint
- [ ] Build admin approval interface (web console)
- [ ] Versioning logic (keep old versions)
- [ ] Notification to admin on new suggestion

**Files**:
- `backend/alembic/versions/xxx_entity_corrections.py` (migration)
- `backend/app/routers/entities.py` (update)
- `backend/app/models/entity.py` (update)
- `web/app/admin/entity-corrections/page.tsx` (new)

**Acceptance**:
- Moderators can submit corrections
- Admin can approve/reject
- Old versions retained for audit
- Routes update immediately on approval

---

#### Day 3: Offline Mode
**Task**: Handle poor network gracefully
- [ ] Offline recording queue (SQLite)
- [ ] Background sync when online
- [ ] "इंटरनेट धीमा है" message
- [ ] Text input fallback option
- [ ] SLA timing handled correctly (starts on sync, not record)

**Files**:
- `mobile/src/services/offlineQueue.ts` (new)
- `mobile/src/services/syncManager.ts` (new)
- `mobile/src/context/NetworkContext.tsx` (new)

**Acceptance**:
- Users can record without internet
- Audio queued and synced automatically
- SLA starts when case reaches backend
- No data loss

---

#### Day 4: ASR Failure Fallbacks
**Task**: Graceful handling when Azure fails
- [ ] Detect Azure API failures
- [ ] Offer text input: "बोलने में दिक्कत? लिखें"
- [ ] Use LLM on text instead of audio
- [ ] Keep raw audio for manual review
- [ ] Retry logic (3 attempts)

**Files**:
- `backend/app/services/azureSpeech.py` (update)
- `mobile/src/screens/ConversationScreen.tsx` (update)
- `mobile/src/components/TextInputFallback.tsx` (new)

**Acceptance**:
- Users never stuck on ASR failure
- Text input works as backup
- Audio saved for future improvement
- UX remains smooth

---

#### Day 5: Final Testing & Bug Fixes
**Test Coverage**:
- [ ] End-to-end: Triage → Submit → See next steps
- [ ] Personal diary → Convert to grievance
- [ ] Low-confidence retries
- [ ] Offline → Online sync
- [ ] ASR failures → Text fallback
- [ ] All 3 case types (grievance/community/personal)
- [ ] Entity corrections workflow
- [ ] Privacy (personal notes never leak)

**Bug Fixes**:
- [ ] Fix any crash bugs
- [ ] Polish UI transitions
- [ ] Optimize API response times
- [ ] Test on real Android devices (mid-range phones)

---

### Phase 2C Deliverable
✅ All edge cases handled gracefully
✅ Entity corrections workflow complete
✅ Offline mode + ASR fallbacks working
✅ App is production-ready

---

## 🟡 Phase 2D: AI Coach Onboarding System (2-3 Weeks)

### Goal
Train new users how to report effectively for first 5-6 reports, then auto-switch to simple mode

### Week 6: Training Mode Backend

#### Day 1-2: Database Schema & Migrations
**Task**: Add training state tracking and conversation tables
- [ ] Add 3 columns to users table: training_reports_count, training_completed, training_mode_enabled
- [ ] Create conversations table (id, user_id, case_id, turn_count, is_complete, completeness_score)
- [ ] Create conversation_turns table (id, conversation_id, turn_number, transcript, AI response, fields_extracted)
- [ ] Write Alembic migrations
- [ ] Create SQLAlchemy models

**Files**:
- `backend/alembic/versions/xxx_ai_coach_training.py` (migration)
- `backend/app/models/conversation.py` (new)
- `backend/app/models/conversation_turn.py` (new)
- `backend/app/models/user.py` (update)

**Acceptance**:
- All tables created successfully
- Foreign keys working correctly
- Indexes on user_id and conversation_id
- Default values set properly

---

#### Day 3-5: Completeness Analysis Service
**Task**: Build AI-powered completeness checker
- [ ] Create `completeness_analyzer.py` service
- [ ] Azure OpenAI integration for field extraction
- [ ] Define required fields per intent (grievance/community/personal)
- [ ] Implement missing field detection (critical fields only)
- [ ] Generate conversational follow-up questions (Hindi + English)
- [ ] Rule: Maximum 2 follow-up questions
- [ ] Calculate completeness score

**Files**:
- `backend/app/services/completeness_analyzer.py` (new)
- `backend/app/prompts/completeness_prompts.py` (new)
- `backend/app/schemas/completeness.py` (new)

**Acceptance**:
- Correctly identifies missing critical fields
- Generates appropriate Hindi questions
- Respects 2-question maximum rule
- Completeness score accurate (0.0-1.0)

---

### Week 7: Multi-Turn Conversation API

#### Day 1-3: Modify Voice Pipeline Endpoint
**Task**: Update /v1/transcription/transcribe-and-classify for dual-mode
- [ ] Add mode detection logic (training vs simple)
- [ ] Modify endpoint to accept turn_number and conversation_id
- [ ] Implement conversation context loading
- [ ] Store conversation turns in database
- [ ] Return completeness analysis for training mode
- [ ] Simple mode bypasses completeness check
- [ ] Graduation check after 5th report

**Files**:
- `backend/app/routers/transcription.py` (update)
- `backend/app/services/conversation_service.py` (new)
- `backend/app/services/training_service.py` (new)

**Request Schema** (Training Mode):
```json
{
  "audio": "file",
  "user_id": "uuid",
  "turn_number": 1,
  "conversation_id": "uuid | null",
  "language": "hi-IN"
}
```

**Response Schema** (Training Mode):
```json
{
  "success": true,
  "training_mode": true,
  "conversation_id": "conv-uuid",
  "transcript": "हमारे क्षेत्र में पानी की समस्या है",
  "completeness_analysis": {
    "collected_fields": ["issue_type", "description"],
    "missing_fields": [
      {
        "field": "location",
        "importance": "critical",
        "prompt_hi": "यह समस्या किस इलाके में है?",
        "prompt_en": "Which area has this problem?"
      }
    ],
    "completeness_score": 0.4,
    "is_complete": false
  },
  "turn_count": 1
}
```

**Acceptance**:
- Training mode works for first 5 reports
- Simple mode for experienced users
- Conversation context maintained across turns
- Graduation triggers after 5th report

---

#### Day 4-5: Graduation & Settings API
**Task**: Handle training completion and toggle
- [ ] Create `POST /v1/conversations/complete` endpoint
- [ ] Increment training_reports_count
- [ ] Check for graduation (count >= 5)
- [ ] Return graduation status
- [ ] Create `PATCH /v1/users/{id}/training-mode` endpoint
- [ ] Settings toggle for re-enabling training

**Files**:
- `backend/app/routers/conversations.py` (new)
- `backend/app/routers/users.py` (update)

**Acceptance**:
- Graduation detected correctly
- Settings toggle persists
- Training mode can be re-enabled anytime
- Progress tracked accurately (1/5, 2/5, etc.)

---

### Week 8: Mobile UI Implementation

#### Day 1-2: Training Mode Voice UI
**Task**: Build multi-turn conversation UI
- [ ] Create TrainingVoiceScreen.tsx
- [ ] Display progress indicator (1/5, 2/5, etc.)
- [ ] Show AI follow-up questions in Hindi/English
- [ ] Record button for each turn
- [ ] Display collected fields as visual chips
- [ ] "Need Help?" link to re-enable training
- [ ] Minimalist design (one primary action per screen)

**Files**:
- `mobile/src/screens/TrainingVoiceScreen.tsx` (new)
- `mobile/src/components/TrainingProgress.tsx` (new)
- `mobile/src/components/CollectedFieldsChips.tsx` (new)
- `mobile/src/components/AIQuestionBubble.tsx` (new)

**Acceptance**:
- Progress shows clearly (1/5, 2/5)
- AI questions display in large Hindi text
- One primary action per screen
- Beautiful, minimalist design

---

#### Day 3-4: Graduation Celebration Screen
**Task**: Celebration after 5th report
- [ ] Create GraduationScreen.tsx
- [ ] Hindi + English bilingual message
- [ ] Confetti animation
- [ ] Explain simple mode benefits
- [ ] Settings navigation hint
- [ ] "Continue" button to dismiss

**Files**:
- `mobile/src/screens/GraduationScreen.tsx` (new)
- `mobile/src/components/ConfettiAnimation.tsx` (new)

**UI Design**:
```
┌─────────────────────────────────────┐
│  🎉 बधाई हो! Congratulations!      │
│                                     │
│  आपने प्रशिक्षण पूरा कर लिया है!   │
│  You've completed AI Coach training!│
│                                     │
│  From now on:                       │
│  ✓ Faster reporting (one recording)│
│  ✓ No follow-up questions          │
│  ✓ Instant submission              │
│                                     │
│  You can re-enable training mode    │
│  anytime from Settings > AI Coach   │
│                                     │
│  [Continue]                         │
└─────────────────────────────────────┘
```

**Acceptance**:
- Celebration shows on 5th report completion
- Clear benefits explanation
- Settings hint visible
- Dismissible with single tap

---

#### Day 5: Settings Toggle & Integration
**Task**: Settings screen toggle for training mode
- [ ] Add "AI Coach" section in Settings
- [ ] Toggle switch: "Enable training mode"
- [ ] Explain what training mode does
- [ ] Show current progress if < 5 reports
- [ ] Update training_mode_enabled via API
- [ ] Integrate with voice recording flow

**Files**:
- `mobile/src/screens/SettingsScreen.tsx` (update)
- `mobile/src/services/userService.ts` (update)
- `mobile/src/context/TrainingContext.tsx` (new)

**Acceptance**:
- Toggle works correctly
- Training progress visible in settings
- Mode persists across app restarts
- Seamless integration with voice flow

---

### Phase 2D Deliverable
✅ AI Coach trains new users for first 5-6 reports
✅ Multi-turn conversations with max 2 follow-ups
✅ Auto-graduation to simple mode after training
✅ Settings toggle for re-enabling training
✅ Minimalist, Steve Jobs-level UX

---

## 🟢 Phase 2E: Photo Upload & Storage (1 Week)

### Goal
Allow users to attach photos to reports with MinIO storage

### Week 9: Photo Upload System

#### Day 1-2: MinIO Setup & Backend
**Task**: Configure MinIO and create upload API
- [ ] Install MinIO locally (Docker)
- [ ] Create boloo-media bucket
- [ ] Add MinIO config to .env
- [ ] Create media table (storage_url, storage_key, file_type, file_size)
- [ ] Build MediaService class
- [ ] Create `POST /v1/media/upload` endpoint
- [ ] Validate file (type, size, dimensions)
- [ ] Generate presigned URLs (7-day expiry)
- [ ] Link photos to case_id

**Files**:
- `backend/app/services/media_service.py` (new)
- `backend/app/routers/media.py` (new)
- `backend/app/models/media.py` (new)
- `backend/alembic/versions/xxx_media_table.py` (migration)
- `backend/docker-compose.yml` (add MinIO service)

**Acceptance**:
- MinIO running locally
- Photo upload works
- Presigned URLs generated correctly
- Max 3 photos per case enforced

---

#### Day 3-4: Mobile Photo Upload UI
**Task**: Camera + gallery picker with compression
- [ ] Create PhotoUploadScreen.tsx
- [ ] Camera capture button
- [ ] Gallery picker button
- [ ] Client-side image compression (expo-image-manipulator)
- [ ] Preview before upload
- [ ] Upload progress indicator
- [ ] Max 3 photos validation
- [ ] Max 5MB per photo validation

**Files**:
- `mobile/src/screens/PhotoUploadScreen.tsx` (new)
- `mobile/src/components/PhotoPicker.tsx` (new)
- `mobile/src/components/PhotoPreview.tsx` (new)
- `mobile/src/services/mediaService.ts` (new)

**Acceptance**:
- Camera and gallery work
- Images compressed before upload
- Max 3 photos enforced
- Progress indicator shows upload status
- Preview shows before final submit

---

#### Day 5: Testing & Integration
- [ ] Test photo upload end-to-end
- [ ] Test with large images (> 5MB)
- [ ] Test with various formats (JPEG, PNG)
- [ ] Test offline handling (queue for sync)
- [ ] Integrate with case creation flow

---

### Phase 2E Deliverable
✅ Photo upload working (max 3 per case)
✅ MinIO storage configured
✅ Client-side compression
✅ Presigned URLs for secure access

---

## 🟢 Phase 2F: Feed System (1-2 Weeks)

### Goal
RSS-style community feed showing approved stories with photos

### Week 10: Feed Backend & API

#### Day 1-3: Feed API Implementation
**Task**: Build feed endpoints with filtering
- [ ] Create `GET /v1/feed/{feed_type}` endpoint
- [ ] Support 3 types: community, my_reports, local
- [ ] Filter by district (community feed)
- [ ] Filter by 5km radius (local feed)
- [ ] Filter by user_id (my reports)
- [ ] Join with media table for photos
- [ ] Include engagement metrics (likes, comments)
- [ ] Pagination (limit=20, offset)

**Files**:
- `backend/app/routers/feed.py` (new)
- `backend/app/services/feed_service.py` (new)
- `backend/app/schemas/feed.py` (new)

**Response Schema**:
```json
{
  "stories": [
    {
      "case_id": "uuid",
      "title": "Road Repair Completed",
      "summary": "पोथोल भरे गए, सड़क ठीक हो गई।",
      "photos": ["url1", "url2"],
      "location_text": "Raipur, Sector 5",
      "created_at": "2025-10-28T14:30:00Z",
      "status": "resolved",
      "likes_count": 45,
      "comments_count": 12
    }
  ]
}
```

**Acceptance**:
- All 3 feed types work
- Photos included in response
- Pagination works correctly
- Only approved public cases shown

---

#### Day 4-5: Mobile Feed UI
**Task**: RSS-style feed with photo grids
- [ ] Create FeedScreen.tsx
- [ ] Tab bar: Community / My Reports / Local
- [ ] Photo grid layout (1-3 photos)
- [ ] Large Hindi text for summaries
- [ ] Location pin icon
- [ ] Status badges (resolved, in progress)
- [ ] Like and comment counts
- [ ] Timestamp (relative: "2h ago")
- [ ] Pull-to-refresh
- [ ] Infinite scroll

**Files**:
- `mobile/src/screens/FeedScreen.tsx` (new)
- `mobile/src/components/FeedCard.tsx` (new)
- `mobile/src/components/PhotoGrid.tsx` (new)
- `mobile/src/services/feedService.ts` (new)

**UI Design**:
```
┌─────────────────────────────────────┐
│  Community | My Reports | Local     │
├─────────────────────────────────────┤
│  [Photo Grid - 1-3 photos]         │
│  📍 Raipur, Sector 5                │
│  🏗️ Road Repair Completed          │
│  "पोथोल भरे गए, सड़क ठीक हो गई।"  │
│  👍 45    💬 12    🕐 2h ago        │
└─────────────────────────────────────┘
```

**Acceptance**:
- Feed loads quickly
- Photos display in grid
- Pull-to-refresh works
- Infinite scroll loads more
- Minimalist, clean design

---

### Phase 2F Deliverable
✅ RSS-style feed with 3 types
✅ Photo grids in feed cards
✅ Like and comment counts
✅ Pull-to-refresh and infinite scroll

---

## 🟢 Phase 2G: Moderation Queue (1 Week, Post-Trial)

### Goal
Moderation system for first-timer reports and photos

### Week 11: Moderation System

#### Day 1-3: Moderation Backend
**Task**: Build moderation queue API
- [ ] Create `GET /v1/moderation/queue` endpoint
- [ ] Filter pending cases and photos
- [ ] Create `POST /v1/moderation/{item_id}/approve` endpoint
- [ ] Create `POST /v1/moderation/{item_id}/reject` endpoint
- [ ] Create `POST /v1/moderation/{item_id}/edit` endpoint
- [ ] Log all actions in case_events
- [ ] Send notifications to users on decision

**Files**:
- `backend/app/routers/moderation.py` (new)
- `backend/app/services/moderation_service.py` (new)

**Acceptance**:
- Queue shows pending items
- Approve/reject/edit works
- Actions logged properly
- Users notified of decisions

---

#### Day 4-5: Web Moderation Console
**Task**: Simple moderation interface
- [ ] Create moderation page in Next.js web console
- [ ] Display pending queue (cases + photos)
- [ ] Show full transcript and photos
- [ ] Action buttons: Approve / Reject / Edit / Flag
- [ ] Rejection reason form
- [ ] Bulk actions (approve multiple)
- [ ] Queue filters (by type, date)

**Files**:
- `web/app/moderation/page.tsx` (new)
- `web/components/ModerationCard.tsx` (new)
- `web/components/ModerationActions.tsx` (new)

**Acceptance**:
- Queue displays clearly
- All actions work
- Bulk approve works
- Filters functional

---

### Future Enhancement (Post-Trial)
**Task**: Research open-source CMS integration
- [ ] Evaluate: Strapi, Directus, Payload CMS
- [ ] Custom moderation workflows
- [ ] AI-assisted moderation (GPT-4o-mini pre-screening)
- [ ] Bulk actions and keyboard shortcuts

---

### Phase 2G Deliverable
✅ Moderation queue functional
✅ Approve/reject/edit working
✅ Web console for moderators
✅ Open-source CMS plan for future

---

## 📊 Implementation Priority Matrix

### 🔴 MUST-HAVE (Phase 2A - Critical)
| Feature | Backend | Mobile | Complexity | Impact |
|---------|---------|--------|------------|--------|
| Triage API | 3 days | - | Medium | 🔥 Critical |
| Triage UI overlay | - | 2 days | Easy | 🔥 Critical |
| "Agla Kya Hoga" API | 2 days | - | Medium | 🔥 Critical |
| SLA clock card | - | 2 days | Easy | 🔥 Critical |
| Personal diary | 1 day | 2 days | Easy | 🔥 High |

### 🟡 IMPORTANT (Phase 2B - High)
| Feature | Backend | Mobile | Complexity | Impact |
|---------|---------|--------|------------|--------|
| Slot extraction | 2 days | - | Medium | 🔶 High |
| Chat UI + live transcript | - | 3 days | Hard | 🔶 High |
| Tone engine | 1 day | 1 day | Easy | 🔶 Medium |
| Azure Speech | 2 days | 2 days | Hard | 🔶 High |

### 🟢 GOOD-TO-HAVE (Phase 2C - Medium)
| Feature | Backend | Mobile | Complexity | Impact |
|---------|---------|--------|------------|--------|
| Entity corrections | 2 days | - | Medium | 🟢 Medium |
| Offline mode | - | 2 days | Medium | 🟢 Medium |
| ASR fallbacks | 1 day | 1 day | Easy | 🟢 Low |

### 🟡 AI COACH ONBOARDING (Phase 2D - High)
| Feature | Backend | Mobile | Complexity | Impact |
|---------|---------|--------|------------|--------|
| Training database schema | 2 days | - | Easy | 🔶 High |
| Completeness analysis | 3 days | - | Hard | 🔶 High |
| Dual-mode voice pipeline | 3 days | - | Medium | 🔶 High |
| Training mode UI | - | 3 days | Medium | 🔶 High |
| Graduation celebration | - | 2 days | Easy | 🔶 Medium |
| Settings toggle | 1 day | 1 day | Easy | 🔶 Medium |

### 🟢 PHOTO & FEED SYSTEM (Phase 2E-2F - Medium)
| Feature | Backend | Mobile | Complexity | Impact |
|---------|---------|--------|------------|--------|
| MinIO setup + media API | 2 days | - | Medium | 🟢 High |
| Photo upload UI | - | 3 days | Medium | 🟢 High |
| Feed API (3 types) | 3 days | - | Medium | 🟢 Medium |
| Feed UI with photos | - | 2 days | Easy | 🟢 Medium |
| Moderation queue | 3 days | - | Medium | 🟢 Low |
| Moderation console | 2 days | - | Easy | 🟢 Low |

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] Triage API classification accuracy
- [ ] SLA calculation logic
- [ ] Slot extraction accuracy
- [ ] Routing confidence thresholds
- [ ] Entity corrections versioning

### Integration Tests
- [ ] End-to-end: Record → Triage → Submit → Next steps
- [ ] Personal diary → Convert to grievance
- [ ] Offline → Online sync
- [ ] Azure Speech → Transcript → Slots

### User Acceptance Tests
- [ ] Real users in Chhattisgarh villages
- [ ] Noisy environments (markets, roads)
- [ ] Code-mix speech (Hindi + English + Chhattisgarhi)
- [ ] Low literacy users (voice-only)
- [ ] Mid-range Android phones (3-4 years old)

---

## 📈 Success Criteria

### Phase 2A Success
- [ ] Triage accuracy ≥85%
- [ ] User override rate <10%
- [ ] SLA card shown 100% of time
- [ ] Personal diary usage >20%

### Phase 2B Success
- [ ] ASR accuracy ≥90% (Hindi)
- [ ] Average follow-up questions <2
- [ ] Chat UI feels natural (user testing)
- [ ] Formal summaries remain professional

### Phase 2C Success
- [ ] Zero crashes in 7-day test
- [ ] Offline sync success rate 100%
- [ ] Entity corrections workflow smooth
- [ ] All edge cases handled gracefully

### Phase 2D Success (AI Coach)
- [ ] Training mode works for first 5 reports
- [ ] Max 2 follow-up questions respected
- [ ] Graduation triggers correctly
- [ ] Settings toggle persists
- [ ] Completeness analysis accuracy ≥85%
- [ ] User satisfaction with training ≥90%

### Phase 2E Success (Photo Upload)
- [ ] Photo upload success rate ≥95%
- [ ] Image compression reduces size by 50%+
- [ ] MinIO storage working reliably
- [ ] Presigned URLs valid and secure

### Phase 2F Success (Feed System)
- [ ] Feed loads in <2 seconds
- [ ] Photo grids display correctly
- [ ] All 3 feed types functional
- [ ] User engagement with feed ≥30%

### Phase 2G Success (Moderation)
- [ ] Moderation queue always up-to-date
- [ ] Approve/reject <30 seconds per item
- [ ] Bulk actions work smoothly
- [ ] User notification on decision within 5 min

---

## 🛠️ Tech Stack Summary

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL + PostGIS
- **LLM**: Claude API (Anthropic)
- **ASR**: Azure Speech Services (hi-IN)
- **Queue**: Redis (for background jobs)
- **Storage**: MinIO (S3-compatible)

### Mobile
- **Framework**: React Native + Expo
- **Navigation**: React Navigation
- **State**: React Context + AsyncStorage
- **Audio**: expo-av
- **Offline**: SQLite + background sync
- **Notifications**: expo-notifications

### Web Console
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS
- **Data Fetching**: SWR
- **Auth**: JWT tokens

---

## 📅 Timeline Estimate

### Conservative (With Buffer) - Full Implementation
- **Phase 2A**: 2.5 weeks (Triage + Uncertainty-Killer UI)
- **Phase 2B**: 2 weeks (Conversation + Tone Engine)
- **Phase 2C**: 1.5 weeks (Polish + Edge Cases)
- **Phase 2D**: 3 weeks (AI Coach Onboarding)
- **Phase 2E**: 1.5 weeks (Photo Upload & Storage)
- **Phase 2F**: 2 weeks (Feed System)
- **Phase 2G**: 1.5 weeks (Moderation Queue)
- **Total**: **14 weeks** (~3.5 months)

### Aggressive (Ideal Conditions)
- **Phase 2A**: 2 weeks
- **Phase 2B**: 1.5 weeks
- **Phase 2C**: 1 week
- **Phase 2D**: 2 weeks (AI Coach Onboarding)
- **Phase 2E**: 1 week (Photo Upload)
- **Phase 2F**: 1 week (Feed System)
- **Phase 2G**: 1 week (Moderation)
- **Total**: **9.5 weeks** (~2.5 months)

### Recommended Approach
**Two-track development**:
- **Track 1 (Core - Phases 2A-2C)**: 4.5-6 weeks - Voice recording, triage, next steps
- **Track 2 (AI Coach + Feed - Phases 2D-2G)**: 5.5-8.5 weeks - Training system, photos, feed, moderation

**Phases 2A-2C can proceed immediately** (already started with Azure AI integration).

**Phases 2D-2G implementation sequence**:
1. Start Phase 2D (AI Coach) after 2C completes
2. Phase 2E (Photos) can run parallel with Phase 2D Week 3
3. Phase 2F (Feed) depends on 2E completion
4. Phase 2G (Moderation) can wait until post-trial

---

## 🎯 Next Actions

### ✅ Completed (Oct 27-28, 2025)
1. ✅ **Set up Azure OpenAI** - GPT-4o-mini deployed and tested
2. ✅ **Set up Azure Speech** - Hindi transcription working
3. ✅ **FFmpeg installation** - Audio conversion functional
4. ✅ **Voice AI integration** - Complete pipeline working
5. ✅ **Documentation** - AZURE_AI_INTEGRATION.md, PROJECT_STATUS.md

### 🔄 In Progress (Oct 31, 2025)
1. 🔄 **Documentation Updates** - Integrating AI Coach into docs
2. 🔄 **TRIAGE_AND_UX_REQUIREMENTS.md** - Added Section 9 (AI Coach) + Section 10 (Photos/Feed)
3. 🔄 **ARCHITECTURE.md** - Updated with conversation tables, feed system, photo storage
4. 🔄 **IMPLEMENTATION_ROADMAP_v2.md** - Adding Phases 2D-2G

### Immediate Next Steps (Week 1)
1. **Finalize Documentation** - Complete all doc updates
2. **Delete AI_STORY_COACH_SYSTEM.md** - No longer needed (integrated into requirements)
3. **Create Phase 2D Feature Branch** - AI Coach implementation
4. **Begin Phase 2D Week 6 Day 1** - Database schema for training state
5. **Write Alembic migrations** - conversations, conversation_turns, media tables

### Week 2-3 (Phase 2D Start)
1. Begin completeness analysis service
2. Modify voice pipeline for dual-mode
3. Build training mode UI
4. Implement graduation celebration

---

## 📚 Related Documents
- **Gap Analysis**: `docs/ANDROID_GAP_ANALYSIS.md`
- **Requirements**: `docs/TRIAGE_AND_UX_REQUIREMENTS.md` (includes AI Coach Section 9, Photos/Feed Section 10)
- **Current Status**: `docs/PROJECT_STATUS_OCT_28_2025.md` (Voice AI integration complete)
- **Architecture**: `docs/ARCHITECTURE.md` (updated with conversations, media, feed)
- **Azure AI Integration**: `docs/AZURE_AI_INTEGRATION.md` (Azure OpenAI + Speech setup)

---

**Roadmap Version**: 2.1 (Updated with AI Coach + Feed System)
**Last Updated**: October 31, 2025
**Next Review**: After Phase 2D completion (AI Coach implementation)
