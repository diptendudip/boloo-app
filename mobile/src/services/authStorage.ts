import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '../types';

/**
 * Enhanced Authentication Storage Service
 * Handles persistent login with JWT tokens and OTP verification tracking
 */

// Storage Keys - MUST match keys used in api.ts and apiAuth.ts
const KEYS = {
  AUTH_TOKEN: '@boloo_auth_token',
  USER_DATA: '@boloo_user',
  USER_ID: '@boloo_user_id',
  TOKEN_EXPIRY: '@boloo_token_expiry',
  OTP_VERIFIED_PREFIX: '@boloo_otp_verified_', // @boloo_otp_verified_+919876543210
  OTP_TIMESTAMP_PREFIX: '@boloo_otp_timestamp_', // @boloo_otp_timestamp_+919876543210
  LAST_LOGIN_TIME: '@boloo_last_login_time',
  SESSION_ID: '@boloo_session_id',
};

export interface AuthTokenData {
  token: string;
  expiresAt: number; // Unix timestamp
  refreshToken?: string;
}

export interface OTPVerificationData {
  phoneNumber: string;
  verified: boolean;
  timestamp: number; // Unix timestamp
  expiresAt: number; // Unix timestamp (24 hours from verification)
}

/**
 * Enhanced storage service for authentication persistence
 */
export const authStorage = {
  /**
   * Save authentication token with expiry tracking
   * @param token - JWT access token
   * @param expiresIn - Token expiry duration in seconds (default: 24 hours)
   */
  async saveAuthToken(token: string, expiresIn: number = 86400): Promise<void> {
    try {
      const expiresAt = Date.now() + expiresIn * 1000;
      const tokenData: AuthTokenData = {
        token,
        expiresAt,
      };

      await AsyncStorage.multiSet([
        [KEYS.AUTH_TOKEN, token],
        [KEYS.TOKEN_EXPIRY, expiresAt.toString()],
        [KEYS.LAST_LOGIN_TIME, Date.now().toString()],
      ]);

      console.log('[AuthStorage] Token saved successfully, expires at:', new Date(expiresAt).toISOString());
    } catch (error) {
      console.error('[AuthStorage] Failed to save auth token:', error);
      throw error;
    }
  },

  /**
   * Retrieve stored authentication token
   * @returns Token string or null if not found/expired
   */
  async getAuthToken(): Promise<string | null> {
    try {
      const token = await AsyncStorage.getItem(KEYS.AUTH_TOKEN);
      if (!token) {
        console.log('[AuthStorage] No token found');
        return null;
      }

      // Check token expiry
      const expiryStr = await AsyncStorage.getItem(KEYS.TOKEN_EXPIRY);
      if (expiryStr) {
        const expiresAt = parseInt(expiryStr, 10);
        if (Date.now() >= expiresAt) {
          console.log('[AuthStorage] Token expired, clearing...');
          await this.clearAuthToken();
          return null;
        }
      }

      return token;
    } catch (error) {
      console.error('[AuthStorage] Failed to get auth token:', error);
      return null;
    }
  },

  /**
   * Clear authentication token
   */
  async clearAuthToken(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        KEYS.AUTH_TOKEN,
        KEYS.TOKEN_EXPIRY,
        KEYS.LAST_LOGIN_TIME,
        KEYS.SESSION_ID,
      ]);
      console.log('[AuthStorage] Auth token cleared');
    } catch (error) {
      console.error('[AuthStorage] Failed to clear auth token:', error);
      throw error;
    }
  },

  /**
   * Check if token is expired
   * @returns true if token is expired or missing
   */
  async isTokenExpired(): Promise<boolean> {
    try {
      const expiryStr = await AsyncStorage.getItem(KEYS.TOKEN_EXPIRY);
      if (!expiryStr) return true;

      const expiresAt = parseInt(expiryStr, 10);
      return Date.now() >= expiresAt;
    } catch (error) {
      console.error('[AuthStorage] Failed to check token expiry:', error);
      return true;
    }
  },

  /**
   * Get token expiry time
   * @returns Unix timestamp or null
   */
  async getTokenExpiry(): Promise<number | null> {
    try {
      const expiryStr = await AsyncStorage.getItem(KEYS.TOKEN_EXPIRY);
      return expiryStr ? parseInt(expiryStr, 10) : null;
    } catch (error) {
      console.error('[AuthStorage] Failed to get token expiry:', error);
      return null;
    }
  },

  /**
   * Save OTP verification status for a phone number
   * @param phoneNumber - Phone number in E.164 format (+919876543210)
   * @param verified - Verification status
   */
  async saveOTPVerificationStatus(phoneNumber: string, verified: boolean): Promise<void> {
    try {
      const timestamp = Date.now();
      const expiresAt = timestamp + 24 * 60 * 60 * 1000; // 24 hours

      const verificationData: OTPVerificationData = {
        phoneNumber,
        verified,
        timestamp,
        expiresAt,
      };

      await AsyncStorage.multiSet([
        [`${KEYS.OTP_VERIFIED_PREFIX}${phoneNumber}`, verified.toString()],
        [`${KEYS.OTP_TIMESTAMP_PREFIX}${phoneNumber}`, JSON.stringify(verificationData)],
      ]);

      console.log(`[AuthStorage] OTP verification saved for ${phoneNumber}: ${verified}`);
    } catch (error) {
      console.error('[AuthStorage] Failed to save OTP verification:', error);
      throw error;
    }
  },

  /**
   * Get OTP verification status for a phone number
   * @param phoneNumber - Phone number in E.164 format
   * @returns OTP verification data or null if not found/expired
   */
  async getOTPVerificationStatus(phoneNumber: string): Promise<OTPVerificationData | null> {
    try {
      const dataStr = await AsyncStorage.getItem(`${KEYS.OTP_TIMESTAMP_PREFIX}${phoneNumber}`);
      if (!dataStr) {
        console.log(`[AuthStorage] No OTP verification data for ${phoneNumber}`);
        return null;
      }

      const data: OTPVerificationData = JSON.parse(dataStr);

      // Check if verification expired (24 hours)
      if (Date.now() >= data.expiresAt) {
        console.log(`[AuthStorage] OTP verification expired for ${phoneNumber}`);
        await this.clearOTPVerificationStatus(phoneNumber);
        return null;
      }

      return data;
    } catch (error) {
      console.error('[AuthStorage] Failed to get OTP verification status:', error);
      return null;
    }
  },

  /**
   * Clear OTP verification status for a phone number
   * @param phoneNumber - Phone number in E.164 format
   */
  async clearOTPVerificationStatus(phoneNumber: string): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        `${KEYS.OTP_VERIFIED_PREFIX}${phoneNumber}`,
        `${KEYS.OTP_TIMESTAMP_PREFIX}${phoneNumber}`,
      ]);
      console.log(`[AuthStorage] OTP verification cleared for ${phoneNumber}`);
    } catch (error) {
      console.error('[AuthStorage] Failed to clear OTP verification:', error);
      throw error;
    }
  },

  /**
   * Check if user has verified OTP recently (within 24 hours)
   * @param phoneNumber - Phone number in E.164 format
   * @returns true if verified and not expired
   */
  async isOTPVerified(phoneNumber: string): Promise<boolean> {
    const data = await this.getOTPVerificationStatus(phoneNumber);
    return data !== null && data.verified;
  },

  /**
   * Save user data
   * @param user - User object
   */
  async saveUser(user: User): Promise<void> {
    try {
      await AsyncStorage.multiSet([
        [KEYS.USER_DATA, JSON.stringify(user)],
        [KEYS.USER_ID, user.id],
      ]);
      console.log('[AuthStorage] User data saved');
    } catch (error) {
      console.error('[AuthStorage] Failed to save user data:', error);
      throw error;
    }
  },

  /**
   * Get stored user data
   * @returns User object or null
   */
  async getUser(): Promise<User | null> {
    try {
      const userStr = await AsyncStorage.getItem(KEYS.USER_DATA);
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('[AuthStorage] Failed to get user data:', error);
      return null;
    }
  },

  /**
   * Clear user data
   */
  async clearUser(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([KEYS.USER_DATA, KEYS.USER_ID]);
      console.log('[AuthStorage] User data cleared');
    } catch (error) {
      console.error('[AuthStorage] Failed to clear user data:', error);
      throw error;
    }
  },

  /**
   * Clear all authentication and user data
   */
  async clearAll(): Promise<void> {
    try {
      const user = await this.getUser();
      await this.clearAuthToken();
      await this.clearUser();

      // Clear OTP verification for current user
      if (user?.phone) {
        await this.clearOTPVerificationStatus(user.phone);
      }

      console.log('[AuthStorage] All auth data cleared');
    } catch (error) {
      console.error('[AuthStorage] Failed to clear all data:', error);
      throw error;
    }
  },

  /**
   * Get last login timestamp
   * @returns Unix timestamp or null
   */
  async getLastLoginTime(): Promise<number | null> {
    try {
      const timeStr = await AsyncStorage.getItem(KEYS.LAST_LOGIN_TIME);
      return timeStr ? parseInt(timeStr, 10) : null;
    } catch (error) {
      console.error('[AuthStorage] Failed to get last login time:', error);
      return null;
    }
  },

  /**
   * Generate and save session ID
   * @returns Session ID
   */
  async generateSessionId(): Promise<string> {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    await AsyncStorage.setItem(KEYS.SESSION_ID, sessionId);
    return sessionId;
  },

  /**
   * Get current session ID
   * @returns Session ID or null
   */
  async getSessionId(): Promise<string | null> {
    return await AsyncStorage.getItem(KEYS.SESSION_ID);
  },

  /**
   * Check if user session is valid
   * @returns true if valid session exists
   */
  async isSessionValid(): Promise<boolean> {
    try {
      const token = await this.getAuthToken();
      const user = await this.getUser();
      const isExpired = await this.isTokenExpired();

      return !!(token && user && !isExpired);
    } catch (error) {
      console.error('[AuthStorage] Failed to check session validity:', error);
      return false;
    }
  },

  /**
   * Get complete authentication state
   * @returns Authentication state object
   */
  async getAuthState(): Promise<{
    token: string | null;
    user: User | null;
    isExpired: boolean;
    lastLogin: number | null;
    sessionId: string | null;
  }> {
    const token = await this.getAuthToken();
    const user = await this.getUser();
    const isExpired = await this.isTokenExpired();
    const lastLogin = await this.getLastLoginTime();
    const sessionId = await this.getSessionId();

    return {
      token,
      user,
      isExpired,
      lastLogin,
      sessionId,
    };
  },
};
