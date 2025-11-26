# Boloo Mobile App - Android Deployment Guide

## Overview

This guide covers the deployment process for the Boloo mobile app on Android. The app is configured for **Android-only** deployment to Google Play Store.

## Prerequisites

### Required Tools
- Node.js (v18+)
- Expo CLI (`npm install -g expo-cli`)
- EAS CLI (`npm install -g eas-cli`)
- Android Studio (for local testing)
- Expo Account (sign up at https://expo.dev)

### Required Accounts
- Expo Account
- Google Play Console Account
- Azure Account (for backend API access)

## Configuration

### Backend API
- **Resource Group**: `boloo-production-rg`
- **Backend API**: `boloo-backend-api.azurewebsites.net`
- **API URL**: `https://boloo-backend-api.azurewebsites.net`

### App Configuration
- **Package Name**: `com.boloo.citizen`
- **Version**: `1.0.0`
- **Version Code**: `1`
- **Platforms**: Android only

## Build Profiles

### 1. Development Profile
```bash
npm run build:android:dev
```
- **Purpose**: Internal testing and development
- **Distribution**: Internal
- **Output**: Debug APK
- **Development Client**: Enabled

### 2. Preview Profile
```bash
npm run build:android:preview
```
- **Purpose**: Testing before production release
- **Distribution**: Internal
- **Output**: APK
- **Use Case**: Share with testers for feedback

### 3. Production Profile (APK)
```bash
npm run build:android
```
- **Purpose**: Production release (APK format)
- **Distribution**: Google Play Store
- **Output**: Release APK
- **Use Case**: Direct download or sideloading

### 4. Production Profile (AAB)
```bash
npm run build:android:aab
```
- **Purpose**: Production release (Android App Bundle)
- **Distribution**: Google Play Store
- **Output**: AAB (recommended by Google)
- **Use Case**: Google Play Store upload

## Environment Setup

### 1. Install Dependencies
```bash
cd /Users/diptendu/boloo\ app/boloo-app/mobile
npm install
```

### 2. Login to Expo
```bash
eas login
```

### 3. Configure Project
```bash
eas build:configure
```

## Build Process

### Step 1: Choose Build Profile

For testing:
```bash
npm run build:android:preview
```

For production APK:
```bash
npm run build:android
```

For production AAB (recommended):
```bash
npm run build:android:aab
```

### Step 2: Monitor Build
- EAS Build will create a build in the cloud
- Monitor progress at: https://expo.dev/accounts/[your-account]/projects/boloo-citizen/builds
- Build typically takes 10-20 minutes

### Step 3: Download Build
After successful build:
- Download from Expo dashboard
- Or use CLI: `eas build:download --platform android --profile production`

## Google Play Store Submission

### Prerequisites
1. Google Play Console account
2. App created in Play Console
3. Service account JSON key (for automated submission)

### Manual Submission

1. Go to Google Play Console
2. Navigate to your app
3. Create a new release
4. Upload the AAB file
5. Fill in release notes
6. Review and publish

### Automated Submission

```bash
npm run submit:android
```

**Requirements:**
- Service account key at `./playstore-service-account.json`
- Proper permissions in Google Play Console

### Submission Configuration
Edit `eas.json` submit section:
```json
"submit": {
  "production": {
    "android": {
      "serviceAccountKeyPath": "./playstore-service-account.json",
      "track": "internal"
    }
  }
}
```

**Track Options:**
- `internal` - Internal testing
- `alpha` - Alpha testing
- `beta` - Beta testing
- `production` - Production release

## Testing

### Local Android Testing
```bash
npm run android
```

### Testing on Physical Device
1. Install Expo Go app from Play Store
2. Run `npm start`
3. Scan QR code with Expo Go

### Testing APK Build
1. Download APK from EAS Build
2. Install on Android device
3. Test all features thoroughly

## Permissions

The app requires these Android permissions:
- `CAMERA` - For taking photos of grievances
- `RECORD_AUDIO` - For recording audio evidence
- `ACCESS_FINE_LOCATION` - For geotagging reports
- `ACCESS_COARSE_LOCATION` - For geotagging reports
- `READ_EXTERNAL_STORAGE` - For accessing photos
- `WRITE_EXTERNAL_STORAGE` - For saving files

## App Features

### Adaptive Icon
- Foreground: `./assets/adaptive-icon.png`
- Background: `#2563eb` (Blue)

### Splash Screen
- Image: `./assets/splash-icon.png`
- Background: `#2563eb`
- Resize Mode: contain

### JavaScript Engine
- **Hermes**: Enabled for better performance

### Modern Android Features
- Edge-to-edge display enabled
- Predictive back gesture disabled

## Troubleshooting

### Build Fails
1. Check EAS Build logs
2. Verify all dependencies are compatible
3. Check Android-specific configurations in `app.json`

### App Crashes on Launch
1. Check Hermes compatibility
2. Verify all native modules are properly linked
3. Check crash logs in Google Play Console

### Permission Issues
1. Verify permissions in `app.json`
2. Test permission requests on device
3. Check Android manifest merge

### API Connection Issues
1. Verify backend URL: `https://boloo-backend-api.azurewebsites.net`
2. Check network permissions
3. Test API endpoints directly

## Version Management

### Updating Version
1. Update `version` in `app.json`
2. Increment `versionCode` in `app.json` android section
3. Update `APP_VERSION` in `.env.production`
4. Update `BUILD_NUMBER` in `.env.production`

### Version Naming Convention
- **Version**: Semantic versioning (e.g., 1.0.0, 1.1.0)
- **Version Code**: Integer (must increment for each release)

## Over-the-Air (OTA) Updates

### Publishing Updates
```bash
npm run update
```

**Note**: OTA updates work for JavaScript changes only. Native changes require new builds.

## Scripts Reference

| Script | Description |
|--------|-------------|
| `npm start` | Start Expo development server |
| `npm run android` | Start on Android device/emulator |
| `npm run web` | Start web version |
| `npm run build:android` | Build production APK |
| `npm run build:android:aab` | Build production AAB |
| `npm run build:android:preview` | Build preview APK |
| `npm run build:android:dev` | Build development build |
| `npm run submit:android` | Submit to Play Store |
| `npm run update` | Publish OTA update |
| `npm run clean:android` | Clean Android build cache |

## Security Considerations

### API Security
- All API calls use HTTPS
- Backend URL is configurable via environment
- API timeout: 30 seconds

### Code Obfuscation
- Hermes bytecode provides basic obfuscation
- ProGuard/R8 enabled for release builds

### Sensitive Data
- Never commit `.env.production` with real credentials
- Use environment variables for sensitive data
- Service account keys should be securely stored

## Resources

- **Expo Documentation**: https://docs.expo.dev
- **EAS Build**: https://docs.expo.dev/build/introduction/
- **Google Play Console**: https://play.google.com/console
- **React Native**: https://reactnative.dev

## Support

For issues or questions:
1. Check Expo forums: https://forums.expo.dev
2. Review EAS Build logs
3. Check Google Play Console for app-specific issues
4. Contact development team

## Next Steps

1. Complete first build using preview profile
2. Test thoroughly on multiple Android devices
3. Submit to internal testing track
4. Gather feedback and iterate
5. Submit to production when ready

---

**Last Updated**: 2025-01-22
**App Version**: 1.0.0
**Platform**: Android Only
