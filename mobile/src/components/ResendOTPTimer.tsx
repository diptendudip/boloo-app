import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { COLORS } from '../constants/config';

interface ResendOTPTimerProps {
  initialSeconds?: number;
  onResend: (type: 'sms' | 'voice') => Promise<void>;
  disabled?: boolean;
  phoneNumber: string;
}

export default function ResendOTPTimer({
  initialSeconds = 30,
  onResend,
  disabled = false,
  phoneNumber,
}: ResendOTPTimerProps) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const [isResending, setIsResending] = useState(false);
  const [canResend, setCanResend] = useState(false);
  const [showVoiceOption, setShowVoiceOption] = useState(false);

  useEffect(() => {
    if (seconds > 0) {
      const timer = setTimeout(() => setSeconds(seconds - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [seconds]);

  const handleResend = async (type: 'sms' | 'voice' = 'sms') => {
    if (!canResend || isResending || disabled) return;

    setIsResending(true);
    try {
      await onResend(type);
      // Reset timer after successful resend
      setSeconds(initialSeconds);
      setCanResend(false);

      // Show voice option after first SMS resend
      if (type === 'sms') {
        setShowVoiceOption(true);
      }
    } catch (error) {
      console.error('Resend OTP error:', error);
    } finally {
      setIsResending(false);
    }
  };

  const formatTime = (sec: number): string => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isResending) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color={COLORS.primary} />
        <Text style={styles.loadingText}>Sending OTP...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!canResend ? (
        <View style={styles.timerContainer}>
          <Text style={styles.timerText}>
            Resend OTP in {formatTime(seconds)}
          </Text>
        </View>
      ) : (
        <View style={styles.resendContainer}>
          <Text style={styles.resendText}>Didn't receive the code? </Text>
          <View style={styles.buttonGroup}>
            <TouchableOpacity
              onPress={() => handleResend('sms')}
              disabled={disabled}
              style={styles.resendButton}
            >
              <Text style={[styles.resendLink, disabled && styles.disabledLink]}>
                Resend SMS
              </Text>
            </TouchableOpacity>

            {showVoiceOption && (
              <>
                <Text style={styles.separator}>or</Text>
                <TouchableOpacity
                  onPress={() => handleResend('voice')}
                  disabled={disabled}
                  style={styles.resendButton}
                >
                  <Text style={[styles.resendLink, disabled && styles.disabledLink]}>
                    Call Me
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    marginVertical: 16,
  },
  timerContainer: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: COLORS.gray[100],
    borderRadius: 8,
  },
  timerText: {
    fontSize: 14,
    color: COLORS.gray[600],
    fontWeight: '500',
  },
  resendContainer: {
    alignItems: 'center',
  },
  resendText: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginBottom: 8,
  },
  buttonGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  resendButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  resendLink: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  separator: {
    fontSize: 14,
    color: COLORS.gray[500],
    marginHorizontal: 8,
  },
  disabledLink: {
    color: COLORS.gray[400],
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
    color: COLORS.gray[600],
  },
});
