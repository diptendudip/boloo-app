import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '../types';
import { authStorage } from './authStorage';

/**
 * Legacy storage service - kept for backward compatibility
 * New code should use authStorage from './authStorage'
 */
export const storage = {
  // Auth token
  async setToken(token: string): Promise<void> {
    await authStorage.saveAuthToken(token);
  },

  async getToken(): Promise<string | null> {
    return await authStorage.getAuthToken();
  },

  async removeToken(): Promise<void> {
    await authStorage.clearAuthToken();
  },

  // User data
  async setUser(user: User): Promise<void> {
    await authStorage.saveUser(user);
  },

  async getUser(): Promise<User | null> {
    return await authStorage.getUser();
  },

  async removeUser(): Promise<void> {
    await authStorage.clearUser();
  },

  // Clear all
  async clearAll(): Promise<void> {
    await authStorage.clearAll();
  },
};
