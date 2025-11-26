/**
 * NotificationManager.ts
 *
 * Comprehensive push notification management for Boloo app
 * Handles registration, permissions, token storage, and notification handling
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Constants from 'expo-constants';

// Notification types in the system
export enum NotificationType {
  STATUS_UPDATE = 'STATUS_UPDATE',
  CASE_ASSIGNMENT = 'CASE_ASSIGNMENT',
  CASE_RESOLUTION = 'CASE_RESOLUTION',
  NEW_COMMENT = 'NEW_COMMENT',
  SYSTEM_ANNOUNCEMENT = 'SYSTEM_ANNOUNCEMENT',
}

// Notification payload interface
export interface NotificationPayload {
  type: NotificationType;
  caseId?: string;
  title: string;
  body: string;
  data?: Record<string, any>;
}

// Notification response interface
export interface NotificationResponse {
  notification: Notifications.Notification;
  actionIdentifier: string;
}

// Storage keys
const STORAGE_KEYS = {
  PUSH_TOKEN: '@boloo_push_token',
  NOTIFICATION_SETTINGS: '@boloo_notification_settings',
  LAST_TOKEN_SYNC: '@boloo_last_token_sync',
};

// API configuration - use same config as app
const API_BASE_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000';
const TOKEN_SYNC_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours

/**
 * NotificationManager class
 * Singleton pattern for managing all push notification operations
 */
class NotificationManager {
  private static instance: NotificationManager;
  private pushToken: string | null = null;
  private notificationListener: Notifications.Subscription | null = null;
  private responseListener: Notifications.Subscription | null = null;
  private isInitialized: boolean = false;

  private constructor() {
    // Configure notification handler behavior
    this.configureNotificationHandler();
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager();
    }
    return NotificationManager.instance;
  }

  /**
   * Configure how notifications are handled when app is in foreground
   */
  private configureNotificationHandler(): void {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
  }

  /**
   * Initialize notification system
   * Should be called when app starts or user logs in
   */
  public async initialize(userId?: string): Promise<boolean> {
    if (this.isInitialized) {
      console.log('NotificationManager already initialized');
      return true;
    }

    try {
      // Request permissions
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        console.warn('Notification permissions not granted');
        return false;
      }

      // Get push token
      const token = await this.getPushToken();
      if (!token) {
        console.error('Failed to get push token');
        return false;
      }

      // Store token locally
      await this.storePushTokenLocally(token);

      // Sync token with backend if user is logged in
      if (userId) {
        await this.syncTokenWithBackend(token, userId);
      }

      // Set up notification listeners
      this.setupNotificationListeners();

      this.isInitialized = true;
      console.log('NotificationManager initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize NotificationManager:', error);
      return false;
    }
  }

  /**
   * Request notification permissions from user
   */
  public async requestPermissions(): Promise<boolean> {
    try {
      // Check if running on physical device
      if (!Device.isDevice) {
        Alert.alert(
          'सूचना',
          'पुश नोटिफिकेशन केवल असली डिवाइस पर काम करते हैं',
          [{ text: 'ठीक है' }]
        );
        return false;
      }

      // Get current permission status
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      // Request permissions if not already granted
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      // Check if permissions were granted
      if (finalStatus !== 'granted') {
        Alert.alert(
          'अनुमति आवश्यक',
          'कृपया सेटिंग्स में जाकर नोटिफिकेशन की अनुमति दें',
          [{ text: 'ठीक है' }]
        );
        return false;
      }

      // Android-specific channel setup
      if (Platform.OS === 'android') {
        await this.setupAndroidNotificationChannel();
      }

      return true;
    } catch (error) {
      console.error('Error requesting permissions:', error);
      return false;
    }
  }

  /**
   * Setup Android notification channel
   */
  private async setupAndroidNotificationChannel(): Promise<void> {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
      sound: 'default',
    });

    // Create additional channels for different notification types
    await Notifications.setNotificationChannelAsync('status_updates', {
      name: 'स्टेटस अपडेट',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      sound: 'default',
    });

    await Notifications.setNotificationChannelAsync('assignments', {
      name: 'केस असाइनमेंट',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      sound: 'default',
    });

    await Notifications.setNotificationChannelAsync('resolutions', {
      name: 'समाधान',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      sound: 'default',
    });
  }

  /**
   * Get Expo push token
   */
  private async getPushToken(): Promise<string | null> {
    try {
      const projectId = Constants.expoConfig?.extra?.eas?.projectId;

      if (!projectId) {
        console.error('Expo project ID not found');
        return null;
      }

      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId,
      });

      this.pushToken = tokenData.data;
      return this.pushToken;
    } catch (error) {
      console.error('Error getting push token:', error);
      return null;
    }
  }

  /**
   * Store push token locally
   */
  private async storePushTokenLocally(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.PUSH_TOKEN, token);
      await AsyncStorage.setItem(
        STORAGE_KEYS.LAST_TOKEN_SYNC,
        Date.now().toString()
      );
    } catch (error) {
      console.error('Error storing push token:', error);
    }
  }

  /**
   * Sync token with backend server
   */
  public async syncTokenWithBackend(token: string, userId: string): Promise<boolean> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/push-token`,
        {
          push_token: token,
          user_id: userId,
          device_type: Platform.OS,
          device_info: {
            brand: Device.brand,
            modelName: Device.modelName,
            osVersion: Device.osVersion,
          },
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.status === 200) {
        await AsyncStorage.setItem(
          STORAGE_KEYS.LAST_TOKEN_SYNC,
          Date.now().toString()
        );
        console.log('Push token synced with backend');
        return true;
      }

      return false;
    } catch (error) {
      console.error('Error syncing token with backend:', error);
      return false;
    }
  }

  /**
   * Check if token needs to be synced with backend
   */
  public async shouldSyncToken(): Promise<boolean> {
    try {
      const lastSync = await AsyncStorage.getItem(STORAGE_KEYS.LAST_TOKEN_SYNC);
      if (!lastSync) return true;

      const timeSinceSync = Date.now() - parseInt(lastSync, 10);
      return timeSinceSync > TOKEN_SYNC_INTERVAL;
    } catch (error) {
      console.error('Error checking token sync status:', error);
      return true;
    }
  }

  /**
   * Setup notification listeners
   */
  private setupNotificationListeners(): void {
    // Remove existing listeners if any
    this.removeNotificationListeners();

    // Listen for notifications received while app is foregrounded
    this.notificationListener = Notifications.addNotificationReceivedListener(
      this.handleNotificationReceived.bind(this)
    );

    // Listen for user interactions with notifications
    this.responseListener = Notifications.addNotificationResponseReceivedListener(
      this.handleNotificationResponse.bind(this)
    );
  }

  /**
   * Handle notification received while app is in foreground
   */
  private handleNotificationReceived(notification: Notifications.Notification): void {
    console.log('Notification received:', notification);

    const { type } = notification.request.content.data || {};

    // Custom handling based on notification type
    switch (type) {
      case NotificationType.STATUS_UPDATE:
        this.handleStatusUpdateNotification(notification);
        break;
      case NotificationType.CASE_ASSIGNMENT:
        this.handleCaseAssignmentNotification(notification);
        break;
      case NotificationType.CASE_RESOLUTION:
        this.handleCaseResolutionNotification(notification);
        break;
      case NotificationType.NEW_COMMENT:
        this.handleNewCommentNotification(notification);
        break;
      default:
        console.log('Unknown notification type:', type);
    }
  }

  /**
   * Handle user interaction with notification
   */
  private handleNotificationResponse(response: NotificationResponse): void {
    console.log('Notification response:', response);

    const { notification } = response;
    const { data } = notification.request.content;

    // Navigate to appropriate screen based on notification type
    if (data?.caseId) {
      this.navigateToCaseDetails(data.caseId);
    } else if (data?.screen) {
      this.navigateToScreen(data.screen, data.params);
    }
  }

  /**
   * Handle status update notifications
   */
  private handleStatusUpdateNotification(notification: Notifications.Notification): void {
    const { data } = notification.request.content;
    console.log('Status update for case:', data?.caseId);
    // Additional custom logic can be added here
  }

  /**
   * Handle case assignment notifications
   */
  private handleCaseAssignmentNotification(notification: Notifications.Notification): void {
    const { data } = notification.request.content;
    console.log('Case assigned:', data?.caseId);
    // Additional custom logic can be added here
  }

  /**
   * Handle case resolution notifications
   */
  private handleCaseResolutionNotification(notification: Notifications.Notification): void {
    const { data } = notification.request.content;
    console.log('Case resolved:', data?.caseId);
    // Additional custom logic can be added here
  }

  /**
   * Handle new comment notifications
   */
  private handleNewCommentNotification(notification: Notifications.Notification): void {
    const { data } = notification.request.content;
    console.log('New comment on case:', data?.caseId);
    // Additional custom logic can be added here
  }

  /**
   * Navigate to case details screen
   * This should be implemented based on your navigation setup
   */
  private navigateToCaseDetails(caseId: string): void {
    // TODO: Implement navigation logic
    console.log('Navigate to case details:', caseId);
    // Example: navigation.navigate('CaseDetails', { caseId });
  }

  /**
   * Navigate to a specific screen
   */
  private navigateToScreen(screen: string, params?: Record<string, any>): void {
    // TODO: Implement navigation logic
    console.log('Navigate to screen:', screen, params);
    // Example: navigation.navigate(screen, params);
  }

  /**
   * Remove notification listeners
   */
  private removeNotificationListeners(): void {
    if (this.notificationListener) {
      Notifications.removeNotificationSubscription(this.notificationListener);
      this.notificationListener = null;
    }

    if (this.responseListener) {
      Notifications.removeNotificationSubscription(this.responseListener);
      this.responseListener = null;
    }
  }

  /**
   * Schedule a local notification
   */
  public async scheduleLocalNotification(
    title: string,
    body: string,
    data?: Record<string, any>,
    seconds: number = 0
  ): Promise<string | null> {
    try {
      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data,
          sound: 'default',
        },
        trigger: seconds > 0 ? { seconds } : null,
      });

      return notificationId;
    } catch (error) {
      console.error('Error scheduling notification:', error);
      return null;
    }
  }

  /**
   * Cancel a scheduled notification
   */
  public async cancelNotification(notificationId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
    } catch (error) {
      console.error('Error canceling notification:', error);
    }
  }

  /**
   * Cancel all scheduled notifications
   */
  public async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Error canceling all notifications:', error);
    }
  }

  /**
   * Get badge count
   */
  public async getBadgeCount(): Promise<number> {
    try {
      return await Notifications.getBadgeCountAsync();
    } catch (error) {
      console.error('Error getting badge count:', error);
      return 0;
    }
  }

  /**
   * Set badge count
   */
  public async setBadgeCount(count: number): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(count);
    } catch (error) {
      console.error('Error setting badge count:', error);
    }
  }

  /**
   * Clear badge count
   */
  public async clearBadgeCount(): Promise<void> {
    await this.setBadgeCount(0);
  }

  /**
   * Get current push token
   */
  public getCurrentToken(): string | null {
    return this.pushToken;
  }

  /**
   * Cleanup and remove all listeners
   */
  public cleanup(): void {
    this.removeNotificationListeners();
    this.isInitialized = false;
    this.pushToken = null;
    console.log('NotificationManager cleaned up');
  }
}

// Export singleton instance
export default NotificationManager.getInstance();
