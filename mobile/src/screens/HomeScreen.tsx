/**
 * HomeScreen - Chat-first UI
 *
 * New design:
 * - ChatInterface at the top for immediate reporting
 * - Recent Reports Feed below
 * - No category selection - go straight to chat
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Dimensions,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { COLORS } from '../constants/config';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types';
import { ChatInterface } from '../components/ChatInterface';
import { OfflineIndicator } from '../components/OfflineIndicator';
import { Ionicons } from '@expo/vector-icons';

type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Home'>;

interface Props {
  navigation: HomeScreenNavigationProp;
}

const SCREEN_HEIGHT = Dimensions.get('window').height;

export default function HomeScreen({ navigation }: Props) {
  const { user, logout } = useAuth();
  const [showChat, setShowChat] = useState(false);

  const handleChatSubmitComplete = (result: any) => {
    // Report submitted successfully
    setShowChat(false);

    // Optionally navigate to MyCases to see the submitted report
    if (result.case_id) {
      navigation.navigate('MyCases');
    }
  };

  if (showChat && user) {
    // Full-screen chat mode
    return (
      <SafeAreaView style={styles.chatContainer}>
        <View style={styles.chatHeader}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => setShowChat(false)}
          >
            <Ionicons name="arrow-back" size={24} color={COLORS.gray[900]} />
          </TouchableOpacity>
          <Text style={styles.chatHeaderTitle}>नई रिपोर्ट</Text>
          <View style={{ width: 24 }} />
        </View>
        <OfflineIndicator />
        <ChatInterface
          userId={user.id}
          onSubmitComplete={handleChatSubmitComplete}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Offline Indicator */}
      <OfflineIndicator />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Boloo</Text>
          <Text style={styles.subtitle}>नागरिक शिकायत प्रणाली</Text>
        </View>
        <TouchableOpacity
          style={styles.profileButton}
          onPress={() => navigation.navigate('MyCases')}
        >
          <Ionicons name="person-circle-outline" size={32} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {/* Quick Report Button (Chat) */}
      <View style={styles.quickReportSection}>
        <TouchableOpacity
          style={styles.chatButton}
          onPress={() => setShowChat(true)}
        >
          <View style={styles.chatButtonContent}>
            <Ionicons name="chatbubbles" size={32} color="#fff" />
            <View style={styles.chatButtonText}>
              <Text style={styles.chatButtonTitle}>समस्या रिपोर्ट करें</Text>
              <Text style={styles.chatButtonSubtitle}>
                अपनी बात बताएं - लिखकर या बोलकर
              </Text>
            </View>
          </View>
        </TouchableOpacity>

        <Text style={styles.helpText}>
          💡 आप अपनी समस्या के बारे में बातचीत की तरह बता सकते हैं
        </Text>
      </View>

      {/* Recent Reports Feed */}
      <View style={styles.feedSection}>
        <View style={styles.feedHeader}>
          <Text style={styles.feedTitle}>हाल की रिपोर्ट्स</Text>
          <TouchableOpacity onPress={() => navigation.navigate('MyCases')}>
            <Text style={styles.seeAllText}>सभी देखें →</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.emptyFeed}>
          <Ionicons name="document-text-outline" size={48} color={COLORS.gray[400]} />
          <Text style={styles.emptyFeedText}>अभी तक कोई रिपोर्ट नहीं है</Text>
          <Text style={styles.emptyFeedSubtext}>
            ऊपर बटन दबाकर अपनी पहली रिपोर्ट करें
          </Text>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.quickActionButton}
          onPress={() => navigation.navigate('MyCases')}
        >
          <Ionicons name="folder-open-outline" size={24} color={COLORS.primary} />
          <Text style={styles.quickActionText}>मेरी रिपोर्ट्स</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickActionButton}
          onPress={logout}
        >
          <Ionicons name="log-out-outline" size={24} color={COLORS.error} />
          <Text style={[styles.quickActionText, { color: COLORS.error }]}>
            लॉगआउट
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  chatContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    padding: 8,
  },
  chatHeaderTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 20,
    paddingTop: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  profileButton: {
    padding: 4,
  },
  quickReportSection: {
    padding: 20,
    paddingTop: 8,
  },
  chatButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 5,
  },
  chatButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chatButtonText: {
    flex: 1,
    marginLeft: 16,
  },
  chatButtonTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  chatButtonSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  helpText: {
    fontSize: 13,
    color: COLORS.gray[600],
    marginTop: 12,
    textAlign: 'center',
  },
  feedSection: {
    flex: 1,
    padding: 20,
    paddingTop: 8,
  },
  feedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  feedTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  seeAllText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '500',
  },
  emptyFeed: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyFeedText: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginTop: 12,
  },
  emptyFeedSubtext: {
    fontSize: 14,
    color: COLORS.gray[500],
    marginTop: 4,
    textAlign: 'center',
  },
  quickActions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 20,
    gap: 12,
  },
  quickActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gray[900],
    marginLeft: 8,
  },
});
