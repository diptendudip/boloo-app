/**
 * useNotifications.ts
 *
 * React hook for managing push notifications in Boloo app
 * Provides easy-to-use interface for notification features
 */

import { useState, useEffect, useCallback } from 'react';
import NotificationManager from '../utils/NotificationManager';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface NotificationHookResult {
  isInitialized: boolean;
  pushToken: string | null;
  isLoading: boolean;
  error: string | null;
  initialize: (userId?: string) => Promise<boolean>;
  requestPermissions: () => Promise<boolean>;
  syncToken: (userId: string) => Promise<boolean>;
  scheduleNotification: (
    title: string,
    body: string,
    data?: Record<string, any>,
    seconds?: number
  ) => Promise<string | null>;
  clearBadge: () => Promise<void>;
  cleanup: () => void;
}

/**
 * Custom hook for managing push notifications
 */
export const useNotifications = (): NotificationHookResult => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [pushToken, setPushToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Initialize notification system
   */
  const initialize = useCallback(async (userId?: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const success = await NotificationManager.initialize(userId);

      if (success) {
        const token = NotificationManager.getCurrentToken();
        setPushToken(token);
        setIsInitialized(true);
      } else {
        setError('Failed to initialize notifications');
      }

      return success;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Request notification permissions
   */
  const requestPermissions = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const granted = await NotificationManager.requestPermissions();

      if (!granted) {
        setError('Notification permissions not granted');
      }

      return granted;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Sync push token with backend
   */
  const syncToken = useCallback(async (userId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = NotificationManager.getCurrentToken();

      if (!token) {
        setError('No push token available');
        return false;
      }

      const success = await NotificationManager.syncTokenWithBackend(token, userId);

      if (!success) {
        setError('Failed to sync token with backend');
      }

      return success;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Schedule a local notification
   */
  const scheduleNotification = useCallback(
    async (
      title: string,
      body: string,
      data?: Record<string, any>,
      seconds: number = 0
    ): Promise<string | null> => {
      try {
        return await NotificationManager.scheduleLocalNotification(
          title,
          body,
          data,
          seconds
        );
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        return null;
      }
    },
    []
  );

  /**
   * Clear notification badge
   */
  const clearBadge = useCallback(async (): Promise<void> => {
    try {
      await NotificationManager.clearBadgeCount();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    }
  }, []);

  /**
   * Cleanup notification manager
   */
  const cleanup = useCallback((): void => {
    NotificationManager.cleanup();
    setIsInitialized(false);
    setPushToken(null);
  }, []);

  // Auto-initialize on mount if user is logged in
  useEffect(() => {
    const autoInitialize = async () => {
      try {
        // Check if user is logged in
        const userId = await AsyncStorage.getItem('@boloo_user_id');

        if (userId && !isInitialized) {
          await initialize(userId);
        }
      } catch (err) {
        console.error('Error auto-initializing notifications:', err);
      }
    };

    autoInitialize();

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, []);

  return {
    isInitialized,
    pushToken,
    isLoading,
    error,
    initialize,
    requestPermissions,
    syncToken,
    scheduleNotification,
    clearBadge,
    cleanup,
  };
};

export default useNotifications;
