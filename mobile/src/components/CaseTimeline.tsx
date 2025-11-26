import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { COLORS } from '../constants/config';
import { useLanguage } from '../context/LanguageContext';
import type { CaseUpdate, CaseStatus } from '../types/nextSteps';

interface CaseTimelineProps {
  updates: CaseUpdate[];
  maxItems?: number;
  showSLA?: boolean;
  slaRemaining?: number; // hours remaining
}

interface TimelineItemProps {
  update: CaseUpdate;
  isLast: boolean;
  slaRemaining?: number;
}

// Event type icons
const EVENT_ICONS: Record<string, string> = {
  case_created: '📝',
  case_triaged: '📋',
  status_change: '🔄',
  comment: '💬',
  resolution: '✅',
  escalation: '⬆️',
  waiting_info: '⏳',
  default: '📌',
};

// Status colors
const STATUS_COLORS: Record<CaseStatus, string> = {
  OPEN: '#f59e0b', // yellow
  IN_PROGRESS: '#2563eb', // blue
  WAITING_INFO: '#f59e0b', // yellow
  RESOLVED: '#10b981', // green
  ESCALATED: '#ef4444', // red
  CLOSED: '#64748b', // gray
};

function TimelineItem({ update, isLast, slaRemaining }: TimelineItemProps) {
  const { language } = useLanguage();
  const [expanded, setExpanded] = useState(false);

  const getEventIcon = (): string => {
    if (update.message.includes('रिपोर्ट बनाई गई') || update.message.includes('created')) {
      return EVENT_ICONS.case_created;
    }
    if (update.message.includes('भेजा') || update.message.includes('Assigned')) {
      return EVENT_ICONS.case_triaged;
    }
    if (update.status_change) {
      if (update.status_change.to === 'RESOLVED') {
        return EVENT_ICONS.resolution;
      }
      if (update.status_change.to === 'ESCALATED') {
        return EVENT_ICONS.escalation;
      }
      if (update.status_change.to === 'WAITING_INFO') {
        return EVENT_ICONS.waiting_info;
      }
      return EVENT_ICONS.status_change;
    }
    if (update.actor.type === 'official') {
      return EVENT_ICONS.comment;
    }
    return EVENT_ICONS.default;
  };

  const getStatusColor = (): string => {
    if (update.status_change) {
      return STATUS_COLORS[update.status_change.to] || COLORS.gray[500];
    }
    return COLORS.primary;
  };

  const formatTimestamp = (timestamp: string): { hi: string; en: string } => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return { hi: 'अभी', en: 'Just now' };
    if (diffMins < 60)
      return { hi: `${diffMins} मिनट पहले`, en: `${diffMins} min ago` };
    if (diffHours < 24)
      return { hi: `${diffHours} घंटे पहले`, en: `${diffHours} hours ago` };
    if (diffDays < 7)
      return { hi: `${diffDays} दिन पहले`, en: `${diffDays} days ago` };

    const formatted = date.toLocaleDateString('hi-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
    return { hi: formatted, en: formatted };
  };

  const getStatusLabel = (status: CaseStatus): { hi: string; en: string } => {
    const labels: Record<CaseStatus, { hi: string; en: string }> = {
      OPEN: { hi: 'खुला', en: 'Open' },
      IN_PROGRESS: { hi: 'प्रगति में', en: 'In Progress' },
      WAITING_INFO: { hi: 'जानकारी की प्रतीक्षा', en: 'Waiting for Info' },
      RESOLVED: { hi: 'हल', en: 'Resolved' },
      ESCALATED: { hi: 'आगे भेजा गया', en: 'Escalated' },
      CLOSED: { hi: 'बंद', en: 'Closed' },
    };
    return labels[status] || { hi: status, en: status };
  };

  const getActorLabel = (type: string, name?: string): { hi: string; en: string } => {
    if (name) {
      return { hi: name, en: name };
    }
    const labels: Record<string, { hi: string; en: string }> = {
      citizen: { hi: 'नागरिक', en: 'Citizen' },
      official: { hi: 'अधिकारी', en: 'Official' },
      system: { hi: 'सिस्टम', en: 'System' },
    };
    return labels[type] || { hi: type, en: type };
  };

  const getEventTypeLabel = (): { hi: string; en: string } => {
    if (update.message.includes('रिपोर्ट बनाई गई') || update.message.includes('created')) {
      return { hi: 'रिपोर्ट बनाई गई', en: 'Report Created' };
    }
    if (update.message.includes('भेजा') || update.message.includes('Assigned')) {
      return { hi: 'अधिकारी को भेजा', en: 'Assigned to Officer' };
    }
    if (update.status_change) {
      const toStatus = getStatusLabel(update.status_change.to);
      return toStatus;
    }
    if (update.actor.type === 'official') {
      return { hi: 'अधिकारी की टिप्पणी', en: 'Officer Comment' };
    }
    return { hi: 'अपडेट', en: 'Update' };
  };

  const timeLabels = formatTimestamp(update.timestamp);
  const actorLabels = getActorLabel(update.actor.type, update.actor.name);
  const eventLabels = getEventTypeLabel();
  const statusColor = getStatusColor();

  return (
    <View style={[styles.timelineItem, isLast && styles.lastItem]}>
      {/* Timeline Dot with Status Color */}
      <View style={[styles.timelineDot, { borderColor: statusColor }]}>
        <Text style={styles.eventIcon}>{getEventIcon()}</Text>
      </View>

      {/* Timeline Line */}
      {!isLast && <View style={styles.timelineLine} />}

      {/* Content */}
      <TouchableOpacity
        style={styles.content}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Text style={styles.eventType}>
              {language === 'hi' ? eventLabels.hi : eventLabels.en}
            </Text>
            <Text style={styles.timestamp}>
              {language === 'hi' ? timeLabels.hi : timeLabels.en}
            </Text>
          </View>
          {expanded ? (
            <Text style={styles.expandIcon}>▼</Text>
          ) : (
            <Text style={styles.expandIcon}>▶</Text>
          )}
        </View>

        {/* Status Change Badge */}
        {update.status_change && (
          <View style={styles.statusChangeContainer}>
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: STATUS_COLORS[update.status_change.from] + '20' },
              ]}
            >
              <Text
                style={[
                  styles.statusText,
                  { color: STATUS_COLORS[update.status_change.from] },
                ]}
              >
                {language === 'hi'
                  ? getStatusLabel(update.status_change.from).hi
                  : getStatusLabel(update.status_change.from).en}
              </Text>
            </View>
            <Text style={styles.arrow}>→</Text>
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: STATUS_COLORS[update.status_change.to] + '20' },
              ]}
            >
              <Text
                style={[
                  styles.statusText,
                  { color: STATUS_COLORS[update.status_change.to] },
                ]}
              >
                {language === 'hi'
                  ? getStatusLabel(update.status_change.to).hi
                  : getStatusLabel(update.status_change.to).en}
              </Text>
            </View>
          </View>
        )}

        {/* Expanded Details */}
        {expanded && (
          <View style={styles.expandedContent}>
            {/* Message */}
            <Text style={styles.message}>{update.message}</Text>

            {/* Actor Information */}
            <View style={styles.actorInfo}>
              <Text style={styles.actorLabel}>
                {language === 'hi' ? 'द्वारा:' : 'By:'}
              </Text>
              <Text style={styles.actorName}>
                {language === 'hi' ? actorLabels.hi : actorLabels.en}
              </Text>
            </View>

            {/* SLA Warning (if applicable) */}
            {slaRemaining !== undefined && slaRemaining < 24 && (
              <View style={styles.slaWarning}>
                <Text style={styles.slaWarningIcon}>⏰</Text>
                <Text style={styles.slaWarningText}>
                  {language === 'hi'
                    ? `${Math.floor(slaRemaining)} घंटे शेष`
                    : `${Math.floor(slaRemaining)} hours remaining`}
                </Text>
              </View>
            )}

            {/* Full Timestamp */}
            <Text style={styles.fullTimestamp}>
              {new Date(update.timestamp).toLocaleString(
                language === 'hi' ? 'hi-IN' : 'en-IN',
                {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                }
              )}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    </View>
  );
}

export default function CaseTimeline({
  updates,
  maxItems = 10,
  showSLA = false,
  slaRemaining,
}: CaseTimelineProps) {
  const { language } = useLanguage();
  const displayUpdates = updates.slice(0, maxItems);

  if (displayUpdates.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>📭</Text>
        <Text style={styles.emptyText}>
          {language === 'hi' ? 'कोई अपडेट नहीं' : 'No updates yet'}
        </Text>
        <Text style={styles.emptySubtext}>
          {language === 'hi'
            ? 'जैसे ही आपकी शिकायत पर कार्रवाई होगी, अपडेट यहां दिखाई देंगे'
            : 'Updates will appear here as your case progresses'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* SLA Header (if enabled) */}
      {showSLA && slaRemaining !== undefined && (
        <View
          style={[
            styles.slaHeader,
            slaRemaining < 24 && styles.slaHeaderUrgent,
            slaRemaining < 6 && styles.slaHeaderCritical,
          ]}
        >
          <Text style={styles.slaHeaderIcon}>⏱️</Text>
          <View style={styles.slaHeaderContent}>
            <Text style={styles.slaHeaderLabel}>
              {language === 'hi' ? 'समय शेष' : 'Time Remaining'}
            </Text>
            <Text style={styles.slaHeaderValue}>
              {slaRemaining >= 24
                ? `${Math.floor(slaRemaining / 24)} ${language === 'hi' ? 'दिन' : 'days'}`
                : `${Math.floor(slaRemaining)} ${language === 'hi' ? 'घंटे' : 'hours'}`}
            </Text>
          </View>
        </View>
      )}

      {/* Timeline */}
      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        nestedScrollEnabled={true}
      >
        {displayUpdates.map((update, index) => (
          <TimelineItem
            key={update.id}
            update={update}
            isLast={index === displayUpdates.length - 1}
            slaRemaining={slaRemaining}
          />
        ))}

        {updates.length > maxItems && (
          <TouchableOpacity style={styles.moreButton}>
            <Text style={styles.moreText}>
              {language === 'hi'
                ? `और ${updates.length - maxItems} अपडेट देखें...`
                : `View ${updates.length - maxItems} more updates...`}
            </Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  emptyContainer: {
    flex: 1,
    padding: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 13,
    color: COLORS.gray[500],
    textAlign: 'center',
    lineHeight: 20,
  },
  slaHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '10',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  slaHeaderUrgent: {
    backgroundColor: '#f59e0b' + '10',
    borderLeftColor: '#f59e0b',
  },
  slaHeaderCritical: {
    backgroundColor: '#ef4444' + '10',
    borderLeftColor: '#ef4444',
  },
  slaHeaderIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  slaHeaderContent: {
    flex: 1,
  },
  slaHeaderLabel: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginBottom: 2,
  },
  slaHeaderValue: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.gray[900],
  },
  timelineItem: {
    flexDirection: 'row',
    paddingBottom: 24,
    position: 'relative',
  },
  lastItem: {
    paddingBottom: 8,
  },
  timelineDot: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.white,
    borderWidth: 3,
    borderColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  eventIcon: {
    fontSize: 20,
  },
  timelineLine: {
    position: 'absolute',
    left: 21,
    top: 44,
    bottom: 0,
    width: 2,
    backgroundColor: COLORS.gray[300],
    zIndex: 1,
  },
  content: {
    flex: 1,
    marginLeft: 16,
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerLeft: {
    flex: 1,
  },
  eventType: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.gray[900],
    marginBottom: 4,
  },
  timestamp: {
    fontSize: 12,
    color: COLORS.gray[500],
  },
  expandIcon: {
    fontSize: 12,
    color: COLORS.gray[400],
    marginLeft: 8,
  },
  statusChangeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[200],
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  arrow: {
    fontSize: 16,
    color: COLORS.gray[400],
    marginHorizontal: 8,
  },
  expandedContent: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[200],
  },
  message: {
    fontSize: 14,
    color: COLORS.gray[700],
    lineHeight: 22,
    marginBottom: 12,
  },
  actorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  actorLabel: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginRight: 6,
  },
  actorName: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.gray[700],
  },
  slaWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f59e0b' + '15',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    marginBottom: 8,
  },
  slaWarningIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  slaWarningText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#f59e0b',
  },
  fullTimestamp: {
    fontSize: 11,
    color: COLORS.gray[400],
    fontStyle: 'italic',
  },
  moreButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  moreText: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '600',
  },
});
