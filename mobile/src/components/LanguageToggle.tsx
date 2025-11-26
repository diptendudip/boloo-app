import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useLanguage } from '../context/LanguageContext';
import { COLORS } from '../constants/config';

interface LanguageToggleProps {
  variant?: 'compact' | 'full';
}

export default function LanguageToggle({ variant = 'compact' }: LanguageToggleProps) {
  const { language, setLanguage } = useLanguage();

  const handleToggle = () => {
    setLanguage(language === 'en' ? 'hi' : 'en');
  };

  if (variant === 'compact') {
    return (
      <TouchableOpacity
        style={styles.compactContainer}
        onPress={handleToggle}
        activeOpacity={0.7}
      >
        <View style={[
          styles.compactOption,
          language === 'en' && styles.compactOptionActive
        ]}>
          <Text style={[
            styles.compactText,
            language === 'en' && styles.compactTextActive
          ]}>EN</Text>
        </View>
        <View style={[
          styles.compactOption,
          language === 'hi' && styles.compactOptionActive
        ]}>
          <Text style={[
            styles.compactText,
            language === 'hi' && styles.compactTextActive
          ]}>हिं</Text>
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.fullContainer}>
      <TouchableOpacity
        style={[
          styles.fullOption,
          language === 'en' && styles.fullOptionActive
        ]}
        onPress={() => setLanguage('en')}
        activeOpacity={0.7}
      >
        <Text style={[
          styles.fullText,
          language === 'en' && styles.fullTextActive
        ]}>English</Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[
          styles.fullOption,
          language === 'hi' && styles.fullOptionActive
        ]}
        onPress={() => setLanguage('hi')}
        activeOpacity={0.7}
      >
        <Text style={[
          styles.fullText,
          language === 'hi' && styles.fullTextActive
        ]}>हिंदी</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  // Compact variant (for header)
  compactContainer: {
    flexDirection: 'row',
    backgroundColor: COLORS.gray[200],
    borderRadius: 8,
    padding: 2,
  },
  compactOption: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  compactOptionActive: {
    backgroundColor: COLORS.white,
  },
  compactText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.gray[600],
  },
  compactTextActive: {
    color: COLORS.primary,
  },

  // Full variant (for standalone)
  fullContainer: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 12,
    overflow: 'hidden',
  },
  fullOption: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: COLORS.white,
    alignItems: 'center',
  },
  fullOptionActive: {
    backgroundColor: COLORS.primary,
  },
  fullText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[700],
  },
  fullTextActive: {
    color: COLORS.white,
  },
});
