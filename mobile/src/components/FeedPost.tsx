/**
 * FeedPost Component
 *
 * Individual post card in the community feed
 * Displays case details with like, comment, and share interactions
 * Hindi-first UI with smooth animations
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  StyleSheet,
  Animated,
  Alert,
  Dimensions,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/config';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const IMAGE_HEIGHT = 200;

interface FeedPostProps {
  post: {
    id: string;
    user_id: string;
    title: string;
    summary: string;
    transcript_text?: string;
    audio_url?: string;
    media_urls?: string[] | null;
    location_text?: string;
    issue_type?: string | null;
    status: 'submitted' | 'pending' | 'in_progress' | 'resolved' | 'closed';
    priority: string;
    created_at: string;
    updated_at: string;
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
  };
  onLike: (postId: string, currentlyLiked: boolean) => void;
  onComment: (postId: string) => void;
  onShare: (postId: string, caseId: string) => void;
  onDelete: (postId: string) => void;
}

export default function FeedPost({
  post,
  onLike,
  onComment,
  onShare,
  onDelete,
}: FeedPostProps) {
  const [imageLoading, setImageLoading] = useState(true);
  const likeScale = useRef(new Animated.Value(1)).current;

  // Get status badge details
  const getStatusBadge = () => {
    switch (post.status) {
      case 'submitted':
        return {
          labelHi: 'प्रस्तुत',
          labelEn: 'Submitted',
          color: COLORS.primary,
          icon: 'checkmark-circle-outline',
        };
      case 'pending':
        return {
          labelHi: 'लंबित',
          labelEn: 'Pending',
          color: COLORS.warning,
          icon: 'time-outline',
        };
      case 'in_progress':
        return {
          labelHi: 'प्रगति में',
          labelEn: 'In Progress',
          color: COLORS.primary,
          icon: 'sync-outline',
        };
      case 'resolved':
        return {
          labelHi: 'हल हो गया',
          labelEn: 'Resolved',
          color: COLORS.success,
          icon: 'checkmark-circle-outline',
        };
      case 'closed':
        return {
          labelHi: 'बंद',
          labelEn: 'Closed',
          color: COLORS.gray[500],
          icon: 'close-circle-outline',
        };
      default:
        return {
          labelHi: 'अज्ञात',
          labelEn: 'Unknown',
          color: COLORS.gray[500],
          icon: 'help-circle-outline',
        };
    }
  };

  // Format timestamp in Hindi
  const formatTimestamp = (timestamp: string): { hi: string; en: string } => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) {
      return { hi: 'अभी', en: 'Just now' };
    } else if (diffMins < 60) {
      return { hi: `${diffMins} मिनट पहले`, en: `${diffMins}m ago` };
    } else if (diffHours < 24) {
      return { hi: `${diffHours} घंटे पहले`, en: `${diffHours}h ago` };
    } else if (diffDays < 7) {
      return { hi: `${diffDays} दिन पहले`, en: `${diffDays}d ago` };
    } else {
      const formatted = date.toLocaleDateString('hi-IN', {
        day: 'numeric',
        month: 'short',
      });
      return { hi: formatted, en: formatted };
    }
  };

  // Handle like with animation
  const handleLike = () => {
    // Animate button
    Animated.sequence([
      Animated.spring(likeScale, {
        toValue: 1.3,
        useNativeDriver: true,
        speed: 50,
      }),
      Animated.spring(likeScale, {
        toValue: 1,
        useNativeDriver: true,
        speed: 50,
      }),
    ]).start();

    onLike(post.id, post.engagement.has_liked);
  };

  // Handle long press for more options
  const handleLongPress = () => {
    // Only allow delete if user owns the post
    // For now, we'll disable delete since backend doesn't return can_delete
    // TODO: Add can_delete field to backend response
    return;
  };

  const statusBadge = getStatusBadge();
  const timestamp = formatTimestamp(post.created_at);
  const displayName = post.user.is_anonymous ? 'गुमनाम' : post.user.name || 'उपयोगकर्ता';
  const firstImage = post.media_urls && post.media_urls.length > 0 ? post.media_urls[0] : null;

  return (
    <TouchableOpacity
      activeOpacity={0.95}
      onLongPress={handleLongPress}
      style={styles.container}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.userInfo}>
          <View style={styles.avatar}>
            <Ionicons
              name={post.user.is_anonymous ? 'person-outline' : 'person'}
              size={20}
              color={COLORS.gray[600]}
            />
          </View>
          <View style={styles.userDetails}>
            <Text style={styles.userName}>{displayName}</Text>
            <View style={styles.metaRow}>
              <Text style={styles.timestamp}>{timestamp.hi}</Text>
              {post.location_text && (
                <>
                  <Text style={styles.metaDot}>•</Text>
                  <Ionicons name="location-outline" size={12} color={COLORS.gray[500]} />
                  <Text style={styles.location} numberOfLines={1}>
                    {post.location_text}
                  </Text>
                </>
              )}
            </View>
          </View>
        </View>

        {/* Status Badge */}
        <View style={[styles.statusBadge, { backgroundColor: `${statusBadge.color}15` }]}>
          <Ionicons name={statusBadge.icon as any} size={14} color={statusBadge.color} />
          <Text style={[styles.statusText, { color: statusBadge.color }]}>
            {statusBadge.labelHi}
          </Text>
        </View>
      </View>

      {/* Issue Type Tag (if available) */}
      {post.issue_type && (
        <View style={styles.categoryTag}>
          <Text style={styles.categoryTextHindi}>{post.issue_type}</Text>
        </View>
      )}

      {/* Content */}
      <View style={styles.content}>
        {post.title && <Text style={styles.title}>{post.title}</Text>}
        <Text style={styles.description} numberOfLines={3}>
          {post.summary}
        </Text>
      </View>

      {/* Image */}
      {firstImage && (
        <View style={styles.imageContainer}>
          <Image
            source={{ uri: firstImage }}
            style={styles.image}
            onLoadStart={() => setImageLoading(true)}
            onLoadEnd={() => setImageLoading(false)}
            resizeMode="cover"
          />
          {imageLoading && (
            <View style={styles.imageLoader}>
              <View style={styles.imagePlaceholder}>
                <Ionicons name="image-outline" size={40} color={COLORS.gray[400]} />
              </View>
            </View>
          )}
          {post.media_urls && post.media_urls.length > 1 && (
            <View style={styles.imageCountBadge}>
              <Ionicons name="images-outline" size={14} color={COLORS.white} />
              <Text style={styles.imageCountText}>{post.media_urls.length}</Text>
            </View>
          )}
        </View>
      )}

      {/* Audio Indicator */}
      {post.audio_url && (
        <View style={styles.audioIndicator}>
          <Ionicons name="mic-outline" size={16} color={COLORS.primary} />
          <Text style={styles.audioText}>ऑडियो रिकॉर्डिंग उपलब्ध</Text>
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        {/* Like Button */}
        <Animated.View style={{ transform: [{ scale: likeScale }] }}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={handleLike}
            activeOpacity={0.7}
          >
            <Ionicons
              name={post.engagement.has_liked ? 'heart' : 'heart-outline'}
              size={22}
              color={post.engagement.has_liked ? COLORS.error : COLORS.gray[600]}
            />
            <Text
              style={[
                styles.actionText,
                post.engagement.has_liked && { color: COLORS.error, fontWeight: '600' },
              ]}
            >
              {post.engagement.likes_count > 0 ? post.engagement.likes_count : 'पसंद'}
            </Text>
          </TouchableOpacity>
        </Animated.View>

        {/* Comment Button */}
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => onComment(post.id)}
          activeOpacity={0.7}
        >
          <Ionicons name="chatbubble-outline" size={20} color={COLORS.gray[600]} />
          <Text style={styles.actionText}>
            {post.engagement.comments_count > 0 ? post.engagement.comments_count : 'टिप्पणी'}
          </Text>
        </TouchableOpacity>

        {/* Share Button */}
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => onShare(post.id, post.id)}
          activeOpacity={0.7}
        >
          <Ionicons name="share-social-outline" size={20} color={COLORS.gray[600]} />
          <Text style={styles.actionText}>साझा करें</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
    marginBottom: 8,
    borderBottomWidth: 8,
    borderBottomColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.gray[200],
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 2,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timestamp: {
    fontSize: 12,
    color: COLORS.gray[500],
  },
  metaDot: {
    fontSize: 12,
    color: COLORS.gray[400],
    marginHorizontal: 6,
  },
  location: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginLeft: 2,
    flex: 1,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  categoryTag: {
    backgroundColor: COLORS.gray[100],
    paddingHorizontal: 16,
    paddingVertical: 6,
    marginHorizontal: 16,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  categoryTextHindi: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.gray[800],
  },
  categoryTextEnglish: {
    fontSize: 11,
    color: COLORS.gray[600],
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 6,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.gray[700],
  },
  imageContainer: {
    marginTop: 12,
    position: 'relative',
  },
  image: {
    width: SCREEN_WIDTH,
    height: IMAGE_HEIGHT,
    backgroundColor: COLORS.gray[100],
  },
  imageLoader: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: COLORS.gray[100],
  },
  imagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageCountBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  imageCountText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.white,
  },
  audioIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: `${COLORS.primary}10`,
    gap: 8,
  },
  audioText: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '500',
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[100],
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 24,
    minWidth: 48,
    minHeight: 48,
    justifyContent: 'center',
    gap: 6,
  },
  actionText: {
    fontSize: 14,
    color: COLORS.gray[600],
    fontWeight: '500',
  },
});
