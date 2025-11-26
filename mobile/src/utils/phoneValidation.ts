/**
 * Phone Number Validation Utility
 *
 * Handles Indian phone number validation and formatting
 */

export interface PhoneValidationResult {
  isValid: boolean;
  formatted?: string;
  error?: string;
}

/**
 * Validates Indian phone number
 * Rules:
 * - Must be exactly 10 digits
 * - Must start with 6, 7, 8, or 9
 * - No special characters allowed (except when formatting)
 */
export const validateIndianPhoneNumber = (phone: string): PhoneValidationResult => {
  // Remove all non-digit characters for validation
  const cleaned = phone.replace(/\D/g, '');

  // Check length
  if (cleaned.length === 0) {
    return {
      isValid: false,
      error: 'Phone number is required'
    };
  }

  if (cleaned.length < 10) {
    return {
      isValid: false,
      error: `Phone number must be 10 digits (${cleaned.length}/10)`
    };
  }

  if (cleaned.length > 10) {
    return {
      isValid: false,
      error: 'Phone number cannot exceed 10 digits'
    };
  }

  // Check if starts with valid digit (6-9)
  const firstDigit = cleaned[0];
  if (!['6', '7', '8', '9'].includes(firstDigit)) {
    return {
      isValid: false,
      error: 'Phone number must start with 6, 7, 8, or 9'
    };
  }

  // Valid phone number
  return {
    isValid: true,
    formatted: `+91${cleaned}`
  };
};

/**
 * Format phone number for display (adds +91 prefix)
 */
export const formatPhoneNumber = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '');

  if (cleaned.length === 10) {
    return `+91${cleaned}`;
  }

  if (cleaned.length === 12 && cleaned.startsWith('91')) {
    return `+${cleaned}`;
  }

  return phone;
};

/**
 * Extract digits only from phone number
 */
export const cleanPhoneNumber = (phone: string): string => {
  return phone.replace(/\D/g, '');
};

/**
 * Format phone for display with spacing (e.g., +91 98765 43210)
 */
export const formatPhoneForDisplay = (phone: string): string => {
  const cleaned = cleanPhoneNumber(phone);

  if (cleaned.length === 10) {
    return `+91 ${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
  }

  if (cleaned.length === 12 && cleaned.startsWith('91')) {
    const number = cleaned.slice(2);
    return `+91 ${number.slice(0, 5)} ${number.slice(5)}`;
  }

  return phone;
};

/**
 * Check if phone number is in E.164 format (+91XXXXXXXXXX)
 */
export const isE164Format = (phone: string): boolean => {
  const e164Regex = /^\+91[6-9]\d{9}$/;
  return e164Regex.test(phone);
};
