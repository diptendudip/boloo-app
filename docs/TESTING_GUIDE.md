# Boloo App - Testing Guide

Quick guide to get the Boloo app running for testing the new triage and personal diary features.

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd boloo-app/backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` and set your API keys**:
   ```env
   # Required for triage classification
   ANTHROPIC_API_KEY=sk-ant-your-key-here

   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/boloo_db

   # JWT Secret
   JWT_SECRET_KEY=your-secret-key-here
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Mobile Setup

1. **Navigate to mobile directory**:
   ```bash
   cd boloo-app/mobile
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Update API URL** (if needed):
   Edit `mobile/src/constants/config.ts` to point to your backend:
   ```typescript
   export const API_URL = 'http://192.168.1.x:8000';  // Your local IP
   ```

4. **Start Expo**:
   ```bash
   npx expo start
   ```

5. **Run on device**:
   - Scan QR code with Expo Go app (iOS/Android)
   - Or press `a` for Android emulator
   - Or press `i` for iOS simulator

## ✨ Features to Test

### 1. **3-Way Triage System**

**Test Flow:**
1. Login to the app
2. Go to voice recording screen
3. Speak a complaint (e.g., "पानी की सप्लाई नहीं आ रही है 2 हफ्ते से")
4. Wait for transcription
5. **See triage overlay** pop up with classification:
   - Intent badge (📢 Grievance / 📰 Community / 📝 Personal)
   - Confidence percentage
   - Option to override if wrong

**Expected Results:**
- Water complaint → Classified as "Grievance" with high confidence (>70%)
- Community event → Classified as "Community"
- Personal reminder → Classified as "Personal"

**API Test:**
```bash
curl -X POST http://localhost:8000/api/v1/triage/classify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "transcript_text": "हमारे क्षेत्र में पानी की समस्या है 2 हफ्ते से",
    "location_hint": "Raipur, Chhattisgarh"
  }'
```

### 2. **"Agla Kya Hoga?" (What Happens Next)**

**Test Flow:**
1. Submit a grievance (after triage classifies it)
2. On `CaseSubmittedScreen`, see:
   - ✅ Success message with case reference number
   - 🏘️ Responsible entity card (Gram Panchayat / BDO / District Office)
   - ⏰ SLA countdown clock showing time remaining
   - Expected actions list
   - Escalation path preview

**Expected Results:**
- SLA clock shows 72h for Gram Panchayat cases
- Clock color changes: Green (< 70% used) → Yellow (70-90%) → Red (> 90%)
- Escalation path shows: Current office → Next office (if SLA expires)

**API Test:**
```bash
curl -X GET http://localhost:8000/api/v1/cases/{case_id}/next-steps \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. **Personal Diary**

**Test Flow:**
1. Login to app
2. Tap "मेरी डायरी" (My Diary) from navigation
3. Create new note:
   - Add title and content
   - Toggle "शिकायत में बदला जा सकता है" (Can convert to grievance)
   - Set reminder (7/14/30 days)
   - Save note
4. View note from list
5. Try converting to grievance
6. See note now shows "शिकायत बन चुका है" badge

**Expected Results:**
- Notes are 100% private (not visible to anyone else)
- Reminders show upcoming dates with 🔔 icon
- Convertible notes have 💡 indicator
- Converting creates a public grievance case

**API Tests:**
```bash
# Create note
curl -X POST http://localhost:8000/api/v1/personal-diary \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "School admission forms",
    "content": "Need to submit forms by end of month",
    "is_convertible": true,
    "reminder_date": "2025-11-10T10:00:00Z"
  }'

# Get notes
curl -X GET http://localhost:8000/api/v1/personal-diary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Convert to grievance
curl -X POST http://localhost:8000/api/v1/personal-diary/{note_id}/convert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "additional_info": {
      "location_text": "Raipur",
      "issue_type": "education"
    }
  }'
```

## 🔍 Testing Checklist

### Triage Classification
- [ ] Grievance detection works (civic issues)
- [ ] Community detection works (events, organizing)
- [ ] Personal detection works (reminders, private notes)
- [ ] Confidence scoring is reasonable (0.0-1.0)
- [ ] Manual override works (can select different intent)
- [ ] Hindi/English/Chhattisgarhi code-mix handled correctly

### Next Steps Display
- [ ] Case reference number displayed correctly
- [ ] SLA clock shows correct time remaining
- [ ] Clock updates every minute
- [ ] Responsible entity shown with contact info
- [ ] Expected actions list populated
- [ ] Timeline shows case history
- [ ] Escalation path displays next office

### Personal Diary
- [ ] Can create new notes
- [ ] Notes list displays correctly
- [ ] Filter by reminders works
- [ ] Filter by convertible works
- [ ] Note detail shows all info
- [ ] Can delete notes (with confirmation)
- [ ] Can convert to grievance
- [ ] Converted notes show badge
- [ ] Privacy enforced (only user can see their notes)

### Mobile UI
- [ ] Hindi text renders correctly
- [ ] Animations smooth (fade-ins, transitions)
- [ ] Touch targets accessible (44x44 minimum)
- [ ] Loading states show properly
- [ ] Error messages displayed in Hindi + English
- [ ] Back navigation works throughout

### Backend APIs
- [ ] Triage endpoint returns within 2-3 seconds
- [ ] Next steps endpoint loads quickly
- [ ] Personal diary CRUD operations work
- [ ] Privacy middleware enforces user isolation
- [ ] Error handling provides helpful messages
- [ ] Logs show useful debugging info

## 🐛 Common Issues

### "Claude API Error"
- Check `ANTHROPIC_API_KEY` is set in `.env`
- Verify key has sufficient credits
- Check network connectivity

### "Database Connection Error"
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Run migrations: `alembic upgrade head`

### "Network Request Failed" (Mobile)
- Update `API_URL` to your machine's local IP (not localhost)
- Ensure backend is running on `0.0.0.0:8000`
- Check firewall allows connections
- Both phone and computer on same WiFi

### Triage Not Working
- Check backend logs for Claude API errors
- Verify transcript text is not empty
- Check confidence scoring logic
- Test with different sample texts

### Personal Diary Notes Not Showing
- Check user authentication token
- Verify privacy middleware allows access
- Check database has personal_notes table
- Test API endpoint directly with curl

## 📊 Performance Expectations

- **Triage Classification**: 2-3 seconds (Claude API call)
- **Next Steps Load**: < 500ms (database query)
- **Personal Diary Load**: < 300ms (database query)
- **SLA Clock Updates**: Every 60 seconds
- **Mobile Screen Transitions**: < 300ms

## 📝 Testing Notes

**Voice Input:**
- Try various complaint types (water, roads, electricity, etc.)
- Test code-mixed language: "हमारे area में problem है"
- Test vague inputs to see low confidence handling

**Edge Cases:**
- Empty transcript
- Very long transcript (> 5000 chars)
- Special characters in notes
- Reminders in past dates
- Converting already-converted notes

## 🎯 Success Criteria

The app is ready for user testing when:
1. ✅ All 3 intents classify correctly (>80% accuracy on test set)
2. ✅ SLA clock updates in real-time
3. ✅ Personal notes are fully private (no data leaks)
4. ✅ Hindi UI displays properly on all screens
5. ✅ Error handling graceful (no crashes)
6. ✅ Navigation flows smoothly between screens

## 📞 Support

If you encounter issues:
1. Check backend logs: `tail -f logs/app.log`
2. Check mobile console: Look for red error messages
3. Test API endpoints directly with curl
4. Verify all environment variables are set

Happy testing! 🚀
