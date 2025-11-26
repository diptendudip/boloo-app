import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../constants/config';
import api from '../services/api';

interface Case {
  id: string;
  title: string;
  summary?: string;
  transcript_text?: string;
  status: string;
  created_at: string;
  location_text?: string;
  kind?: string;
  issue_type?: string;
}

interface CasesResponse {
  cases: Case[];
  total: number;
}

export default function MyCasesScreen() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      setError(null);

      // Get user ID from AsyncStorage - use correct storage keys
      let userId = await AsyncStorage.getItem('@boloo_user_id');

      // Fallback: Try reading from user object if user_id not found
      if (!userId) {
        const userJson = await AsyncStorage.getItem('@boloo_user');
        if (userJson) {
          try {
            const user = JSON.parse(userJson);
            userId = user.id;
            // Store user_id for future use
            if (userId) {
              await AsyncStorage.setItem('@boloo_user_id', userId);
            }
          } catch (parseError) {
            console.error('Error parsing user JSON:', parseError);
          }
        }
      }

      if (!userId) {
        setError('No user ID found. Please login again.');
        setLoading(false);
        return;
      }

      // Use Bearer token authentication (handled by api.ts interceptor)
      const response = await api.get<CasesResponse>('/v1/cases', {
        params: {
          limit: 50,
        },
      });

      setCases(response.data.cases || []);
    } catch (err: any) {
      console.error('Error fetching cases:', err);
      setError(err.response?.data?.detail || 'Failed to load cases');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchCases();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'submitted':
        return '#3B82F6'; // blue
      case 'in_progress':
        return '#F59E0B'; // amber
      case 'resolved':
        return '#10B981'; // green
      case 'closed':
        return '#6B7280'; // gray
      case 'draft':
        return '#8B5CF6'; // purple
      default:
        return '#6B7280';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInHours = diffInMs / (1000 * 60 * 60);

    if (diffInHours < 24) {
      const hours = Math.floor(diffInHours);
      return hours === 0 ? 'Just now' : `${hours}h ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
      });
    }
  };

  const renderCaseCard = ({ item }: { item: Case }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => {
        Alert.alert(
          item.title,
          `Status: ${item.status}\n\n${item.summary || item.transcript_text || 'No description'}`
        );
      }}
    >
      <View style={styles.cardHeader}>
        <View style={styles.cardTitleRow}>
          <Text style={styles.cardTitle} numberOfLines={2}>
            {item.title}
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}>
            <Text style={styles.statusText}>{item.status}</Text>
          </View>
        </View>
      </View>

      {(item.summary || item.transcript_text) && (
        <Text style={styles.cardDescription} numberOfLines={3}>
          {item.summary || item.transcript_text}
        </Text>
      )}

      <View style={styles.cardFooter}>
        {item.location_text && (
          <View style={styles.footerItem}>
            <Text style={styles.footerIcon}>📍</Text>
            <Text style={styles.footerText} numberOfLines={1}>
              {item.location_text}
            </Text>
          </View>
        )}
        {item.issue_type && (
          <View style={styles.footerItem}>
            <Text style={styles.footerIcon}>🏷️</Text>
            <Text style={styles.footerText} numberOfLines={1}>
              {item.issue_type}
            </Text>
          </View>
        )}
        <View style={styles.footerItem}>
          <Text style={styles.footerIcon}>🕐</Text>
          <Text style={styles.footerText}>{formatDate(item.created_at)}</Text>
        </View>
      </View>

      {item.kind && item.kind !== 'grievance' && (
        <View style={styles.kindBadge}>
          <Text style={styles.kindText}>
            {item.kind === 'personal' ? '🔒 Personal' : '📰 Community Story'}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Cases</Text>
        </View>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading your cases...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Cases</Text>
        </View>
        <View style={styles.centerContent}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchCases}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (cases.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Cases</Text>
        </View>
        <View style={styles.centerContent}>
          <Text style={styles.icon}>📋</Text>
          <Text style={styles.title}>No Cases Yet</Text>
          <Text style={styles.subtitle}>
            Your submitted grievances will appear here
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Cases</Text>
        <Text style={styles.headerSubtitle}>
          {cases.length} {cases.length === 1 ? 'case' : 'cases'}
        </Text>
      </View>

      <FlatList
        data={cases}
        renderItem={renderCaseCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.gray[900],
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.gray[600],
  },
  listContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  cardHeader: {
    marginBottom: 12,
  },
  cardTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
  },
  cardTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
    lineHeight: 24,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
    textTransform: 'capitalize',
  },
  cardDescription: {
    fontSize: 14,
    color: COLORS.gray[700],
    lineHeight: 20,
    marginBottom: 12,
  },
  cardFooter: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  footerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    maxWidth: '45%',
  },
  footerIcon: {
    fontSize: 14,
  },
  footerText: {
    fontSize: 13,
    color: COLORS.gray[600],
    flex: 1,
  },
  kindBadge: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[200],
  },
  kindText: {
    fontSize: 12,
    color: COLORS.gray[600],
    fontWeight: '500',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: COLORS.gray[600],
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#DC2626',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  icon: {
    fontSize: 80,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.gray[600],
    textAlign: 'center',
  },
});
