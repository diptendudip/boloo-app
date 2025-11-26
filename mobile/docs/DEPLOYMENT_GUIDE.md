# Boloo Mobile App - Deployment Guide

## 📱 Complete Deployment Pipeline for Android & iOS

This guide covers the complete deployment process for the Boloo Citizen Reporting mobile application to Google Play Store and Apple App Store.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Configuration](#environment-configuration)
4. [Building for Production](#building-for-production)
5. [Android Deployment](#android-deployment)
6. [iOS Deployment](#ios-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Post-Deployment](#post-deployment)

---

## Prerequisites

### Required Accounts
- **Expo Account**: Sign up at https://expo.dev
- **Google Play Console**: https://play.google.com/console (One-time fee: $25)
- **Apple Developer Program**: https://developer.apple.com ($99/year)

### Required Tools
```bash
# Install Node.js (v18 or higher)
node --version  # Should be >= 18.0.0

# Install EAS CLI globally
npm install -g eas-cli

# Verify installation
eas --version
```

### Development Environment
- **macOS**: Required for iOS builds (Xcode)
- **Windows/Linux**: Can build Android only
- **Xcode**: Latest version (macOS only)
- **Android Studio**: For Android development

---

## Initial Setup

### 1. Install EAS CLI and Login

```bash
# Install EAS CLI globally
npm install -g eas-cli

# Login to your Expo account
eas login

# Verify you're logged in
eas whoami
```

### 2. Link Project to EAS

```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"

# Initialize EAS project (if not already done)
eas init

# This will:
# - Create an Expo project if needed
# - Link to your Expo account
# - Set up project identifiers
```

### 3. Configure Project

The `eas.json` file is already configured with build profiles:

- **development**: For testing with Expo Go
- **preview**: For internal testing (APK for Android)
- **production**: Final build for app stores (APK)
- **production-aab**: Google Play Store bundle (AAB)

---

## Environment Configuration

### 1. Update app.json

Ensure the API URL is correct:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://boloo-backend-app.azurewebsites.net"
    }
  }
}
```

### 2. Configure Environment Variables

Edit `.env.production`:

```bash
API_URL=https://boloo-backend-app.azurewebsites.net
APP_ENV=production
APP_VERSION=1.0.0
ENABLE_ANALYTICS=true
```

### 3. Update Version Numbers

In `app.json`:

```json
{
  "expo": {
    "version": "1.0.0",
    "android": {
      "versionCode": 1
    },
    "ios": {
      "buildNumber": "1"
    }
  }
}
```

**Version Increment Rules:**
- **version**: User-facing version (1.0.0 → 1.0.1 → 1.1.0)
- **versionCode** (Android): Integer, must increase (1 → 2 → 3)
- **buildNumber** (iOS): String, must increase ("1" → "2" → "3")

---

## Building for Production

### Android Build

#### Option 1: APK (For Testing)

```bash
# Build APK for testing/sideloading
eas build --platform android --profile production

# Or use the npm script
npm run build:android
```

#### Option 2: AAB (For Play Store)

```bash
# Build AAB bundle for Google Play Store
eas build --platform android --profile production-aab

# Or use the npm script
npm run build:android:aab
```

#### Monitor Build Progress

```bash
# Build will run on EAS servers
# You'll get a link to monitor progress
# Example: https://expo.dev/accounts/YOUR_ACCOUNT/projects/boloo-citizen/builds/BUILD_ID

# Check build status
eas build:list --platform android
```

#### Download Build

Once complete, download from:
- EAS Dashboard: https://expo.dev
- Or use CLI: `eas build:download --platform android --latest`

### iOS Build

```bash
# Build for iOS
eas build --platform ios --profile production

# Or use the npm script
npm run build:ios
```

**Note**: iOS builds require:
- Apple Developer Account
- App Store Connect setup
- Proper certificates and provisioning profiles (EAS handles this)

---

## Android Deployment

### 1. Google Play Console Setup

#### Create Application

1. Go to https://play.google.com/console
2. Create new application
3. Fill in:
   - **App name**: Boloo - Citizen Reporting
   - **Default language**: English (or your primary language)
   - **App or game**: App
   - **Free or paid**: Free

#### Set Up Store Listing

Required information:

**App Details**
- **App name**: Boloo - Citizen Reporting
- **Short description** (80 chars):
  ```
  Report civic issues easily. Help improve your community with Boloo.
  ```
- **Full description** (4000 chars max):
  ```
  Boloo empowers citizens to report civic grievances and issues directly to local authorities.

  Features:
  • Report civic issues with photos and location
  • Track your reports in real-time
  • Receive updates on resolution status
  • Support for multiple languages including Hindi
  • Easy-to-use interface

  Categories:
  • Potholes and road damage
  • Street lighting issues
  • Garbage and sanitation
  • Water supply problems
  • And many more...

  Make your community better, one report at a time!
  ```

**Graphics Assets**

Required sizes (create these):

1. **App Icon**: 512x512 PNG
2. **Feature Graphic**: 1024x500 PNG
3. **Screenshots**:
   - Phone: At least 2, up to 8 (min 320px on shortest side)
   - 7-inch tablet: At least 2
   - 10-inch tablet: At least 2

**Categorization**
- **Category**: Productivity or Social
- **Tags**: civic engagement, community, reporting

**Contact Details**
- **Email**: your-support@boloo.com
- **Privacy Policy URL**: https://boloo.com/privacy (must create)

### 2. Upload APK/AAB

#### Using Console

1. Go to **Production** → **Create new release**
2. Upload your AAB file
3. Add release notes:
   ```
   Initial release of Boloo - Citizen Reporting

   Features:
   - Report civic issues with photos
   - Real-time tracking
   - Multi-language support
   ```

#### Using EAS Submit (Automated)

```bash
# Setup service account (one-time)
# Download JSON key from Google Cloud Console
# Save as playstore-service-account.json

# Submit to Play Store
eas submit --platform android --latest

# Or use npm script
npm run submit:android
```

### 3. Content Rating

1. Go to **Content rating** section
2. Complete questionnaire
3. Save rating

### 4. App Content

Required declarations:
- **Privacy Policy**: URL required
- **Ads**: Declare if you show ads
- **Target audience**: Age groups
- **Data safety**: What data you collect

### 5. Release

1. **Internal testing**: Test with up to 100 users
2. **Closed testing**: Beta testing (alpha/beta tracks)
3. **Open testing**: Public beta
4. **Production**: Full release

```bash
# Promote to production after testing
# This is done in Play Console UI
```

---

## iOS Deployment

### 1. Apple Developer Setup

#### Certificates & Identifiers

EAS handles most of this automatically, but you need:

1. **Apple Developer Account**: $99/year
2. **App Store Connect Access**
3. **Team ID**: Found in Apple Developer account

#### Configure eas.json

```json
{
  "submit": {
    "production": {
      "ios": {
        "ascAppId": "YOUR_APP_STORE_CONNECT_APP_ID",
        "appleId": "your.email@example.com",
        "appleTeamId": "YOUR_10_CHAR_TEAM_ID"
      }
    }
  }
}
```

### 2. App Store Connect Setup

#### Create App

1. Go to https://appstoreconnect.apple.com
2. **My Apps** → **+** → **New App**
3. Fill in:
   - **Platform**: iOS
   - **Name**: Boloo - Citizen Reporting
   - **Primary Language**: English
   - **Bundle ID**: com.boloo.citizen
   - **SKU**: com.boloo.citizen (unique identifier)

#### App Information

- **Subtitle**: Report civic issues easily
- **Category**:
  - Primary: Productivity
  - Secondary: Social Networking
- **Content Rights**: Check if you own content

#### Pricing and Availability

- **Price**: Free
- **Availability**: All countries (or select specific)

### 3. Build and Upload

```bash
# Build for iOS
eas build --platform ios --profile production

# Submit to App Store (after build completes)
eas submit --platform ios --latest

# Or use npm scripts
npm run build:ios
npm run submit:ios
```

### 4. Prepare for Review

#### Screenshots Required

- **6.7" Display** (iPhone 15 Pro Max): 1320x2868 pixels
- **6.5" Display** (iPhone 11 Pro Max): 1284x2778 pixels
- **5.5" Display** (iPhone 8 Plus): 1242x2208 pixels

Need at least 3-10 screenshots per device size.

#### App Preview Video (Optional)

- 15-30 seconds
- Demonstrate key features
- Same sizes as screenshots

#### Description

```
Boloo empowers citizens to report civic grievances and issues directly to local authorities.

KEY FEATURES:
• Report Issues: Take photos, add descriptions, mark location
• Real-time Tracking: Monitor your report status
• Multi-language: Support for Hindi and English
• Easy Interface: Simple and intuitive design
• Categories: Potholes, lighting, sanitation, water, and more

MAKE A DIFFERENCE:
Help improve your community by reporting issues that matter. Track progress and see real change happen.

PRIVACY:
Your data is secure. We only collect information necessary to process your reports. See our privacy policy for details.

Support: support@boloo.com
Website: https://boloo.com
```

#### Keywords

```
civic, reporting, grievance, community, issue, complaint, municipal, local, government, service
```

#### What's New (Release Notes)

```
Initial release of Boloo - Citizen Reporting

New Features:
• Report civic issues with photos and location
• Track your reports in real-time
• Multi-language support
• Easy-to-use interface
```

### 5. Submit for Review

1. **App Review Information**:
   - Contact info
   - Demo account (if login required)
   - Notes for reviewer

2. **Version Release**:
   - **Manual**: You control when it goes live
   - **Automatic**: Auto-release after approval

3. **Submit**: Click "Submit for Review"

**Review Time**: Typically 24-48 hours

---

## Troubleshooting

### Common Build Errors

#### 1. Android Build Fails

```bash
# Clear cache and rebuild
eas build:clean --platform android
eas build --platform android --profile production --clear-cache
```

#### 2. iOS Code Signing Issues

```bash
# EAS usually handles this, but if issues persist:
eas credentials

# Choose iOS → Production → Manage credentials
# Regenerate certificates if needed
```

#### 3. Version Code/Build Number Issues

**Error**: "Version code must be greater than previous"

**Fix**: Increment in app.json:
```json
{
  "expo": {
    "android": {
      "versionCode": 2  // Increment this
    },
    "ios": {
      "buildNumber": "2"  // Increment this
    }
  }
}
```

#### 4. Asset Errors

```bash
# Ensure all assets exist
ls -la assets/

# Required files:
# - icon.png (1024x1024)
# - splash-icon.png
# - adaptive-icon.png (Android)
# - favicon.png
```

#### 5. API Connection Issues

Check `.env.production`:
```bash
# Ensure URL is correct
API_URL=https://boloo-backend-app.azurewebsites.net

# Test endpoint
curl https://boloo-backend-app.azurewebsites.net/api/health
```

### Build Logs

```bash
# View build logs
eas build:list --platform android

# View specific build
eas build:view BUILD_ID

# Download logs
eas build:logs BUILD_ID
```

### Debugging Production Build

```bash
# Install production build on device
adb install app-release.apk

# View logs while running
adb logcat | grep "com.boloo.citizen"
```

---

## Post-Deployment

### Monitoring

#### Analytics Setup

Consider adding:
- **Firebase Analytics**
- **Sentry** (crash reporting)
- **Amplitude** (user behavior)

```bash
# Install analytics
npm install @react-native-firebase/analytics
npm install @sentry/react-native
```

#### Performance Monitoring

```bash
# Monitor app performance in:
# - Google Play Console → Vitals
# - App Store Connect → App Analytics
```

### Updates

#### Over-the-Air (OTA) Updates

For minor updates (JS code only):

```bash
# Publish update
eas update --branch production --message "Bug fixes"

# Users get update automatically
```

**Note**: Native code changes require new build.

#### New Version Release

1. Update version in `app.json`:
```json
{
  "version": "1.0.1",
  "android": { "versionCode": 2 },
  "ios": { "buildNumber": "2" }
}
```

2. Build and submit:
```bash
npm run build:android:aab
npm run submit:android

npm run build:ios
npm run submit:ios
```

### User Feedback

Monitor reviews:
```bash
# Set up Google Play Console notifications
# Set up App Store Connect notifications
```

Respond to reviews:
- Google Play: Can respond publicly
- App Store: Can respond through App Store Connect

---

## Quick Reference Commands

### Build Commands

```bash
# Android APK (Testing)
eas build --platform android --profile production

# Android AAB (Play Store)
eas build --platform android --profile production-aab

# iOS (App Store)
eas build --platform ios --profile production

# Both platforms
eas build --platform all --profile production
```

### Submit Commands

```bash
# Submit Android
eas submit --platform android --latest

# Submit iOS
eas submit --platform ios --latest

# Both platforms
eas submit --platform all --latest
```

### Update Commands

```bash
# OTA update
eas update --branch production --message "Description"

# Check update status
eas update:list --branch production
```

### Utility Commands

```bash
# Check build status
eas build:list

# View credentials
eas credentials

# Check project info
eas project:info

# Logout
eas logout
```

---

## Checklist Before Release

### Pre-Build Checklist

- [ ] All features tested locally
- [ ] API URL points to production backend
- [ ] Version numbers incremented
- [ ] Assets (icons, splash screens) finalized
- [ ] Environment variables configured
- [ ] Privacy policy created and linked
- [ ] Terms of service created
- [ ] Support email set up

### Android Checklist

- [ ] AAB built successfully
- [ ] Tested on multiple Android devices
- [ ] Screenshots prepared (phone + tablets)
- [ ] Store listing completed
- [ ] Content rating completed
- [ ] Data safety form completed
- [ ] Release notes written

### iOS Checklist

- [ ] IPA built successfully
- [ ] Tested on multiple iOS devices
- [ ] Screenshots prepared (all sizes)
- [ ] App Store listing completed
- [ ] Keywords optimized
- [ ] Privacy policy linked
- [ ] Demo account created (if applicable)
- [ ] Release notes written

---

## Support Resources

### Documentation
- **Expo Docs**: https://docs.expo.dev
- **EAS Build**: https://docs.expo.dev/build/introduction/
- **EAS Submit**: https://docs.expo.dev/submit/introduction/
- **React Native**: https://reactnative.dev

### Community
- **Expo Forums**: https://forums.expo.dev
- **Discord**: https://chat.expo.dev
- **Stack Overflow**: Tag with `expo`, `eas`

### App Stores
- **Play Console Help**: https://support.google.com/googleplay/android-developer
- **App Store Connect**: https://help.apple.com/app-store-connect

---

## Security Notes

### Sensitive Files (Never Commit)

```bash
# Add to .gitignore:
.env.production
*.jks
*.p12
*.mobileprovision
playstore-service-account.json
```

### API Keys

- Store in environment variables
- Use secrets management (Expo Secrets)
- Rotate keys regularly

```bash
# Add secrets to EAS
eas secret:create --name API_KEY --value "your-key"
```

---

## Cost Breakdown

### One-Time Costs
- **Google Play Console**: $25 (lifetime)
- **Apple Developer Program**: $99/year

### EAS Build Costs
- **Free Tier**: Limited builds per month
- **Paid Plans**: Starting at $29/month

Check current pricing: https://expo.dev/pricing

---

## Conclusion

This guide covers the complete deployment pipeline. For issues not covered here:

1. Check official documentation
2. Search Expo forums
3. Contact support@boloo.com

**Good luck with your deployment! 🚀**
