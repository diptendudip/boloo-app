import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { FONTS, COLORS } from '../constants/config';

/**
 * FontTest Component
 * Test component to verify Noto Sans Devanagari font rendering
 * This component displays various Hindi text samples with different font weights
 */
export const FontTest: React.FC = () => {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.heading}>Font Test - Noto Sans Devanagari</Text>

        {/* Regular Weight */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>Regular (400):</Text>
          <Text style={[styles.text, { fontFamily: FONTS.regular }]}>
            नमस्ते - शिकायत दर्ज करें
          </Text>
          <Text style={[styles.text, { fontFamily: FONTS.regular }]}>
            कृपया अपनी शिकायत का विवरण दें
          </Text>
        </View>

        {/* Medium Weight */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>Medium (500):</Text>
          <Text style={[styles.text, { fontFamily: FONTS.medium }]}>
            नमस्ते - शिकायत दर्ज करें
          </Text>
          <Text style={[styles.text, { fontFamily: FONTS.medium }]}>
            कृपया अपनी शिकायत का विवरण दें
          </Text>
        </View>

        {/* SemiBold Weight */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>SemiBold (600):</Text>
          <Text style={[styles.text, { fontFamily: FONTS.semibold }]}>
            नमस्ते - शिकायत दर्ज करें
          </Text>
          <Text style={[styles.text, { fontFamily: FONTS.semibold }]}>
            कृपया अपनी शिकायत का विवरण दें
          </Text>
        </View>

        {/* Bold Weight */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>Bold (700):</Text>
          <Text style={[styles.text, { fontFamily: FONTS.bold }]}>
            नमस्ते - शिकायत दर्ज करें
          </Text>
          <Text style={[styles.text, { fontFamily: FONTS.bold }]}>
            कृपया अपनी शिकायत का विवरण दें
          </Text>
        </View>

        {/* Devanagari Numbers */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>Devanagari Numbers:</Text>
          <Text style={[styles.text, { fontFamily: FONTS.regular }]}>
            १२३४५६७८९०
          </Text>
        </View>

        {/* Complex Text */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>Complex Text (Conjuncts):</Text>
          <Text style={[styles.text, { fontFamily: FONTS.regular }]}>
            संयुक्ताक्षर - क्षत्रिय - ज्ञान
          </Text>
          <Text style={[styles.text, { fontFamily: FONTS.regular }]}>
            विद्यालय - कार्यालय - सरकार
          </Text>
        </View>

        {/* Long Paragraph */}
        <View style={styles.testBlock}>
          <Text style={styles.label}>Long Paragraph:</Text>
          <Text style={[styles.paragraph, { fontFamily: FONTS.regular }]}>
            बोलू ऐप नागरिकों को अपनी शिकायतें दर्ज करने और ट्रैक करने में मदद करता है।
            आप फोटो, वीडियो और ऑडियो रिकॉर्डिंग के साथ अपनी शिकायत सबमिट कर सकते हैं।
            सभी शिकायतें जियोटैग की जाती हैं और संबंधित अधिकारियों को भेजी जाती हैं।
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  section: {
    padding: 20,
  },
  heading: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.black,
    marginBottom: 20,
    textAlign: 'center',
  },
  testBlock: {
    backgroundColor: COLORS.white,
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  label: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginBottom: 8,
    fontWeight: '600',
  },
  text: {
    fontSize: 18,
    color: COLORS.black,
    marginBottom: 4,
  },
  paragraph: {
    fontSize: 16,
    color: COLORS.black,
    lineHeight: 24,
  },
});

export default FontTest;
