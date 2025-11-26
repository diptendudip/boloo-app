# Boloo Android App

**Citizen Grievance Reporting Mobile Application**

Built with Expo React Native for Android devices.

---

## Features Implemented

### ✅ Phase 1 MVP Features

1. **Email OTP Authentication**
   - Secure email-based login
   - 6-digit OTP verification
   - Integrated with backend API
   - Auto-creates user on first login

2. **Voice Recording**
   - Record grievances using expo-av
   - High-quality audio recording
   - Play/pause/delete controls
   - Maximum duration: 5 minutes
   - Microphone permission handling

3. **Bilingual Support**
   - Hindi (हिंदी) and English toggle
   - Persistent language preference
   - Complete UI translations
   - Context-based language system

4. **Navigation**
   - React Navigation with stack navigator
   - Authentication flow
   - Case submission flow
   - Smooth transitions

---

## Tech Stack

- **Framework**: Expo SDK ~54.0
- **Language**: TypeScript
- **UI**: React Native
- **Navigation**: React Navigation v7
- **State Management**: React Context API
- **Storage**: AsyncStorage
- **Audio**: expo-av
- **Permissions**: expo-location, expo-image-picker
- **HTTP Client**: Axios

---

## Project Structure

```
mobile/
├── src/
│   ├── components/       # Reusable UI components
│   │   └── LanguageToggle.tsx
│   ├── context/          # React Context providers
│   │   ├── AuthContext.tsx
│   │   └── LanguageContext.tsx
│   ├── screens/          # App screens
│   │   ├── LoginScreen.tsx
│   │   ├── VerifyOTPScreen.tsx
│   │   ├── HomeScreen.tsx
│   │   ├── VoiceRecordScreen.tsx
│   │   ├── IssueSelectionScreen.tsx
│   │   └── MyCasesScreen.tsx
│   ├── services/         # API and business logic
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── storage.ts
│   ├── navigation/       # Navigation configuration
│   │   └── AppNavigator.tsx
│   ├── constants/        # App constants
│   │   └── config.ts
│   └── types/            # TypeScript types
│       └── index.ts
├── assets/               # Images, icons, fonts
├── App.tsx               # Root component
├── app.json              # Expo configuration
└── package.json          # Dependencies
```

---

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm/yarn
- Expo CLI: `npm install -g expo-cli`
- Android Studio (for Android emulator) OR physical Android device
- Backend API running at `http://localhost:8000`

### Installation

1. **Navigate to mobile directory**:
   ```bash
   cd "/Users/diptendu/boloo app/boloo-app/mobile"
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure API URL** (if different from localhost):
   Edit `app.json`:
   ```json
   "extra": {
     "apiUrl": "http://YOUR_BACKEND_IP:8000"
   }
   ```

4. **Start Expo development server**:
   ```bash
   npm start
   ```

5. **Run on Android**:
   - Press `a` to open in Android emulator
   - OR scan QR code with Expo Go app on physical device

---

## Usage

### 1. Login with Email OTP

- Enter your email address
- Tap "Send OTP" (or "OTP भेजें" in Hindi)
- Check your email for 6-digit code
- Enter OTP to verify and login

### 2. Change Language

- Tap the EN/हिं toggle in the top right
- All UI text updates immediately
- Preference is saved for future sessions

### 3. Record Grievance

- Navigate to voice recording screen
- Tap the red button to start recording
- Describe your issue in Hindi or English
- Tap again to stop recording
- Play to review or delete to re-record
- Tap "Continue" to proceed

---

## Configuration

### App Settings

Edit `app.json` to configure:

- App name and description
- Bundle identifier: `com.boloo.citizen`
- Permissions (camera, microphone, location)
- Icons and splash screen
- API URL

### Backend API

API endpoints used:

- `POST /v1/auth/otp/request` - Request OTP
- `POST /v1/auth/otp/verify` - Verify OTP and get token
- (More endpoints to be added for case submission)

### Constants

Edit `src/constants/config.ts`:

```typescript
export const APP_CONFIG = {
  maxAudioDuration: 300,  // 5 minutes
  maxPhotos: 5,
  maxPhotoSize: 5 * 1024 * 1024,  // 5MB
};
```

---

## Dependencies

### Core Dependencies

```json
{
  "@react-navigation/native": "^7.1.18",
  "@react-navigation/stack": "^7.5.0",
  "expo": "~54.0.20",
  "expo-av": "^16.0.7",
  "expo-location": "^19.0.7",
  "expo-image-picker": "^17.0.8",
  "react-native": "0.81.5",
  "axios": "^1.12.2",
  "@react-native-async-storage/async-storage": "^2.2.0"
}
```

### Permission Requirements

Configured in `app.json`:

- **RECORD_AUDIO**: Voice recording
- **CAMERA**: Photo capture
- **ACCESS_FINE_LOCATION**: GPS location
- **READ/WRITE_EXTERNAL_STORAGE**: File access

---

## Development

### Running the App

```bash
# Start development server
npm start

# Run on Android emulator
npm run android

# Run on iOS simulator (macOS only)
npm run ios

# Run on web
npm run web
```

### Building for Production

```bash
# Build Android APK
expo build:android

# Build Android App Bundle (AAB) for Play Store
expo build:android -t app-bundle

# Build iOS (requires Apple Developer account)
expo build:ios
```

### Environment Variables

Create `.env` file:

```
API_URL=http://localhost:8000
```

---

## Language System

### Adding New Translations

Edit `src/context/LanguageContext.tsx`:

```typescript
const translations: Record<Language, Record<string, string>> = {
  en: {
    'key.name': 'English Text',
  },
  hi: {
    'key.name': 'हिंदी पाठ',
  },
};
```

### Using Translations

```typescript
import { useLanguage } from '../context/LanguageContext';

function MyComponent() {
  const { t } = useLanguage();
  return <Text>{t('key.name')}</Text>;
}
```

### Language Toggle

```typescript
import LanguageToggle from '../components/LanguageToggle';

// Compact variant (for headers)
<LanguageToggle variant="compact" />

// Full variant (for settings)
<LanguageToggle variant="full" />
```

---

## Authentication Flow

1. User enters email on LoginScreen
2. Backend sends OTP to email
3. User enters OTP on VerifyOTPScreen
4. Backend validates OTP and returns JWT token
5. Token stored in AsyncStorage
6. User navigated to HomeScreen
7. All API calls include token in Authorization header

---

## Voice Recording Flow

1. VoiceRecordScreen requests microphone permission
2. User taps button to start recording
3. Timer shows duration (max 5 minutes)
4. User taps again to stop
5. Playback controls appear
6. User can play, delete, or continue
7. Audio URI passed to next screen

---

## API Integration

### Making Authenticated Requests

```typescript
import api from '../services/api';

// Token automatically added to headers
const response = await api.get('/v1/cases');
```

### Auth Service

```typescript
import { authService } from '../services/auth';

// Request OTP
await authService.requestOTP('user@example.com');

// Verify OTP
const authResponse = await authService.verifyOTP('user@example.com', '123456');

// Logout
await authService.logout();
```

---

## Known Issues

1. **Timer cleanup**: Recording timer needs cleanup on unmount (implemented)
2. **Network errors**: Need better error handling for offline mode
3. **Audio playback**: Sound cleanup on component unmount (implemented)

---

## Pending Features (Phase 1)

- [ ] Location picker screen
- [ ] Photo upload screen
- [ ] Case submission review
- [ ] My Cases list
- [ ] Case detail view
- [ ] Offline mode with SQLite
- [ ] Background sync

---

## Testing

### Manual Testing Checklist

- [ ] Email OTP flow works end-to-end
- [ ] Language toggle persists across app restarts
- [ ] Voice recording works on physical device
- [ ] Voice playback works correctly
- [ ] Navigation flows work smoothly
- [ ] Permissions are requested correctly
- [ ] Error states display properly
- [ ] Backend API integration works

### Test Devices

**Recommended Android Devices** (for Phase 3 testing):
- Samsung Galaxy series
- Xiaomi Redmi series
- Realme series
- OnePlus series
- Vivo series

**Minimum Android Version**: Android 8.0 (API level 26)

---

## Troubleshooting

### Common Issues

**App won't start**:
```bash
rm -rf node_modules package-lock.json
npm install
npx expo start --clear
```

**Metro bundler issues**:
```bash
npx expo start --clear
```

**Can't connect to backend**:
- Ensure backend is running at `http://localhost:8000`
- For physical device, use your computer's IP address
- Check firewall settings

**Permission errors**:
- Ensure `app.json` has all required permissions
- Reinstall app after permission changes

**Audio recording not working**:
- Test on physical device (emulator has limited audio support)
- Check microphone permissions in device settings
- Ensure expo-av is properly installed

---

## Performance Optimization

- Images optimized and lazy-loaded
- Navigation uses stack navigator for memory efficiency
- AsyncStorage for persistent data
- Minimal re-renders with React.memo where needed

---

## Security

- JWT tokens stored securely in AsyncStorage
- No sensitive data in plain text
- HTTPS enforced for production
- Input validation on all forms
- OTP expires after 5 minutes

---

## Future Enhancements

1. **Offline Mode**: SQLite for local storage
2. **Background Sync**: Upload when network available
3. **Push Notifications**: Case status updates
4. **Biometric Auth**: Fingerprint/Face ID
5. **Dark Mode**: System theme support
6. **Accessibility**: Screen reader support

---

## Contributing

When adding new features:

1. Follow existing code structure
2. Add TypeScript types
3. Update translations in both languages
4. Test on physical Android device
5. Update this README

---

## Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)
- [React Navigation](https://reactnavigation.org/)
- [Expo AV Audio](https://docs.expo.dev/versions/latest/sdk/audio/)

---

## License

Proprietary - Chhattisgarh Government

---

## Support

For issues or questions:
- Check existing documentation
- Review error logs
- Contact development team

**Last Updated**: 2025-10-26
**Version**: 1.0.0
**Status**: Phase 1 MVP (60% complete)
