/**
 * OfflineIndicator - Shows offline status banner with sync controls
 *
 * Features:
 * - Displays when offline with queue count
 * - Manual sync button
 * - Shows sync progress
 * - Auto-hides when online and queue is empty
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { offlineManager, SyncStatus } from '../utils/OfflineManager';
import { COLORS } from '../constants/config';

export const OfflineIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState(true);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isSyncing: false,
    queueCount: 0,
    successCount: 0,
    failedCount: 0,
  });
  const [slideAnim] = useState(new Animated.Value(-100));
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Subscribe to network status
    const unsubscribeNetwork = offlineManager.onNetworkStatusChange((online) => {
      setIsOnline(online);
    });

    // Subscribe to sync status
    const unsubscribeSync = offlineManager.onSyncStatusChange((status) => {
      setSyncStatus(status);
    });

    // Initialize status
    checkStatus();

    return () => {
      unsubscribeNetwork();
      unsubscribeSync();
    };
  }, []);

  useEffect(() => {
    // Show banner if offline OR if there are queued items
    const shouldShow = !isOnline || syncStatus.queueCount > 0;

    if (shouldShow && !isVisible) {
      setIsVisible(true);
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        tension: 65,
        friction: 8,
      }).start();
    } else if (!shouldShow && isVisible) {
      Animated.timing(slideAnim, {
        toValue: -100,
        duration: 200,
        useNativeDriver: true,
      }).start(() => {
        setIsVisible(false);
      });
    }
  }, [isOnline, syncStatus.queueCount, isVisible]);

  const checkStatus = async () => {
    const online = offlineManager.getNetworkStatus();
    const status = await offlineManager.getSyncStatus();
    setIsOnline(online);
    setSyncStatus(status);
  };

  const handleManualSync = async () => {
    if (!syncStatus.isSyncing && isOnline) {
      await offlineManager.syncQueue();
    }
  };

  const getBannerStyle = () => {
    if (syncStatus.isSyncing) {
      return styles.bannerSyncing;
    }
    if (!isOnline) {
      return styles.bannerOffline;
    }
    return styles.bannerQueued;
  };

  const getBannerMessage = () => {
    if (syncStatus.isSyncing) {
      return `सिंक हो रहा है... (${syncStatus.queueCount} बाकी)`;
    }
    if (!isOnline) {
      if (syncStatus.queueCount > 0) {
        return `ऑफलाइन (${syncStatus.queueCount} रिपोर्ट्स भेजने के लिए तैयार)`;
      }
      return 'ऑफलाइन';
    }
    if (syncStatus.queueCount > 0) {
      return `${syncStatus.queueCount} रिपोर्ट्स भेजने के लिए तैयार`;
    }
    return '';
  };

  const getIcon = () => {
    if (syncStatus.isSyncing) {
      return <ActivityIndicator size="small" color="#fff" />;
    }
    if (!isOnline) {
      return <Ionicons name="cloud-offline" size={20} color="#fff" />;
    }
    return <Ionicons name="cloud-upload-outline" size={20} color="#fff" />;
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Animated.View
      style={[
        styles.container,
        getBannerStyle(),
        { transform: [{ translateY: slideAnim }] },
      ]}
    >
      <View style={styles.content}>
        <View style={styles.leftSection}>
          {getIcon()}
          <Text style={styles.message}>{getBannerMessage()}</Text>
        </View>

        {isOnline && syncStatus.queueCount > 0 && !syncStatus.isSyncing && (
          <TouchableOpacity
            style={styles.syncButton}
            onPress={handleManualSync}
          >
            <Ionicons name="sync" size={18} color="#fff" />
            <Text style={styles.syncButtonText}>सिंक करें</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Sync progress bar */}
      {syncStatus.isSyncing && (
        <View style={styles.progressContainer}>
          <View
            style={[
              styles.progressBar,
              {
                width: `${((syncStatus.successCount + syncStatus.failedCount) /
                  (syncStatus.queueCount + syncStatus.successCount + syncStatus.failedCount)) * 100}%`,
              },
            ]}
          />
        </View>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  bannerOffline: {
    backgroundColor: COLORS.error,
  },
  bannerQueued: {
    backgroundColor: COLORS.warning,
  },
  bannerSyncing: {
    backgroundColor: COLORS.primary,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  leftSection: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  message: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 10,
    flex: 1,
  },
  syncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginLeft: 8,
  },
  syncButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  progressContainer: {
    height: 3,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    marginTop: 8,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#fff',
    borderRadius: 2,
  },
});
