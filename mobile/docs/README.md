# Boloo Mobile App - Deployment Documentation

## 📚 Documentation Overview

This directory contains all documentation needed for deploying the Boloo mobile application to Google Play Store and Apple App Store.

---

## 📖 Available Guides

### 1. **QUICK_START.md** - Start Here! ⭐
Quick 30-minute guide to get your app built and submitted.
- Prerequisites
- Build commands
- Store submission basics
- Common commands reference

**Use this if**: You want to deploy quickly and have basic knowledge of mobile deployment.

### 2. **DEPLOYMENT_GUIDE.md** - Complete Reference 📘
Comprehensive deployment guide covering every aspect.
- Detailed setup instructions
- Platform-specific configurations
- Store submission process
- Troubleshooting
- Post-deployment monitoring

**Use this if**: You need detailed explanations, are new to EAS/Expo, or encountered issues.

### 3. **BUILD_CHECKLIST.md** - Quality Assurance ✅
Step-by-step checklist for builds and releases.
- Pre-build verification
- Build process steps
- Store submission checklist
- Post-release monitoring
- Version update templates

**Use this if**: You want to ensure nothing is missed before deployment.

### 4. **STORE_ASSETS_GUIDE.md** - Graphics & Media 🎨
Complete guide for creating store assets.
- Required image sizes
- Screenshot guidelines
- Asset creation tools
- Directory structure
- Content templates

**Use this if**: You need to create or update app store graphics and screenshots.

---

## 🚀 Quick Navigation

### For First-Time Deployment
1. Read `QUICK_START.md`
2. Follow `BUILD_CHECKLIST.md`
3. Reference `DEPLOYMENT_GUIDE.md` for details
4. Use `STORE_ASSETS_GUIDE.md` for graphics

### For Updates
1. Check version in `app.json`
2. Follow `BUILD_CHECKLIST.md` (Version Update section)
3. Build and submit using commands from `QUICK_START.md`

### For Troubleshooting
1. Check `DEPLOYMENT_GUIDE.md` Troubleshooting section
2. Review build logs with `eas build:logs`
3. Verify configuration in `eas.json` and `app.json`

---

## 📁 File Structure

```
/mobile/
├── docs/                           # 📚 This directory
│   ├── README.md                   # This file
│   ├── QUICK_START.md             # Quick deployment guide
│   ├── DEPLOYMENT_GUIDE.md        # Comprehensive guide
│   ├── BUILD_CHECKLIST.md         # Build checklist
│   └── STORE_ASSETS_GUIDE.md      # Asset creation guide
│
├── app-store-assets/              # 🎨 Store submission assets
│   ├── icons/                     # App icons
│   ├── screenshots/               # Store screenshots
│   │   ├── android/              # Android screenshots
│   │   └── ios/                  # iOS screenshots
│   └── descriptions/             # Store descriptions
│       ├── play-store-description.txt
│       ├── app-store-description.txt
│       └── release-notes.txt
│
├── eas.json                       # ⚙️ EAS Build configuration
├── app.json                       # 📱 Expo app configuration
├── .env.production               # 🔐 Production environment vars
└── package.json                  # 📦 Dependencies & scripts
```

---

## 🎯 Common Tasks

### Build for Testing
```bash
npm run build:preview
```

### Build for Production
```bash
# Android
npm run build:android:aab

# iOS
npm run build:ios

# Both
npm run build:all
```

### Submit to Stores
```bash
# Android
npm run submit:android

# iOS
npm run submit:ios

# Both
npm run submit:all
```

### Push Update (OTA)
```bash
npm run update
```

---

## 📋 Pre-Deployment Checklist

Before your first deployment:

### Configuration
- [ ] Review `eas.json` build profiles
- [ ] Verify API URL in `app.json`
- [ ] Check version numbers in `app.json`
- [ ] Configure `.env.production`

### Assets
- [ ] App icon (1024x1024) ready
- [ ] Splash screen created
- [ ] Screenshots prepared
- [ ] Store descriptions written

### Accounts
- [ ] Expo account created
- [ ] Google Play Console access ($25)
- [ ] Apple Developer account ($99/year)

### Testing
- [ ] Tested on Android device
- [ ] Tested on iOS device (if deploying to iOS)
- [ ] All features working
- [ ] API connection verified

---

## 🔧 Configuration Files

### eas.json
Defines build profiles:
- `development`: Testing with dev client
- `preview`: Internal testing (APK)
- `production`: App store build (APK)
- `production-aab`: Play Store bundle (AAB)

### app.json
Main app configuration:
- App name, version, icons
- Platform-specific settings
- Permissions and capabilities
- API configuration

### .env.production
Environment variables:
- API URL
- Feature flags
- Configuration values

---

## 📱 Platform Requirements

### Android (Google Play Store)

**One-time cost**: $25
**Review time**: 1-3 days

**Required**:
- App icon (512x512)
- Feature graphic (1024x500)
- 2+ screenshots
- Privacy policy URL
- App description
- Content rating

**Build format**: AAB (Android App Bundle)

### iOS (Apple App Store)

**Annual cost**: $99/year
**Review time**: 24-48 hours

**Required**:
- App icon (1024x1024)
- 3+ screenshots per size
- Privacy policy URL
- App description
- Keywords
- Support URL

**Build format**: IPA

---

## 🛠️ Tools & Services

### Required
- **EAS CLI**: Build and deployment tool
- **Expo Account**: Build service access
- **Node.js**: v18 or higher

### Optional
- **Android Studio**: Android development
- **Xcode**: iOS development (macOS only)
- **Fastlane**: Automated screenshots

---

## 🆘 Getting Help

### Documentation
Start with the guides in order:
1. QUICK_START.md
2. BUILD_CHECKLIST.md
3. DEPLOYMENT_GUIDE.md
4. STORE_ASSETS_GUIDE.md

### External Resources
- **Expo Docs**: https://docs.expo.dev
- **EAS Build**: https://docs.expo.dev/build/introduction/
- **React Native**: https://reactnative.dev

### Community Support
- **Expo Forums**: https://forums.expo.dev
- **Discord**: https://chat.expo.dev
- **Stack Overflow**: Tag with `expo`, `eas`

### App Store Help
- **Play Console**: https://support.google.com/googleplay/android-developer
- **App Store Connect**: https://help.apple.com/app-store-connect

---

## 🔄 Version History

### Version 1.0.0 (Current)
- Initial deployment documentation
- Complete build and submission guides
- Store assets templates
- Troubleshooting guides

---

## 🔐 Security Notes

**Never commit**:
- `.env.production`
- `*.jks` (Android keystore)
- `*.p12` (iOS certificates)
- `playstore-service-account.json`
- `GoogleService-Info.plist`

All sensitive files are in `.gitignore`.

---

## 📊 Deployment Workflow

```
1. Development
   ├── Code features
   ├── Test locally
   └── Commit changes

2. Prepare Release
   ├── Update version numbers
   ├── Update release notes
   ├── Test thoroughly
   └── Review checklist

3. Build
   ├── Run EAS build
   ├── Monitor build progress
   ├── Download artifacts
   └── Test build on devices

4. Submit
   ├── Upload to store
   ├── Fill store listing
   ├── Submit for review
   └── Monitor review status

5. Post-Release
   ├── Monitor crashes
   ├── Check reviews
   ├── Track analytics
   └── Plan updates
```

---

## 🎓 Best Practices

### Version Management
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Always increment versionCode/buildNumber
- Document changes in release notes

### Testing
- Test on physical devices
- Test all critical flows
- Verify API connections
- Check permissions

### Store Optimization
- Use high-quality screenshots
- Write clear descriptions
- Choose relevant keywords
- Respond to reviews

### Monitoring
- Set up crash reporting (Sentry)
- Track analytics (Firebase)
- Monitor performance metrics
- Review user feedback regularly

---

## 📞 Support Contacts

### Technical Issues
- **Email**: dev@boloo.com
- **Internal Docs**: [Link to internal wiki]

### Store Submission
- **Product Team**: product@boloo.com

### Design/Assets
- **Design Team**: design@boloo.com

---

## 🚦 Status Indicators

Use this to track deployment progress:

### Android
- [ ] Development build tested
- [ ] Preview build tested
- [ ] Production AAB built
- [ ] Play Console listing complete
- [ ] Submitted for review
- [ ] Approved and published

### iOS
- [ ] Development build tested
- [ ] Production IPA built
- [ ] App Store listing complete
- [ ] TestFlight testing done
- [ ] Submitted for review
- [ ] Approved and published

---

## 📈 Next Steps

After successful deployment:

1. **Monitor**: Set up analytics and crash reporting
2. **Market**: Promote app to target audience
3. **Support**: Set up user support channels
4. **Iterate**: Plan feature updates based on feedback
5. **Scale**: Optimize for growth

---

## 🎉 Congratulations!

Once deployed, your app will be live and helping citizens report civic issues. Good luck with your deployment!

**Questions?** Check the guides above or reach out to the team.

---

**Last Updated**: 2025-11-22
**Version**: 1.0.0
**Maintained by**: Boloo Development Team
