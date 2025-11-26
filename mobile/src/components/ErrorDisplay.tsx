/**
 * ErrorDisplay Component
 *
 * Displays Hindi-first error messages with context-aware recovery actions
 * Uses the error message system from constants/errorMessages.ts
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/config';
import { ERROR_MESSAGES, getErrorFromStatus, getActionText, ErrorMessage } from '../constants/errorMessages';

interface ErrorDisplayProps {
  error: string | number; // Error key or HTTP status code
  onAction?: () => void; // Optional action callback
  style?: any;
}

export default function ErrorDisplay({ error, onAction, style }: ErrorDisplayProps) {
  // Get error message from key or status code
  const errorMessage: ErrorMessage = typeof error === 'number'
    ? getErrorFromStatus(error)
    : ERROR_MESSAGES[error] || ERROR_MESSAGES.UNKNOWN_ERROR;

  const actionText = getActionText(errorMessage.action);

  const handleAction = () => {
    if (onAction) {
      onAction();
    } else {
      // Default actions based on type
      switch (errorMessage.action) {
        case 'CHECK_INTERNET':
          // User should check their internet connection
          break;
        case 'LOGIN_AGAIN':
          // Navigate to login screen
          break;
        case 'GO_HOME':
          // Navigate to home screen
          break;
        case 'CONTACT_SUPPORT':
          // Show support contact info
          break;
        default:
          // RETRY or RETRY_LATER - caller should provide onAction
          break;
      }
    }
  };

  return (
    <View style={[styles.container, style]}>
      {/* Icon */}
      <View style={styles.iconContainer}>
        <Text style={styles.icon}>{errorMessage.icon || '⚠️'}</Text>
      </View>

      {/* Error Message */}
      <View style={styles.messageContainer}>
        <Text style={styles.messageHindi}>{errorMessage.hi}</Text>
        <Text style={styles.messageEnglish}>{errorMessage.en}</Text>
      </View>

      {/* Action Button */}
      {onAction && (
        <TouchableOpacity style={styles.actionButton} onPress={handleAction}>
          <Text style={styles.actionTextHindi}>{actionText.hi}</Text>
          <Text style={styles.actionTextEnglish}>{actionText.en}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  iconContainer: {
    marginBottom: 16,
  },
  icon: {
    fontSize: 48,
  },
  messageContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  messageHindi: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
    textAlign: 'center',
    marginBottom: 4,
  },
  messageEnglish: {
    fontSize: 14,
    color: COLORS.gray[600],
    textAlign: 'center',
  },
  actionButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    minWidth: 200,
    alignItems: 'center',
  },
  actionTextHindi: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 2,
  },
  actionTextEnglish: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
  },
});
