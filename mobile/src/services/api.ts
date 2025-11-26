import axios, { AxiosInstance, AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../constants/config';

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 120 seconds (2 minutes) to accommodate Azure OpenAI processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Storage key for auth token (must match authStorage.ts)
const AUTH_TOKEN_KEY = '@boloo_auth_token';

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    // Use the correct storage key that matches authStorage.ts
    const token = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API] Using Bearer token authentication');
    } else {
      // PRODUCTION: No token available - request will fail with 401
      // This is expected for unauthenticated users
      console.log('[API] No auth token found - request may require authentication');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired, logout - use correct storage keys
      await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
      await AsyncStorage.removeItem('@boloo_user');
      await AsyncStorage.removeItem('@boloo_user_id');
    }
    return Promise.reject(error);
  }
);

export default api;
