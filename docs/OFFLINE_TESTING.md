# 🎉 Offline Testing Guide - Boloo App

**The app is now fully testable without backend!**

## ✅ What Works Offline:

### 1. **Authentication** ✅
- Login with any 10-digit phone number
- OTP: `123456` for any number
- Session persists across app restarts
- No backend required!

### 2. **Issue Selection** ✅
- Shows 5 dummy issue categories
- Water Supply, Road, Electricity, Sanitation, Health
- All in Hindi + English

### 3. **Voice Recording** ✅
- **"🧪 Test Without Recording"** button
- Choose from 2 test transcripts:
  - Water complaint (Hindi)
  - Road complaint (Hindi)
- Skips actual audio recording

### 4. **Triage Classification** ✅
- Smart keyword-based classification
- Detects: Grievance, Community, or Personal
- Shows confidence percentage
- Displays reasoning (e.g., "Detected civic infrastructure keywords")

### 5. **Case Submission** ✅
- Saves case locally to AsyncStorage
- Generates case reference number (BOL12345678)
- No backend API call needed

### 6. **"What Happens Next" Screen** ✅
- Shows dummy SLA info (72h countdown)
- Responsible entity: ग्राम पंचायत
- Expected actions timeline
- Escalation path
- Full Hindi + English

---

## 🚀 How to Test:

### **Step 1: Start the App**
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npx expo start
```
Scan QR code with Expo Go app

### **Step 2: Login**
1. Enter any phone: `9876543210`
2. Click "Send OTP"
3. Enter OTP: `1-2-3-4-5-6`
4. Click "Verify & Continue"
5. ✅ You're logged in!

### **Step 3: Report Complaint**
1. Click "📢 Report New Issue"
2. Select any issue type (e.g., "जल आपूर्ति / Water Supply")
3. Click **"🧪 Test Without Recording"** button
4. Choose "Test Water Complaint" or "Test Road Complaint"

### **Step 4: See Classification**
- Alert shows:
  ```
  🎯 Classification Result
  Intent: 📢 Grievance (शिकायत)
  Confidence: 88%

  🧪 TESTING MODE: Detected civic infrastructure keywords. Classified as grievance.
  ```
- Click **"Submit Case"**

### **Step 5: View Success Screen**
- See ✅ "शिकायत दर्ज हो गई!" (Complaint registered!)
- Case reference number: BOL12345678
- **SLA Clock** showing 72h countdown
- Responsible entity card
- Expected actions list
- Escalation path

---

## 🎯 Test Scenarios:

### **Scenario 1: Water Complaint**
**Test Transcript:**
```
हमारे क्षेत्र में पानी की समस्या है 2 हफ्ते से। कृपया जल्दी ध्यान दें।
```
**Expected Result:**
- Intent: 📢 Grievance
- Confidence: 88%
- Keywords detected: "पानी", "समस्या"

### **Scenario 2: Road Complaint**
**Test Transcript:**
```
सड़क बहुत खराब हो गई है। गड्ढे बहुत हैं। बारिश में पानी भर जाता है।
```
**Expected Result:**
- Intent: 📢 Grievance
- Confidence: 88%
- Keywords detected: "सड़क", "समस्या"

### **Scenario 3: Multiple Submissions**
- Submit 3-4 test complaints
- Each gets unique case reference
- All saved locally
- Can view on "My Cases" screen (if implemented)

---

## 🔍 What You're Testing:

### **UI/UX Flow** ✅
- Login screen
- Issue selection screen
- Voice recording screen with test mode
- Classification alert
- Success screen with next steps

### **Triage Classification** ✅
- Hindi keyword detection
- Confidence scoring
- Smart categorization (grievance vs community vs personal)

### **Data Persistence** ✅
- Login session saved
- Cases saved locally
- Survives app restart

### **Hindi Support** ✅
- Hindi text displays correctly
- Mixed Hindi/English UI
- Clear bilingual labels

---

## 🧪 Testing Mode Indicators:

Look for these throughout the app:

1. **Login Screen**:
   - "🧪 Testing Mode - Use OTP: 123456" banner

2. **Voice Record**:
   - "🧪 Test Without Recording" button

3. **Classification**:
   - "🧪 TESTING MODE: Detected..." in reasoning

4. **Next Steps**:
   - "🧪 TESTING MODE: यह डमी डेटा है" in guidance

5. **Console Logs**:
   - `[TESTING MODE]` prefix on all dummy operations

---

## 📊 Expected Console Output:

```
LOG  TESTING MODE: Login successful! {...}
LOG  [IssueSelection] TESTING MODE: Using dummy issues
LOG  [VoiceRecord] Test transcript: हमारे क्षेत्र में पानी...
LOG  [TriageService] TESTING MODE: Using dummy classification
LOG  [VoiceRecord] Classification result: {...}
LOG  [VoiceRecord] Case saved offline: {...}
LOG  [NextStepsService] TESTING MODE: Using dummy next steps
```

---

## ✨ Features You Can Test:

### **Working:**
- ✅ Login/logout
- ✅ Issue selection
- ✅ Complaint submission (with test transcripts)
- ✅ Triage classification
- ✅ SLA tracking display
- ✅ Next steps information
- ✅ Case timeline
- ✅ Escalation path
- ✅ Session persistence

### **Not Working (Backend Required):**
- ❌ Real voice recording + transcription
- ❌ Fetching existing cases from server
- ❌ Real-time case updates
- ❌ Actual case processing by officials

---

## 🎉 Success Criteria:

The conversational reporting flow is working if:

1. ✅ You can login with dummy auth
2. ✅ Select an issue type
3. ✅ Use test mode to skip recording
4. ✅ See classification result with confidence
5. ✅ Submit case successfully
6. ✅ View "What Happens Next" screen with:
   - SLA countdown
   - Responsible entity
   - Expected actions
   - Timeline

---

## 🐛 Troubleshooting:

### **"Network Error" on Home Screen**
- **Expected!** Home tries to fetch cases from backend
- Ignore this - click "Report New Issue" to test

### **Can't Login**
- Make sure you entered exactly `123456` as OTP
- Check console for "TESTING MODE: Login successful!"

### **No Classification Shown**
- Check console for errors
- Try different test transcript option

### **App Crashes**
- Check Expo console for error details
- Try restarting app: `r` in terminal

---

## 📝 What to Look For:

### **Good Things:**
- 🟢 Smooth navigation flow
- 🟢 Hindi text renders clearly
- 🟢 Classification makes sense
- 🟢 UI is clean and professional
- 🟢 Loading states show properly

### **Issues to Report:**
- 🔴 UI elements overlapping
- 🔴 Hindi text showing boxes □□
- 🔴 Navigation gets stuck
- 🔴 Classification seems random
- 🔴 Crashes or freezes

---

## 🎯 Next Steps:

Once you've tested this offline flow:

1. **Give Feedback** on:
   - Is the flow intuitive?
   - Does classification make sense?
   - Is Hindi readable?
   - Any UI improvements?

2. **Backend Integration** (later):
   - Connect to real SMS/OTP service
   - Real voice transcription API
   - Claude API for triage
   - Database for case storage

3. **Additional Features** (later):
   - Real voice recording
   - Photo upload
   - Location picker
   - Case tracking

---

## 🚀 You're Ready!

The conversational capability reporting is fully testable offline now:

```
Login → Select Issue → Test Transcript → Classification → Submit → Success Screen
```

**Everything works without backend!** 🎉

Start testing and let me know what you think!
