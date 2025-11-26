import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { COLORS } from '../constants/config';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';
import OTPInput from '../components/OTPInput';
import ResendOTPTimer from '../components/ResendOTPTimer';
import { formatPhoneForDisplay } from '../utils/phoneValidation';
import { OTP_MESSAGES, getOTPErrorMessage } from '../constants/otpMessages';
import { authService } from '../services/auth';
import { analytics, AnalyticsEvent } from '../utils/analytics';

type VerifyOTPScreenNavigationProp = StackNavigationProp<RootStackParamList, 'VerifyOTP'>;
type VerifyOTPScreenRouteProp = RouteProp<RootStackParamList, 'VerifyOTP'>;

interface Props {
  navigation: VerifyOTPScreenNavigationProp;
  route: VerifyOTPScreenRouteProp;
}

const TESTING_MODE = __DEV__; // Enable testing mode in development
const TEST_OTP = '123456';

export default function VerifyOTPScreen({ navigation, route }: Props) {
  const { phoneNumber } = route.params;
  const [otp, setOTP] = useState<string[]>(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const { login } = useAuth();

  // Auto-verify when OTP is complete
  useEffect(() => {
    const otpCode = otp.join('');
    if (otpCode.length === 6) {
      handleVerifyOTP();
    }
  }, [otp]);

  const handleOTPChange = (newOTP: string[]) => {
    setOTP(newOTP);
    // Clear error when user types
    if (errorMessage) {
      setErrorMessage('');
    }
  };

  const handleVerifyOTP = async () => {
    const otpCode = otp.join('');

    if (otpCode.length !== 6) {
      setErrorMessage(OTP_MESSAGES.OTP_INCOMPLETE);
      return;
    }

    analytics.track(AnalyticsEvent.OTP_VERIFY_INITIATED, {
      phone_length: phoneNumber.length,
    });

    setIsLoading(true);
    setErrorMessage('');

    try {
      if (TESTING_MODE && otpCode === TEST_OTP) {
        // TESTING MODE: Accept dummy OTP
        console.log('[VerifyOTP] TESTING MODE: OTP accepted, logging in...');

        await login(phoneNumber, otpCode);

        analytics.trackOTPVerify(phoneNumber, true);

        Alert.alert(
          'Success',
          'Login successful!',
          [{ text: 'OK' }]
        );
        // Navigation handled by AuthContext
      } else if (TESTING_MODE) {
        // Wrong OTP in testing mode
        throw new Error(`Testing mode: Use OTP ${TEST_OTP}`);
      } else {
        // PRODUCTION MODE: Verify with backend
        console.log('[VerifyOTP] Verifying OTP with backend...');
        await login(phoneNumber, otpCode);

        analytics.trackOTPVerify(phoneNumber, true);

        Alert.alert(
          'Success',
          OTP_MESSAGES.OTP_VERIFIED,
          [{ text: 'OK' }]
        );
      }
    } catch (error: any) {
      console.error('[VerifyOTP] Verification failed:', error);
      const errorMsg = getOTPErrorMessage(error);
      setErrorMessage(errorMsg);

      analytics.trackOTPVerify(phoneNumber, false, errorMsg);

      // Clear OTP on error
      setOTP(['', '', '', '', '', '']);

      Alert.alert(
        'Verification Failed',
        errorMsg,
        [{ text: 'Try Again' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async (type: 'sms' | 'voice' = 'sms') => {
    analytics.trackOTPResend(phoneNumber, type);

    try {
      if (TESTING_MODE) {
        // TESTING MODE: Show dummy OTP
        console.log('[VerifyOTP] TESTING MODE: Resend OTP');

        Alert.alert(
          'Testing Mode',
          `OTP: ${TEST_OTP}\n\nIn production, you will receive ${type === 'voice' ? 'a call' : 'an SMS'}`,
          [{ text: 'OK' }]
        );
      } else {
        // PRODUCTION MODE: Resend via backend
        console.log(`[VerifyOTP] Resending OTP (${type}) to:`, phoneNumber);
        await authService.resendOTP(phoneNumber, type);

        Alert.alert(
          'OTP Sent',
          type === 'voice' ? OTP_MESSAGES.VOICE_OTP_SENT : OTP_MESSAGES.OTP_RESENT,
          [{ text: 'OK' }]
        );
      }

      // Clear OTP inputs
      setOTP(['', '', '', '', '', '']);
      setErrorMessage('');
    } catch (error: any) {
      console.error('[VerifyOTP] Resend failed:', error);
      const errorMsg = getOTPErrorMessage(error);

      analytics.trackError('api', errorMsg, 'resend_otp');

      Alert.alert(
        'Error',
        errorMsg,
        [{ text: 'OK' }]
      );
      throw error; // Re-throw so ResendOTPTimer can handle it
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Verify OTP</Text>
          <Text style={styles.subtitle}>
            Enter the 6-digit code sent to
          </Text>
          <Text style={styles.phoneText}>
            {formatPhoneForDisplay(phoneNumber)}
          </Text>

          {TESTING_MODE && (
            <View style={styles.devModeBanner}>
              <Text style={styles.devModeText}>
                DEV MODE - OTP: {TEST_OTP}
              </Text>
            </View>
          )}

          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.changePhoneButton}
          >
            <Text style={styles.changePhone}>Change number</Text>
          </TouchableOpacity>
        </View>

        {/* OTP Input */}
        <View style={styles.otpSection}>
          <OTPInput
            value={otp}
            onChange={handleOTPChange}
            disabled={isLoading}
            autoFocus
          />

          {errorMessage && (
            <Text style={styles.errorText}>{errorMessage}</Text>
          )}
        </View>

        {/* Verify Button */}
        <TouchableOpacity
          style={[
            styles.button,
            (isLoading || otp.join('').length !== 6) && styles.buttonDisabled
          ]}
          onPress={handleVerifyOTP}
          disabled={isLoading || otp.join('').length !== 6}
        >
          {isLoading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.buttonText}>Verify & Continue</Text>
          )}
        </TouchableOpacity>

        {/* Resend OTP Timer */}
        <ResendOTPTimer
          onResend={handleResendOTP}
          disabled={isLoading}
          phoneNumber={phoneNumber}
          initialSeconds={30}
        />

        {/* Help Text */}
        <View style={styles.helpContainer}>
          <Text style={styles.helpText}>
            Make sure you have a stable internet connection
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
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.gray[600],
    marginBottom: 8,
  },
  phoneText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 16,
  },
  changePhoneButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  changePhone: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  otpSection: {
    marginBottom: 32,
  },
  errorText: {
    fontSize: 12,
    color: COLORS.error,
    marginTop: 12,
    textAlign: 'center',
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
    marginBottom: 24,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  helpContainer: {
    marginTop: 16,
    alignItems: 'center',
  },
  helpText: {
    fontSize: 12,
    color: COLORS.gray[500],
    textAlign: 'center',
  },
  devModeBanner: {
    backgroundColor: COLORS.warning + '20',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: COLORS.warning,
  },
  devModeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.warning,
    textAlign: 'center',
  },
});
