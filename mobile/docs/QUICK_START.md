# Boloo Mobile App - Quick Start Guide

## Android-Only Deployment

This app is configured for **Android deployment only** to Google Play Store.

## Quick Commands

### Development
```bash
# Start development server
npm start

# Run on Android device/emulator
npm run android

# Run on web
npm run web
```

### Building

#### For Testing
```bash
# Preview build (share with testers)
npm run build:android:preview

# Development build
npm run build:android:dev
```

#### For Production
```bash
# APK (for direct distribution)
npm run build:android

# AAB (recommended for Play Store)
npm run build:android:aab
```

### Deployment
```bash
# Submit to Google Play Store
npm run submit:android

# Push OTA update (JS-only changes)
npm run update
```

### Maintenance
```bash
# Clean Android build cache
npm run clean:android

# Run linter
npm run lint
```

## First Time Setup

### 1. Install Dependencies
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npm install
```

### 2. Install EAS CLI
```bash
npm install -g eas-cli
```

### 3. Login to Expo
```bash
eas login
```

### 4. Create First Build
```bash
# Preview build for testing
npm run build:android:preview
```

## Backend Configuration

**Backend API**: `https://boloo-backend-api.azurewebsites.net`

- Resource Group: `boloo-production-rg`
- Location: South India
- Status: Running

## Build Profiles

| Profile | Command | Output | Use Case |
|---------|---------|--------|----------|
| **development** | `npm run build:android:dev` | Debug APK | Development & testing |
| **preview** | `npm run build:android:preview` | Release APK | Pre-release testing |
| **production** | `npm run build:android` | Release APK | Direct distribution |
| **production-aab** | `npm run build:android:aab` | AAB | Play Store (recommended) |

## App Information

- **Package Name**: `com.boloo.citizen`
- **App Name**: Boloo - Citizen Reporting
- **Version**: 1.0.0
- **Platform**: Android only

## Required Permissions

- Camera (photo evidence)
- Audio recording (audio evidence)
- Location (geotagging)
- Storage (file access)

## Testing Workflow

1. **Build preview**: `npm run build:android:preview`
2. **Download APK** from EAS dashboard
3. **Install on device**
4. **Test all features**
5. **Fix issues** and repeat
6. **Build production** when ready

## Production Release Workflow

1. **Update version** in `app.json`
2. **Build AAB**: `npm run build:android:aab`
3. **Test thoroughly**
4. **Submit to Play Store**: `npm run submit:android`

## Monitoring Builds

- Dashboard: https://expo.dev
- Navigate to: Accounts > Projects > boloo-citizen > Builds
- Build time: ~10-20 minutes

## Documentation

- **Complete Guide**: `docs/ANDROID_DEPLOYMENT.md`
- **Configuration**: `docs/CONFIGURATION_SUMMARY.md`
- **This Guide**: `docs/QUICK_START.md`

## Support

- Expo Docs: https://docs.expo.dev
- EAS Build: https://docs.expo.dev/build/introduction/
- Play Console: https://play.google.com/console

## Common Issues

### Build fails
```bash
# Check logs at expo.dev dashboard
# Clean and rebuild
npm run clean:android
npm run build:android:preview
```

### API not connecting
- Verify backend is running in Azure
- Check URL in `app.json` and `.env.production`

### Can't submit to Play Store
- Ensure service account key is configured
- Check `eas.json` submit configuration
- Verify Play Console permissions

---

**Ready to build**: All configurations complete!
**Platform**: Android only
**Backend**: Configured and running
