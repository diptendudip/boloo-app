/**
 * HelpScreen
 *
 * FAQ and support information for rural users
 * Hindi-first with visual guides
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/config';

interface FAQItem {
  questionHindi: string;
  questionEnglish: string;
  answerHindi: string;
  answerEnglish: string;
}

const FAQS: FAQItem[] = [
  {
    questionHindi: 'कैसे रिपोर्ट करें?',
    questionEnglish: 'How to report?',
    answerHindi: 'होम स्क्रीन पर "समस्या रिपोर्ट करें" बटन दबाएं, फिर अपनी समस्या बोलें या लिखें',
    answerEnglish: 'Tap "Report Issue" button on home screen, then speak or type your problem',
  },
  {
    questionHindi: 'मेरी रिपोर्ट कहाँ जाती है?',
    questionEnglish: 'Where does my report go?',
    answerHindi: 'आपकी रिपोर्ट सीधे संबंधित सरकारी विभाग को जाती है',
    answerEnglish: 'Your report goes directly to the relevant government department',
  },
  {
    questionHindi: 'स्टेटस कैसे देखें?',
    questionEnglish: 'How to check status?',
    answerHindi: '"मेरी रिपोर्ट्स" टैब में जाकर अपनी सभी रिपोर्ट्स और उनका स्टेटस देख सकते हैं',
    answerEnglish: 'Go to "My Reports" tab to see all your reports and their status',
  },
  {
    questionHindi: 'कितने दिन में समाधान होगा?',
    questionEnglish: 'How long for resolution?',
    answerHindi: 'समस्या के प्रकार पर निर्भर करता है - आमतौर पर 7-30 दिन',
    answerEnglish: 'Depends on issue type - usually 7-30 days',
  },
  {
    questionHindi: 'क्या मुझे सूचना मिलेगी?',
    questionEnglish: 'Will I get notified?',
    answerHindi: 'हां, जब आपकी रिपोर्ट पर कार्रवाई होगी तो आपको सूचना मिलेगी',
    answerEnglish: 'Yes, you will be notified when action is taken on your report',
  },
];

export default function HelpScreen() {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleCallSupport = () => {
    Linking.openURL('tel:1800-XXX-XXXX');
  };

  const handleEmailSupport = () => {
    Linking.openURL('mailto:support@boloo-cg.gov.in');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        {/* Header */}
        <View style={styles.header}>
          <Ionicons name="help-circle" size={48} color={COLORS.primary} />
          <Text style={styles.headerTitle}>सहायता केंद्र</Text>
          <Text style={styles.headerSubtitle}>Help Center</Text>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            संपर्क करें / Contact Us
          </Text>

          <TouchableOpacity style={styles.contactButton} onPress={handleCallSupport}>
            <Ionicons name="call-outline" size={24} color={COLORS.primary} />
            <View style={styles.contactTextContainer}>
              <Text style={styles.contactTextHindi}>हेल्पलाइन पर कॉल करें</Text>
              <Text style={styles.contactTextEnglish}>Call Helpline: 1800-XXX-XXXX</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.contactButton} onPress={handleEmailSupport}>
            <Ionicons name="mail-outline" size={24} color={COLORS.primary} />
            <View style={styles.contactTextContainer}>
              <Text style={styles.contactTextHindi}>ईमेल भेजें</Text>
              <Text style={styles.contactTextEnglish}>Email: support@boloo-cg.gov.in</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>
        </View>

        {/* FAQs */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            अक्सर पूछे जाने वाले सवाल / FAQs
          </Text>

          {FAQS.map((faq, index) => (
            <View key={index} style={styles.faqItem}>
              <TouchableOpacity
                style={styles.faqQuestion}
                onPress={() => toggleExpand(index)}
              >
                <View style={styles.faqQuestionText}>
                  <Text style={styles.faqQuestionHindi}>{faq.questionHindi}</Text>
                  <Text style={styles.faqQuestionEnglish}>{faq.questionEnglish}</Text>
                </View>
                <Ionicons
                  name={expandedIndex === index ? 'chevron-up' : 'chevron-down'}
                  size={24}
                  color={COLORS.gray[600]}
                />
              </TouchableOpacity>

              {expandedIndex === index && (
                <View style={styles.faqAnswer}>
                  <Text style={styles.faqAnswerHindi}>{faq.answerHindi}</Text>
                  <Text style={styles.faqAnswerEnglish}>{faq.answerEnglish}</Text>
                </View>
              )}
            </View>
          ))}
        </View>

        {/* Tips Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            सुझाव / Tips
          </Text>

          <View style={styles.tipItem}>
            <Ionicons name="bulb-outline" size={24} color={COLORS.primary} />
            <View style={styles.tipText}>
              <Text style={styles.tipTextHindi}>
                साफ और सही जानकारी दें
              </Text>
              <Text style={styles.tipTextEnglish}>
                Provide clear and accurate information
              </Text>
            </View>
          </View>

          <View style={styles.tipItem}>
            <Ionicons name="location-outline" size={24} color={COLORS.primary} />
            <View style={styles.tipText}>
              <Text style={styles.tipTextHindi}>
                अपनी लोकेशन बताएं
              </Text>
              <Text style={styles.tipTextEnglish}>
                Share your location for faster resolution
              </Text>
            </View>
          </View>

          <View style={styles.tipItem}>
            <Ionicons name="camera-outline" size={24} color={COLORS.primary} />
            <View style={styles.tipText}>
              <Text style={styles.tipTextHindi}>
                फोटो जोड़ें (अगर संभव हो)
              </Text>
              <Text style={styles.tipTextEnglish}>
                Add photos if possible
              </Text>
            </View>
          </View>
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
  header: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginTop: 16,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginTop: 4,
  },
  section: {
    padding: 16,
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 16,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  contactTextContainer: {
    flex: 1,
    marginLeft: 16,
  },
  contactTextHindi: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  contactTextEnglish: {
    fontSize: 13,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  faqItem: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
  },
  faqQuestion: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  faqQuestionText: {
    flex: 1,
  },
  faqQuestionHindi: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  faqQuestionEnglish: {
    fontSize: 13,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  faqAnswer: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[200],
  },
  faqAnswerHindi: {
    fontSize: 14,
    color: COLORS.gray[700],
    lineHeight: 20,
  },
  faqAnswerEnglish: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginTop: 4,
    lineHeight: 18,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.primary + '08',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  tipText: {
    flex: 1,
    marginLeft: 12,
  },
  tipTextHindi: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gray[900],
  },
  tipTextEnglish: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginTop: 2,
  },
});
