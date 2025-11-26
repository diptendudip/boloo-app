# Font Installation Testing Instructions

## Installation Completed ✓

Noto Sans Devanagari fonts have been successfully installed and configured in the Boloo mobile app.

## Files Modified/Created

### Created:
1. `/Users/diptendu/boloo app/boloo-app/mobile/assets/fonts/NotoSansDevanagari-Regular.ttf` (287KB)
2. `/Users/diptendu/boloo app/boloo-app/mobile/assets/fonts/NotoSansDevanagari-Medium.ttf` (287KB)
3. `/Users/diptendu/boloo app/boloo-app/mobile/assets/fonts/NotoSansDevanagari-SemiBold.ttf` (287KB)
4. `/Users/diptendu/boloo app/boloo-app/mobile/assets/fonts/NotoSansDevanagari-Bold.ttf` (287KB)
5. `/Users/diptendu/boloo app/boloo-app/mobile/src/hooks/useFonts.ts`
6. `/Users/diptendu/boloo app/boloo-app/mobile/src/hooks/index.ts`
7. `/Users/diptendu/boloo app/boloo-app/mobile/src/components/FontTest.tsx`
8. `/Users/diptendu/boloo app/boloo-app/mobile/docs/FONT_SETUP.md`

### Modified:
1. `/Users/diptendu/boloo app/boloo-app/mobile/app.json` - Added fonts array and expo-font plugin
2. `/Users/diptendu/boloo app/boloo-app/mobile/src/constants/config.ts` - Updated FONTS constant
3. `/Users/diptendu/boloo app/boloo-app/mobile/App.tsx` - Added font loading logic

## Testing Steps

### 1. Clear Cache and Start App
```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npx expo start -c
```

### 2. Run on Device/Emulator
- Press 'a' for Android
- Press 'i' for iOS
- Scan QR code with Expo Go app

### 3. Verify Font Loading
1. Check that the app shows a loading spinner while fonts load
2. Ensure the app doesn't crash or show errors
3. Look for any console warnings about font loading

### 4. Test Hindi Text Rendering

#### Option A: Use FontTest Component
Add this to your navigation to test fonts:

```typescript
// In your navigation file
import FontTest from '../components/FontTest';

// Add a route
<Stack.Screen name="FontTest" component={FontTest} />
```

Then navigate to the FontTest screen to see all font weights.

#### Option B: Manual Testing
Navigate to existing screens with Hindi text:
- Home screen
- Report submission screen
- Category selection
- Any screen with Hindi labels

### 5. Visual Checks
Verify that:
- [ ] Hindi text is clearly readable
- [ ] Different font weights are visually distinct
- [ ] Conjunct characters (संयुक्ताक्षर) render correctly
- [ ] Devanagari numbers (१२३) display properly
- [ ] No boxes or missing glyphs appear
- [ ] Text alignment is correct

### 6. Performance Checks
- [ ] App startup time is acceptable
- [ ] No lag when scrolling Hindi text
- [ ] Memory usage is normal

## Expected Behavior

### Font Loading Sequence:
1. App starts
2. Shows loading spinner (ActivityIndicator)
3. Fonts load (should take 1-2 seconds)
4. App renders with Hindi text using Noto Sans Devanagari

### Font Usage:
```typescript
// All Hindi text should now use these fonts:
FONTS.regular    // Body text
FONTS.medium     // Labels, emphasized text
FONTS.semibold   // Subheadings, buttons
FONTS.bold       // Headings, titles
```

## Troubleshooting

### Issue: Fonts Not Loading
**Solution:**
```bash
# Clear all caches
npx expo start -c

# Rebuild the app
rm -rf node_modules
npm install
npx expo start -c
```

### Issue: Hindi Text Appears as Boxes
**Check:**
1. Verify font files exist in `assets/fonts/`
2. Check `fontsLoaded` is true before rendering
3. Ensure font family names match in StyleSheets

### Issue: Performance Issues
**Fix:**
- Fonts should load once at startup
- Check that you're not reloading fonts on every render
- Verify `useFonts` is called once in App.tsx

## Example Test Cases

### Test 1: Basic Hindi Text
```
Input: नमस्ते
Expected: Clear, readable Hindi greeting
```

### Test 2: Complex Conjuncts
```
Input: क्षत्रिय, ज्ञान, विद्यालय
Expected: All conjunct characters render correctly
```

### Test 3: Numbers
```
Input: १२३४५६७८९०
Expected: Devanagari numerals display properly
```

### Test 4: Long Paragraph
```
Input: बोलू ऐप नागरिकों को अपनी शिकायतें दर्ज करने और ट्रैक करने में मदद करता है।
Expected: Full paragraph renders without issues
```

## Next Steps

After successful testing:
1. Update all existing components to use Devanagari fonts
2. Test on physical Android and iOS devices
3. Verify in different screen sizes
4. Consider adding loading error handling
5. Update UI components to use font constants from config.ts

## Documentation

For detailed setup information, see:
`/Users/diptendu/boloo app/boloo-app/mobile/docs/FONT_SETUP.md`

## Support

If you encounter issues:
1. Check console for error messages
2. Verify all files were created correctly
3. Ensure expo-font is installed: `npm list expo-font`
4. Review the FONT_SETUP.md documentation
