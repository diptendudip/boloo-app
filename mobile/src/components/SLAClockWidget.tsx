import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../constants/config';
import type { SLAInfo } from '../types/nextSteps';

interface SLAClockWidgetProps {
  sla: SLAInfo;
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
}

export default function SLAClockWidget({
  sla,
  size = 'medium',
  showDetails = true,
}: SLAClockWidgetProps) {
  const [remainingTime, setRemainingTime] = useState(sla.remaining_hours);

  useEffect(() => {
    // Update remaining time every minute
    const interval = setInterval(() => {
      setRemainingTime((prev) => Math.max(0, prev - 1 / 60));
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const getTimeColor = () => {
    if (sla.percentage_used >= 90) return COLORS.error;
    if (sla.percentage_used >= 70) return COLORS.warning;
    return COLORS.success;
  };

  const formatTimeRemaining = () => {
    const hours = Math.floor(remainingTime);
    const minutes = Math.floor((remainingTime - hours) * 60);

    if (hours >= 24) {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return `${days}d ${remainingHours}h`;
    }

    return `${hours}h ${minutes}m`;
  };

  const getClockSize = () => {
    switch (size) {
      case 'small':
        return 60;
      case 'large':
        return 120;
      default:
        return 80;
    }
  };

  const getFontSize = () => {
    switch (size) {
      case 'small':
        return 14;
      case 'large':
        return 24;
      default:
        return 18;
    }
  };

  const clockSize = getClockSize();
  const strokeWidth = size === 'small' ? 4 : size === 'large' ? 8 : 6;
  const radius = (clockSize - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - sla.percentage_used / 100);

  return (
    <View style={styles.container}>
      {/* Circular Progress */}
      <View style={[styles.clockContainer, { width: clockSize, height: clockSize }]}>
        <svg width={clockSize} height={clockSize} style={styles.svg}>
          {/* Background circle */}
          <circle
            cx={clockSize / 2}
            cy={clockSize / 2}
            r={radius}
            stroke={COLORS.gray[200]}
            strokeWidth={strokeWidth}
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx={clockSize / 2}
            cy={clockSize / 2}
            r={radius}
            stroke={getTimeColor()}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${clockSize / 2} ${clockSize / 2})`}
          />
        </svg>

        {/* Time Text Overlay */}
        <View style={styles.timeOverlay}>
          <Text
            style={[
              styles.timeText,
              { fontSize: getFontSize(), color: getTimeColor() },
            ]}
          >
            {formatTimeRemaining()}
          </Text>
          {size !== 'small' && (
            <Text style={styles.timeLabel}>बचा है</Text>
          )}
        </View>
      </View>

      {/* Details Section */}
      {showDetails && (
        <View style={styles.details}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>कुल समय:</Text>
            <Text style={styles.detailValue}>{sla.sla_hours}h</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>बीत चुका:</Text>
            <Text style={styles.detailValue}>{sla.elapsed_hours.toFixed(1)}h</Text>
          </View>
          {sla.is_escalated && (
            <View style={[styles.detailRow, styles.escalationBadge]}>
              <Text style={styles.escalationText}>
                🔼 स्तर {sla.escalation_level} पर भेजा गया
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  clockContainer: {
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  svg: {
    position: 'absolute',
  },
  timeOverlay: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeText: {
    fontWeight: 'bold',
    fontVariant: ['tabular-nums'],
  },
  timeLabel: {
    fontSize: 10,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  details: {
    marginTop: 12,
    width: '100%',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  detailLabel: {
    fontSize: 12,
    color: COLORS.gray[600],
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  escalationBadge: {
    marginTop: 8,
    backgroundColor: COLORS.warning + '20',
    padding: 8,
    borderRadius: 6,
    justifyContent: 'center',
  },
  escalationText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.warning,
    textAlign: 'center',
  },
});
