import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService } from '../services/auth';
import { authStorage } from '../services/authStorage';
import { User } from '../types';
import { offlineManager, SyncStatus } from '../utils/OfflineManager';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isOnline: boolean;
  offlineQueueCount: number;
  syncStatus: SyncStatus | null;
  login: (phoneNumber: string, otp: string) => Promise<void>;
  logout: () => Promise<void>;
  requestOTP: (phoneNumber: string) => Promise<void>;
  syncOfflineQueue: () => Promise<void>;
  completeOnboarding: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);


export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [offlineQueueCount, setOfflineQueueCount] = useState(0);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);

  useEffect(() => {
    checkAuthStatus();
    initializeOfflineManager();
  }, []);

  const initializeOfflineManager = () => {
    // Subscribe to network status changes
    const unsubscribeNetwork = offlineManager.onNetworkStatusChange((online) => {
      setIsOnline(online);
      console.log('Network status changed in AuthContext:', online);
    });

    // Subscribe to sync status changes
    const unsubscribeSync = offlineManager.onSyncStatusChange((status) => {
      setSyncStatus(status);
      setOfflineQueueCount(status.queueCount);
      console.log('Sync status changed:', status);
    });

    // Initialize status
    updateOfflineStatus();

    // Cleanup subscriptions
    return () => {
      unsubscribeNetwork();
      unsubscribeSync();
    };
  };

  const updateOfflineStatus = async () => {
    const online = offlineManager.getNetworkStatus();
    const status = await offlineManager.getSyncStatus();
    setIsOnline(online);
    setSyncStatus(status);
    setOfflineQueueCount(status.queueCount);
  };

  const checkAuthStatus = async () => {
    try {
      console.log('[AuthContext] Checking auth status...');

      // Get stored authentication data using enhanced authStorage
      const authState = await authStorage.getAuthState();

      if (authState.token && authState.user && !authState.isExpired) {
        const storedUser = authState.user;

        setUser(storedUser);
        setIsAuthenticated(true);
        console.log('[AuthContext] Session restored:', storedUser.phone);

        // Validate token with backend if not in dev mode with dummy token
        if (!(__DEV__ && authState.token.startsWith('dummy-token-'))) {
          try {
            const currentUser = await authService.getCurrentUser();
            if (currentUser) {
              setUser(currentUser);
              await authStorage.saveUser(currentUser);
            }
          } catch (error) {
            console.log('[AuthContext] Backend validation failed, using cached session');
          }
        }
      } else {
        console.log('[AuthContext] No valid session found');
      }
    } catch (error) {
      console.error('[AuthContext] Error checking auth status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const requestOTP = async (phoneNumber: string) => {
    await authService.requestOTP(phoneNumber);
  };

  const login = async (phoneNumber: string, otp: string) => {
    // PRODUCTION: Use real backend authentication - NO dummy OTP bypass
    console.log('[AuthContext] Verifying OTP with backend for:', phoneNumber);

    const response = await authService.verifyOTP(phoneNumber, otp);

    // Save authentication data with enhanced storage (uses @boloo_ prefixed keys)
    await authStorage.saveAuthToken(response.access_token, response.expires_in || 86400);
    await authStorage.saveUser(response.user);
    await authStorage.saveOTPVerificationStatus(phoneNumber, true);
    await AsyncStorage.setItem('@boloo_user_id', response.user.id);

    // Cache user data for offline access
    await offlineManager.cacheUserData(response.user);

    setUser(response.user);
    setIsAuthenticated(true);

    console.log('[AuthContext] Login successful!', response.user);
  };

  const completeOnboarding = async () => {
    if (!user) return;

    // Update user object to mark onboarding as complete
    const updatedUser = { ...user, is_first_timer: false };

    // Save to AsyncStorage - use correct storage key
    await AsyncStorage.setItem('@boloo_user', JSON.stringify(updatedUser));

    // Cache updated user data for offline access
    await offlineManager.cacheUserData(updatedUser);

    // Update state
    setUser(updatedUser);

    console.log('Onboarding completed for user:', user.phone);
  };

  const logout = async () => {
    console.log('[AuthContext] Logging out user...');

    // Clear all authentication data using enhanced storage (uses @boloo_ prefixed keys)
    await authStorage.clearAll();
    await AsyncStorage.removeItem('@boloo_user_id'); // Clear user_id as well

    // Clear offline cache and queue
    await offlineManager.clearCache();
    await offlineManager.clearQueue();

    // Clear backend session (only if backend available)
    try {
      await authService.logout();
    } catch (error) {
      console.log('[AuthContext] Backend logout skipped (testing mode)');
    }

    setUser(null);
    setIsAuthenticated(false);

    console.log('[AuthContext] Logout successful');
  };

  const syncOfflineQueue = async () => {
    await offlineManager.syncQueue();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        isOnline,
        offlineQueueCount,
        syncStatus,
        login,
        logout,
        requestOTP,
        syncOfflineQueue,
        completeOnboarding,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
