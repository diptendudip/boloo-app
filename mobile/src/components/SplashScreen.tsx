import React from 'react';
import {
  View,
  Text,
  ActivityIndicator,
  StyleSheet,
  Image,
} from 'react-native';
import { COLORS } from '../constants/config';

interface SplashScreenProps {
  message?: string;
}

/**
 * Splash screen shown during authentication check
 */
export default function SplashScreen({ message = 'Loading...' }: SplashScreenProps) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {/* App Logo/Icon */}
        <View style={styles.logoContainer}>
          <Text style={styles.logoEmoji}>🗣️</Text>
          <Text style={styles.logoText}>बोलो</Text>
          <Text style={styles.logoSubtext}>Boloo</Text>
        </View>

        {/* Loading Indicator */}
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>{message}</Text>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Powered by Chhattisgarh Government
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    width: '100%',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logoEmoji: {
    fontSize: 72,
    marginBottom: 16,
  },
  logoText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginBottom: 8,
  },
  logoSubtext: {
    fontSize: 24,
    color: COLORS.gray[600],
    fontWeight: '600',
  },
  loadingContainer: {
    alignItems: 'center',
    marginTop: 32,
  },
  loadingText: {
    fontSize: 16,
    color: COLORS.gray[600],
    marginTop: 16,
    fontWeight: '500',
  },
  footer: {
    position: 'absolute',
    bottom: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: COLORS.gray[500],
    textAlign: 'center',
  },
});
