import Constants from 'expo-constants';

// Production URL - used for web deployment (bultoo.com)
export const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://boloo-backend-api.azurewebsites.net';
export const API_BASE_URL = API_URL; // Alias for compatibility with different services

export const COLORS = {
  primary: '#2563eb',
  secondary: '#64748b',
  success: '#10b981',
  error: '#ef4444',
  warning: '#f59e0b',
  background: '#f8fafc',
  white: '#ffffff',
  black: '#0f172a',
  gray: {
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  }
};

export const FONTS = {
  regular: 'NotoSansDevanagari-Regular',
  medium: 'NotoSansDevanagari-Medium',
  bold: 'NotoSansDevanagari-Bold',
  semibold: 'NotoSansDevanagari-SemiBold',
};

export const SIZES = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  xxl: 24,
};

export const APP_CONFIG = {
  maxAudioDuration: 300, // 5 minutes in seconds
  maxPhotos: 5,
  maxPhotoSize: 5 * 1024 * 1024, // 5MB
};
