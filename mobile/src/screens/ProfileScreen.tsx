/**
 * ProfileScreen
 *
 * User profile and settings
 * Hindi-first with logout option
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  Alert,
  RefreshControl,
  ActivityIndicator,
  Modal,
  Pressable,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../context/AuthContext';
import { COLORS } from '../constants/config';
import api from '../services/api';
import { User } from '../types';

export default function ProfileScreen() {
  const navigation = useNavigation();
  const { user: cachedUser, logout } = useAuth();
  const [user, setUser] = useState<User | null>(cachedUser);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState<'hi' | 'en'>('hi');
  const [showNameModal, setShowNameModal] = useState(false);
  const [editingName, setEditingName] = useState('');
  const [savingName, setSavingName] = useState(false);

  // Fetch fresh user data when screen mounts and when screen is focused
  useEffect(() => {
    fetchUserProfile();

    // Add focus listener to refresh data when returning to this screen
    const unsubscribe = navigation.addListener('focus', () => {
      fetchUserProfile();
    });

    return unsubscribe;
  }, [navigation]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get('/v1/users/me');
      console.log('✅ Fetched fresh user data:', response.data);
      setUser(response.data);
    } catch (error: any) {
      console.log('⚠️ API call failed (expected in test mode):', error.message);
      console.log('📝 Using cached user data as fallback');
      // Fall back to cached user if API fails (expected in test/dummy mode)
      setUser(cachedUser);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchUserProfile();
    setRefreshing(false);
  };

  const handleLogout = () => {
    Alert.alert(
      'लॉगआउट करें?',
      'Logout?',
      [
        {
          text: 'रद्द करें / Cancel',
          style: 'cancel',
        },
        {
          text: 'हां / Yes',
          onPress: logout,
          style: 'destructive',
        },
      ]
    );
  };

  const handleChangePhone = () => {
    // Navigate to ChangePhoneScreen
    navigation.navigate('ChangePhone' as never);
  };

  const handleLanguageChange = async (language: 'hi' | 'en') => {
    try {
      await AsyncStorage.setItem('@boloo_language', language);
      setCurrentLanguage(language);
      setShowLanguageModal(false);

      Alert.alert(
        language === 'hi' ? 'भाषा बदल गई' : 'Language Changed',
        language === 'hi'
          ? 'आपकी भाषा हिंदी में बदल दी गई है। ऐप को पूरी तरह से लागू करने के लिए पुनः आरंभ करें।'
          : 'Your language has been changed to English. Restart the app to fully apply.',
        [{ text: language === 'hi' ? 'ठीक है' : 'OK' }]
      );
    } catch (error) {
      console.error('Failed to save language:', error);
    }
  };

  const handleEditName = () => {
    setEditingName(user?.name || '');
    setShowNameModal(true);
  };

  const handleSaveName = async () => {
    if (!editingName.trim()) {
      Alert.alert('त्रुटि / Error', 'कृपया नाम दर्ज करें / Please enter a name');
      return;
    }

    try {
      setSavingName(true);

      // Update name via API
      const response = await api.put('/v1/users/me', { name: editingName.trim() });
      console.log('✅ Name updated:', response.data);

      // Update local state
      setUser(prev => prev ? { ...prev, name: editingName.trim() } : null);

      // Update cached user in AsyncStorage
      const userJson = await AsyncStorage.getItem('@boloo_user');
      if (userJson) {
        const userData = JSON.parse(userJson);
        userData.name = editingName.trim();
        await AsyncStorage.setItem('@boloo_user', JSON.stringify(userData));
      }

      setShowNameModal(false);
      Alert.alert(
        'सफलता / Success',
        'आपका नाम अपडेट हो गया है / Your name has been updated'
      );
    } catch (error: any) {
      console.error('Failed to update name:', error);
      Alert.alert(
        'त्रुटि / Error',
        error.response?.data?.detail || 'नाम अपडेट करने में विफल / Failed to update name'
      );
    } finally {
      setSavingName(false);
    }
  };

  const formatPhone = (phone?: string) => {
    if (!phone) return 'N/A';
    // Format +919876543210 as +91 98765 43210
    return phone.replace(/(\+\d{2})(\d{5})(\d{5})/, '$1 $2 $3');
  };

  // Load saved language on mount
  useEffect(() => {
    const loadLanguage = async () => {
      try {
        const savedLang = await AsyncStorage.getItem('@boloo_language');
        if (savedLang === 'hi' || savedLang === 'en') {
          setCurrentLanguage(savedLang);
        }
      } catch (error) {
        console.error('Failed to load language:', error);
      }
    };
    loadLanguage();
  }, []);

  if (loading && !user) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.avatarContainer}>
            <Ionicons name="person" size={60} color={COLORS.white} />
          </View>

          <TouchableOpacity onPress={handleEditName} style={styles.nameEditContainer}>
            <Text style={styles.nameHindi}>
              {user?.name || 'उपयोगकर्ता'}
            </Text>
            <Text style={styles.nameEnglish}>
              {user?.name || 'User'}
            </Text>
            <View style={styles.editNameHint}>
              <Ionicons name="pencil" size={14} color={COLORS.primary} />
              <Text style={styles.editNameHintText}>नाम बदलने के लिए टैप करें</Text>
            </View>
          </TouchableOpacity>

          <Text style={styles.phone}>
            {formatPhone(user?.phone)}
          </Text>
        </View>

        {/* Profile Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            प्रोफाइल जानकारी / Profile Info
          </Text>

          <View style={styles.infoItem}>
            <Ionicons name="call-outline" size={24} color={COLORS.gray[600]} />
            <View style={styles.infoText}>
              <Text style={styles.infoLabelHindi}>फोन नंबर</Text>
              <Text style={styles.infoLabelEnglish}>Phone Number</Text>
              <Text style={styles.infoValue}>{formatPhone(user?.phone)}</Text>
            </View>
          </View>

          {user?.email && (
            <View style={styles.infoItem}>
              <Ionicons name="mail-outline" size={24} color={COLORS.gray[600]} />
              <View style={styles.infoText}>
                <Text style={styles.infoLabelHindi}>ईमेल</Text>
                <Text style={styles.infoLabelEnglish}>Email</Text>
                <Text style={styles.infoValue}>{user.email}</Text>
              </View>
            </View>
          )}

          <View style={styles.infoItem}>
            <Ionicons name="shield-checkmark-outline" size={24} color={COLORS.gray[600]} />
            <View style={styles.infoText}>
              <Text style={styles.infoLabelHindi}>भूमिका</Text>
              <Text style={styles.infoLabelEnglish}>Role</Text>
              <Text style={styles.infoValue}>{user?.role || 'citizen'}</Text>
            </View>
          </View>

          {/* Location/Address Section - Always show, tappable to update */}
          <TouchableOpacity
            style={styles.infoItem}
            onPress={() => navigation.navigate('UpdateAddress' as never)}
          >
            <Ionicons name="location-outline" size={24} color={COLORS.primary} />
            <View style={styles.infoText}>
              <Text style={styles.infoLabelHindi}>पता</Text>
              <Text style={styles.infoLabelEnglish}>Address</Text>
              {user?.location_formatted_address ? (
                <Text style={styles.infoValue}>{user.location_formatted_address}</Text>
              ) : user?.location_district || user?.location_village ? (
                <Text style={styles.infoValue}>
                  {[
                    user?.location_street,
                    user?.location_village,
                    user?.location_panchayat && `पंचायत ${user.location_panchayat}`,
                    user?.location_block && `ब्लॉक ${user.location_block}`,
                    user?.location_district && `जिला ${user.location_district}`,
                    user?.location_state
                  ].filter(Boolean).join(', ')}
                </Text>
              ) : (
                <Text style={[styles.infoValue, styles.infoValuePlaceholder]}>
                  पता जोड़ने के लिए टैप करें / Tap to add address
                </Text>
              )}
            </View>
            <Ionicons name="chevron-forward" size={20} color={COLORS.gray[400]} />
          </TouchableOpacity>
        </View>

        {/* Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            सेटिंग्स / Settings
          </Text>

          <TouchableOpacity style={styles.actionButton} onPress={handleChangePhone}>
            <Ionicons name="phone-portrait-outline" size={24} color={COLORS.primary} />
            <View style={styles.actionText}>
              <Text style={styles.actionTextHindi}>फोन नंबर बदलें</Text>
              <Text style={styles.actionTextEnglish}>Change Phone Number</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="notifications-outline" size={24} color={COLORS.primary} />
            <View style={styles.actionText}>
              <Text style={styles.actionTextHindi}>सूचनाएं</Text>
              <Text style={styles.actionTextEnglish}>Notifications</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton} onPress={() => setShowLanguageModal(true)}>
            <Ionicons name="language-outline" size={24} color={COLORS.primary} />
            <View style={styles.actionText}>
              <Text style={styles.actionTextHindi}>भाषा</Text>
              <Text style={styles.actionTextEnglish}>Language</Text>
            </View>
            <View style={styles.languageBadge}>
              <Text style={styles.languageBadgeText}>{currentLanguage === 'hi' ? 'हिंदी' : 'English'}</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            जानकारी / About
          </Text>

          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="information-circle-outline" size={24} color={COLORS.gray[600]} />
            <View style={styles.actionText}>
              <Text style={styles.actionTextHindi}>ऐप के बारे में</Text>
              <Text style={styles.actionTextEnglish}>About App</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="document-text-outline" size={24} color={COLORS.gray[600]} />
            <View style={styles.actionText}>
              <Text style={styles.actionTextHindi}>नियम और शर्तें</Text>
              <Text style={styles.actionTextEnglish}>Terms & Conditions</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="shield-outline" size={24} color={COLORS.gray[600]} />
            <View style={styles.actionText}>
              <Text style={styles.actionTextHindi}>गोपनीयता नीति</Text>
              <Text style={styles.actionTextEnglish}>Privacy Policy</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.gray[400]} />
          </TouchableOpacity>
        </View>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color={COLORS.error} />
          <Text style={styles.logoutTextHindi}>लॉगआउट</Text>
          <Text style={styles.logoutTextEnglish}>Logout</Text>
        </TouchableOpacity>

        {/* Version */}
        <Text style={styles.version}>संस्करण / Version 1.0.0</Text>
      </ScrollView>

      {/* Language Selection Modal */}
      <Modal
        visible={showLanguageModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowLanguageModal(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setShowLanguageModal(false)}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>भाषा चुनें / Select Language</Text>

            <TouchableOpacity
              style={[styles.languageOption, currentLanguage === 'hi' && styles.languageOptionSelected]}
              onPress={() => handleLanguageChange('hi')}
            >
              <Text style={styles.languageOptionTextHindi}>हिंदी</Text>
              <Text style={styles.languageOptionTextEnglish}>Hindi</Text>
              {currentLanguage === 'hi' && (
                <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.languageOption, currentLanguage === 'en' && styles.languageOptionSelected]}
              onPress={() => handleLanguageChange('en')}
            >
              <Text style={styles.languageOptionTextHindi}>अंग्रेज़ी</Text>
              <Text style={styles.languageOptionTextEnglish}>English</Text>
              {currentLanguage === 'en' && (
                <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowLanguageModal(false)}
            >
              <Text style={styles.modalCloseButtonText}>बंद करें / Close</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>

      {/* Name Edit Modal */}
      <Modal
        visible={showNameModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowNameModal(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setShowNameModal(false)}>
          <Pressable style={styles.modalContent} onPress={(e) => e.stopPropagation()}>
            <Text style={styles.modalTitle}>नाम बदलें / Edit Name</Text>

            <TextInput
              style={styles.nameInput}
              value={editingName}
              onChangeText={setEditingName}
              placeholder="अपना नाम दर्ज करें / Enter your name"
              placeholderTextColor={COLORS.gray[400]}
              autoFocus
              maxLength={50}
            />

            <View style={styles.modalButtonRow}>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonCancel]}
                onPress={() => setShowNameModal(false)}
                disabled={savingName}
              >
                <Text style={styles.modalButtonCancelText}>रद्द करें / Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonSave]}
                onPress={handleSaveName}
                disabled={savingName}
              >
                {savingName ? (
                  <ActivityIndicator size="small" color={COLORS.white} />
                ) : (
                  <Text style={styles.modalButtonSaveText}>सहेजें / Save</Text>
                )}
              </TouchableOpacity>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
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
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  nameHindi: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  nameEnglish: {
    fontSize: 16,
    color: COLORS.gray[600],
    marginTop: 4,
  },
  phone: {
    fontSize: 14,
    color: COLORS.gray[500],
    marginTop: 8,
  },
  section: {
    padding: 16,
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 12,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  infoText: {
    flex: 1,
    marginLeft: 16,
  },
  infoLabelHindi: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  infoLabelEnglish: {
    fontSize: 11,
    color: COLORS.gray[500],
  },
  infoValue: {
    fontSize: 13,
    color: COLORS.gray[700],
    marginTop: 4,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  actionText: {
    flex: 1,
    marginLeft: 16,
  },
  actionTextHindi: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.gray[900],
  },
  actionTextEnglish: {
    fontSize: 12,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  languageBadge: {
    backgroundColor: COLORS.primary + '15',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  languageBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.error + '10',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 24,
  },
  logoutTextHindi: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.error,
    marginLeft: 12,
  },
  logoutTextEnglish: {
    fontSize: 12,
    color: COLORS.error,
    marginLeft: 4,
  },
  version: {
    fontSize: 12,
    color: COLORS.gray[500],
    textAlign: 'center',
    marginBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: COLORS.gray[600],
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: 20,
    textAlign: 'center',
  },
  languageOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: COLORS.gray[50],
    marginBottom: 12,
  },
  languageOptionSelected: {
    backgroundColor: COLORS.primary + '15',
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  languageOptionTextHindi: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  languageOptionTextEnglish: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginRight: 12,
  },
  modalCloseButton: {
    marginTop: 8,
    padding: 12,
    alignItems: 'center',
  },
  modalCloseButtonText: {
    fontSize: 14,
    color: COLORS.gray[600],
  },
  nameEditContainer: {
    alignItems: 'center',
  },
  editNameHint: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: COLORS.primary + '15',
    borderRadius: 12,
    gap: 4,
  },
  editNameHintText: {
    fontSize: 11,
    color: COLORS.primary,
    fontWeight: '500',
  },
  infoValuePlaceholder: {
    color: COLORS.primary,
    fontStyle: 'italic',
  },
  nameInput: {
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: COLORS.gray[900],
    backgroundColor: COLORS.gray[50],
    marginBottom: 20,
  },
  modalButtonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalButtonCancel: {
    backgroundColor: COLORS.gray[100],
  },
  modalButtonCancelText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.gray[700],
  },
  modalButtonSave: {
    backgroundColor: COLORS.primary,
  },
  modalButtonSaveText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
});
