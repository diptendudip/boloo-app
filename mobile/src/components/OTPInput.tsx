import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  Platform,
  Keyboard,
} from 'react-native';
import { COLORS } from '../constants/config';

interface OTPInputProps {
  length?: number;
  value: string[];
  onChange: (otp: string[]) => void;
  disabled?: boolean;
  autoFocus?: boolean;
}

export default function OTPInput({
  length = 6,
  value,
  onChange,
  disabled = false,
  autoFocus = true,
}: OTPInputProps) {
  const inputRefs = useRef<Array<TextInput | null>>([]);
  const [focusedIndex, setFocusedIndex] = useState<number | null>(autoFocus ? 0 : null);

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  const handleChange = (text: string, index: number) => {
    // Only allow single digit
    if (text.length > 1) {
      return;
    }

    // Only allow numbers
    if (text && !/^\d+$/.test(text)) {
      return;
    }

    const newOTP = [...value];
    newOTP[index] = text;
    onChange(newOTP);

    // Auto-focus next input
    if (text && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit if all filled
    if (text && index === length - 1) {
      const isComplete = newOTP.every(digit => digit.length === 1);
      if (isComplete) {
        Keyboard.dismiss();
      }
    }
  };

  const handleKeyPress = (e: any, index: number) => {
    if (e.nativeEvent.key === 'Backspace') {
      if (!value[index] && index > 0) {
        // Move to previous input on backspace if current is empty
        inputRefs.current[index - 1]?.focus();
      } else {
        // Clear current input
        const newOTP = [...value];
        newOTP[index] = '';
        onChange(newOTP);
      }
    }
  };

  const handleFocus = (index: number) => {
    setFocusedIndex(index);
  };

  const handleBlur = () => {
    setFocusedIndex(null);
  };

  return (
    <View style={styles.container}>
      {Array.from({ length }).map((_, index) => (
        <TextInput
          key={index}
          ref={(ref) => (inputRefs.current[index] = ref)}
          style={[
            styles.input,
            value[index] && styles.inputFilled,
            focusedIndex === index && styles.inputFocused,
            disabled && styles.inputDisabled,
          ]}
          keyboardType="number-pad"
          maxLength={1}
          value={value[index] || ''}
          onChangeText={(text) => handleChange(text, index)}
          onKeyPress={(e) => handleKeyPress(e, index)}
          onFocus={() => handleFocus(index)}
          onBlur={handleBlur}
          editable={!disabled}
          selectTextOnFocus
          textContentType="oneTimeCode"
          autoComplete={index === 0 ? 'sms-otp' : 'off'}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  input: {
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
    ...Platform.select({
      ios: {
        paddingTop: 15,
      },
      android: {
        paddingTop: 10,
      },
    }),
  },
  inputFilled: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '05',
  },
  inputFocused: {
    borderColor: COLORS.primary,
    borderWidth: 3,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  inputDisabled: {
    backgroundColor: COLORS.gray[100],
    borderColor: COLORS.gray[200],
  },
});
