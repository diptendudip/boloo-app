/**
 * API Authentication Utility
 *
 * Centralized authentication helper for API calls
 * Handles token retrieval, dev mode fallback, and header construction
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  AUTH_TOKEN: '@boloo_auth_token',
  USER_ID: '@boloo_user_id',
};

/**
 * Get authentication headers for API requests
 * Returns Bearer token header for production authentication
 */
export async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    // Get auth token from storage
    const token = await AsyncStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);

    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    }

    // No token available - request may fail with 401
    console.warn('[API Auth] No auth token found - request may require authentication');
    return {
      'Content-Type': 'application/json',
    };
  } catch (error) {
    console.error('[API Auth] Error getting auth headers:', error);
    return {
      'Content-Type': 'application/json',
    };
  }
}

/**
 * Get URL for API requests
 * Production mode uses Bearer token in headers, no query params needed
 */
export async function getAuthUrl(baseUrl: string): Promise<string> {
  // Production: Authentication is handled via Bearer token in headers
  // No query params needed for authentication
  return baseUrl;
}

/**
 * Store authentication token
 */
export async function storeAuthToken(token: string): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
    console.log('[API Auth] Token stored successfully');
  } catch (error) {
    console.error('[API Auth] Error storing token:', error);
    throw error;
  }
}

/**
 * Store user ID
 */
export async function storeUserId(userId: string): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.USER_ID, userId);
    console.log('[API Auth] User ID stored successfully');
  } catch (error) {
    console.error('[API Auth] Error storing user ID:', error);
    throw error;
  }
}

/**
 * Get current user ID
 */
export async function getUserId(): Promise<string | null> {
  try {
    return await AsyncStorage.getItem(STORAGE_KEYS.USER_ID);
  } catch (error) {
    console.error('[API Auth] Error getting user ID:', error);
    return null;
  }
}

/**
 * Clear authentication data (logout)
 */
export async function clearAuth(): Promise<void> {
  try {
    await AsyncStorage.multiRemove([STORAGE_KEYS.AUTH_TOKEN, STORAGE_KEYS.USER_ID]);
    console.log('[API Auth] Authentication cleared');
  } catch (error) {
    console.error('[API Auth] Error clearing auth:', error);
    throw error;
  }
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const token = await AsyncStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    // Only JWT token means authenticated in production
    return !!token;
  } catch (error) {
    console.error('[API Auth] Error checking authentication:', error);
    return false;
  }
}

/**
 * Make authenticated API request with automatic error handling
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  try {
    // Get auth headers
    const authHeaders = await getAuthHeaders();

    // Build authenticated URL (adds dev_user_id if needed)
    const authUrl = await getAuthUrl(url);

    // Merge headers
    const headers = {
      ...authHeaders,
      ...(options.headers || {}),
    };

    // Make request
    const response = await fetch(authUrl, {
      ...options,
      headers,
    });

    // Check for auth errors
    if (response.status === 401 || response.status === 403) {
      console.error('[API Auth] Authentication failed:', response.status);
      // Could trigger logout or refresh token here
    }

    return response;
  } catch (error) {
    console.error('[API Auth] Fetch error:', error);
    throw error;
  }
}
