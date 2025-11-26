import api from './api';
import { storage } from './storage';
import { AuthResponse, User } from '../types';

export interface OTPRequestResponse {
  success: boolean;
  message: string;
  request_id?: string;
  type?: string;
}

export interface OTPVerifyResponse {
  success: boolean;
  message: string;
  access_token?: string;
  user?: User;
}

export const authService = {
  /**
   * Request SMS OTP via MSG91
   * Sends OTP to the provided phone number
   *
   * @param phoneNumber - Phone number in E.164 format (e.g., +919876543210)
   * @returns Promise with request details
   */
  async requestOTP(phoneNumber: string): Promise<OTPRequestResponse> {
    console.log('[Auth] Requesting OTP for:', phoneNumber);

    try {
      const response = await api.post('/v1/auth/otp/request', {
        phone_number: phoneNumber
      });

      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to send OTP');
      }

      console.log('[Auth] OTP sent successfully');
      return response.data;
    } catch (error: any) {
      console.error('[Auth] OTP request failed:', error);
      throw error;
    }
  },

  /**
   * Resend OTP via SMS or Voice
   * Supports both SMS retry and voice call OTP delivery
   *
   * @param phoneNumber - Phone number in E.164 format
   * @param retryType - Type of retry: 'sms' or 'voice'
   * @returns Promise with resend confirmation
   */
  async resendOTP(
    phoneNumber: string,
    retryType: 'sms' | 'voice' = 'sms'
  ): Promise<OTPRequestResponse> {
    console.log(`[Auth] Resending OTP (${retryType}) for:`, phoneNumber);

    try {
      const response = await api.post('/v1/auth/otp/resend', {
        phone_number: phoneNumber,
        retry_type: retryType
      });

      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to resend OTP');
      }

      console.log(`[Auth] OTP resent via ${retryType}`);
      return response.data;
    } catch (error: any) {
      console.error('[Auth] OTP resend failed:', error);
      throw error;
    }
  },

  /**
   * Verify SMS OTP
   * Validates the OTP code and authenticates the user
   *
   * @param phoneNumber - Phone number in E.164 format
   * @param otp - 6-digit OTP code
   * @returns Promise with authentication response
   */
  async verifyOTP(phoneNumber: string, otp: string): Promise<AuthResponse> {
    console.log('[Auth] Verifying OTP for:', phoneNumber);

    try {
      const response = await api.post<AuthResponse>('/v1/auth/otp/verify', {
        phone_number: phoneNumber,
        otp_code: otp
      });

      // Store token and user data
      await storage.setToken(response.data.access_token);
      await storage.setUser(response.data.user);

      console.log('[Auth] OTP verified successfully');
      return response.data;
    } catch (error: any) {
      console.error('[Auth] OTP verification failed:', error);
      throw error;
    }
  },

  /**
   * Logout user
   * Clears all stored authentication data
   */
  async logout(): Promise<void> {
    console.log('[Auth] Logging out user');
    await storage.clearAll();
  },

  /**
   * Get currently authenticated user
   * @returns User object or null if not authenticated
   */
  async getCurrentUser(): Promise<User | null> {
    return await storage.getUser();
  },

  /**
   * Check if user is authenticated
   * @returns true if valid token exists
   */
  async isAuthenticated(): Promise<boolean> {
    const token = await storage.getToken();
    return !!token;
  },
};
