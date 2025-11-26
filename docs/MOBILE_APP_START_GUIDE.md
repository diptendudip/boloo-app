# Mobile App Start Guide - Quick Fix

**Issue:** Node.js version mismatch and wrong directory

---

## 🚨 Problems Identified

1. **Wrong Directory**: You ran `npx expo start` from `/Users/diptendu/boloo app/` instead of `/Users/diptendu/boloo app/boloo-app/mobile/`
2. **Node.js Version**: Using Node v18.20.8, but packages require Node v20.19.4+

---

## ✅ Quick Solution (Choose One)

### **Option A: Use Your Current Node Version (Recommended for Testing)**

The warnings are just warnings - the app will likely still work for development:

```bash
# Navigate to correct directory
cd "/Users/diptendu/boloo app/boloo-app/mobile"

# Start Expo
npx expo start
```

**Press:**
- `a` to open on Android device/emulator
- `i` to open on iOS simulator (Mac only)
- `w` to open in web browser

---

### **Option B: Upgrade Node.js (Better Long-Term)**

If Option A doesn't work, upgrade Node.js:

```bash
# Check current version
node --version  # Shows v18.20.8

# Using Homebrew (recommended)
brew install node@20

# Or using nvm (if installed)
nvm install 20
nvm use 20

# Verify new version
node --version  # Should show v20.x.x

# Then navigate and start
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npx expo start
```

---

## 🔧 If You Accidentally Installed Expo in Root

You installed expo in the wrong directory. Clean it up:

```bash
# Remove from root (wrong location)
cd "/Users/diptendu/boloo app"
rm -rf node_modules package-lock.json

# Correct location already has expo installed
cd "/Users/diptendu/boloo app/boloo-app/mobile"
ls -la package.json  # Should exist here
```

---

## 📱 Expected Output When Starting Correctly

When you run `npx expo start` from the **mobile** directory, you should see:

```
Starting Metro Bundler
› Metro waiting on exp://192.168.x.x:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)

› Press a │ open Android
› Press w │ open web

› Press j │ open debugger
› Press r │ reload app
› Press m │ toggle menu
```

---

## 🧪 Quick Test Commands

```bash
# 1. Navigate to mobile directory
cd "/Users/diptendu/boloo app/boloo-app/mobile"

# 2. Verify package.json exists
cat package.json | grep "expo"

# 3. Check Node version (warnings OK for now)
node --version

# 4. Start Expo
npx expo start

# 5. If it starts successfully, press 'a' for Android or 'w' for web
```

---

## 🎯 Testing Checklist (Once App Starts)

After the app starts successfully, test:

1. **Audio Recording** (with new expo-audio):
   - Navigate to chat/grievance submission
   - Tap microphone button
   - Record a short audio message
   - Verify it uploads without errors

2. **Conversation Flow**:
   - Submit a test grievance (text or audio)
   - Verify AI responds naturally (using Azure OpenAI)
   - Check conversation completion indicator

3. **Performance** (with Hermes enabled):
   - App should feel snappier
   - Check startup time
   - Verify no crashes or freezes

---

## ⚠️ Troubleshooting

### **If Metro Bundler Fails:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
rm -rf node_modules
npm install
npx expo start --clear
```

### **If TypeScript Errors:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npx tsc --noEmit  # Check for errors
```

### **If expo-audio Import Errors:**
The ChatInterface.tsx has been updated - but if you see errors:
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npm install expo-audio@~1.0.14
npx expo start --clear
```

---

## 📊 What's Different After Our Fixes

1. **expo-audio** instead of expo-av (modern, maintained)
2. **Hermes engine** enabled (faster performance)
3. **Backend uses real Azure OpenAI** (not mock)
4. **Real SLA tracking** (not dummy data)

---

## 🚀 Next Steps After App Starts

1. Test audio recording on device
2. Test conversation flow
3. Verify backend connection (should be localhost:8000)
4. Build APK for distribution
5. Deploy backend to Azure

---

*Created: Nov 19, 2025*
*Issue: Wrong directory + Node version mismatch*
*Solution: cd to mobile/ directory first*
