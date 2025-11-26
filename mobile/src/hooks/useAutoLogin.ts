import { useState, useEffect } from 'react';
import { authStorage } from '../services/authStorage';
import { User } from '../types';
import api from '../services/api';

export interface AutoLoginState {
  isChecking: boolean;
  isAuthenticated: boolean;
  user: User | null;
  error: string | null;
}

/**
 * Hook to automatically restore user session on app start
 * Checks for stored token, validates it, and restores user session
 */
export const useAutoLogin = () => {
  const [state, setState] = useState<AutoLoginState>({
    isChecking: true,
    isAuthenticated: false,
    user: null,
    error: null,
  });

  useEffect(() => {
    checkAndRestoreSession();
  }, []);

  const checkAndRestoreSession = async () => {
    try {
      console.log('[AutoLogin] Checking for stored session...');

      // Get stored authentication data
      const authState = await authStorage.getAuthState();

      if (!authState.token || !authState.user) {
        console.log('[AutoLogin] No stored session found');
        setState({
          isChecking: false,
          isAuthenticated: false,
          user: null,
          error: null,
        });
        return;
      }

      // Check if token is expired
      if (authState.isExpired) {
        console.log('[AutoLogin] Token expired, clearing session...');
        await authStorage.clearAll();
        setState({
          isChecking: false,
          isAuthenticated: false,
          user: null,
          error: 'Session expired',
        });
        return;
      }

      // In development mode, accept dummy tokens
      if (__DEV__ && authState.token.startsWith('dummy-token-')) {
        console.log('[AutoLogin] Development mode - accepting dummy token');
        setState({
          isChecking: false,
          isAuthenticated: true,
          user: authState.user,
          error: null,
        });
        return;
      }

      // Production mode: Validate token with backend
      try {
        console.log('[AutoLogin] Validating token with backend...');
        const response = await api.get('/v1/auth/verify', {
          headers: {
            Authorization: `Bearer ${authState.token}`,
          },
        });

        if (response.data.success) {
          console.log('[AutoLogin] Token valid, session restored');

          // Update user data if backend returned updated info
          if (response.data.user) {
            await authStorage.saveUser(response.data.user);
            setState({
              isChecking: false,
              isAuthenticated: true,
              user: response.data.user,
              error: null,
            });
          } else {
            setState({
              isChecking: false,
              isAuthenticated: true,
              user: authState.user,
              error: null,
            });
          }
        } else {
          throw new Error('Token validation failed');
        }
      } catch (error: any) {
        console.error('[AutoLogin] Token validation failed:', error);

        // Token invalid, clear session
        await authStorage.clearAll();
        setState({
          isChecking: false,
          isAuthenticated: false,
          user: null,
          error: 'Invalid or expired session',
        });
      }
    } catch (error: any) {
      console.error('[AutoLogin] Session check failed:', error);

      // Clear potentially corrupted data
      await authStorage.clearAll();
      setState({
        isChecking: false,
        isAuthenticated: false,
        user: null,
        error: error.message || 'Failed to restore session',
      });
    }
  };

  /**
   * Manually trigger session refresh
   */
  const refreshSession = async (): Promise<boolean> => {
    try {
      const authState = await authStorage.getAuthState();
      if (!authState.token) return false;

      const response = await api.get('/v1/auth/verify', {
        headers: {
          Authorization: `Bearer ${authState.token}`,
        },
      });

      if (response.data.success) {
        if (response.data.user) {
          await authStorage.saveUser(response.data.user);
          setState(prev => ({ ...prev, user: response.data.user }));
        }
        return true;
      }
      return false;
    } catch (error) {
      console.error('[AutoLogin] Session refresh failed:', error);
      return false;
    }
  };

  /**
   * Check OTP verification status
   */
  const checkOTPVerification = async (phoneNumber: string): Promise<boolean> => {
    return await authStorage.isOTPVerified(phoneNumber);
  };

  return {
    ...state,
    refreshSession,
    checkOTPVerification,
  };
};
