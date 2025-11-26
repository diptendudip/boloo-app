/**
 * OfflineManager - Complete offline mode implementation
 *
 * Features:
 * - Queue pending reports when offline
 * - Automatic sync when connectivity restored
 * - Retry logic with exponential backoff
 * - Persist queue across app restarts
 * - Network status monitoring
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { API_URL } from '../constants/config';

// Storage keys
const QUEUE_STORAGE_KEY = 'offline_report_queue';
const CACHED_USER_KEY = 'cached_user_data';
const CACHED_CASES_KEY = 'cached_cases_data';
const LAST_SYNC_KEY = 'last_sync_timestamp';

// Queue item interface
export interface QueuedReport {
  id: string; // Unique queue ID
  userId: string;
  description: string;
  location?: string;
  category?: string;
  photoUri?: string;
  timestamp: number;
  retryCount: number;
  lastRetryAt?: number;
}

// Sync status interface
export interface SyncStatus {
  isSyncing: boolean;
  queueCount: number;
  successCount: number;
  failedCount: number;
  lastSyncAt?: number;
}

// Network status callback type
type NetworkStatusCallback = (isConnected: boolean) => void;
type SyncStatusCallback = (status: SyncStatus) => void;

class OfflineManager {
  private isOnline: boolean = true;
  private isSyncing: boolean = false;
  private networkListeners: NetworkStatusCallback[] = [];
  private syncListeners: SyncStatusCallback[] = [];
  private syncInProgress: Set<string> = new Set();

  // Retry configuration
  private readonly MAX_RETRIES = 5;
  private readonly BASE_DELAY = 1000; // 1 second
  private readonly MAX_DELAY = 60000; // 1 minute

  constructor() {
    this.initializeNetworkListener();
  }

  /**
   * Initialize network status listener
   */
  private initializeNetworkListener(): void {
    NetInfo.addEventListener((state: NetInfoState) => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected ?? false;

      console.log('Network status changed:', {
        isConnected: this.isOnline,
        type: state.type,
      });

      // Notify all listeners
      this.networkListeners.forEach(callback => callback(this.isOnline));

      // Auto-sync when coming back online
      if (wasOffline && this.isOnline) {
        console.log('📡 Back online! Auto-syncing...');
        this.syncQueue();
      }
    });
  }

  /**
   * Check current network status
   */
  async checkNetworkStatus(): Promise<boolean> {
    const state = await NetInfo.fetch();
    this.isOnline = state.isConnected ?? false;
    return this.isOnline;
  }

  /**
   * Get current network status (cached)
   */
  getNetworkStatus(): boolean {
    return this.isOnline;
  }

  /**
   * Subscribe to network status changes
   */
  onNetworkStatusChange(callback: NetworkStatusCallback): () => void {
    this.networkListeners.push(callback);
    // Return unsubscribe function
    return () => {
      this.networkListeners = this.networkListeners.filter(cb => cb !== callback);
    };
  }

  /**
   * Subscribe to sync status changes
   */
  onSyncStatusChange(callback: SyncStatusCallback): () => void {
    this.syncListeners.push(callback);
    return () => {
      this.syncListeners = this.syncListeners.filter(cb => cb !== callback);
    };
  }

  /**
   * Notify sync status listeners
   */
  private notifySyncStatus(status: Partial<SyncStatus>): void {
    const fullStatus: SyncStatus = {
      isSyncing: this.isSyncing,
      queueCount: 0,
      successCount: 0,
      failedCount: 0,
      ...status,
    };
    this.syncListeners.forEach(callback => callback(fullStatus));
  }

  /**
   * Add report to offline queue
   */
  async addToQueue(report: Omit<QueuedReport, 'id' | 'timestamp' | 'retryCount'>): Promise<string> {
    const queuedReport: QueuedReport = {
      ...report,
      id: `queued_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retryCount: 0,
    };

    const queue = await this.getQueue();
    queue.push(queuedReport);
    await this.saveQueue(queue);

    console.log('📥 Report added to offline queue:', queuedReport.id);
    this.notifySyncStatus({ queueCount: queue.length });

    return queuedReport.id;
  }

  /**
   * Get all queued reports
   */
  async getQueue(): Promise<QueuedReport[]> {
    try {
      const queueJson = await AsyncStorage.getItem(QUEUE_STORAGE_KEY);
      return queueJson ? JSON.parse(queueJson) : [];
    } catch (error) {
      console.error('Error reading queue:', error);
      return [];
    }
  }

  /**
   * Save queue to storage
   */
  private async saveQueue(queue: QueuedReport[]): Promise<void> {
    try {
      await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
    } catch (error) {
      console.error('Error saving queue:', error);
      throw error;
    }
  }

  /**
   * Remove report from queue
   */
  async removeFromQueue(reportId: string): Promise<void> {
    const queue = await this.getQueue();
    const filteredQueue = queue.filter(item => item.id !== reportId);
    await this.saveQueue(filteredQueue);
    console.log('🗑️ Removed from queue:', reportId);
    this.notifySyncStatus({ queueCount: filteredQueue.length });
  }

  /**
   * Clear entire queue
   */
  async clearQueue(): Promise<void> {
    await AsyncStorage.removeItem(QUEUE_STORAGE_KEY);
    console.log('🗑️ Queue cleared');
    this.notifySyncStatus({ queueCount: 0 });
  }

  /**
   * Calculate exponential backoff delay
   */
  private calculateBackoffDelay(retryCount: number): number {
    const delay = Math.min(
      this.BASE_DELAY * Math.pow(2, retryCount),
      this.MAX_DELAY
    );
    // Add jitter (±20%)
    const jitter = delay * 0.2 * (Math.random() - 0.5);
    return Math.round(delay + jitter);
  }

  /**
   * Check if report should be retried
   */
  private shouldRetry(report: QueuedReport): boolean {
    if (report.retryCount >= this.MAX_RETRIES) {
      return false;
    }

    if (!report.lastRetryAt) {
      return true;
    }

    const backoffDelay = this.calculateBackoffDelay(report.retryCount);
    const timeSinceLastRetry = Date.now() - report.lastRetryAt;
    return timeSinceLastRetry >= backoffDelay;
  }

  /**
   * Sync a single report
   */
  private async syncReport(report: QueuedReport): Promise<boolean> {
    // Prevent duplicate syncs
    if (this.syncInProgress.has(report.id)) {
      return false;
    }

    this.syncInProgress.add(report.id);

    try {
      console.log(`🔄 Syncing report ${report.id} (attempt ${report.retryCount + 1}/${this.MAX_RETRIES})`);

      // Call actual report submission API
      const response = await fetch(`${API_URL}/v1/cases`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: report.userId,
          description: report.description,
          location: report.location,
          category: report.category,
          // photoUri would need to be uploaded separately to /v1/uploads/upload
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Report synced successfully:', data.case?.id || 'unknown');

      // Remove from queue on success
      await this.removeFromQueue(report.id);
      return true;

    } catch (error) {
      console.error(`❌ Failed to sync report ${report.id}:`, error);

      // Update retry count and timestamp
      const queue = await this.getQueue();
      const reportIndex = queue.findIndex(item => item.id === report.id);

      if (reportIndex !== -1) {
        queue[reportIndex].retryCount++;
        queue[reportIndex].lastRetryAt = Date.now();

        // Remove if max retries exceeded
        if (queue[reportIndex].retryCount >= this.MAX_RETRIES) {
          console.warn(`⚠️ Report ${report.id} exceeded max retries, removing from queue`);
          queue.splice(reportIndex, 1);
        }

        await this.saveQueue(queue);
      }

      return false;

    } finally {
      this.syncInProgress.delete(report.id);
    }
  }

  /**
   * Sync all queued reports
   */
  async syncQueue(): Promise<void> {
    // Check if already syncing
    if (this.isSyncing) {
      console.log('⏭️ Sync already in progress, skipping...');
      return;
    }

    // Check network status
    const isConnected = await this.checkNetworkStatus();
    if (!isConnected) {
      console.log('📴 No network connection, sync cancelled');
      return;
    }

    this.isSyncing = true;
    const queue = await this.getQueue();

    if (queue.length === 0) {
      console.log('✅ Queue is empty, nothing to sync');
      this.isSyncing = false;
      return;
    }

    console.log(`🚀 Starting sync of ${queue.length} reports...`);
    this.notifySyncStatus({
      isSyncing: true,
      queueCount: queue.length,
      successCount: 0,
      failedCount: 0,
    });

    let successCount = 0;
    let failedCount = 0;

    // Process reports that are ready for retry
    const reportsToSync = queue.filter(report => this.shouldRetry(report));

    for (const report of reportsToSync) {
      const success = await this.syncReport(report);
      if (success) {
        successCount++;
      } else {
        failedCount++;
      }
    }

    // Update last sync timestamp
    await AsyncStorage.setItem(LAST_SYNC_KEY, Date.now().toString());

    const remainingQueue = await this.getQueue();

    console.log(`✅ Sync completed: ${successCount} succeeded, ${failedCount} failed, ${remainingQueue.length} remaining`);

    this.isSyncing = false;
    this.notifySyncStatus({
      isSyncing: false,
      queueCount: remainingQueue.length,
      successCount,
      failedCount,
      lastSyncAt: Date.now(),
    });
  }

  /**
   * Get sync status
   */
  async getSyncStatus(): Promise<SyncStatus> {
    const queue = await this.getQueue();
    const lastSyncStr = await AsyncStorage.getItem(LAST_SYNC_KEY);
    const lastSyncAt = lastSyncStr ? parseInt(lastSyncStr) : undefined;

    return {
      isSyncing: this.isSyncing,
      queueCount: queue.length,
      successCount: 0,
      failedCount: 0,
      lastSyncAt,
    };
  }

  /**
   * Cache user data for offline access
   */
  async cacheUserData(userData: any): Promise<void> {
    try {
      await AsyncStorage.setItem(CACHED_USER_KEY, JSON.stringify(userData));
      console.log('💾 User data cached');
    } catch (error) {
      console.error('Error caching user data:', error);
    }
  }

  /**
   * Get cached user data
   */
  async getCachedUserData(): Promise<any | null> {
    try {
      const cached = await AsyncStorage.getItem(CACHED_USER_KEY);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Error reading cached user data:', error);
      return null;
    }
  }

  /**
   * Cache cases list for offline access
   */
  async cacheCases(cases: any[]): Promise<void> {
    try {
      await AsyncStorage.setItem(CACHED_CASES_KEY, JSON.stringify({
        cases,
        cachedAt: Date.now(),
      }));
      console.log(`💾 Cached ${cases.length} cases`);
    } catch (error) {
      console.error('Error caching cases:', error);
    }
  }

  /**
   * Get cached cases
   */
  async getCachedCases(): Promise<{ cases: any[], cachedAt: number } | null> {
    try {
      const cached = await AsyncStorage.getItem(CACHED_CASES_KEY);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Error reading cached cases:', error);
      return null;
    }
  }

  /**
   * Clear all cached data
   */
  async clearCache(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        CACHED_USER_KEY,
        CACHED_CASES_KEY,
      ]);
      console.log('🗑️ Cache cleared');
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  }

  /**
   * Get queue count (helper method)
   */
  async getQueueCount(): Promise<number> {
    const queue = await this.getQueue();
    return queue.length;
  }
}

// Export singleton instance
export const offlineManager = new OfflineManager();
