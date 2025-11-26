/**
 * FeedScreen Component
 *
 * Social feed displaying community cases with infinite scroll and interactions
 * Hindi-first UI with proper error handling and loading states
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  RefreshControl,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/config';
import ErrorDisplay from '../components/ErrorDisplay';
import FeedPost from '../components/FeedPost';
import { API_BASE_URL } from '../constants/config';
import { authenticatedFetch } from '../utils/apiAuth';

interface FeedItem {
  id: string;
  user_id: string;
  title: string;
  summary: string;
  transcript_text?: string;
  audio_url?: string;
  media_urls?: string[] | null;
  location_text?: string;
  issue_type?: string | null;
  entity_id?: string | null;
  status: 'submitted' | 'pending' | 'in_progress' | 'resolved' | 'closed';
  priority: string;
  sla_due_at?: string | null;
  is_public: boolean;
  metadata?: any;
  created_at: string;
  updated_at: string;
  location_lat?: number | null;
  location_lng?: number | null;
  user: {
    id: string;
    name: string;
    is_anonymous: boolean;
  };
  engagement: {
    likes_count: number;
    comments_count: number;
    shares_count: number;
    has_liked: boolean;
  };
  caption?: string | null;
}

interface FeedData {
  posts: FeedItem[];
  total: number;
  skip: number;
  limit: number;
}

interface FeedResponse {
  success: boolean;
  data: FeedData;
  message?: string;
}

export default function FeedScreen({ navigation }: any) {
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Fetch feed data
  const fetchFeed = useCallback(async (pageNum: number, isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else if (pageNum === 1) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      setError(null);

      // Use authenticated fetch with automatic token/dev_user_id handling
      const response = await authenticatedFetch(
        `${API_BASE_URL}/v1/feed?page=${pageNum}&page_size=10`,
        {
          method: 'GET',
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result: FeedResponse = await response.json();
      const feedData = result.data;

      if (isRefresh || pageNum === 1) {
        setFeedItems(feedData.posts || []);
      } else {
        setFeedItems((prev) => [...prev, ...(feedData.posts || [])]);
      }

      // Calculate has_more: we have more if we got a full page of results
      setHasMore((feedData.posts || []).length >= (feedData.limit || 10));
      setPage(pageNum);
    } catch (err: any) {
      console.error('Feed fetch error:', err);
      if (err.message.includes('HTTP')) {
        const statusCode = parseInt(err.message.replace('HTTP ', ''));
        setError(statusCode.toString());
      } else {
        setError('NETWORK_ERROR');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchFeed(1);
  }, []);

  // Pull to refresh
  const handleRefresh = useCallback(() => {
    fetchFeed(1, true);
  }, [fetchFeed]);

  // Load more on scroll
  const handleLoadMore = useCallback(() => {
    if (!loadingMore && hasMore && !loading) {
      fetchFeed(page + 1);
    }
  }, [loadingMore, hasMore, loading, page, fetchFeed]);

  // Like a post
  const handleLike = useCallback(async (postId: string, currentlyLiked: boolean) => {
    // Optimistic update
    setFeedItems((prev) =>
      prev.map((item) =>
        item.id === postId
          ? {
              ...item,
              engagement: {
                ...item.engagement,
                has_liked: !currentlyLiked,
                likes_count: currentlyLiked
                  ? item.engagement.likes_count - 1
                  : item.engagement.likes_count + 1,
              },
            }
          : item
      )
    );

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/v1/feed/posts/${postId}/like`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        // Revert optimistic update on error
        setFeedItems((prev) =>
          prev.map((item) =>
            item.id === postId
              ? {
                  ...item,
                  engagement: {
                    ...item.engagement,
                    has_liked: currentlyLiked,
                    likes_count: currentlyLiked
                      ? item.engagement.likes_count + 1
                      : item.engagement.likes_count - 1,
                  },
                }
              : item
          )
        );
        throw new Error('Failed to like post');
      }

      const data = await response.json();
      // Update with actual server data
      setFeedItems((prev) =>
        prev.map((item) =>
          item.id === postId
            ? {
                ...item,
                engagement: {
                  ...item.engagement,
                  has_liked: data.is_liked || data.has_liked,
                  likes_count: data.likes_count,
                },
              }
            : item
        )
      );
    } catch (err) {
      console.error('Like error:', err);
      // Error already reverted in optimistic update
    }
  }, []);

  // Navigate to comments
  const handleComment = useCallback(
    (postId: string) => {
      // TODO: Navigate to comments screen when created
      console.log('Navigate to comments:', postId);
      // navigation.navigate('Comments', { postId });
    },
    [navigation]
  );

  // Share post
  const handleShare = useCallback(async (postId: string, caseId: string) => {
    // TODO: Implement share functionality
    console.log('Share post:', postId, caseId);
    // Share case link via native share dialog
  }, []);

  // Delete post (if user owns it)
  const handleDelete = useCallback(async (postId: string) => {
    // TODO: Implement delete with confirmation dialog
    console.log('Delete post:', postId);
  }, []);

  // Retry on error
  const handleRetry = useCallback(() => {
    fetchFeed(1);
  }, [fetchFeed]);

  // Render empty state
  const renderEmpty = () => {
    if (loading) {
      return null;
    }

    return (
      <View style={styles.emptyContainer}>
        <View style={styles.emptyIconContainer}>
          <Ionicons name="chatbubbles-outline" size={80} color={COLORS.gray[300]} />
        </View>
        <Text style={styles.emptyTitleHindi}>कोई पोस्ट नहीं मिली</Text>
        <Text style={styles.emptyTitleEnglish}>No Posts Found</Text>
        <Text style={styles.emptyMessageHindi}>
          समुदाय में अभी तक कोई मामला साझा नहीं किया गया है
        </Text>
        <Text style={styles.emptyMessageEnglish}>
          No cases have been shared in the community yet
        </Text>
        <TouchableOpacity
          style={styles.emptyButton}
          onPress={() => navigation.navigate('NewCase')}
        >
          <Ionicons name="add-circle-outline" size={20} color={COLORS.white} />
          <Text style={styles.emptyButtonText}>पहला मामला दर्ज करें</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Render footer (loading more indicator)
  const renderFooter = () => {
    if (!loadingMore) {
      return null;
    }

    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color={COLORS.primary} />
        <Text style={styles.footerText}>और लोड हो रहा है...</Text>
      </View>
    );
  };

  // Render header
  const renderHeader = () => {
    return (
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitleHindi}>समुदाय फ़ीड</Text>
          <Text style={styles.headerTitleEnglish}>Community Feed</Text>
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => {
            // TODO: Implement filter modal
            console.log('Open filters');
          }}
        >
          <Ionicons name="filter-outline" size={24} color={COLORS.gray[700]} />
        </TouchableOpacity>
      </View>
    );
  };

  // Main render
  if (loading && feedItems.length === 0) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        {renderHeader()}
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>फ़ीड लोड हो रही है...</Text>
          <Text style={styles.loadingTextEnglish}>Loading feed...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error && feedItems.length === 0) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        {renderHeader()}
        <View style={styles.errorContainer}>
          <ErrorDisplay error={error} onAction={handleRetry} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {renderHeader()}
      <FlatList
        data={feedItems}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <FeedPost
            post={item}
            onLike={handleLike}
            onComment={handleComment}
            onShare={handleShare}
            onDelete={handleDelete}
          />
        )}
        ListEmptyComponent={renderEmpty}
        ListFooterComponent={renderFooter}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
            title="ताज़ा करें"
            titleColor={COLORS.gray[600]}
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        contentContainerStyle={
          feedItems.length === 0 ? styles.flatListEmpty : undefined
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
    backgroundColor: COLORS.white,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  headerContent: {
    flex: 1,
  },
  headerTitleHindi: {
    fontSize: 22,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  headerTitleEnglish: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginTop: 2,
  },
  filterButton: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginTop: 16,
  },
  loadingTextEnglish: {
    fontSize: 14,
    color: COLORS.gray[500],
    marginTop: 4,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 60,
  },
  emptyIconContainer: {
    marginBottom: 24,
  },
  emptyTitleHindi: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.gray[800],
    textAlign: 'center',
    marginBottom: 4,
  },
  emptyTitleEnglish: {
    fontSize: 16,
    color: COLORS.gray[500],
    textAlign: 'center',
    marginBottom: 16,
  },
  emptyMessageHindi: {
    fontSize: 15,
    color: COLORS.gray[600],
    textAlign: 'center',
    marginBottom: 4,
  },
  emptyMessageEnglish: {
    fontSize: 13,
    color: COLORS.gray[500],
    textAlign: 'center',
    marginBottom: 32,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    gap: 8,
  },
  emptyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  footerLoader: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginTop: 8,
  },
  flatListEmpty: {
    flexGrow: 1,
  },
});
