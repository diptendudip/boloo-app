import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Language = 'en' | 'hi';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => Promise<void>;
  t: (key: string) => string;
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    // Auth
    'auth.title': 'Boloo',
    'auth.subtitle': 'Citizen Grievance System',
    'auth.description': 'Report grievances and track their resolution',
    'auth.phoneLabel': 'Mobile Number',
    'auth.phonePlaceholder': 'Enter 10-digit mobile number',
    'auth.phoneHint': 'You will receive an OTP via SMS',
    'auth.sendOTP': 'Send OTP',
    'auth.invalidPhone': 'Invalid Mobile Number',
    'auth.invalidPhoneMsg': 'Please enter a valid 10-digit Indian mobile number',
    'auth.error': 'Error',
    'auth.otpSendError': 'Failed to send OTP. Please try again.',

    // Verify OTP
    'verify.title': 'Verify OTP',
    'verify.subtitle': 'Enter the 6-digit code sent to',
    'verify.changeEmail': 'Change email',
    'verify.verifyButton': 'Verify & Continue',
    'verify.invalidOTP': 'Invalid OTP',
    'verify.invalidOTPMsg': 'Please enter the complete 6-digit OTP',
    'verify.otpError': 'Invalid OTP. Please try again.',
    'verify.resendText': "Didn't receive the code? ",
    'verify.resendLink': 'Resend OTP',
    'verify.sending': 'Sending...',
    'verify.otpSent': 'OTP Sent',
    'verify.otpSentMsg': 'A new OTP has been sent to your email',

    // Voice Recording
    'voice.title': 'Record Your Grievance',
    'voice.subtitle': 'Describe your issue in Hindi or English',
    'voice.recording': 'Recording...',
    'voice.maxDuration': 'Max',
    'voice.tapToStart': 'Tap the button to start recording',
    'voice.tapToStop': 'Tap again to stop recording',
    'voice.reviewOrContinue': 'Play to review or continue',
    'voice.continue': 'Continue',
    'voice.noRecording': 'No Recording',
    'voice.noRecordingMsg': 'Please record your grievance first',
    'voice.permissionRequired': 'Permission Required',
    'voice.permissionMsg': 'Microphone permission is required to record audio',
    'voice.recordError': 'Failed to start recording. Please try again.',
    'voice.stopError': 'Failed to stop recording. Please try again.',
    'voice.playError': 'Failed to play recording',

    // Common
    'common.ok': 'OK',
    'common.cancel': 'Cancel',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
  },
  hi: {
    // Auth
    'auth.title': 'बोलो',
    'auth.subtitle': 'नागरिक शिकायत प्रणाली',
    'auth.description': 'शिकायत दर्ज करें और उनका समाधान ट्रैक करें',
    'auth.phoneLabel': 'मोबाइल नंबर',
    'auth.phonePlaceholder': '10 अंकों का मोबाइल नंबर दर्ज करें',
    'auth.phoneHint': 'आपको SMS के माध्यम से OTP प्राप्त होगा',
    'auth.sendOTP': 'OTP भेजें',
    'auth.invalidPhone': 'अमान्य मोबाइल नंबर',
    'auth.invalidPhoneMsg': 'कृपया एक वैध 10-अंकीय भारतीय मोबाइल नंबर दर्ज करें',
    'auth.error': 'त्रुटि',
    'auth.otpSendError': 'OTP भेजने में विफल। कृपया पुनः प्रयास करें।',

    // Verify OTP
    'verify.title': 'OTP सत्यापित करें',
    'verify.subtitle': 'भेजे गए 6-अंकीय कोड को दर्ज करें',
    'verify.changeEmail': 'ईमेल बदलें',
    'verify.verifyButton': 'सत्यापित करें और जारी रखें',
    'verify.invalidOTP': 'अमान्य OTP',
    'verify.invalidOTPMsg': 'कृपया पूर्ण 6-अंकीय OTP दर्ज करें',
    'verify.otpError': 'अमान्य OTP। कृपया पुनः प्रयास करें।',
    'verify.resendText': 'कोड प्राप्त नहीं हुआ? ',
    'verify.resendLink': 'OTP पुनः भेजें',
    'verify.sending': 'भेजा जा रहा है...',
    'verify.otpSent': 'OTP भेजा गया',
    'verify.otpSentMsg': 'आपके ईमेल पर एक नया OTP भेजा गया है',

    // Voice Recording
    'voice.title': 'अपनी शिकायत रिकॉर्ड करें',
    'voice.subtitle': 'हिंदी या अंग्रेजी में अपनी समस्या बताएं',
    'voice.recording': 'रिकॉर्डिंग...',
    'voice.maxDuration': 'अधिकतम',
    'voice.tapToStart': 'रिकॉर्डिंग शुरू करने के लिए बटन दबाएं',
    'voice.tapToStop': 'रिकॉर्डिंग बंद करने के लिए फिर से दबाएं',
    'voice.reviewOrContinue': 'समीक्षा के लिए चलाएं या जारी रखें',
    'voice.continue': 'जारी रखें',
    'voice.noRecording': 'कोई रिकॉर्डिंग नहीं',
    'voice.noRecordingMsg': 'कृपया पहले अपनी शिकायत रिकॉर्ड करें',
    'voice.permissionRequired': 'अनुमति आवश्यक',
    'voice.permissionMsg': 'ऑडियो रिकॉर्ड करने के लिए माइक्रोफोन की अनुमति आवश्यक है',
    'voice.recordError': 'रिकॉर्डिंग शुरू करने में विफल। कृपया पुनः प्रयास करें।',
    'voice.stopError': 'रिकॉर्डिंग बंद करने में विफल। कृपया पुनः प्रयास करें।',
    'voice.playError': 'रिकॉर्डिंग चलाने में विफल',

    // Common
    'common.ok': 'ठीक है',
    'common.cancel': 'रद्द करें',
    'common.loading': 'लोड हो रहा है...',
    'common.error': 'त्रुटि',
    'common.success': 'सफलता',
  },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const LANGUAGE_STORAGE_KEY = '@boloo_language';

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    loadLanguage();
  }, []);

  const loadLanguage = async () => {
    try {
      const savedLanguage = await AsyncStorage.getItem(LANGUAGE_STORAGE_KEY);
      if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'hi')) {
        setLanguageState(savedLanguage);
      }
    } catch (error) {
      console.error('Failed to load language:', error);
    }
  };

  const setLanguage = async (lang: Language) => {
    try {
      await AsyncStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
      setLanguageState(lang);
    } catch (error) {
      console.error('Failed to save language:', error);
    }
  };

  const t = (key: string): string => {
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
