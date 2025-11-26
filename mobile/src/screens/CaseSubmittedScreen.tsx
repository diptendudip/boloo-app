import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { COLORS } from '../constants/config';
import NextStepsCard from '../components/NextStepsCard';
import { nextStepsService } from '../services/nextSteps';
import type { NextStepsInfo } from '../types/nextSteps';

type RootStackParamList = {
  CaseSubmitted: { caseId: string; caseReference: string };
  Home: undefined;
  CaseDetails: { caseId: string };
};

type CaseSubmittedScreenRouteProp = RouteProp<RootStackParamList, 'CaseSubmitted'>;
type CaseSubmittedScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'CaseSubmitted'
>;

export default function CaseSubmittedScreen() {
  const navigation = useNavigation<CaseSubmittedScreenNavigationProp>();
  const route = useRoute<CaseSubmittedScreenRouteProp>();
  const { caseId, caseReference } = route.params;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextSteps, setNextSteps] = useState<NextStepsInfo | null>(null);

  useEffect(() => {
    loadNextSteps();
  }, [caseId]);

  const loadNextSteps = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await nextStepsService.getNextSteps(caseId);
      setNextSteps(data);
    } catch (err) {
      console.error('Error loading next steps:', err);
      setError(err instanceof Error ? err.message : 'Failed to load next steps');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = () => {
    navigation.navigate('CaseDetails', { caseId });
  };

  const handleGoHome = () => {
    navigation.navigate('Home');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>जानकारी लोड हो रही है...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !nextSteps) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Success Header (even if next steps failed) */}
          <View style={styles.successHeader}>
            <Text style={styles.successIcon}>✅</Text>
            <Text style={styles.successTitle}>शिकायत दर्ज हो गई!</Text>
            <Text style={styles.successSubtitle}>Complaint registered successfully</Text>
            <View style={styles.referenceBox}>
              <Text style={styles.referenceLabel}>शिकायत नंबर:</Text>
              <Text style={styles.referenceNumber}>{caseReference}</Text>
            </View>
          </View>

          {/* Error Message */}
          <View style={styles.errorContainer}>
            <Text style={styles.errorIcon}>⚠️</Text>
            <Text style={styles.errorText}>जानकारी लोड नहीं हो सकी</Text>
            <Text style={styles.errorSubtext}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={loadNextSteps}>
              <Text style={styles.retryButtonText}>फिर कोशिश करें</Text>
            </TouchableOpacity>
          </View>

          {/* Go Home Button */}
          <TouchableOpacity style={styles.homeButton} onPress={handleGoHome}>
            <Text style={styles.homeButtonText}>होम पर जाएं</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Success Header */}
        <View style={styles.successHeader}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>शिकायत दर्ज हो गई!</Text>
          <Text style={styles.successSubtitle}>Complaint registered successfully</Text>

          <View style={styles.infoBox}>
            <Text style={styles.infoText}>
              आपकी शिकायत दर्ज कर ली गई है। नीचे देखें कि अब क्या होगा।
            </Text>
            <Text style={styles.infoSubtext}>
              Your complaint has been registered. See below for what happens next.
            </Text>
          </View>
        </View>

        {/* Next Steps Card */}
        <View style={styles.nextStepsContainer}>
          <NextStepsCard
            nextSteps={nextSteps}
            onViewDetails={handleViewDetails}
            compact={false}
          />
        </View>

        {/* Important Tips */}
        <View style={styles.tipsContainer}>
          <Text style={styles.tipsTitle}>महत्वपूर्ण</Text>
          <View style={styles.tipItem}>
            <Text style={styles.tipBullet}>📱</Text>
            <Text style={styles.tipText}>
              शिकायत नंबर सुरक्षित रखें - आप इसे बाद में ट्रैक कर सकते हैं
            </Text>
          </View>
          <View style={styles.tipItem}>
            <Text style={styles.tipBullet}>🔔</Text>
            <Text style={styles.tipText}>
              अपडेट के लिए सूचनाएं चालू रखें
            </Text>
          </View>
          <View style={styles.tipItem}>
            <Text style={styles.tipBullet}>📞</Text>
            <Text style={styles.tipText}>
              जरूरत पड़ने पर अधिकारी से सीधे संपर्क करें
            </Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={styles.detailsButtonFull}
            onPress={handleViewDetails}
          >
            <Text style={styles.detailsButtonText}>पूरा विवरण देखें</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.homeButtonSecondary}
            onPress={handleGoHome}
          >
            <Text style={styles.homeButtonSecondaryText}>होम पर जाएं</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: COLORS.gray[600],
  },
  successHeader: {
    alignItems: 'center',
    paddingVertical: 32,
    backgroundColor: COLORS.white,
    borderRadius: 16,
    marginBottom: 20,
  },
  successIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.success,
    marginBottom: 4,
  },
  successSubtitle: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginBottom: 20,
  },
  referenceBox: {
    backgroundColor: COLORS.primary + '10',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.primary + '30',
  },
  referenceLabel: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginBottom: 4,
  },
  referenceNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
    fontVariant: ['tabular-nums'],
  },
  infoBox: {
    marginTop: 20,
    padding: 16,
    backgroundColor: COLORS.info + '10',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.info,
  },
  infoText: {
    fontSize: 14,
    color: COLORS.gray[800],
    marginBottom: 4,
  },
  infoSubtext: {
    fontSize: 12,
    color: COLORS.gray[600],
  },
  nextStepsContainer: {
    marginBottom: 20,
  },
  tipsContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 16,
  },
  tipItem: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  tipBullet: {
    fontSize: 20,
    marginRight: 12,
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.gray[700],
    lineHeight: 20,
  },
  actionButtons: {
    gap: 12,
  },
  detailsButtonFull: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  detailsButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  homeButtonSecondary: {
    backgroundColor: COLORS.white,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  homeButtonSecondaryText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  errorContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    marginBottom: 20,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 16,
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
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  homeButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  homeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
});
