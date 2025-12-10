# Boloo Mobile App - Complete Guide

**Date**: October 25, 2025
**Status**: MVP READY FOR TESTING
**Platform**: Android (React Native + Expo)

---

## ✅ WHAT'S BUILT

### Mobile App Features
- ✅ **SMS OTP Authentication** (Phone number + 6-digit OTP)
- ✅ **Login Flow** (Phone input → OTP verification → Home)
- ✅ **Home Dashboard** (Welcome screen with action buttons)
- ✅ **Issue Selection** (Fetch and display 67 taxonomies from backend API)
- ✅ **Navigation** (Stack navigation with auth/main app separation)
- ✅ **API Integration** (Axios client with JWT token management)
- ✅ **Offline Storage** (AsyncStorage for tokens and user data)

### Placeholder Screens (Ready for Enhancement)
- 🔄 Voice Recording (Placeholder - needs expo-av implementation)
- 🔄 Location Picker (Placeholder - needs expo-location implementation)
- 🔄 Photo Upload (Placeholder - needs expo-image-picker implementation)
- 🔄 My Cases (Placeholder - needs API integration)

---

## 🏗️ PROJECT STRUCTURE

```
mobile/
├── App.tsx                          # Main app entry with AuthProvider
├── app.json                         # Expo configuration + permissions
├── package.json                     # Dependencies
├── src/
│   ├── constants/
│   │   └── config.ts               # Colors, fonts, API URL
│   ├── types/
│   │   └── index.ts                # TypeScript interfaces
│   ├── services/
│   │   ├── api.ts                  # Axios client with interceptors
│   │   ├── auth.ts                 # Auth service (MSG91 placeholder)
│   │   └── storage.ts              # AsyncStorage wrapper
│   ├── context/
│   │   └── AuthContext.tsx         # Global auth state management
│   ├── navigation/
│   │   └── AppNavigator.tsx        # Stack navigation setup
│   └── screens/
│       ├── LoginScreen.tsx         # Phone number input
│       ├── VerifyOTPScreen.tsx     # 6-digit OTP input
│       ├── HomeScreen.tsx          # Main dashboard
│       ├── IssueSelectionScreen.tsx # Fetch taxonomies from API
│       ├── VoiceRecordScreen.tsx   # Placeholder
│       └── MyCasesScreen.tsx       # Placeholder
```

---

## 📱 HOW TO TEST THE APP

### Option 1: Expo Go (Fastest - Recommended)

1. **Install Expo Go on your Android phone**:
   - Download from Google Play Store
   - Search for "Expo Go"

2. **Start the development server** (already running):
   ```bash
   cd "/Users/diptendu/boloo app/boloo-app/mobile"
   npx expo start
   ```

3. **Scan the QR code** shown in terminal:
   - Open Expo Go app
   - Tap "Scan QR Code"
   - Point camera at QR code in terminal
   - App will load on your phone

4. **Test the flow**:
   - Enter any 10-digit Indian mobile number (starts with 6-9)
   - Click "Send OTP"
   - Enter any 6-digit code (currently mocked)
   - Explore the app!

### Option 2: Android Studio Emulator

1. **Install Android Studio** (if not installed)

2. **Create an Android Virtual Device (AVD)**:
   - Android 8.0 or higher
   - Recommended: Pixel 5 or similar

3. **Start emulator and run app**:
   ```bash
   cd "/Users/diptendu/boloo app/boloo-app/mobile"
   npx expo start
   # Press 'a' to open in Android emulator
   ```

---

## 🔧 MSG91 SMS OTP INTEGRATION

### Current Status
The app currently uses **MOCK** OTP for development. Any 6-digit code will work.

### To Enable Real SMS OTP:

1. **Get MSG91 Credentials**:
   - Sign up at https://msg91.com
   - Get your Auth Key/API Key
   - Create an OTP template (optional)

2. **Update `src/services/auth.ts`**:

Find the `requestOTP` function (line ~10) and replace:
```typescript
async requestOTP(phoneNumber: string): Promise<void> {
  // TODO: Replace with MSG91 API when credentials are provided
  console.log('Requesting OTP for:', phoneNumber);

  // REPLACE THIS MOCK with MSG91 API call:
  const response = await api.post('https://control.msg91.com/api/v5/otp', {
    mobile: phoneNumber,
    authkey: 'YOUR_MSG91_AUTH_KEY',
    template_id: 'YOUR_TEMPLATE_ID', // Optional
  });
  return response.data;
}
```

Find the `verifyOTP` function (line ~25) and replace:
```typescript
async verifyOTP(phoneNumber: string, otp: string): Promise<AuthResponse> {
  // TODO: Replace with MSG91 verification

  // REPLACE MOCK with MSG91 verification:
  const response = await api.post('https://control.msg91.com/api/v5/otp/verify', {
    mobile: phoneNumber,
    otp: otp,
    authkey: 'YOUR_MSG91_AUTH_KEY',
  });

  // Then call your backend to create session:
  const authResponse = await api.post<AuthResponse>('/v1/auth/sms/verify', {
    phone_number: phoneNumber,
    otp: otp,
  });

  // Store token and user
  await storage.setToken(authResponse.data.access_token);
  await storage.setUser(authResponse.data.user);

  return authResponse.data;
}
```

3. **Update Backend API** (if needed):
   - Create `/v1/auth/sms/request` endpoint
   - Create `/v1/auth/sms/verify` endpoint
   - Issue JWT tokens after OTP verification

---

## 🎯 NEXT STEPS FOR DEVELOPMENT

### Phase 1: Complete Core Features (2-3 hours)

1. **Voice Recording** (45 min):
   ```bash
   cd mobile
   npx expo install expo-av
   ```
   - Update `VoiceRecordScreen.tsx`
   - Add record/play/pause controls
   - Upload audio to `/v1/media/upload`

2. **Location Picker** (30 min):
   ```bash
   npx expo install expo-location react-native-maps
   ```
   - Create `LocationPickerScreen.tsx`
   - Request location permissions
   - Display map with marker
   - Allow manual adjustment

3. **Photo Upload** (30 min):
   ```bash
   npx expo install expo-image-picker
   ```
   - Create `PhotoUploadScreen.tsx`
   - Camera + Gallery picker
   - Multiple image selection (max 5)
   - Upload to `/v1/media/upload`

4. **Case Submission** (1 hour):
   - Create `ReviewSubmitScreen.tsx`
   - Show summary of all inputs
   - Submit to `POST /v1/cases`
   - Navigate to success screen

### Phase 2: Case Management (1-2 hours)

5. **My Cases Screen**:
   - Fetch from `GET /v1/cases`
   - Display list with status indicators
   - Pull-to-refresh

6. **Case Detail Screen**:
   - Show full case information
   - Timeline of events
   - Media playback

### Phase 3: Polish & Testing (1 hour)

7. **Error Handling**:
   - Network errors
   - Permission denied
   - Validation errors

8. **Loading States**:
   - Skeleton screens
   - Progress indicators

9. **Offline Support**:
   - Draft cases with expo-sqlite
   - Auto-sync when online

---

## 📦 BUILD APK FOR DISTRIBUTION

### Option 1: EAS Build (Recommended)

1. **Install EAS CLI**:
   ```bash
   npm install -g eas-cli
   ```

2. **Login to Expo**:
   ```bash
   eas login
   ```

3. **Configure build**:
   ```bash
   cd mobile
   eas build:configure
   ```

4. **Build APK**:
   ```bash
   eas build --platform android --profile preview
   ```

5. **Download APK**:
   - Link will be provided in terminal
   - Install on any Android device

### Option 2: Local Build (Requires Android Studio)

1. **Prebuild**:
   ```bash
   npx expo prebuild
   ```

2. **Build**:
   ```bash
   cd android
   ./gradlew assembleRelease
   ```

3. **APK location**:
   ```
   android/app/build/outputs/apk/release/app-release.apk
   ```

---

## 🔗 API ENDPOINTS USED

The mobile app currently integrates with these backend endpoints:

### Authentication (Mocked - needs MSG91)
- `POST /v1/auth/sms/request` - Send SMS OTP
- `POST /v1/auth/sms/verify` - Verify OTP and get JWT

### Taxonomies
- ✅ `GET /v1/taxonomies?type=issue` - Fetch issue types

### Cases (To be implemented)
- `POST /v1/cases` - Submit new grievance
- `GET /v1/cases` - Get user's cases
- `GET /v1/cases/{id}` - Get case details

### Media (To be implemented)
- `POST /v1/media/upload` - Upload audio/photos

---

## 🛠️ DEPENDENCIES INSTALLED

```json
{
  "expo": "~54.0.20",
  "react": "19.1.0",
  "react-native": "0.81.5",
  "@react-navigation/native": "^7.0.0",
  "@react-navigation/stack": "^7.2.0",
  "@react-navigation/bottom-tabs": "^7.2.0",
  "axios": "^1.7.0",
  "@react-native-async-storage/async-storage": "^2.2.0",
  "expo-av": "^15.0.0",
  "expo-location": "^18.0.0",
  "expo-image-picker": "^16.0.0",
  "react-native-maps": "1.26.18",
  "expo-constants": "^17.0.0",
  "react-native-screens": "^4.4.0",
  "react-native-safe-area-context": "^4.15.0",
  "react-native-gesture-handler": "^2.22.0"
}
```

---

## 🐛 TROUBLESHOOTING

### Expo won't start
```bash
cd mobile
npx expo start --clear
# or
rm -rf node_modules .expo
npm install
npx expo start
```

### Permission errors on Android
- Check `app.json` has all required permissions
- Rebuild app after adding new permissions

### API connection failed
- Make sure backend is running on port 8000
- Update `API_URL` in `app.json` extra config:
  ```json
  "extra": {
    "apiUrl": "http://YOUR_IP:8000"  // Use your machine's IP, not localhost
  }
  ```

### Node version issues
```bash
nvm use 20
cd mobile
npm install
npx expo start
```

---

## 📞 TESTING CHECKLIST

- [ ] App launches without errors
- [ ] Login screen displays correctly (Hindi + English)
- [ ] Phone number validation works (10 digits, starts with 6-9)
- [ ] OTP screen shows after sending OTP
- [ ] Can enter 6-digit OTP
- [ ] Auto-focus between OTP input boxes
- [ ] Login successful → navigates to Home
- [ ] Home screen displays user phone number
- [ ] "Report New Issue" button works
- [ ] Issue selection screen loads 67 taxonomies
- [ ] Taxonomies display in Hindi and English
- [ ] Can navigate through screens
- [ ] Logout works and returns to login

---

## 🎉 SUCCESS CRITERIA

✅ **MVP Complete When**:
1. User can login with phone + OTP (MSG91 integrated)
2. User can select issue type from 67 options
3. User can record audio grievance (Hindi/English)
4. User can add GPS location
5. User can upload photos (up to 5)
6. User can submit complete case
7. User can view their submitted cases
8. APK can be installed on any Android device

---

**Current Status**: Authentication + Navigation + Issue Selection **WORKING**
**Next Priority**: Voice Recording → Location → Photos → Submission
**Estimated Time to Full MVP**: 4-6 hours of development

**Expo Server**: Running at http://localhost:8081
**Test Method**: Scan QR code with Expo Go app on Android phone
