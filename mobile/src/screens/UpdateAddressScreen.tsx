/**
 * UpdateAddressScreen - Cascading Dropdown Selection
 *
 * User flow: State → District → Block → Panchayat → Village (text) → Street (text)
 * All dropdowns populated from backend /api/dropdown/* endpoints
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../constants/config';
import api from '../services/api';
import CustomDropdown from '../components/CustomDropdown';

// Types for dropdown data
interface DropdownOption {
  id: number;
  name: string;
  name_en: string;
  state_code?: string;
  lgd_code?: string;
  district_lgd_code?: string;
  block_lgd_code?: string;
}

export default function UpdateAddressScreen() {
  const navigation = useNavigation();

  const [loading, setLoading] = useState(false);
  const [loadingStates, setLoadingStates] = useState(true);

  // Dropdown data arrays
  const [states, setStates] = useState<DropdownOption[]>([]);
  const [districts, setDistricts] = useState<DropdownOption[]>([]);
  const [blocks, setBlocks] = useState<DropdownOption[]>([]);
  const [panchayats, setPanchayats] = useState<DropdownOption[]>([]);

  // Selected values (store LGD codes for API filtering)
  const [selectedStateCode, setSelectedStateCode] = useState<string>('');
  const [selectedDistrictLgd, setSelectedDistrictLgd] = useState<string>('');
  const [selectedBlockLgd, setSelectedBlockLgd] = useState<string>('');
  const [selectedPanchayatLgd, setSelectedPanchayatLgd] = useState<string>('');

  // Display names for saving
  const [selectedStateName, setSelectedStateName] = useState<string>('');
  const [selectedDistrictName, setSelectedDistrictName] = useState<string>('');
  const [selectedBlockName, setSelectedBlockName] = useState<string>('');
  const [selectedPanchayatName, setSelectedPanchayatName] = useState<string>('');

  // Text inputs (village and street only)
  const [village, setVillage] = useState('');
  const [street, setStreet] = useState('');

  // Fetch all states on component mount
  useEffect(() => {
    fetchStates();
  }, []);

  // Fetch districts when state changes
  useEffect(() => {
    if (selectedStateCode) {
      fetchDistricts(selectedStateCode);
      // Reset dependent fields
      setDistricts([]);
      setBlocks([]);
      setPanchayats([]);
      setSelectedDistrictLgd('');
      setSelectedBlockLgd('');
      setSelectedPanchayatLgd('');
      setSelectedDistrictName('');
      setSelectedBlockName('');
      setSelectedPanchayatName('');
    } else {
      setDistricts([]);
      setBlocks([]);
      setPanchayats([]);
    }
  }, [selectedStateCode]);

  // Fetch blocks when district changes
  useEffect(() => {
    if (selectedDistrictLgd) {
      fetchBlocks(selectedDistrictLgd);
      // Reset dependent fields
      setBlocks([]);
      setPanchayats([]);
      setSelectedBlockLgd('');
      setSelectedPanchayatLgd('');
      setSelectedBlockName('');
      setSelectedPanchayatName('');
    } else {
      setBlocks([]);
      setPanchayats([]);
    }
  }, [selectedDistrictLgd]);

  // Fetch panchayats when block changes
  useEffect(() => {
    if (selectedBlockLgd) {
      fetchPanchayats(selectedBlockLgd);
      // Reset dependent fields
      setPanchayats([]);
      setSelectedPanchayatLgd('');
      setSelectedPanchayatName('');
    } else {
      setPanchayats([]);
    }
  }, [selectedBlockLgd]);

  const fetchStates = async () => {
    try {
      setLoadingStates(true);
      console.log('========================================');
      console.log('📍 FETCH STATES - START');
      console.log('========================================');
      console.log('🌐 API Base URL:', api.defaults.baseURL);
      console.log('🔗 Full URL:', `${api.defaults.baseURL}/api/dropdown/states`);

      const response = await api.get('/api/dropdown/states');

      console.log('========================================');
      console.log('✅ API Response Received');
      console.log('========================================');
      console.log('Response Status:', response.status);
      console.log('Response Data Keys:', Object.keys(response.data));
      console.log('Raw response.data:', JSON.stringify(response.data).substring(0, 500));
      console.log('States Array exists?:', !!response.data.states);
      console.log('States Array Length:', response.data.states?.length || 0);

      if (response.data.states && response.data.states.length > 0) {
        console.log('First 5 states:', response.data.states.slice(0, 5).map((s: any) => ({
          id: s.id,
          name_en: s.name_en,
          state_code: s.state_code
        })));

        console.log('========================================');
        console.log('🔄 Calling setStates() with', response.data.states.length, 'states');
        console.log('========================================');

        setStates(response.data.states);

        // Verify state was set
        setTimeout(() => {
          console.log('========================================');
          console.log('✅ VERIFICATION: States in component state:', states.length);
          console.log('========================================');
        }, 500);
      } else {
        console.warn('⚠️ No states in response!');
        setStates([]);
      }
    } catch (error: any) {
      console.error('========================================');
      console.error('❌ ERROR FETCHING STATES');
      console.error('========================================');
      console.error('Error Object:', JSON.stringify(error, null, 2));
      console.error('Error Message:', error.message);
      console.error('Error Code:', error.code);
      if (error.response) {
        console.error('Response Status:', error.response.status);
        console.error('Response Data:', error.response.data);
      } else if (error.request) {
        console.error('❌ No Response Received');
        console.error('❌ Request:', error.request);
      }
      Alert.alert(
        'Connection Error',
        `Could not load states. Please check:\n\n1. Backend is running at localhost:8000\n2. Device/simulator can reach backend\n\nError: ${error.message}`
      );
    } finally {
      setLoadingStates(false);
    }
  };

  const fetchDistricts = async (stateCode: string) => {
    try {
      console.log(`📍 Fetching districts for state ${stateCode}...`);
      const response = await api.get('/api/dropdown/districts', {
        params: { state_code: stateCode },
      });
      setDistricts(response.data.districts || []);
      console.log(`✅ Loaded ${response.data.districts?.length || 0} districts`);
    } catch (error: any) {
      console.error('Error fetching districts:', error);
      Alert.alert('Error', 'Could not load districts for selected state.');
    }
  };

  const fetchBlocks = async (districtLgd: string) => {
    try {
      console.log(`📍 Fetching blocks for district ${districtLgd}...`);
      const response = await api.get('/api/dropdown/blocks', {
        params: { district_lgd_code: districtLgd },
      });
      setBlocks(response.data.blocks || []);
      console.log(`✅ Loaded ${response.data.blocks?.length || 0} blocks`);
    } catch (error: any) {
      console.error('Error fetching blocks:', error);
      Alert.alert('Error', 'Could not load blocks for selected district.');
    }
  };

  const fetchPanchayats = async (blockLgd: string) => {
    try {
      console.log(`📍 Fetching panchayats for block ${blockLgd}...`);
      const response = await api.get('/api/dropdown/panchayats', {
        params: { block_lgd_code: blockLgd },
      });
      setPanchayats(response.data.panchayats || []);
      console.log(`✅ Loaded ${response.data.panchayats?.length || 0} panchayats`);
    } catch (error: any) {
      console.error('Error fetching panchayats:', error);
      Alert.alert('Error', 'Could not load panchayats for selected block.');
    }
  };

  const handleSaveAddress = async () => {
    // Validation: State and District are required
    if (!selectedStateCode || !selectedDistrictLgd) {
      Alert.alert('त्रुटि / Error', 'कृपया राज्य और जिला चुनें\nPlease select state and district');
      return;
    }

    // Village is required (as per user's original requirement)
    if (!village.trim()) {
      Alert.alert('त्रुटि / Error', 'कृपया गाँव का नाम दर्ज करें\nPlease enter village name');
      return;
    }

    try {
      setLoading(true);

      const locationData: any = {
        state: selectedStateName || selectedStateCode,
        district: selectedDistrictName || selectedDistrictLgd,
        block: selectedBlockName || selectedBlockLgd || null,
        panchayat: selectedPanchayatName || selectedPanchayatLgd || null,
        village: village.trim(),
        street: street.trim() || null,
      };

      console.log('💾 Saving location:', locationData);

      // Get user_id for dev bypass
      const userId = await AsyncStorage.getItem('user_id');

      const response = await api.post('/api/location/update-user-location', locationData, {
        params: {
          dev_user_id: userId, // Dev mode bypass
        },
      });

      console.log('✅ Location saved:', response.data);

      Alert.alert(
        'सफलता / Success',
        'आपका पता सफलतापूर्वक सहेजा गया\nYour address has been saved successfully',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error: any) {
      console.error('Save error:', error);
      Alert.alert(
        'त्रुटि / Error',
        error.response?.data?.detail || 'पता सहेजने में विफल। कृपया पुन: प्रयास करें।\nCould not save address. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (loadingStates) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading states...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color={COLORS.gray[900]} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>पता अपडेट करें / Update Address</Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.instructionText}>
              नीचे दिए गए ड्रॉपडाउन से चयन करें
            </Text>
            <Text style={styles.instructionTextEn}>
              Select from dropdowns below
            </Text>
          </View>

          {/* DEBUG INDICATORS - REMOVE AFTER TESTING */}
          <View style={{...styles.section, backgroundColor: '#fffbea', padding: 15, borderWidth: 2, borderColor: '#f59e0b'}}>
            <Text style={{fontSize: 16, fontWeight: 'bold', color: '#92400e', marginBottom: 8}}>
              🐛 DEBUG INFO (Remove this after testing)
            </Text>
            <Text style={{fontSize: 14, color: '#78350f', marginBottom: 4}}>
              States loaded: {states.length}
            </Text>
            <Text style={{fontSize: 14, color: '#78350f', marginBottom: 4}}>
              Districts loaded: {districts.length}
            </Text>
            <Text style={{fontSize: 14, color: '#78350f', marginBottom: 4}}>
              Selected state code: {selectedStateCode || 'None'}
            </Text>
            {states.length > 0 && (
              <Text style={{fontSize: 12, color: '#78350f', marginTop: 8}}>
                First state: {states[0]?.name_en || 'N/A'} (code: {states[0]?.state_code})
              </Text>
            )}
            {states.length === 0 && (
              <Text style={{fontSize: 14, color: '#dc2626', fontWeight: 'bold', marginTop: 8}}>
                ⚠️ NO STATES LOADED - Check console logs!
              </Text>
            )}
          </View>

          {/* State Dropdown */}
          <View style={styles.section}>
            <CustomDropdown
              label="State (Required)"
              labelHindi="राज्य *"
              value={selectedStateCode}
              options={states.map((state) => ({
                label: state.name_en || state.name || 'Unknown',
                value: state.state_code || '',
              }))}
              onValueChange={(value) => {
                setSelectedStateCode(value);
                const selected = states.find(s => s.state_code === value);
                setSelectedStateName(selected?.name_en || selected?.name || '');
              }}
              placeholder="राज्य चुनें / Select State"
              required={true}
            />
          </View>

          {/* District Dropdown */}
          {selectedStateCode && (
            <View style={styles.section}>
              <CustomDropdown
                label="District (Required)"
                labelHindi="जिला *"
                value={selectedDistrictLgd}
                options={districts.map((district) => ({
                  label: district.name_en || district.name || 'Unknown',
                  value: district.lgd_code || '',
                }))}
                onValueChange={(value) => {
                  setSelectedDistrictLgd(value);
                  const selected = districts.find(d => d.lgd_code === value);
                  setSelectedDistrictName(selected?.name_en || selected?.name || '');
                }}
                placeholder="जिला चुनें / Select District"
                disabled={districts.length === 0}
                required={true}
              />
              {districts.length === 0 && (
                <Text style={styles.helperText}>Loading districts...</Text>
              )}
            </View>
          )}

          {/* Block Dropdown */}
          {selectedDistrictLgd && (
            <View style={styles.section}>
              <CustomDropdown
                label="Block (Optional)"
                labelHindi="ब्लॉक"
                value={selectedBlockLgd}
                options={blocks.map((block) => ({
                  label: block.name_en || block.name || 'Unknown',
                  value: block.lgd_code || '',
                }))}
                onValueChange={(value) => {
                  setSelectedBlockLgd(value);
                  const selected = blocks.find(b => b.lgd_code === value);
                  setSelectedBlockName(selected?.name_en || selected?.name || '');
                }}
                placeholder="ब्लॉक चुनें / Select Block"
                disabled={blocks.length === 0}
              />
              {blocks.length === 0 && (
                <Text style={styles.helperText}>Loading blocks...</Text>
              )}
            </View>
          )}

          {/* Panchayat Dropdown */}
          {selectedBlockLgd && (
            <View style={styles.section}>
              <CustomDropdown
                label="Panchayat (Optional)"
                labelHindi="पंचायत"
                value={selectedPanchayatLgd}
                options={panchayats.map((panchayat) => ({
                  label: panchayat.name_en || panchayat.name || 'Unknown',
                  value: panchayat.lgd_code || '',
                }))}
                onValueChange={(value) => {
                  setSelectedPanchayatLgd(value);
                  const selected = panchayats.find(p => p.lgd_code === value);
                  setSelectedPanchayatName(selected?.name_en || selected?.name || '');
                }}
                placeholder="पंचायत चुनें / Select Panchayat"
                disabled={panchayats.length === 0}
              />
              {panchayats.length === 0 && (
                <Text style={styles.helperText}>Loading panchayats...</Text>
              )}
            </View>
          )}

          {/* Village Text Input */}
          {selectedDistrictLgd && (
            <View style={styles.section}>
              <Text style={styles.labelHindi}>गाँव का नाम *</Text>
              <Text style={styles.labelEnglish}>Village Name (Required)</Text>
              <TextInput
                style={styles.input}
                placeholder="गाँव का नाम / Village name"
                value={village}
                onChangeText={setVillage}
              />
            </View>
          )}

          {/* Street Text Input */}
          {village.trim() && (
            <View style={styles.section}>
              <Text style={styles.labelHindi}>गली / सड़क</Text>
              <Text style={styles.labelEnglish}>Street / Locality (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="Main Road, Gandhi Chowk, etc."
                value={street}
                onChangeText={setStreet}
              />
            </View>
          )}

          {/* Save Button */}
          {selectedStateCode && selectedDistrictLgd && village.trim() && (
            <View style={styles.section}>
              <TouchableOpacity
                style={[styles.saveButton, loading && styles.buttonDisabled]}
                onPress={handleSaveAddress}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color={COLORS.white} />
                ) : (
                  <>
                    <Ionicons name="save-outline" size={20} color={COLORS.white} />
                    <Text style={styles.saveButtonText}>सहेजें / Save Address</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
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
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: COLORS.gray[600],
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginLeft: 16,
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  instructionText: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.gray[900],
    textAlign: 'center',
    marginBottom: 4,
  },
  instructionTextEn: {
    fontSize: 13,
    color: COLORS.gray[600],
    textAlign: 'center',
  },
  labelHindi: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: 2,
  },
  labelEnglish: {
    fontSize: 11,
    color: COLORS.gray[600],
    marginBottom: 8,
  },
  pickerContainer: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  input: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: COLORS.gray[900],
  },
  helperText: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginTop: 6,
    fontStyle: 'italic',
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.success,
    borderRadius: 12,
    padding: 16,
    gap: 8,
    marginTop: 8,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});
