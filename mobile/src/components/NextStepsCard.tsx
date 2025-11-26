import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { COLORS } from '../constants/config';
import SLAClockWidget from './SLAClockWidget';
import type { NextStepsInfo, ResponsibleEntity } from '../types/nextSteps';

interface NextStepsCardProps {
  nextSteps: NextStepsInfo;
  onViewDetails?: () => void;
  compact?: boolean;
}

export default function NextStepsCard({
  nextSteps,
  onViewDetails,
  compact = false,
}: NextStepsCardProps) {
  const getEntityIcon = (type: ResponsibleEntity['type']): string => {
    const icons = {
      GRAM_PANCHAYAT: '🏘️',
      BDO: '🏛️',
      DISTRICT_OFFICE: '🏢',
      STATE_OFFICE: '🏛️',
    };
    return icons[type] || '📋';
  };

  const getStatusBadgeStyle = () => {
    switch (nextSteps.status) {
      case 'RESOLVED':
        return styles.statusResolved;
      case 'IN_PROGRESS':
        return styles.statusInProgress;
      case 'ESCALATED':
        return styles.statusEscalated;
      case 'WAITING_INFO':
        return styles.statusWaiting;
      default:
        return styles.statusOpen;
    }
  };

  const getStatusText = () => {
    const statusLabels = {
      OPEN: 'खुला है',
      IN_PROGRESS: 'प्रगति में',
      WAITING_INFO: 'जानकारी की प्रतीक्षा',
      RESOLVED: 'हल हो गया',
      ESCALATED: 'आगे भेजा गया',
      CLOSED: 'बंद',
    };
    return statusLabels[nextSteps.status] || nextSteps.status;
  };

  if (compact) {
    return (
      <TouchableOpacity
        style={styles.compactCard}
        onPress={onViewDetails}
        activeOpacity={0.7}
      >
        <View style={styles.compactHeader}>
          <Text style={styles.caseRef}>{nextSteps.case_reference}</Text>
          <View style={[styles.statusBadge, getStatusBadgeStyle()]}>
            <Text style={styles.statusText}>{getStatusText()}</Text>
          </View>
        </View>

        <View style={styles.compactBody}>
          <View style={styles.entityInfo}>
            <Text style={styles.entityIcon}>
              {getEntityIcon(nextSteps.responsible_entity.type)}
            </Text>
            <Text style={styles.entityName} numberOfLines={1}>
              {nextSteps.responsible_entity.name}
            </Text>
          </View>

          <SLAClockWidget sla={nextSteps.sla} size="small" showDetails={false} />
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>अगला क्या होगा?</Text>
          <Text style={styles.subtitle}>What happens next?</Text>
        </View>
        <View style={[styles.statusBadge, getStatusBadgeStyle()]}>
          <Text style={styles.statusText}>{getStatusText()}</Text>
        </View>
      </View>

      {/* Reference Number */}
      <View style={styles.referenceContainer}>
        <Text style={styles.referenceLabel}>शिकायत नंबर:</Text>
        <Text style={styles.referenceNumber}>{nextSteps.case_reference}</Text>
      </View>

      {/* SLA Clock */}
      <View style={styles.slaSection}>
        <SLAClockWidget sla={nextSteps.sla} size="medium" showDetails={true} />
      </View>

      {/* Responsible Entity */}
      <View style={styles.entitySection}>
        <Text style={styles.sectionTitle}>जिम्मेदार कार्यालय</Text>
        <View style={styles.entityCard}>
          <Text style={styles.entityIconLarge}>
            {getEntityIcon(nextSteps.responsible_entity.type)}
          </Text>
          <View style={styles.entityDetails}>
            <Text style={styles.entityNameLarge}>
              {nextSteps.responsible_entity.name}
            </Text>
            {nextSteps.responsible_entity.jurisdiction && (
              <Text style={styles.entityJurisdiction}>
                {nextSteps.responsible_entity.jurisdiction}
              </Text>
            )}
            {nextSteps.responsible_entity.contact_phone && (
              <Text style={styles.entityContact}>
                📞 {nextSteps.responsible_entity.contact_phone}
              </Text>
            )}
          </View>
        </View>
      </View>

      {/* Expected Actions */}
      {nextSteps.expected_actions.length > 0 && (
        <View style={styles.actionsSection}>
          <Text style={styles.sectionTitle}>क्या होगा</Text>
          {nextSteps.expected_actions.map((action, index) => (
            <View key={index} style={styles.actionItem}>
              <Text style={styles.actionBullet}>•</Text>
              <Text style={styles.actionText}>{action}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Citizen Actions */}
      {nextSteps.citizen_actions && nextSteps.citizen_actions.length > 0 && (
        <View style={styles.actionsSection}>
          <Text style={styles.sectionTitle}>आपको क्या करना है</Text>
          {nextSteps.citizen_actions.map((action, index) => (
            <View key={index} style={styles.actionItem}>
              <Text style={styles.actionBullet}>✓</Text>
              <Text style={styles.actionText}>{action}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Escalation Info */}
      {nextSteps.escalation_path.next && (
        <View style={styles.escalationSection}>
          <Text style={styles.escalationTitle}>अगर समाधान न हो...</Text>
          <View style={styles.escalationFlow}>
            <View style={styles.escalationItem}>
              <Text style={styles.escalationIcon}>
                {getEntityIcon(nextSteps.escalation_path.current.type)}
              </Text>
              <Text style={styles.escalationName}>
                {nextSteps.escalation_path.current.name}
              </Text>
            </View>
            <Text style={styles.escalationArrow}>→</Text>
            <View style={styles.escalationItem}>
              <Text style={styles.escalationIcon}>
                {getEntityIcon(nextSteps.escalation_path.next.type)}
              </Text>
              <Text style={styles.escalationName}>
                {nextSteps.escalation_path.next.name}
              </Text>
            </View>
          </View>
          {nextSteps.escalation_path.escalates_at && (
            <Text style={styles.escalationTime}>
              स्वतः आगे भेजा जाएगा:{' '}
              {new Date(nextSteps.escalation_path.escalates_at).toLocaleDateString(
                'hi-IN'
              )}
            </Text>
          )}
        </View>
      )}

      {/* Recent Updates */}
      {nextSteps.updates.length > 0 && (
        <View style={styles.updatesSection}>
          <Text style={styles.sectionTitle}>अपडेट</Text>
          <ScrollView
            style={styles.updatesList}
            nestedScrollEnabled={true}
            showsVerticalScrollIndicator={false}
          >
            {nextSteps.updates.slice(0, 3).map((update) => (
              <View key={update.id} style={styles.updateItem}>
                <Text style={styles.updateTime}>
                  {new Date(update.timestamp).toLocaleString('hi-IN', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
                <Text style={styles.updateMessage}>{update.message}</Text>
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* View Details Button */}
      {onViewDetails && (
        <TouchableOpacity style={styles.detailsButton} onPress={onViewDetails}>
          <Text style={styles.detailsButtonText}>पूरा विवरण देखें</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 20,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  compactCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  compactHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  subtitle: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusOpen: {
    backgroundColor: COLORS.primary + '20',
  },
  statusInProgress: {
    backgroundColor: COLORS.info + '20',
  },
  statusWaiting: {
    backgroundColor: COLORS.warning + '20',
  },
  statusResolved: {
    backgroundColor: COLORS.success + '20',
  },
  statusEscalated: {
    backgroundColor: COLORS.error + '20',
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  referenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    padding: 12,
    backgroundColor: COLORS.gray[50],
    borderRadius: 8,
  },
  referenceLabel: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginRight: 8,
  },
  referenceNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
    fontVariant: ['tabular-nums'],
  },
  caseRef: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
  },
  slaSection: {
    alignItems: 'center',
    paddingVertical: 20,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: COLORS.gray[200],
  },
  entitySection: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginBottom: 12,
  },
  entityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.primary + '10',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.primary + '30',
  },
  entityIconLarge: {
    fontSize: 36,
    marginRight: 12,
  },
  entityDetails: {
    flex: 1,
  },
  entityNameLarge: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 4,
  },
  entityJurisdiction: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginBottom: 4,
  },
  entityContact: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '500',
  },
  compactBody: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  entityInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  entityIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  entityName: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.gray[800],
    flex: 1,
  },
  actionsSection: {
    marginTop: 16,
  },
  actionItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  actionBullet: {
    fontSize: 16,
    marginRight: 8,
    color: COLORS.primary,
  },
  actionText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.gray[700],
    lineHeight: 20,
  },
  escalationSection: {
    marginTop: 16,
    padding: 16,
    backgroundColor: COLORS.warning + '10',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.warning + '30',
  },
  escalationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.gray[800],
    marginBottom: 12,
  },
  escalationFlow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  escalationItem: {
    flex: 1,
    alignItems: 'center',
  },
  escalationIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  escalationName: {
    fontSize: 11,
    color: COLORS.gray[700],
    textAlign: 'center',
  },
  escalationArrow: {
    fontSize: 24,
    color: COLORS.warning,
    marginHorizontal: 8,
  },
  escalationTime: {
    fontSize: 11,
    color: COLORS.gray[600],
    marginTop: 8,
    textAlign: 'center',
  },
  updatesSection: {
    marginTop: 16,
  },
  updatesList: {
    maxHeight: 120,
  },
  updateItem: {
    paddingVertical: 8,
    borderLeftWidth: 2,
    borderLeftColor: COLORS.primary,
    paddingLeft: 12,
    marginBottom: 8,
  },
  updateTime: {
    fontSize: 11,
    color: COLORS.gray[500],
    marginBottom: 2,
  },
  updateMessage: {
    fontSize: 13,
    color: COLORS.gray[800],
  },
  detailsButton: {
    marginTop: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    alignItems: 'center',
  },
  detailsButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
});
