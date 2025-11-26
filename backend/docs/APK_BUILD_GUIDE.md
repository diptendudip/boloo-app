# APK Build Guide - Bultoo Mobile App

## Overview
This guide covers generating a signed APK for the Bultoo React Native mobile app using Expo Application Services (EAS Build).

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [EAS Build Setup](#eas-build-setup)
3. [Generate APK for Testing](#generate-apk-for-testing)
4. [Internal Testing](#internal-testing)
5. [Play Store Preparation](#play-store-preparation)
6. [CI/CD Integration](#cicd-integration)

---

## Prerequisites

### Required Tools
```bash
# Install/Update Node.js (v18 or higher)
node --version

# Install EAS CLI globally
npm install -g eas-cli

# Login to Expo account (create one if needed at expo.dev)
eas login
```

### Create Expo Account
1. Go to [https://expo.dev](https://expo.dev)
2. Sign up with email or GitHub
3. Verify your email

### Project Configuration

Navigate to your mobile app directory:
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"  # Adjust path as needed
```

Check if `app.json` or `app.config.js` exists:
```bash
ls -la | grep app
```

---

## EAS Build Setup

### 1. Initialize EAS Build

```bash
# Initialize EAS in your project
eas build:configure

# This creates eas.json with default configurations
```

### 2. Configure `eas.json`

Create/update `eas.json` in your project root:

```json
{
  "cli": {
    "version": ">= 5.9.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "android": {
        "gradleCommand": ":app:assembleDebug",
        "buildType": "apk"
      }
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "./google-service-account.json",
        "track": "internal"
      }
    }
  }
}
```

### 3. Update `app.json` or `app.config.js`

**app.json:**
```json
{
  "expo": {
    "name": "Bultoo",
    "slug": "bultoo-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": [
      "**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.bultoo.app"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.bultoo.app",
      "versionCode": 1,
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ]
    },
    "web": {
      "favicon": "./assets/favicon.png"
    },
    "extra": {
      "apiUrl": "https://api.bultoo.com",
      "eas": {
        "projectId": "YOUR_PROJECT_ID"
      }
    }
  }
}
```

### 4. Get EAS Project ID

```bash
# Initialize or link project
eas init

# Or if already initialized
eas project:info

# Copy the Project ID and add it to app.json under extra.eas.projectId
```

---

## Generate APK for Testing

### 1. Generate Keystore (First Time Only)

EAS automatically generates and manages keystores, but you can use your own:

```bash
# Generate keystore manually (optional)
keytool -genkeypair -v \
  -storetype PKCS12 \
  -keystore bultoo-release.keystore \
  -alias bultoo-key \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# You'll be prompted for:
# - Keystore password
# - Key password
# - Your name, organization, etc.

# SAVE THESE CREDENTIALS SECURELY!
```

### 2. Build APK (Development/Testing)

```bash
# Build APK for internal testing
eas build --platform android --profile preview

# Or build locally (requires Android SDK)
eas build --platform android --profile preview --local
```

**What happens:**
1. EAS uploads your code to their servers
2. Builds the APK using Android SDK
3. Signs the APK with auto-generated or provided keystore
4. Provides download link when complete

### 3. Monitor Build Progress

```bash
# Check build status
eas build:list

# View specific build
eas build:view BUILD_ID

# View logs
eas build:view BUILD_ID --log
```

### 4. Download APK

Once build completes:

```bash
# Download APK from terminal
eas build:download --platform android --profile preview

# Or visit Expo dashboard
# https://expo.dev/accounts/YOUR_USERNAME/projects/bultoo-app/builds
```

---

## Internal Testing

### 1. Install APK on Android Device

**Method 1: Direct Download**
```bash
# EAS provides a shareable link
# Share this link: https://expo.dev/artifacts/BUILD_ARTIFACT_ID

# On Android device:
# 1. Open link in browser
# 2. Download APK
# 3. Enable "Install from Unknown Sources"
# 4. Install APK
```

**Method 2: ADB Install**
```bash
# Connect device via USB
adb devices

# Install APK
adb install path/to/bultoo-app.apk

# Or drag & drop to Android emulator
```

**Method 3: Internal Distribution**
```bash
# Create internal distribution build
eas build --platform android --profile preview --auto-submit

# Share link with testers
eas build:list
# Copy the "Install" link
```

### 2. Testing Checklist

Create a testing checklist:

```markdown
## Testing Checklist - Bultoo APK v1.0.0

### Authentication
- [ ] Sign up with email
- [ ] Sign in with existing account
- [ ] Password reset flow
- [ ] Social login (if implemented)
- [ ] Logout functionality

### Core Features
- [ ] Home screen loads correctly
- [ ] Navigation between screens
- [ ] Data fetching from API (api.bultoo.com)
- [ ] Forms submission
- [ ] Image upload
- [ ] Push notifications (if implemented)

### Performance
- [ ] App launches within 3 seconds
- [ ] No crashes on common actions
- [ ] Smooth scrolling
- [ ] No memory leaks

### Network
- [ ] Works on WiFi
- [ ] Works on mobile data
- [ ] Handles offline mode
- [ ] API errors handled gracefully

### Devices
- [ ] Works on Android 10+
- [ ] Works on different screen sizes
- [ ] Works on tablets
```

### 3. Collect Feedback

Use crash reporting and analytics:

```bash
# Install Sentry for crash reporting
npm install @sentry/react-native

# Install Analytics
npm install @react-native-firebase/analytics
```

**Add to app.json:**
```json
{
  "expo": {
    "plugins": [
      "@sentry/react-native/expo"
    ],
    "extra": {
      "sentryDsn": "YOUR_SENTRY_DSN"
    }
  }
}
```

---

## Play Store Preparation

### 1. Generate Production App Bundle (AAB)

```bash
# Build production AAB (required for Play Store)
eas build --platform android --profile production

# This creates an .aab file instead of .apk
```

### 2. Create Google Play Console Account

1. Go to [https://play.google.com/console](https://play.google.com/console)
2. Pay one-time $25 registration fee
3. Create developer account

### 3. Create App Listing

**Required Assets:**
```bash
# Create app assets directory
mkdir -p assets/play-store/{screenshots,graphics}
```

**Required files:**
- App icon (512x512 PNG)
- Feature graphic (1024x500 PNG)
- Screenshots (minimum 2, max 8)
  - Phone: 320-3840px wide
  - Tablet: 320-3840px wide
- Privacy policy URL
- App description

### 4. Configure `eas.json` for Submission

```json
{
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "./google-service-account.json",
        "track": "internal"
      }
    }
  }
}
```

### 5. Create Service Account (for automated submission)

**In Google Cloud Console:**
1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable "Google Play Android Developer API"
4. Create service account
5. Create JSON key
6. Grant access in Play Console

```bash
# Save service account JSON
# Store in: google-service-account.json
# Add to .gitignore!

echo "google-service-account.json" >> .gitignore
```

### 6. Submit to Play Store

```bash
# Build and submit in one command
eas build --platform android --profile production --auto-submit

# Or submit existing build
eas submit --platform android --latest
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/build-apk.yml`:

```yaml
name: Build APK

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

jobs:
  build-android:
    name: Build Android APK
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}

      - name: Install dependencies
        run: |
          cd mobile
          npm ci

      - name: Build APK (Preview)
        run: |
          cd mobile
          eas build --platform android --profile preview --non-interactive

      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: app-preview.apk
          path: mobile/build-*.apk

      - name: Create Release
        if: github.ref == 'refs/heads/main'
        uses: softprops/action-gh-release@v1
        with:
          files: mobile/build-*.apk
          tag_name: v${{ github.run_number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Required GitHub Secrets

Add these secrets in GitHub repository settings:

```bash
# Get Expo token
eas whoami
eas build:list --json

# Generate token
# Visit: https://expo.dev/settings/access-tokens
# Create new token with name "GitHub Actions"
```

**Add to GitHub Secrets:**
- `EXPO_TOKEN` - From Expo dashboard
- `GOOGLE_SERVICE_ACCOUNT` - Service account JSON (for Play Store)

---

## Update Configuration for Production API

### 1. Environment-Based Configuration

Create `config/environment.js`:

```javascript
const ENV = {
  dev: {
    apiUrl: 'http://localhost:8000',
    websocketUrl: 'ws://localhost:8000',
  },
  staging: {
    apiUrl: 'https://staging-api.bultoo.com',
    websocketUrl: 'wss://staging-api.bultoo.com',
  },
  prod: {
    apiUrl: 'https://api.bultoo.com',
    websocketUrl: 'wss://api.bultoo.com',
  }
};

const getEnvVars = () => {
  // __DEV__ is true when running in development
  if (__DEV__) {
    return ENV.dev;
  } else if (process.env.APP_ENV === 'staging') {
    return ENV.staging;
  } else {
    return ENV.prod;
  }
};

export default getEnvVars;
```

### 2. Update API Client

```javascript
// services/api.js
import axios from 'axios';
import getEnvVars from '../config/environment';

const { apiUrl } = getEnvVars();

const api = axios.create({
  baseURL: apiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export default api;
```

### 3. Build with Different Environments

Update `eas.json`:

```json
{
  "build": {
    "development": {
      "env": {
        "APP_ENV": "dev"
      }
    },
    "preview": {
      "env": {
        "APP_ENV": "staging"
      }
    },
    "production": {
      "env": {
        "APP_ENV": "prod"
      }
    }
  }
}
```

---

## Versioning Strategy

### Semantic Versioning

```json
{
  "expo": {
    "version": "1.0.0",  // User-facing version
    "android": {
      "versionCode": 1   // Auto-increment for each build
    }
  }
}
```

### Auto-Increment Version Code

Create `scripts/increment-version.js`:

```javascript
const fs = require('fs');
const path = require('path');

const appJsonPath = path.join(__dirname, '../app.json');
const appJson = require(appJsonPath);

// Increment Android versionCode
appJson.expo.android.versionCode += 1;

// Write back to file
fs.writeFileSync(appJsonPath, JSON.stringify(appJson, null, 2));

console.log(`Version code incremented to: ${appJson.expo.android.versionCode}`);
```

**Add to package.json:**
```json
{
  "scripts": {
    "version:bump": "node scripts/increment-version.js",
    "build:preview": "npm run version:bump && eas build --platform android --profile preview"
  }
}
```

---

## Troubleshooting

### Common Build Errors

**1. Metro Bundler Issues**
```bash
# Clear cache
npx expo start --clear

# Or
npx react-native start --reset-cache
```

**2. Dependency Issues**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear npm cache
npm cache clean --force
```

**3. Build Failed on EAS**
```bash
# Check build logs
eas build:view BUILD_ID --log

# Common fixes:
# - Update dependencies
# - Check app.json configuration
# - Verify EAS project ID
```

**4. APK Install Failed**
```bash
# Enable installation from unknown sources on Android

# Check APK signature
jarsigner -verify -verbose -certs your-app.apk

# Reinstall
adb uninstall com.bultoo.app
adb install your-app.apk
```

### Performance Optimization

```javascript
// Enable Hermes engine in app.json
{
  "expo": {
    "android": {
      "jsEngine": "hermes"
    }
  }
}
```

---

## Testing Distribution Platforms

### 1. Firebase App Distribution

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
firebase init appdistribution

# Distribute APK
firebase appdistribution:distribute \
  path/to/app.apk \
  --app YOUR_FIREBASE_APP_ID \
  --groups "testers" \
  --release-notes "Testing build v1.0.0"
```

### 2. TestFlight Alternative (Android)

Use EAS internal distribution:

```bash
# Build with internal distribution
eas build --platform android --profile preview

# Get shareable link
eas build:list

# Share link with testers
# They can install directly from browser
```

---

## Useful Commands Reference

```bash
# Login to EAS
eas login

# Check account
eas whoami

# Initialize project
eas init

# Configure build
eas build:configure

# Build APK
eas build --platform android --profile preview

# Build AAB (Play Store)
eas build --platform android --profile production

# Check builds
eas build:list

# Download build
eas build:download

# Submit to Play Store
eas submit --platform android

# View credentials
eas credentials

# Delete credentials
eas credentials:delete

# Run locally (requires Android SDK)
eas build --platform android --local
```

---

## Next Steps

1. ✅ Generate preview APK for testing
2. 📱 Install on test devices
3. 🧪 Conduct internal testing
4. 📊 Collect feedback and crash reports
5. 🔄 Iterate and fix issues
6. 🏪 Prepare Play Store listing
7. 🚀 Submit to Play Store (internal testing track)
8. 📈 Gradually roll out to production

---

## Resources

- [EAS Build Documentation](https://docs.expo.dev/build/introduction/)
- [Expo Application Services](https://expo.dev/eas)
- [Google Play Console](https://play.google.com/console)
- [React Native Performance](https://reactnative.dev/docs/performance)
- [Android Developer Guide](https://developer.android.com/studio/publish)
