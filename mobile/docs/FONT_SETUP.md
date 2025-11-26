# Noto Sans Devanagari Font Setup

## Overview
This document describes the Noto Sans Devanagari font integration for proper Hindi text rendering in the Boloo mobile application.

## Fonts Installed
The following Noto Sans Devanagari font weights have been installed:

1. **Regular** (400) - `NotoSansDevanagari-Regular.ttf`
2. **Medium** (500) - `NotoSansDevanagari-Medium.ttf`
3. **SemiBold** (600) - `NotoSansDevanagari-SemiBold.ttf`
4. **Bold** (700) - `NotoSansDevanagari-Bold.ttf`

## Directory Structure
```
mobile/
├── assets/
│   └── fonts/
│       ├── NotoSansDevanagari-Regular.ttf
│       ├── NotoSansDevanagari-Medium.ttf
│       ├── NotoSansDevanagari-SemiBold.ttf
│       └── NotoSansDevanagari-Bold.ttf
└── src/
    ├── hooks/
    │   ├── useFonts.ts
    │   └── index.ts
    └── constants/
        └── config.ts
```

## Configuration Files

### 1. app.json
Font files are registered in the Expo configuration:

```json
{
  "expo": {
    "fonts": [
      "./assets/fonts/NotoSansDevanagari-Regular.ttf",
      "./assets/fonts/NotoSansDevanagari-Medium.ttf",
      "./assets/fonts/NotoSansDevanagari-SemiBold.ttf",
      "./assets/fonts/NotoSansDevanagari-Bold.ttf"
    ],
    "plugins": [
      "expo-font"
    ]
  }
}
```

### 2. src/hooks/useFonts.ts
Custom hook for loading fonts:

```typescript
import { useFonts as useExpoFonts } from 'expo-font';

export const useFonts = () => {
  const [fontsLoaded, error] = useExpoFonts({
    'NotoSansDevanagari-Regular': require('../../assets/fonts/NotoSansDevanagari-Regular.ttf'),
    'NotoSansDevanagari-Medium': require('../../assets/fonts/NotoSansDevanagari-Medium.ttf'),
    'NotoSansDevanagari-SemiBold': require('../../assets/fonts/NotoSansDevanagari-SemiBold.ttf'),
    'NotoSansDevanagari-Bold': require('../../assets/fonts/NotoSansDevanagari-Bold.ttf'),
  });

  return { fontsLoaded, error };
};
```

### 3. src/constants/config.ts
Font family constants:

```typescript
export const FONTS = {
  regular: 'NotoSansDevanagari-Regular',
  medium: 'NotoSansDevanagari-Medium',
  bold: 'NotoSansDevanagari-Bold',
  semibold: 'NotoSansDevanagari-SemiBold',
};
```

### 4. App.tsx
Font loading in the main app component:

```typescript
import { useFonts } from './src/hooks/useFonts';

export default function App() {
  const { fontsLoaded, error } = useFonts();

  if (error) {
    console.error('Error loading fonts:', error);
  }

  if (!fontsLoaded) {
    return <ActivityIndicator />;
  }

  return <AppNavigator />;
}
```

## Usage in Components

### Using Font Constants
```typescript
import { FONTS } from '../constants/config';
import { Text, StyleSheet } from 'react-native';

const MyComponent = () => (
  <Text style={styles.hindiText}>
    नमस्ते
  </Text>
);

const styles = StyleSheet.create({
  hindiText: {
    fontFamily: FONTS.regular,
    fontSize: 16,
  },
  boldHindiText: {
    fontFamily: FONTS.bold,
    fontSize: 18,
  },
});
```

### Font Weight Mapping
| Weight | Constant | Use Case |
|--------|----------|----------|
| Regular (400) | `FONTS.regular` | Body text, default text |
| Medium (500) | `FONTS.medium` | Emphasized text, labels |
| SemiBold (600) | `FONTS.semibold` | Subheadings, buttons |
| Bold (700) | `FONTS.bold` | Headings, titles |

## Testing Hindi Text Rendering

### Test Strings
Use these Hindi text samples to verify proper rendering:

1. **Basic**: नमस्ते (Namaste/Hello)
2. **Numbers**: १२३४५६७८९० (Devanagari numerals)
3. **Complex**: शिकायत दर्ज करें (Register complaint)
4. **Long text**: कृपया अपनी शिकायत का विवरण दें (Please provide details of your complaint)

### Verification Steps
1. Run the app: `npx expo start`
2. Navigate to screens with Hindi text
3. Verify all Hindi characters render correctly
4. Check that conjunct characters (संयुक्ताक्षर) display properly
5. Confirm different font weights render distinctly

## Dependencies

### Required Packages
```json
{
  "expo-font": "^14.0.9",
  "@expo/vector-icons": "latest"
}
```

### Installation
```bash
npx expo install expo-font @expo/vector-icons
```

## Troubleshooting

### Fonts Not Loading
1. Clear Metro bundler cache: `npx expo start -c`
2. Verify font files exist in `assets/fonts/`
3. Check for typos in font file names
4. Ensure `expo-font` is installed

### Hindi Text Appears as Boxes
1. Confirm fonts are loaded before rendering
2. Check `fontsLoaded` state in App.tsx
3. Verify font family names in StyleSheets match config

### Performance Issues
1. Fonts are loaded once at app startup
2. Use `ActivityIndicator` while fonts load
3. Consider font subsetting for production builds

## Build Configuration

### Android
No additional configuration needed. Fonts are automatically bundled.

### iOS
No additional configuration needed. Fonts are automatically bundled.

## Font Source
Fonts downloaded from: [Google Fonts - Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari)

## License
Noto Sans Devanagari is licensed under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL)

## Next Steps
1. Update all existing components using Hindi text to use Devanagari fonts
2. Test on physical Android and iOS devices
3. Verify text rendering in different screen sizes
4. Consider adding additional font weights if needed (Light, ExtraBold)

## Support
For issues related to Hindi text rendering, check:
- Expo Font Documentation: https://docs.expo.dev/versions/latest/sdk/font/
- Noto Fonts Project: https://github.com/notofonts/devanagari
