import React, { useState, useRef } from 'react';
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
import { COLORS } from '../constants/config';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';

type VerifyOTPScreenNavigationProp = StackNavigationProp<RootStackParamList, 'VerifyOTP'>;
type VerifyOTPScreenRouteProp = RouteProp<RootStackParamList, 'VerifyOTP'>;

interface Props {
  navigation: VerifyOTPScreenNavigationProp;
  route: VerifyOTPScreenRouteProp;
}

export default function VerifyOTPScreen({ navigation, route }: Props) {
  const { phoneNumber } = route.params;
  const [otp, setOTP] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const { login, requestOTP } = useAuth();
  const inputRefs = useRef<Array<TextInput | null>>([]);

  const handleOTPChange = (value: string, index: number) => {
    if (value.length > 1) return; // Only allow single digit

    const newOTP = [...otp];
    newOTP[index] = value;
    setOTP(newOTP);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleBackspace = (value: string, index: number) => {
    if (!value && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyOTP = async () => {
    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      Alert.alert('Invalid OTP', 'Please enter the complete 6-digit OTP');
      return;
    }

    setIsLoading(true);
    try {
      // DUMMY AUTH FOR TESTING
      // Accept "123456" as valid OTP for any phone number
      if (otpCode === '123456') {
        console.log('TESTING MODE: OTP accepted, logging in...');

        // Create a dummy user session
        await login(phoneNumber, otpCode);

        Alert.alert('Success', 'Login successful!');
        // Navigation to Home will be handled by App.tsx based on auth state
      } else {
        // Show helpful message for testing
        Alert.alert(
          'Testing Mode',
          'For testing, please use OTP: 123456\n\nYou entered: ' + otpCode
        );
        setOTP(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (error) {
      Alert.alert('Error', 'Login failed. Please try OTP: 123456');
      console.error('OTP verification error:', error);
      setOTP(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setIsResending(true);
    try {
      // DUMMY AUTH FOR TESTING
      // Simulate OTP resend
      await new Promise(resolve => setTimeout(resolve, 500));
      Alert.alert('Testing Mode', 'Use OTP: 123456 for any phone number');
      setOTP(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (error) {
      Alert.alert('Error', 'Failed to resend OTP. Please try again.');
    } finally {
      setIsResending(false);
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
          <Text style={styles.phoneText}>{phoneNumber}</Text>
          {__DEV__ && (
            <View style={styles.devModeBanner}>
              <Text style={styles.devModeText}>DEV MODE - OTP: 123456</Text>
            </View>
          )}
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.changePhone}>Change number</Text>
          </TouchableOpacity>
        </View>

        {/* OTP Input */}
        <View style={styles.otpContainer}>
          {otp.map((digit, index) => (
            <TextInput
              key={index}
              ref={(ref) => (inputRefs.current[index] = ref)}
              style={[styles.otpInput, digit && styles.otpInputFilled]}
              keyboardType="number-pad"
              maxLength={1}
              value={digit}
              onChangeText={(value) => handleOTPChange(value, index)}
              onKeyPress={({ nativeEvent }) => {
                if (nativeEvent.key === 'Backspace') {
                  handleBackspace(digit, index);
                }
              }}
              editable={!isLoading}
            />
          ))}
        </View>

        {/* Verify Button */}
        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleVerifyOTP}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.buttonText}>Verify & Continue</Text>
          )}
        </TouchableOpacity>

        {/* Resend OTP */}
        <View style={styles.resendContainer}>
          <Text style={styles.resendText}>Didn't receive the code? </Text>
          <TouchableOpacity onPress={handleResendOTP} disabled={isResending}>
            <Text style={styles.resendLink}>
              {isResending ? 'Sending...' : 'Resend OTP'}
            </Text>
          </TouchableOpacity>
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
  changePhone: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  otpContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  otpInput: {
    width: 50,
    height: 60,
    borderWidth: 2,
    borderColor: COLORS.gray[300],
    borderRadius: 12,
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    backgroundColor: COLORS.white,
    color: COLORS.gray[900],
  },
  otpInputFilled: {
    borderColor: COLORS.primary,
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
  resendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  resendText: {
    fontSize: 14,
    color: COLORS.gray[600],
  },
  resendLink: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  devModeBanner: {
    backgroundColor: COLORS.gray[200],
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginVertical: 12,
    alignSelf: 'center',
  },
  devModeText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.gray[700],
    textAlign: 'center',
  },
});
