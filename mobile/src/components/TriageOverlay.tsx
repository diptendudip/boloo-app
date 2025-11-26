import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { COLORS } from '../constants/config';
import type { TriageResult } from '../types/triage';

interface TriageOverlayProps {
  visible: boolean;
  loading: boolean;
  result: TriageResult | null;
  error: string | null;
  onSelectIntent: (intent: string) => void;
  onRetry: () => void;
}

export default function TriageOverlay({
  visible,
  loading,
  result,
  error,
  onSelectIntent,
  onRetry,
}: TriageOverlayProps) {
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    if (visible) {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
    >
      <Animated.View
        style={[styles.overlay, { opacity: fadeAnim }]}
      >
        <View style={styles.card}>
          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={COLORS.primary} />
              <Text style={styles.loadingText}>विश्लेषण हो रहा है...</Text>
              <Text style={styles.loadingSubtext}>Analyzing...</Text>
            </View>
          )}

          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorIcon}>⚠️</Text>
              <Text style={styles.errorText}>कुछ गलत हो गया</Text>
              <Text style={styles.errorSubtext}>{error}</Text>
              <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
                <Text style={styles.retryButtonText}>फिर कोशिश करें</Text>
              </TouchableOpacity>
              <Text style={styles.orText}>या मैन्युअली चुनें</Text>
              {renderIntentChips()}
            </View>
          )}

          {result && !loading && !error && (
            <View style={styles.resultContainer}>
              <Text style={styles.resultTitle}>वर्गीकृत किया गया</Text>
              <Text style={styles.resultSubtitle}>Classified</Text>

              <View style={styles.intentBadge}>
                <Text style={styles.intentIcon}>
                  {getIntentIcon(result.intent)}
                </Text>
                <Text style={styles.intentText}>
                  {getIntentLabel(result.intent)}
                </Text>
                <View style={styles.confidenceBadge}>
                  <Text style={styles.confidenceText}>
                    {Math.round(result.confidence * 100)}%
                  </Text>
                </View>
              </View>

              {result.confidence < 0.7 && (
                <View style={styles.changeSection}>
                  <Text style={styles.changePrompt}>सही नहीं है? बदलें:</Text>
                  {renderIntentChips()}
                </View>
              )}

              {result.confidence >= 0.7 && (
                <TouchableOpacity
                  style={styles.changeButton}
                  onPress={() => {/* Show chips */}}
                >
                  <Text style={styles.changeButtonText}>बदलें</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>
      </Animated.View>
    </Modal>
  );

  function renderIntentChips() {
    const intents = [
      { key: 'grievance', icon: '📢', label: 'शिकायत\nGrievance' },
      { key: 'community', icon: '📰', label: 'समुदाय\nCommunity' },
      { key: 'personal', icon: '📝', label: 'व्यक्तिगत\nPersonal' },
    ];

    return (
      <View style={styles.chipsContainer}>
        {intents.map((intent) => (
          <TouchableOpacity
            key={intent.key}
            style={styles.chip}
            onPress={() => onSelectIntent(intent.key)}
          >
            <Text style={styles.chipIcon}>{intent.icon}</Text>
            <Text style={styles.chipLabel}>{intent.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  }
}

function getIntentIcon(intent: string): string {
  const icons = {
    grievance: '📢',
    community: '📰',
    personal: '📝',
    uncertain: '❓',
  };
  return icons[intent as keyof typeof icons] || '❓';
}

function getIntentLabel(intent: string): string {
  const labels = {
    grievance: 'शिकायत (Grievance)',
    community: 'समुदाय (Community)',
    personal: 'व्यक्तिगत (Personal)',
    uncertain: 'अनिश्चित (Uncertain)',
  };
  return labels[intent as keyof typeof labels] || 'Unknown';
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginTop: 16,
  },
  loadingSubtext: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginTop: 4,
  },
  errorContainer: {
    alignItems: 'center',
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.error,
    marginBottom: 8,
  },
  errorSubtext: {
    fontSize: 14,
    color: COLORS.gray[600],
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  retryButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  orText: {
    fontSize: 14,
    color: COLORS.gray[500],
    marginBottom: 16,
  },
  resultContainer: {
    alignItems: 'center',
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  resultSubtitle: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginBottom: 20,
  },
  intentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  intentIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  intentText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    flex: 1,
  },
  confidenceBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.white,
  },
  changeSection: {
    width: '100%',
    alignItems: 'center',
  },
  changePrompt: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginBottom: 12,
  },
  chipsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    gap: 12,
  },
  chip: {
    flex: 1,
    backgroundColor: COLORS.gray[100],
    paddingVertical: 16,
    paddingHorizontal: 8,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  chipIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  chipLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.gray[800],
    textAlign: 'center',
    lineHeight: 16,
  },
  changeButton: {
    marginTop: 12,
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  changeButtonText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
});
