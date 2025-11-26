# App Store Assets Guide

## 📱 Required Graphics and Media Assets

This guide lists all required graphics assets for Google Play Store and Apple App Store submissions.

---

## Google Play Store Requirements

### 1. App Icon
- **Size**: 512 x 512 pixels
- **Format**: PNG (no transparency)
- **File name**: `icon-512.png`
- **Location**: `/mobile/app-store-assets/icons/`
- **Notes**:
  - 32-bit PNG
  - Must be square
  - No rounded corners
  - No alpha/transparency

### 2. Feature Graphic
- **Size**: 1024 x 500 pixels
- **Format**: PNG or JPG
- **File name**: `feature-graphic.png`
- **Location**: `/mobile/app-store-assets/`
- **Notes**:
  - Displayed prominently in Play Store
  - Should showcase app branding
  - No transparency

### 3. Screenshots (Phone)

**Required**: Minimum 2, maximum 8

**Recommended Sizes**:
- Modern phones: 1080 x 2400 pixels
- Alternative: 1080 x 1920 pixels

**File format**: PNG or JPG
**Location**: `/mobile/app-store-assets/screenshots/android/phone/`

**Naming convention**:
- `phone-01.png`
- `phone-02.png`
- `phone-03.png`
- etc.

**Recommended screenshots**:
1. Home screen / Dashboard
2. Report submission form
3. Camera/Photo upload
4. Location selection
5. Report tracking
6. Category selection
7. Profile/Settings
8. Report details

### 4. Screenshots (7-inch Tablet)

**Required**: Minimum 2
**Size**: 1200 x 1920 pixels
**Location**: `/mobile/app-store-assets/screenshots/android/tablet-7/`

### 5. Screenshots (10-inch Tablet)

**Required**: Minimum 2
**Size**: 1800 x 2560 pixels
**Location**: `/mobile/app-store-assets/screenshots/android/tablet-10/`

### 6. Promo Video (Optional)

**Format**: YouTube link
**Duration**: 30 seconds to 2 minutes
**Content**: App demo/overview

---

## Apple App Store Requirements

### 1. App Icon
- **Size**: 1024 x 1024 pixels
- **Format**: PNG (no transparency)
- **File name**: `icon-1024.png`
- **Location**: `/mobile/app-store-assets/icons/`
- **Notes**:
  - No alpha channel
  - No rounded corners (iOS adds automatically)

### 2. iPhone Screenshots

#### 6.7" Display (iPhone 15 Pro Max, 14 Pro Max)
- **Size**: 1320 x 2868 pixels
- **Required**: 3-10 screenshots
- **Location**: `/mobile/app-store-assets/screenshots/ios/6.7-inch/`
- **File names**: `6.7-01.png`, `6.7-02.png`, etc.

#### 6.5" Display (iPhone 11 Pro Max, XS Max)
- **Size**: 1284 x 2778 pixels
- **Required**: 3-10 screenshots
- **Location**: `/mobile/app-store-assets/screenshots/ios/6.5-inch/`

#### 5.5" Display (iPhone 8 Plus)
- **Size**: 1242 x 2208 pixels
- **Required**: 3-10 screenshots
- **Location**: `/mobile/app-store-assets/screenshots/ios/5.5-inch/`

### 3. iPad Screenshots (Optional but Recommended)

#### 12.9" iPad Pro (3rd gen)
- **Size**: 2048 x 2732 pixels
- **Location**: `/mobile/app-store-assets/screenshots/ios/ipad-12.9/`

#### 11" iPad Pro
- **Size**: 1668 x 2388 pixels
- **Location**: `/mobile/app-store-assets/screenshots/ios/ipad-11/`

### 4. App Preview Video (Optional)

**Sizes Required** (same as screenshots):
- 6.7" Display: 1320 x 2868 pixels
- 6.5" Display: 1284 x 2778 pixels
- 5.5" Display: 1242 x 2208 pixels

**Format**: .mp4 or .mov
**Duration**: 15-30 seconds
**Max file size**: 500 MB
**Location**: `/mobile/app-store-assets/videos/`

---

## Directory Structure

```
/mobile/app-store-assets/
├── icons/
│   ├── icon-512.png          # Google Play
│   ├── icon-1024.png         # App Store
│   └── adaptive-icon.png     # Android adaptive
├── feature-graphic.png       # Google Play
├── screenshots/
│   ├── android/
│   │   ├── phone/
│   │   │   ├── phone-01.png
│   │   │   ├── phone-02.png
│   │   │   └── ...
│   │   ├── tablet-7/
│   │   │   ├── tablet7-01.png
│   │   │   └── tablet7-02.png
│   │   └── tablet-10/
│   │       ├── tablet10-01.png
│   │       └── tablet10-02.png
│   └── ios/
│       ├── 6.7-inch/
│       │   ├── 6.7-01.png
│       │   ├── 6.7-02.png
│       │   └── ...
│       ├── 6.5-inch/
│       │   ├── 6.5-01.png
│       │   └── ...
│       └── 5.5-inch/
│           ├── 5.5-01.png
│           └── ...
├── videos/
│   ├── android/
│   │   └── promo.mp4
│   └── ios/
│       ├── 6.7-preview.mp4
│       └── 6.5-preview.mp4
└── descriptions/
    ├── play-store-description.txt
    ├── app-store-description.txt
    └── release-notes.txt
```

---

## Screenshot Content Guidelines

### What to Include

1. **Welcome/Dashboard**
   - Show clean, populated interface
   - Display key features prominently
   - Use realistic but clean data

2. **Core Feature - Report Submission**
   - Show form with example data filled in
   - Display camera/photo upload
   - Show category selection

3. **Location/Map View**
   - Display map with pin
   - Show location accuracy
   - Clean map view

4. **Report Tracking**
   - Show list of reports
   - Display status indicators
   - Show progress/timeline

5. **Report Details**
   - Full report view
   - Comments/updates
   - Status history

6. **Profile/Settings**
   - User information
   - App settings
   - Language options

### Best Practices

**DO:**
- Use high-quality mockup data
- Show app in action
- Use consistent branding
- Highlight unique features
- Show multi-language support
- Use real device screenshots

**DON'T:**
- Use Lorem ipsum text
- Show error states
- Include personal information
- Use low-resolution images
- Show empty states
- Include watermarks

---

## Tools for Creating Screenshots

### 1. Device Screenshots (Recommended)

**Android**:
```bash
# Using ADB
adb shell screencap /sdcard/screenshot.png
adb pull /sdcard/screenshot.png

# Or use Android Studio Device Manager
```

**iOS**:
```bash
# Using Simulator
xcrun simctl io booted screenshot screenshot.png

# Or use Xcode Simulator: Cmd+S
```

### 2. Screenshot Framing Tools

- **Mockuuups**: https://mockuuups.studio
- **Previewed**: https://previewed.app
- **Shotbot**: https://shotbot.io
- **Screely**: https://www.screely.com

### 3. Design Tools

- **Figma**: https://figma.com
- **Sketch**: https://sketch.com
- **Adobe XD**: https://adobe.com/xd
- **Canva**: https://canva.com

### 4. Screenshot Management

- **Fastlane Screenshots**: Automate screenshot generation
- **Expo Screenshot**: Built-in Expo tools

---

## Creating Screenshots with Expo

### Using Expo Go

1. Open app in Expo Go
2. Navigate to desired screen
3. Take screenshot on device
4. Transfer to computer
5. Resize to required dimensions

### Using Expo Dev Client

```bash
# Build dev client
eas build --profile preview --platform ios

# Install on device or simulator
# Navigate and capture screenshots
```

---

## Text Content Requirements

### Google Play Store

#### Short Description (80 characters)
```
Report civic issues easily. Help improve your community with Boloo.
```

#### Full Description (4000 characters max)

See: `/mobile/app-store-assets/descriptions/play-store-description.txt`

**Structure**:
1. Opening hook (1-2 sentences)
2. Key features (bullet points)
3. Categories/Use cases
4. Call to action

### Apple App Store

#### Subtitle (30 characters)
```
Report civic issues easily
```

#### Description (4000 characters max)

See: `/mobile/app-store-assets/descriptions/app-store-description.txt`

**Structure**:
1. Opening statement
2. KEY FEATURES section
3. MAKE A DIFFERENCE section
4. PRIVACY section
5. Contact information

#### Keywords (100 characters, comma-separated)
```
civic,reporting,grievance,community,issue,complaint,municipal,local,government,service
```

#### Promotional Text (170 characters)
```
Now available! Report civic issues in your community easily. Track progress and make a real difference. Download now and join thousands of active citizens!
```

---

## Asset Optimization

### Image Optimization Tools

```bash
# Install ImageMagick
brew install imagemagick

# Resize image
convert input.png -resize 1024x512 output.png

# Compress PNG
pngquant input.png --output output.png

# Compress JPG
jpegoptim --max=85 input.jpg
```

### Online Tools
- **TinyPNG**: https://tinypng.com
- **ImageOptim**: https://imageoptim.com (macOS)
- **Squoosh**: https://squoosh.app

---

## Localization

If supporting multiple languages, provide:

### Screenshots
- Separate screenshots for each language
- Update folder structure: `screenshots/android/phone/en/`, `screenshots/android/phone/hi/`

### Store Listings
- Translated descriptions
- Translated keywords
- Localized screenshots

---

## Quality Checklist

Before uploading assets:

- [ ] All images are correct size
- [ ] Images are high quality (no pixelation)
- [ ] No personal/sensitive information visible
- [ ] Consistent branding across all images
- [ ] Text is readable on all devices
- [ ] App icon has no transparency
- [ ] Feature graphic represents app well
- [ ] Screenshots show real app functionality
- [ ] All required sizes provided
- [ ] File formats are correct
- [ ] File names follow convention
- [ ] Images optimized for size
- [ ] Checked on different screen sizes

---

## Template Files

### Feature Graphic Template (Photoshop/Figma)

Layers:
1. Background (1024x500)
2. App branding/logo
3. Key feature screenshots (3-4)
4. App name and tagline
5. Call to action (optional)

### Screenshot Frame Template

Elements:
- Device frame (optional)
- Status bar
- App screenshot
- Caption (optional)
- Branding elements

---

## Automated Screenshot Generation

### Using Fastlane

```ruby
# Fastfile
lane :screenshots do
  capture_screenshots(
    devices: [
      "iPhone 15 Pro Max",
      "iPhone 11 Pro Max",
      "iPhone 8 Plus"
    ],
    languages: ["en-US", "hi-IN"],
    output_directory: "./app-store-assets/screenshots/ios"
  )
end
```

### Using Expo + Playwright

```typescript
// screenshot.test.ts
import { test } from '@playwright/test';

test('capture screenshots', async ({ page }) => {
  await page.goto('http://localhost:19006');

  // Navigate to each screen and capture
  await page.screenshot({
    path: 'screenshots/home.png',
    fullPage: true
  });
});
```

---

## Support

For asset creation help:
- **Design Team**: design@boloo.com
- **Marketing**: marketing@boloo.com

For technical issues:
- **Dev Team**: dev@boloo.com

---

**Last Updated**: 2025-11-22
**Version**: 1.0.0
