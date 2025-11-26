/**
 * PreviewCard Component - Shows submission preview
 *
 * Displays extracted data before final submission to build trust
 * Part of Option B UX redesign
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

interface PreviewCardProps {
  location?: string;
  issue?: string;
  reporter?: string;
  phone?: string;
  actions?: string;
  onEdit?: () => void;
}

export const PreviewCard: React.FC<PreviewCardProps> = ({
  location,
  issue,
  reporter,
  phone,
  actions,
  onEdit
}) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>रिपोर्ट सारांश</Text>
        {onEdit && (
          <TouchableOpacity onPress={onEdit} style={styles.editButton}>
            <Text style={styles.editText}>संपादित करें</Text>
          </TouchableOpacity>
        )}
      </View>

      {location && (
        <View style={styles.row}>
          <Text style={styles.icon}>📍</Text>
          <View style={styles.textContainer}>
            <Text style={styles.label}>स्थान</Text>
            <Text style={styles.value}>{location}</Text>
          </View>
        </View>
      )}

      {issue && (
        <View style={styles.row}>
          <Text style={styles.icon}>⚡</Text>
          <View style={styles.textContainer}>
            <Text style={styles.label}>समस्या</Text>
            <Text style={styles.value} numberOfLines={3}>
              {issue}
            </Text>
          </View>
        </View>
      )}

      {reporter && (
        <View style={styles.row}>
          <Text style={styles.icon}>👤</Text>
          <View style={styles.textContainer}>
            <Text style={styles.label}>नाम</Text>
            <Text style={styles.value}>{reporter}</Text>
          </View>
        </View>
      )}

      {phone && (
        <View style={styles.row}>
          <Text style={styles.icon}>📞</Text>
          <View style={styles.textContainer}>
            <Text style={styles.label}>फोन</Text>
            <Text style={styles.value}>{phone}</Text>
          </View>
        </View>
      )}

      {actions && (
        <View style={styles.row}>
          <Text style={styles.icon}>🔧</Text>
          <View style={styles.textContainer}>
            <Text style={styles.label}>की गई कोशिश</Text>
            <Text style={styles.value} numberOfLines={2}>
              {actions}
            </Text>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  editButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#E3F2FD',
  },
  editText: {
    color: '#1976D2',
    fontSize: 14,
    fontWeight: '600',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  icon: {
    fontSize: 24,
    marginRight: 12,
    marginTop: 2,
  },
  textContainer: {
    flex: 1,
  },
  label: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
    fontWeight: '600',
  },
  value: {
    fontSize: 15,
    color: '#333',
    lineHeight: 20,
  },
});
