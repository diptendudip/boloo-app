/**
 * OTP Flow Messages and Error Codes
 *
 * Centralized message constants for OTP authentication flow
 */

export const OTP_MESSAGES = {
  // Success messages
  OTP_SENT: 'OTP sent successfully to your phone',
  OTP_RESENT: 'OTP resent successfully',
  OTP_VERIFIED: 'Phone number verified successfully',
  VOICE_OTP_SENT: 'You will receive a call with your OTP shortly',

  // Error messages - Phone validation
  PHONE_REQUIRED: 'Phone number is required',
  PHONE_INVALID: 'Please enter a valid 10-digit phone number',
  PHONE_INVALID_START: 'Phone number must start with 6, 7, 8, or 9',
  PHONE_TOO_SHORT: 'Phone number must be 10 digits',
  PHONE_TOO_LONG: 'Phone number cannot exceed 10 digits',

  // Error messages - OTP validation
  OTP_REQUIRED: 'Please enter the OTP code',
  OTP_INCOMPLETE: 'Please enter the complete 6-digit OTP',
  OTP_INVALID: 'Invalid OTP. Please try again',
  OTP_EXPIRED: 'OTP has expired. Please request a new one',
  OTP_ATTEMPTS_EXCEEDED: 'Too many failed attempts. Please request a new OTP',

  // Error messages - Network & Server
  NETWORK_ERROR: 'Network error. Please check your internet connection',
  SERVER_ERROR: 'Server error. Please try again later',
  REQUEST_TIMEOUT: 'Request timeout. Please try again',
  SERVICE_UNAVAILABLE: 'Service temporarily unavailable',

  // Error messages - Rate limiting
  TOO_MANY_REQUESTS: 'Too many OTP requests. Please try again after some time',
  RESEND_COOLDOWN: 'Please wait before requesting another OTP',

  // General messages
  TESTING_MODE: 'Testing Mode: Use OTP 123456',
  CHANGE_NUMBER: 'Want to change your number?',
};

export const OTP_ERROR_CODES = {
  INVALID_PHONE: 'INVALID_PHONE',
  INVALID_OTP: 'INVALID_OTP',
  OTP_EXPIRED: 'OTP_EXPIRED',
  OTP_NOT_FOUND: 'OTP_NOT_FOUND',
  TOO_MANY_ATTEMPTS: 'TOO_MANY_ATTEMPTS',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  NETWORK_ERROR: 'NETWORK_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  TIMEOUT: 'TIMEOUT',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
};

/**
 * Get user-friendly error message from error code or API response
 */
export const getOTPErrorMessage = (error: any): string => {
  // Check for error code in response
  if (error?.response?.data?.error_code) {
    const code = error.response.data.error_code;

    switch (code) {
      case OTP_ERROR_CODES.INVALID_PHONE:
        return OTP_MESSAGES.PHONE_INVALID;
      case OTP_ERROR_CODES.INVALID_OTP:
        return OTP_MESSAGES.OTP_INVALID;
      case OTP_ERROR_CODES.OTP_EXPIRED:
        return OTP_MESSAGES.OTP_EXPIRED;
      case OTP_ERROR_CODES.TOO_MANY_ATTEMPTS:
        return OTP_MESSAGES.OTP_ATTEMPTS_EXCEEDED;
      case OTP_ERROR_CODES.RATE_LIMIT_EXCEEDED:
        return OTP_MESSAGES.TOO_MANY_REQUESTS;
      default:
        return error.response.data.message || OTP_MESSAGES.SERVER_ERROR;
    }
  }

  // Check for HTTP status codes
  if (error?.response?.status) {
    const status = error.response.status;

    if (status === 429) return OTP_MESSAGES.TOO_MANY_REQUESTS;
    if (status === 503) return OTP_MESSAGES.SERVICE_UNAVAILABLE;
    if (status >= 500) return OTP_MESSAGES.SERVER_ERROR;
    if (status === 408) return OTP_MESSAGES.REQUEST_TIMEOUT;
  }

  // Check for network errors
  if (error?.message?.toLowerCase().includes('network')) {
    return OTP_MESSAGES.NETWORK_ERROR;
  }

  if (error?.message?.toLowerCase().includes('timeout')) {
    return OTP_MESSAGES.REQUEST_TIMEOUT;
  }

  // Return error message if available, otherwise default
  return error?.response?.data?.message || error?.message || OTP_MESSAGES.SERVER_ERROR;
};
