# Boloo Mobile App - Android Configuration Summary

## Configuration Complete

All configurations have been updated for **Android-only** deployment.

## What Changed

### 1. app.json
- **Removed**: All iOS-specific configurations
- **Added**: `"platforms": ["android"]` to explicitly set Android-only
- **Updated**: Backend API URL from `boloo-backend-app` to `boloo-backend-api`

### 2. eas.json
- **Removed**: All iOS build profiles from all build configurations
- **Removed**: iOS submission configuration
- **Kept**: 4 Android build profiles:
  - `development` - For internal testing
  - `preview` - For pre-release testing
  - `production` - APK for production
  - `production-aab` - AAB for Google Play Store

### 3. .env.production
- **Updated**: API URL to `https://boloo-backend-api.azurewebsites.net`
- **Confirmed**: Azure backend API is running and accessible

### 4. package.json
- **Removed**: All iOS-specific scripts (`ios`, `build:ios`, `submit:ios`)
- **Added**: Android-specific testing and build scripts
- **Enhanced**: Better script organization for Android development

## Android Build Profiles

### Development
```bash
npm run build:android:dev
```
- Creates debug APK for development
- Enables development client
- Internal distribution

### Preview
```bash
npm run build:android:preview
```
- Creates release APK for testing
- Internal distribution
- Test before production release

### Production (APK)
```bash
npm run build:android
```
- Creates production APK
- For direct distribution or sideloading
- Release configuration

### Production (AAB)
```bash
npm run build:android:aab
```
- Creates Android App Bundle
- **Recommended for Google Play Store**
- Optimized app size

## Backend Configuration

### Azure Resource Group
- **Name**: `boloo-production-rg`
- **Location**: South India
- **Status**: Active

### Backend API
- **Name**: `boloo-backend-api`
- **URL**: `https://boloo-backend-api.azurewebsites.net`
- **Status**: Running
- **Region**: South India

## Updated Scripts

### Build Scripts
```bash
npm run build:android              # Production APK
npm run build:android:aab          # Production AAB (recommended)
npm run build:android:preview      # Preview APK
npm run build:android:dev          # Development build
```

### Testing Scripts
```bash
npm start                          # Start Expo dev server
npm run android                    # Run on Android device/emulator
npm run test:android               # Test Android app
npm run clean:android              # Clean Android build cache
```

### Deployment Scripts
```bash
npm run submit:android             # Submit to Play Store
npm run submit:android:preview     # Submit preview to Play Store
npm run update                     # OTA update
```

## App Details

### Package Information
- **Package Name**: `com.boloo.citizen`
- **App Name**: `Boloo - Citizen Reporting`
- **Version**: `1.0.0`
- **Version Code**: `1`
- **Platform**: Android only

### Android Features
- **JavaScript Engine**: Hermes (enabled)
- **Edge-to-Edge**: Enabled
- **Predictive Back**: Disabled
- **Adaptive Icon**: Blue background (#2563eb)

### Required Permissions
- Camera (for photo evidence)
- Audio recording (for audio evidence)
- Location (for geotagging)
- Storage (for saving files)

## Next Steps

### 1. First Build
```bash
# Login to Expo
eas login

# Configure EAS (if needed)
eas build:configure

# Create preview build for testing
npm run build:android:preview
```

### 2. Testing
- Download APK from EAS dashboard
- Install on Android device
- Test all features thoroughly
- Verify API connectivity

### 3. Production Release
```bash
# Build AAB for Play Store
npm run build:android:aab

# Submit to Play Store
npm run submit:android
```

### 4. Google Play Console Setup
- Create app in Play Console
- Configure app details
- Set up service account for automated submissions
- Upload AAB file

## Verification Checklist

- [x] iOS configurations removed from app.json
- [x] iOS build profiles removed from eas.json
- [x] Correct backend API URL configured
- [x] Android-only platform specified
- [x] Package.json scripts updated
- [x] Build profiles configured correctly
- [x] Android deployment documentation created
- [ ] First preview build created (next step)
- [ ] APK tested on device (next step)
- [ ] Google Play Console configured (next step)
- [ ] Production build submitted (next step)

## Important Files

### Configuration Files
```
/mobile/app.json                    # Expo app configuration
/mobile/eas.json                    # EAS Build configuration
/mobile/.env.production             # Production environment variables
/mobile/package.json                # NPM scripts and dependencies
```

### Documentation
```
/mobile/docs/ANDROID_DEPLOYMENT.md     # Complete deployment guide
/mobile/docs/CONFIGURATION_SUMMARY.md  # This file
```

## Troubleshooting

### If Build Fails
1. Check EAS build logs at https://expo.dev
2. Verify dependencies are compatible
3. Run `npm run clean:android` and retry

### If API Doesn't Connect
1. Verify backend is running: `az webapp show --name boloo-backend-api --resource-group boloo-production-rg`
2. Check API URL in app.json and .env.production
3. Test API endpoint directly

### If Submission Fails
1. Verify service account key is present
2. Check Google Play Console permissions
3. Ensure version code is incremented

## Resources

- **Expo Documentation**: https://docs.expo.dev
- **EAS Build Guide**: https://docs.expo.dev/build/introduction/
- **Android Deployment**: See ANDROID_DEPLOYMENT.md
- **Google Play Console**: https://play.google.com/console

---

**Configuration Date**: 2025-01-22
**Status**: Ready for EAS Build
**Platform**: Android Only
**Backend**: boloo-backend-api.azurewebsites.net
