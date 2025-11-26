# Build and Deployment Checklist

## Pre-Build Verification

### 1. Code Quality
- [ ] All TypeScript errors resolved
- [ ] No console.log statements in production code
- [ ] All TODO comments addressed or documented
- [ ] Code formatted and linted
- [ ] Dead code removed

### 2. Testing
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing completed on:
  - [ ] Android physical device
  - [ ] Android emulator
  - [ ] iOS physical device (if available)
  - [ ] iOS simulator
- [ ] Tested on different screen sizes
- [ ] Tested offline functionality
- [ ] Tested permissions flow
- [ ] Tested all API endpoints

### 3. Configuration
- [ ] API URL points to production: `https://boloo-backend-app.azurewebsites.net`
- [ ] Environment variables configured in `.env.production`
- [ ] App version incremented in `app.json`
- [ ] Android versionCode incremented
- [ ] iOS buildNumber incremented
- [ ] Bundle identifiers correct:
  - Android: `com.boloo.citizen`
  - iOS: `com.boloo.citizen`

### 4. Assets
- [ ] App icon (1024x1024) finalized
- [ ] Splash screen designed and exported
- [ ] Adaptive icon for Android ready
- [ ] All image assets optimized
- [ ] Fonts loaded correctly

### 5. Dependencies
- [ ] All dependencies up to date
- [ ] No security vulnerabilities (`npm audit`)
- [ ] Unnecessary dependencies removed
- [ ] package.json cleaned up

### 6. Permissions
- [ ] Android permissions declared correctly
- [ ] iOS permission descriptions added
- [ ] Minimal permissions requested
- [ ] Permission flows tested

---

## Build Process

### Android Build

#### APK Build (Testing)
```bash
# Clean build
eas build --platform android --profile production --clear-cache

# Standard build
eas build --platform android --profile production
```

**Checklist:**
- [ ] Build started successfully
- [ ] No build errors in logs
- [ ] APK downloaded and verified
- [ ] APK size reasonable (<50MB ideally)
- [ ] Installed on test device
- [ ] All features work as expected

#### AAB Build (Play Store)
```bash
# Build app bundle
eas build --platform android --profile production-aab
```

**Checklist:**
- [ ] AAB built successfully
- [ ] File size checked
- [ ] Ready for Play Console upload

### iOS Build

```bash
# Build for App Store
eas build --platform ios --profile production
```

**Checklist:**
- [ ] Build completed without errors
- [ ] IPA downloaded and verified
- [ ] File size checked
- [ ] Ready for App Store Connect

---

## Google Play Store Submission

### 1. Store Listing
- [ ] App name: "Boloo - Citizen Reporting"
- [ ] Short description (80 chars max) written
- [ ] Full description written
- [ ] Screenshots uploaded (min 2):
  - [ ] Phone screenshots
  - [ ] 7" tablet screenshots
  - [ ] 10" tablet screenshots
- [ ] Feature graphic (1024x500) uploaded
- [ ] App icon (512x512) uploaded
- [ ] Category selected: Productivity
- [ ] Tags added
- [ ] Content rating questionnaire completed

### 2. Privacy & Legal
- [ ] Privacy Policy URL added
- [ ] Terms of Service URL added
- [ ] Data Safety form completed
- [ ] Ad declarations made
- [ ] Target audience selected

### 3. App Content
- [ ] Age rating received
- [ ] Content declarations completed
- [ ] Government regulations addressed (if applicable)

### 4. Release Management
- [ ] Release notes written
- [ ] Internal testing completed (if applicable)
- [ ] Closed testing completed (if applicable)
- [ ] Production release created
- [ ] AAB uploaded
- [ ] Release reviewed and confirmed

### 5. Post-Submission
- [ ] Submission confirmed
- [ ] Monitoring review status
- [ ] Response plan for review issues ready

---

## Apple App Store Submission

### 1. App Information
- [ ] App name: "Boloo - Citizen Reporting"
- [ ] Subtitle written
- [ ] Privacy Policy URL added
- [ ] Category selected
- [ ] Age rating selected
- [ ] Copyright info added

### 2. Pricing & Availability
- [ ] Price tier set (Free)
- [ ] Countries/regions selected
- [ ] Release date set

### 3. Prepare for Submission
- [ ] Screenshots prepared and uploaded:
  - [ ] 6.7" Display (iPhone 15 Pro Max)
  - [ ] 6.5" Display (iPhone 11 Pro Max)
  - [ ] 5.5" Display (iPhone 8 Plus)
- [ ] App preview video uploaded (optional)
- [ ] Description written
- [ ] Keywords added (100 chars max)
- [ ] Support URL added
- [ ] Marketing URL added (optional)

### 4. Version Information
- [ ] What's New text written
- [ ] Build selected from TestFlight
- [ ] Promotional text added (optional)

### 5. App Review Information
- [ ] Contact information added
- [ ] Demo account credentials provided (if login required)
- [ ] Notes for reviewer added
- [ ] Attachment added (if applicable)

### 6. Export Compliance
- [ ] Encryption usage declared
- [ ] Export compliance answered

### 7. Submission
- [ ] All required fields completed
- [ ] Submit for Review clicked
- [ ] Confirmation email received

---

## Post-Release Monitoring

### First 24 Hours
- [ ] Monitor crash reports
- [ ] Check user reviews
- [ ] Verify analytics tracking
- [ ] Test production download
- [ ] Monitor server load
- [ ] Check API error rates

### First Week
- [ ] Daily crash report review
- [ ] Respond to user reviews
- [ ] Monitor app store ratings
- [ ] Track download numbers
- [ ] Monitor performance metrics
- [ ] Check for critical bugs

### Ongoing
- [ ] Weekly analytics review
- [ ] Monthly performance review
- [ ] Plan updates based on feedback
- [ ] Monitor competitor apps
- [ ] Track feature requests

---

## Version Update Checklist

### Minor Update (Bug Fixes)
- [ ] Increment patch version (1.0.0 → 1.0.1)
- [ ] Increment versionCode/buildNumber
- [ ] Update release notes
- [ ] Build and test
- [ ] Submit to stores

### Feature Update
- [ ] Increment minor version (1.0.0 → 1.1.0)
- [ ] Increment versionCode/buildNumber
- [ ] Update app description if needed
- [ ] Update screenshots if UI changed
- [ ] Build and test
- [ ] Submit to stores

### Major Update
- [ ] Increment major version (1.0.0 → 2.0.0)
- [ ] Complete retest of all features
- [ ] Update all store assets
- [ ] Update marketing materials
- [ ] Plan announcement/promotion
- [ ] Build and test
- [ ] Submit to stores

---

## Emergency Rollback Plan

### If Critical Bug Found After Release

#### Option 1: Quick Fix
1. Create hotfix branch
2. Fix critical bug
3. Test thoroughly
4. Increment versionCode/buildNumber
5. Emergency build and submit
6. Monitor expedited review

#### Option 2: Rollback (Play Store Only)
1. Go to Play Console
2. Navigate to Production release
3. Create new release with previous APK/AAB
4. Submit for review
5. Communicate with users

#### Option 3: OTA Update (If JS-only bug)
```bash
# For non-native code bugs
eas update --branch production --message "Critical bug fix"
```

---

## Communication Templates

### Release Announcement (Email)
```
Subject: Boloo Mobile App Now Available! 🎉

Dear Boloo Users,

We're excited to announce that the Boloo Citizen Reporting mobile app is now available on Google Play Store and Apple App Store!

Download now:
📱 Android: [Play Store Link]
🍎 iOS: [App Store Link]

Features:
✅ Report civic issues with photos
✅ Track your reports in real-time
✅ Multi-language support
✅ Easy-to-use interface

Thank you for being part of our community!

Best regards,
Boloo Team
```

### Update Release Notes Template
```
Version 1.0.1 Release Notes

What's New:
• [Feature 1]
• [Feature 2]

Improvements:
• [Improvement 1]
• [Improvement 2]

Bug Fixes:
• Fixed [bug 1]
• Fixed [bug 2]

Thank you for using Boloo!
```

---

## Contacts & Resources

### Team Contacts
- **Technical Lead**: [email]
- **Product Manager**: [email]
- **Support Team**: support@boloo.com

### External Contacts
- **Google Play Support**: Use Play Console Help
- **Apple Developer Support**: https://developer.apple.com/support/

### Key Links
- **Expo Dashboard**: https://expo.dev
- **Play Console**: https://play.google.com/console
- **App Store Connect**: https://appstoreconnect.apple.com
- **Analytics Dashboard**: [your analytics URL]

---

## Notes

### Build Numbers
- **Android versionCode**: Must increment by at least 1
- **iOS buildNumber**: Must be higher than previous
- Keep track in version.txt or similar

### Timing
- **Google Play**: Review typically 1-3 days
- **Apple App Store**: Review typically 24-48 hours
- **Expedited Review**: Available for critical bugs (Apple)

### Best Practices
- Build on stable internet connection
- Keep build logs for reference
- Test on physical devices when possible
- Have fallback plan ready
- Communicate with users proactively

---

**Last Updated**: 2025-11-22
**Version**: 1.0.0
