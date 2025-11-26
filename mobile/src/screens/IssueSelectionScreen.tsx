import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import api from '../services/api';
import { Taxonomy } from '../types';
import { COLORS } from '../constants/config';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';

type IssueSelectionScreenNavigationProp = StackNavigationProp<RootStackParamList, 'IssueSelection'>;

interface Props {
  navigation: IssueSelectionScreenNavigationProp;
}

export default function IssueSelectionScreen({ navigation }: Props) {
  const { user } = useAuth();
  const [issues, setIssues] = useState<Taxonomy[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchIssues();
  }, []);

  const fetchIssues = async () => {
    try {
      const response = await api.get<{ taxonomies: Taxonomy[] }>('/v1/taxonomies?type=issue');
      setIssues(response.data.taxonomies);
    } catch (error) {
      console.error('Failed to fetch issues:', error);

      // TESTING MODE: Use dummy issues if API fails
      console.log('[IssueSelection] TESTING MODE: Using dummy issues');
      setIssues([
        {
          id: 'test-water',
          type: 'issue',
          key: 'water',
          label_en: 'Water Supply',
          label_hi: 'जल आपूर्ति',
          taxonomy_metadata: {},
          is_active: true,
        },
        {
          id: 'test-road',
          type: 'issue',
          key: 'road',
          label_en: 'Road & Infrastructure',
          label_hi: 'सड़क और बुनियादी ढांचा',
          taxonomy_metadata: {},
          is_active: true,
        },
        {
          id: 'test-electricity',
          type: 'issue',
          key: 'electricity',
          label_en: 'Electricity',
          label_hi: 'बिजली',
          taxonomy_metadata: {},
          is_active: true,
        },
        {
          id: 'test-sanitation',
          type: 'issue',
          key: 'sanitation',
          label_en: 'Sanitation & Cleanliness',
          label_hi: 'स्वच्छता और सफाई',
          taxonomy_metadata: {},
          is_active: true,
        },
        {
          id: 'test-health',
          type: 'issue',
          key: 'health',
          label_en: 'Health Services',
          label_hi: 'स्वास्थ्य सेवाएं',
          taxonomy_metadata: {},
          is_active: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectIssue = (taxonomy: Taxonomy) => {
    console.log('[IssueSelection] Routing to Voice Record');
    navigation.navigate('VoiceRecord', { taxonomyId: taxonomy.id });
  };

  const renderIssue = ({ item }: { item: Taxonomy }) => (
    <TouchableOpacity
      style={styles.issueCard}
      onPress={() => handleSelectIssue(item)}
    >
      <Text style={styles.issueTitleHindi}>{item.label_hi}</Text>
      <Text style={styles.issueTitle}>{item.label_en}</Text>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Select Issue Type</Text>
        <Text style={styles.subtitle}>Choose the category for your grievance</Text>
      </View>
      <FlatList
        data={issues}
        renderItem={renderIssue}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.gray[600],
  },
  listContent: {
    padding: 16,
  },
  issueCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  issueTitleHindi: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 4,
  },
  issueTitle: {
    fontSize: 14,
    color: COLORS.gray[600],
  },
});
