import {
  useFonts as useNotoSansDevanagari,
  NotoSansDevanagari_400Regular,
  NotoSansDevanagari_500Medium,
  NotoSansDevanagari_600SemiBold,
  NotoSansDevanagari_700Bold,
} from '@expo-google-fonts/noto-sans-devanagari';

/**
 * Custom hook to load Noto Sans Devanagari fonts for proper Hindi text rendering
 * Returns loading state and error (if any)
 *
 * Uses @expo-google-fonts package for reliable font loading
 */
export const useFonts = () => {
  const [fontsLoaded, error] = useNotoSansDevanagari({
    'NotoSansDevanagari-Regular': NotoSansDevanagari_400Regular,
    'NotoSansDevanagari-Medium': NotoSansDevanagari_500Medium,
    'NotoSansDevanagari-SemiBold': NotoSansDevanagari_600SemiBold,
    'NotoSansDevanagari-Bold': NotoSansDevanagari_700Bold,
  });

  return {
    fontsLoaded,
    error,
  };
};

export default useFonts;
