import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import LanguageToggle from '../components/LanguageToggle';
import { COLORS, SIZES } from '../constants/config';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types';
import { validateIndianPhoneNumber } from '../utils/phoneValidation';
import { OTP_MESSAGES, getOTPErrorMessage } from '../constants/otpMessages';
import { authService } from '../services/auth';
import { analytics, AnalyticsEvent } from '../utils/analytics';

type LoginScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Login'>;

interface Props {
  navigation: LoginScreenNavigationProp;
}

const TESTING_MODE = __DEV__; // Enable testing mode in development

export default function LoginScreen({ navigation }: Props) {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const { requestOTP } = useAuth();
  const { t } = useLanguage();

  const handlePhoneChange = (text: string) => {
    // Only allow digits
    const cleaned = text.replace(/\D/g, '');
    setPhoneNumber(cleaned);

    // Clear error when user types
    if (errorMessage) {
      setErrorMessage('');
    }
  };

  const handleSendOTP = async () => {
    // Validate phone number
    const validation = validateIndianPhoneNumber(phoneNumber);

    if (!validation.isValid) {
      setErrorMessage(validation.error || OTP_MESSAGES.PHONE_INVALID);
      analytics.trackPhoneValidationError(phoneNumber, validation.error || '');
      return;
    }

    analytics.track(AnalyticsEvent.OTP_REQUEST_INITIATED, {
      phone_length: phoneNumber.length,
    });

    setIsLoading(true);
    setErrorMessage('');

    try {
      const fullNumber = validation.formatted!; // +91XXXXXXXXXX

      // Always call backend to create OTP record (backend handles demo account)
      console.log('[Login] Requesting OTP for:', fullNumber);
      await authService.requestOTP(fullNumber);

      if (TESTING_MODE && fullNumber === '+919999999999') {
        // TESTING MODE with demo number: Show the fixed OTP
        console.log('[Login] TESTING MODE with demo number, OTP: 123456');
        Alert.alert(
          'Demo Mode',
          'OTP: 123456\n\nThis is a demo account for testing.',
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert(
          'OTP Sent',
          OTP_MESSAGES.OTP_SENT,
          [{ text: 'OK' }]
        );
      }

      analytics.trackOTPRequest(fullNumber, true);

      // Navigate to OTP verification screen
      navigation.navigate('VerifyOTP', { phoneNumber: fullNumber });
    } catch (error: any) {
      console.error('[Login] OTP request failed:', error);
      const errorMsg = getOTPErrorMessage(error);
      setErrorMessage(errorMsg);

      analytics.trackOTPRequest(phoneNumber, false, errorMsg);

      Alert.alert(
        'Error',
        errorMsg,
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        {/* Language Toggle */}
        <View style={styles.languageToggleContainer}>
          <LanguageToggle variant="compact" />
        </View>

        {/* Welcome Message */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeTitle}>🙏 बोलो ऐप में आपका स्वागत है</Text>
          <Text style={styles.welcomeSubtitle}>Welcome to Boloo App</Text>
          <Text style={styles.welcomeDescription}>
            यहाँ आप अपनी समस्याओं की रिपोर्ट कर सकते हैं{'\n'}
            <Text style={styles.welcomeDescriptionEn}>Report your grievances here</Text>
          </Text>
        </View>

        {/* Logo/Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{t('auth.title')}</Text>
          <Text style={styles.subtitle}>{t('auth.subtitle')}</Text>
          <Text style={styles.description}>
            {t('auth.description')}
          </Text>
        </View>

        {/* Phone Input */}
        <View style={styles.form}>
          <Text style={styles.label}>{t('auth.phoneLabel')}</Text>
          <View style={[
            styles.phoneInputContainer,
            errorMessage && styles.phoneInputError
          ]}>
            <Text style={styles.countryCode}>+91</Text>
            <TextInput
              style={styles.phoneInput}
              placeholder={t('auth.phonePlaceholder')}
              keyboardType="phone-pad"
              maxLength={10}
              value={phoneNumber}
              onChangeText={handlePhoneChange}
              editable={!isLoading}
              autoFocus
            />
          </View>
          {errorMessage ? (
            <Text style={styles.errorText}>{errorMessage}</Text>
          ) : (
            <Text style={styles.hint}>
              {t('auth.phoneHint')}
            </Text>
          )}
        </View>

        {/* Send OTP Button */}
        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleSendOTP}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.buttonText}>{t('auth.sendOTP')}</Text>
          )}
        </TouchableOpacity>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Powered by Chhattisgarh Government
          </Text>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  languageToggleContainer: {
    position: 'absolute',
    top: 60,
    right: 24,
    zIndex: 10,
  },
  welcomeSection: {
    alignItems: 'center',
    marginBottom: 24,
    marginTop: 40,
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: COLORS.primary + '10',
    borderRadius: 12,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
    textAlign: 'center',
    marginBottom: 8,
  },
  welcomeSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[700],
    textAlign: 'center',
    marginBottom: 8,
  },
  welcomeDescription: {
    fontSize: 14,
    color: COLORS.gray[600],
    textAlign: 'center',
    lineHeight: 20,
  },
  welcomeDescriptionEn: {
    fontSize: 12,
    color: COLORS.gray[500],
    fontStyle: 'italic',
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: COLORS.gray[600],
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: COLORS.gray[500],
    textAlign: 'center',
  },
  form: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginBottom: 8,
  },
  phoneInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 12,
    backgroundColor: COLORS.white,
    paddingHorizontal: 16,
  },
  phoneInputError: {
    borderColor: COLORS.error,
    borderWidth: 2,
  },
  countryCode: {
    fontSize: 16,
    color: COLORS.gray[700],
    marginRight: 8,
    paddingRight: 8,
    borderRightWidth: 1,
    borderRightColor: COLORS.gray[300],
  },
  phoneInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 16,
    color: COLORS.gray[900],
  },
  hint: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginTop: 8,
  },
  errorText: {
    fontSize: 12,
    color: COLORS.error,
    marginTop: 8,
    fontWeight: '500',
  },
  button: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  footer: {
    marginTop: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: COLORS.gray[500],
  },
});
