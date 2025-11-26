/**
 * ChangePhoneScreen
 *
 * 3-step phone number change flow:
 * Step 1: Verify current phone with OTP
 * Step 2: Enter new phone number
 * Step 3: Verify new phone with OTP
 *
 * Security features:
 * - Verify current phone ownership first
 * - Check new phone not already registered
 * - Send confirmation SMS to both numbers
 * - Rate limiting and cooldown period
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../context/AuthContext';
import { COLORS, API_BASE_URL } from '../constants/config';

type Step = 1 | 2 | 3;

interface PhoneChangeSession {
  sessionId: string;
  currentPhone: string;
  newPhone?: string;
  expiresAt: string;
}

export default function ChangePhoneScreen() {
  const navigation = useNavigation();
  const { user, token, updateUser } = useAuth();

  // Step management
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);

  // Session data
  const [session, setSession] = useState<PhoneChangeSession | null>(null);

  // Step 1: Current phone OTP
  const [currentOtp, setCurrentOtp] = useState(['', '', '', '', '', '']);
  const [currentOtpSent, setCurrentOtpSent] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);

  // Step 2: New phone number
  const [newPhone, setNewPhone] = useState('');
  const [newPhoneError, setNewPhoneError] = useState('');

  // Step 3: New phone OTP
  const [newOtp, setNewOtp] = useState(['', '', '', '', '', '']);
  const [newOtpSent, setNewOtpSent] = useState(false);

  // OTP input refs
  const currentOtpRefs = useRef<TextInput[]>([]);
  const newOtpRefs = useRef<TextInput[]>([]);

  // Timer for resend
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  // Format phone number for display
  const formatPhone = (phone?: string) => {
    if (!phone) return 'N/A';
    return phone.replace(/(\+\d{2})(\d{5})(\d{5})/, '$1 $2 $3');
  };

  // Step 1: Request OTP for current phone
  const requestCurrentPhoneOtp = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/v1/users/phone-change/request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send OTP');
      }

      setSession({
        sessionId: data.session_id,
        currentPhone: user?.phone || '',
        expiresAt: data.expires_at,
      });
      setCurrentOtpSent(true);
      setResendTimer(60);

      Alert.alert(
        'OTP भेजा गया / OTP Sent',
        `आपके फोन ${formatPhone(user?.phone)} पर OTP भेजा गया है\nOTP sent to your phone ${formatPhone(user?.phone)}`,
        [{ text: 'ठीक है / OK' }]
      );
    } catch (error: any) {
      Alert.alert(
        'त्रुटि / Error',
        error.message || 'Failed to send OTP',
        [{ text: 'ठीक है / OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Verify current phone OTP
  const verifyCurrentPhoneOtp = async () => {
    const otpCode = currentOtp.join('');
    if (otpCode.length !== 6) {
      Alert.alert(
        'अधूरा OTP / Incomplete OTP',
        'कृपया 6 अंकों का OTP डालें\nPlease enter 6-digit OTP',
        [{ text: 'ठीक है / OK' }]
      );
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/v1/users/phone-change/verify-current`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: session?.sessionId,
          otp: otpCode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Invalid OTP');
      }

      // Move to step 2
      setCurrentStep(2);
    } catch (error: any) {
      Alert.alert(
        'गलत OTP / Invalid OTP',
        error.message || 'Please check and try again',
        [{ text: 'ठीक है / OK' }]
      );
      setCurrentOtp(['', '', '', '', '', '']);
      currentOtpRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Send OTP to new phone
  const sendNewPhoneOtp = async () => {
    // Validate phone number
    const phoneRegex = /^[6-9]\d{9}$/;
    if (!phoneRegex.test(newPhone)) {
      setNewPhoneError('कृपया मान्य फोन नंबर डालें / Please enter valid phone number');
      return;
    }

    // Check if new phone is same as current
    if (`+91${newPhone}` === user?.phone) {
      setNewPhoneError('नया नंबर मौजूदा नंबर से अलग होना चाहिए / New number must be different');
      return;
    }

    setLoading(true);
    setNewPhoneError('');

    try {
      const response = await fetch(`${API_BASE_URL}/v1/users/phone-change/send-new-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: session?.sessionId,
          new_phone: `+91${newPhone}`,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send OTP');
      }

      setSession({
        ...session!,
        newPhone: `+91${newPhone}`,
      });
      setNewOtpSent(true);
      setCurrentStep(3);

      Alert.alert(
        'OTP भेजा गया / OTP Sent',
        `आपके नए फोन ${formatPhone(`+91${newPhone}`)} पर OTP भेजा गया है\nOTP sent to your new phone ${formatPhone(`+91${newPhone}`)}`,
        [{ text: 'ठीक है / OK' }]
      );
    } catch (error: any) {
      setNewPhoneError(error.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Verify new phone OTP and complete change
  const verifyNewPhoneOtp = async () => {
    const otpCode = newOtp.join('');
    if (otpCode.length !== 6) {
      Alert.alert(
        'अधूरा OTP / Incomplete OTP',
        'कृपया 6 अंकों का OTP डालें\nPlease enter 6-digit OTP',
        [{ text: 'ठीक है / OK' }]
      );
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/v1/users/phone-change/verify-new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: session?.sessionId,
          otp: otpCode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Invalid OTP');
      }

      // Update user context
      if (updateUser && session?.newPhone) {
        updateUser({ ...user!, phone: session.newPhone });
      }

      Alert.alert(
        'सफलता! / Success!',
        `आपका फोन नंबर सफलतापूर्वक बदल दिया गया है\nYour phone number has been changed successfully\n\nनया नंबर / New Number: ${formatPhone(session?.newPhone)}`,
        [
          {
            text: 'ठीक है / OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error: any) {
      Alert.alert(
        'गलत OTP / Invalid OTP',
        error.message || 'Please check and try again',
        [{ text: 'ठीक है / OK' }]
      );
      setNewOtp(['', '', '', '', '', '']);
      newOtpRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  // Handle OTP input change
  const handleOtpChange = (
    text: string,
    index: number,
    isCurrentPhone: boolean
  ) => {
    const otp = isCurrentPhone ? currentOtp : newOtp;
    const setOtp = isCurrentPhone ? setCurrentOtp : setNewOtp;
    const refs = isCurrentPhone ? currentOtpRefs : newOtpRefs;

    // Update OTP array
    const newOtpArray = [...otp];
    newOtpArray[index] = text;
    setOtp(newOtpArray);

    // Auto-focus next input
    if (text.length === 1 && index < 5) {
      refs.current[index + 1]?.focus();
    }
  };

  // Handle OTP backspace
  const handleOtpKeyPress = (
    e: any,
    index: number,
    isCurrentPhone: boolean
  ) => {
    const otp = isCurrentPhone ? currentOtp : newOtp;
    const refs = isCurrentPhone ? currentOtpRefs : newOtpRefs;

    if (e.nativeEvent.key === 'Backspace' && !otp[index] && index > 0) {
      refs.current[index - 1]?.focus();
    }
  };

  // Render progress indicator
  const renderProgress = () => (
    <View style={styles.progressContainer}>
      <View style={styles.progressSteps}>
        {[1, 2, 3].map((step) => (
          <View key={step} style={styles.progressStepWrapper}>
            <View
              style={[
                styles.progressStep,
                currentStep >= step && styles.progressStepActive,
                currentStep > step && styles.progressStepCompleted,
              ]}
            >
              {currentStep > step ? (
                <Ionicons name="checkmark" size={16} color={COLORS.white} />
              ) : (
                <Text
                  style={[
                    styles.progressStepText,
                    currentStep >= step && styles.progressStepTextActive,
                  ]}
                >
                  {step}
                </Text>
              )}
            </View>
            {step < 3 && (
              <View
                style={[
                  styles.progressLine,
                  currentStep > step && styles.progressLineActive,
                ]}
              />
            )}
          </View>
        ))}
      </View>

      <View style={styles.progressLabels}>
        <Text style={styles.progressLabel}>वर्तमान{'\n'}Current</Text>
        <Text style={styles.progressLabel}>नया नंबर{'\n'}New Number</Text>
        <Text style={styles.progressLabel}>सत्यापित{'\n'}Verify</Text>
      </View>
    </View>
  );

  // Render Step 1: Verify current phone
  const renderStep1 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <Ionicons name="shield-checkmark" size={48} color={COLORS.primary} />
        <Text style={styles.stepTitleHindi}>अपना मौजूदा फोन सत्यापित करें</Text>
        <Text style={styles.stepTitleEnglish}>Verify Your Current Phone</Text>
      </View>

      <View style={styles.phoneDisplay}>
        <Text style={styles.phoneLabel}>आपका मौजूदा फोन / Your Current Phone</Text>
        <Text style={styles.phoneNumber}>{formatPhone(user?.phone)}</Text>
      </View>

      {!currentOtpSent ? (
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={requestCurrentPhoneOtp}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <>
              <Text style={styles.primaryButtonTextHindi}>OTP भेजें</Text>
              <Text style={styles.primaryButtonTextEnglish}>Send OTP</Text>
            </>
          )}
        </TouchableOpacity>
      ) : (
        <>
          <View style={styles.otpContainer}>
            <Text style={styles.otpLabel}>OTP डालें / Enter OTP</Text>
            <View style={styles.otpInputs}>
              {currentOtp.map((digit, index) => (
                <TextInput
                  key={index}
                  ref={(ref) => (currentOtpRefs.current[index] = ref!)}
                  style={styles.otpInput}
                  value={digit}
                  onChangeText={(text) => handleOtpChange(text, index, true)}
                  onKeyPress={(e) => handleOtpKeyPress(e, index, true)}
                  keyboardType="number-pad"
                  maxLength={1}
                  selectTextOnFocus
                />
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={verifyCurrentPhoneOtp}
            disabled={loading || currentOtp.join('').length !== 6}
          >
            {loading ? (
              <ActivityIndicator color={COLORS.white} />
            ) : (
              <>
                <Text style={styles.primaryButtonTextHindi}>आगे बढ़ें</Text>
                <Text style={styles.primaryButtonTextEnglish}>Next</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkButton}
            onPress={requestCurrentPhoneOtp}
            disabled={resendTimer > 0 || loading}
          >
            <Text style={styles.linkButtonText}>
              {resendTimer > 0
                ? `फिर से भेजें (${resendTimer}s) / Resend (${resendTimer}s)`
                : 'फिर से OTP भेजें / Resend OTP'}
            </Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  );

  // Render Step 2: Enter new phone
  const renderStep2 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <Ionicons name="phone-portrait" size={48} color={COLORS.primary} />
        <Text style={styles.stepTitleHindi}>नया फोन नंबर डालें</Text>
        <Text style={styles.stepTitleEnglish}>Enter New Phone Number</Text>
      </View>

      <View style={styles.phoneInputContainer}>
        <Text style={styles.inputLabel}>नया फोन नंबर / New Phone Number</Text>
        <View style={styles.phoneInputWrapper}>
          <Text style={styles.countryCode}>+91</Text>
          <TextInput
            style={styles.phoneInput}
            value={newPhone}
            onChangeText={(text) => {
              setNewPhone(text.replace(/[^0-9]/g, ''));
              setNewPhoneError('');
            }}
            placeholder="98765 43210"
            keyboardType="phone-pad"
            maxLength={10}
            autoFocus
          />
        </View>
        {newPhoneError ? (
          <Text style={styles.errorText}>{newPhoneError}</Text>
        ) : null}
      </View>

      <View style={styles.infoBox}>
        <Ionicons name="information-circle" size={20} color={COLORS.info} />
        <Text style={styles.infoText}>
          नया नंबर पंजीकृत नहीं होना चाहिए{'\n'}
          New number must not be already registered
        </Text>
      </View>

      <TouchableOpacity
        style={styles.primaryButton}
        onPress={sendNewPhoneOtp}
        disabled={loading || newPhone.length !== 10}
      >
        {loading ? (
          <ActivityIndicator color={COLORS.white} />
        ) : (
          <>
            <Text style={styles.primaryButtonTextHindi}>OTP भेजें</Text>
            <Text style={styles.primaryButtonTextEnglish}>Send OTP</Text>
          </>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.secondaryButton}
        onPress={() => setCurrentStep(1)}
      >
        <Ionicons name="arrow-back" size={20} color={COLORS.gray[600]} />
        <Text style={styles.secondaryButtonText}>पीछे जाएं / Go Back</Text>
      </TouchableOpacity>
    </View>
  );

  // Render Step 3: Verify new phone
  const renderStep3 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <Ionicons name="checkmark-circle" size={48} color={COLORS.success} />
        <Text style={styles.stepTitleHindi}>नया फोन सत्यापित करें</Text>
        <Text style={styles.stepTitleEnglish}>Verify New Phone</Text>
      </View>

      <View style={styles.phoneDisplay}>
        <Text style={styles.phoneLabel}>नए नंबर पर OTP भेजा गया / OTP sent to new number</Text>
        <Text style={styles.phoneNumber}>{formatPhone(session?.newPhone)}</Text>
      </View>

      <View style={styles.otpContainer}>
        <Text style={styles.otpLabel}>OTP डालें / Enter OTP</Text>
        <View style={styles.otpInputs}>
          {newOtp.map((digit, index) => (
            <TextInput
              key={index}
              ref={(ref) => (newOtpRefs.current[index] = ref!)}
              style={styles.otpInput}
              value={digit}
              onChangeText={(text) => handleOtpChange(text, index, false)}
              onKeyPress={(e) => handleOtpKeyPress(e, index, false)}
              keyboardType="number-pad"
              maxLength={1}
              selectTextOnFocus
            />
          ))}
        </View>
      </View>

      <TouchableOpacity
        style={styles.primaryButton}
        onPress={verifyNewPhoneOtp}
        disabled={loading || newOtp.join('').length !== 6}
      >
        {loading ? (
          <ActivityIndicator color={COLORS.white} />
        ) : (
          <>
            <Text style={styles.primaryButtonTextHindi}>बदलाव पूरा करें</Text>
            <Text style={styles.primaryButtonTextEnglish}>Complete Change</Text>
          </>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.secondaryButton}
        onPress={() => setCurrentStep(2)}
      >
        <Ionicons name="arrow-back" size={20} color={COLORS.gray[600]} />
        <Text style={styles.secondaryButtonText}>पीछे जाएं / Go Back</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color={COLORS.gray[900]} />
          </TouchableOpacity>
          <View style={styles.headerTitles}>
            <Text style={styles.headerTitleHindi}>फोन नंबर बदलें</Text>
            <Text style={styles.headerTitleEnglish}>Change Phone Number</Text>
          </View>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView style={styles.scrollView}>
          {/* Progress Indicator */}
          {renderProgress()}

          {/* Current Step */}
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}

          {/* Security Notice */}
          <View style={styles.securityNotice}>
            <Ionicons name="lock-closed" size={16} color={COLORS.gray[500]} />
            <Text style={styles.securityText}>
              सुरक्षित और एन्क्रिप्टेड / Secure & Encrypted
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  backButton: {
    padding: 8,
  },
  headerTitles: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitleHindi: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  headerTitleEnglish: {
    fontSize: 12,
    color: COLORS.gray[600],
  },
  headerSpacer: {
    width: 40,
  },
  scrollView: {
    flex: 1,
  },
  progressContainer: {
    padding: 24,
    backgroundColor: COLORS.white,
    marginBottom: 8,
  },
  progressSteps: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  progressStepWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressStep: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.gray[200],
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressStepActive: {
    backgroundColor: COLORS.primary,
  },
  progressStepCompleted: {
    backgroundColor: COLORS.success,
  },
  progressStepText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[600],
  },
  progressStepTextActive: {
    color: COLORS.white,
  },
  progressLine: {
    width: 60,
    height: 2,
    backgroundColor: COLORS.gray[200],
    marginHorizontal: 8,
  },
  progressLineActive: {
    backgroundColor: COLORS.success,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
  },
  progressLabel: {
    fontSize: 10,
    color: COLORS.gray[600],
    textAlign: 'center',
    width: 80,
  },
  stepContainer: {
    padding: 24,
    backgroundColor: COLORS.white,
    marginBottom: 8,
  },
  stepHeader: {
    alignItems: 'center',
    marginBottom: 32,
  },
  stepTitleHindi: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginTop: 16,
    textAlign: 'center',
  },
  stepTitleEnglish: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginTop: 4,
    textAlign: 'center',
  },
  phoneDisplay: {
    backgroundColor: COLORS.gray[50],
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
  },
  phoneLabel: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginBottom: 8,
    textAlign: 'center',
  },
  phoneNumber: {
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  phoneInputContainer: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginBottom: 8,
  },
  phoneInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.gray[50],
    borderRadius: 12,
    borderWidth: 2,
    borderColor: COLORS.gray[200],
    paddingHorizontal: 16,
  },
  countryCode: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginRight: 12,
  },
  phoneInput: {
    flex: 1,
    fontSize: 18,
    fontWeight: '500',
    color: COLORS.gray[900],
    paddingVertical: 16,
  },
  errorText: {
    fontSize: 12,
    color: COLORS.error,
    marginTop: 8,
  },
  otpContainer: {
    marginBottom: 24,
  },
  otpLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginBottom: 12,
    textAlign: 'center',
  },
  otpInputs: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  otpInput: {
    width: 48,
    height: 56,
    backgroundColor: COLORS.gray[50],
    borderRadius: 12,
    borderWidth: 2,
    borderColor: COLORS.gray[200],
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.gray[900],
    textAlign: 'center',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.info + '10',
    borderRadius: 12,
    padding: 12,
    marginBottom: 24,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: COLORS.info,
    marginLeft: 8,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  primaryButtonTextHindi: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  primaryButtonTextEnglish: {
    fontSize: 12,
    color: COLORS.white,
    marginTop: 2,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.gray[100],
    borderRadius: 12,
    padding: 16,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginLeft: 8,
  },
  linkButton: {
    alignItems: 'center',
    padding: 12,
  },
  linkButtonText: {
    fontSize: 14,
    color: COLORS.primary,
  },
  securityNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  securityText: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginLeft: 8,
  },
});
