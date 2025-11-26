/**
 * Hindi-first error messages with context-aware recovery actions
 */

export interface ErrorMessage {
  hi: string;
  en: string;
  action: 'RETRY' | 'RETRY_LATER' | 'GO_HOME' | 'CONTACT_SUPPORT' | 'CHECK_INTERNET' | 'LOGIN_AGAIN';
  icon?: string;
}

export const ERROR_MESSAGES: Record<string, ErrorMessage> = {
  // Network Errors
  NO_INTERNET: {
    hi: 'इंटरनेट कनेक्शन नहीं है',
    en: 'No internet connection',
    action: 'CHECK_INTERNET',
    icon: '📡'
  },
  NETWORK_ERROR: {
    hi: 'नेटवर्क में समस्या है',
    en: 'Network error',
    action: 'RETRY',
    icon: '⚠️'
  },
  SLOW_NETWORK: {
    hi: 'इंटरनेट बहुत धीमा है',
    en: 'Network is too slow',
    action: 'RETRY_LATER',
    icon: '🐢'
  },

  // Server Errors
  SERVER_ERROR: {
    hi: 'सर्वर में समस्या है',
    en: 'Server error',
    action: 'RETRY_LATER',
    icon: '🔧'
  },
  SERVICE_UNAVAILABLE: {
    hi: 'सेवा अभी उपलब्ध नहीं है',
    en: 'Service unavailable',
    action: 'RETRY_LATER',
    icon: '⏸️'
  },

  // Authentication Errors
  INVALID_OTP: {
    hi: 'गलत OTP। कृपया फिर से प्रयास करें',
    en: 'Invalid OTP. Please try again',
    action: 'RETRY',
    icon: '❌'
  },
  OTP_EXPIRED: {
    hi: 'OTP समय समाप्त हो गया है',
    en: 'OTP expired',
    action: 'RETRY',
    icon: '⏰'
  },
  UNAUTHORIZED: {
    hi: 'कृपया फिर से लॉगिन करें',
    en: 'Please login again',
    action: 'LOGIN_AGAIN',
    icon: '🔒'
  },
  SESSION_EXPIRED: {
    hi: 'सत्र समाप्त हो गया है',
    en: 'Session expired',
    action: 'LOGIN_AGAIN',
    icon: '⏲️'
  },

  // Data Errors
  CASE_NOT_FOUND: {
    hi: 'शिकायत नहीं मिली',
    en: 'Case not found',
    action: 'GO_HOME',
    icon: '🔍'
  },
  DATA_NOT_FOUND: {
    hi: 'जानकारी नहीं मिली',
    en: 'Data not found',
    action: 'GO_HOME',
    icon: '📭'
  },

  // Validation Errors
  INVALID_PHONE: {
    hi: 'मोबाइल नंबर गलत है',
    en: 'Invalid phone number',
    action: 'RETRY',
    icon: '📱'
  },
  INVALID_INPUT: {
    hi: 'कुछ जानकारी गलत है',
    en: 'Invalid input',
    action: 'RETRY',
    icon: '✏️'
  },
  REQUIRED_FIELD: {
    hi: 'यह जानकारी ज़रूरी है',
    en: 'This field is required',
    action: 'RETRY',
    icon: '⚠️'
  },

  // Upload Errors
  FILE_TOO_LARGE: {
    hi: 'फ़ाइल बहुत बड़ी है (अधिकतम 10MB)',
    en: 'File too large (max 10MB)',
    action: 'RETRY',
    icon: '📦'
  },
  UPLOAD_FAILED: {
    hi: 'फ़ाइल अपलोड नहीं हो सकी',
    en: 'Upload failed',
    action: 'RETRY',
    icon: '📤'
  },

  // Audio Errors
  RECORDING_FAILED: {
    hi: 'रिकॉर्डिंग में समस्या आई',
    en: 'Recording failed',
    action: 'RETRY',
    icon: '🎙️'
  },
  AUDIO_PERMISSION_DENIED: {
    hi: 'माइक्रोफ़ोन की अनुमति नहीं मिली',
    en: 'Microphone permission denied',
    action: 'CONTACT_SUPPORT',
    icon: '🚫'
  },

  // Generic Errors
  UNKNOWN_ERROR: {
    hi: 'कुछ गड़बड़ हो गई',
    en: 'Something went wrong',
    action: 'RETRY',
    icon: '❓'
  },
  TRY_AGAIN: {
    hi: 'कृपया फिर से कोशिश करें',
    en: 'Please try again',
    action: 'RETRY',
    icon: '🔄'
  }
};

/**
 * Get error message from HTTP status code
 */
export function getErrorFromStatus(statusCode: number): ErrorMessage {
  switch (statusCode) {
    case 400:
      return ERROR_MESSAGES.INVALID_INPUT;
    case 401:
      return ERROR_MESSAGES.UNAUTHORIZED;
    case 403:
      return ERROR_MESSAGES.UNAUTHORIZED;
    case 404:
      return ERROR_MESSAGES.DATA_NOT_FOUND;
    case 408:
      return ERROR_MESSAGES.SLOW_NETWORK;
    case 500:
    case 502:
    case 503:
      return ERROR_MESSAGES.SERVER_ERROR;
    case 504:
      return ERROR_MESSAGES.SLOW_NETWORK;
    default:
      return ERROR_MESSAGES.UNKNOWN_ERROR;
  }
}

/**
 * Get action button text in Hindi
 */
export function getActionText(action: ErrorMessage['action']): { hi: string; en: string } {
  switch (action) {
    case 'RETRY':
      return { hi: 'फिर से कोशिश करें', en: 'Try Again' };
    case 'RETRY_LATER':
      return { hi: 'बाद में कोशिश करें', en: 'Try Later' };
    case 'GO_HOME':
      return { hi: 'होम पर जाएं', en: 'Go Home' };
    case 'CONTACT_SUPPORT':
      return { hi: 'सहायता संपर्क करें', en: 'Contact Support' };
    case 'CHECK_INTERNET':
      return { hi: 'इंटरनेट चेक करें', en: 'Check Internet' };
    case 'LOGIN_AGAIN':
      return { hi: 'फिर से लॉगिन करें', en: 'Login Again' };
    default:
      return { hi: 'ठीक है', en: 'OK' };
  }
}
