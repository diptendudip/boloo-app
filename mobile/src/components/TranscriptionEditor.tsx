/**
 * TranscriptionEditor.tsx
 *
 * Full-screen editor for reviewing and editing audio transcriptions
 * Supports Hindi-first interface with auto-save functionality
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface TranscriptionEditorProps {
  visible: boolean;
  initialText: string;
  recordingId?: string;
  onSave: (text: string) => void;
  onCancel: () => void;
  language?: 'hi' | 'en';
}

interface DraftData {
  text: string;
  timestamp: number;
  wordCount: number;
  characterCount: number;
}

const DRAFT_STORAGE_KEY = '@boloo:transcription_draft';
const AUTO_SAVE_INTERVAL = 3000; // 3 seconds

export const TranscriptionEditor: React.FC<TranscriptionEditorProps> = ({
  visible,
  initialText,
  recordingId,
  onSave,
  onCancel,
  language = 'hi',
}) => {
  const [text, setText] = useState(initialText);
  const [wordCount, setWordCount] = useState(0);
  const [characterCount, setCharacterCount] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const textInputRef = useRef<TextInput>(null);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Calculate word and character counts
   */
  const calculateCounts = useCallback((inputText: string) => {
    const trimmedText = inputText.trim();

    // Character count (excluding spaces)
    const chars = trimmedText.replace(/\s/g, '').length;
    setCharacterCount(chars);

    // Word count (split by whitespace)
    const words = trimmedText.length > 0
      ? trimmedText.split(/\s+/).filter(word => word.length > 0).length
      : 0;
    setWordCount(words);
  }, []);

  /**
   * Update text and counts
   */
  const handleTextChange = useCallback((newText: string) => {
    setText(newText);
    calculateCounts(newText);
    setHasUnsavedChanges(true);
  }, [calculateCounts]);

  /**
   * Save draft to AsyncStorage
   */
  const saveDraft = useCallback(async (textToSave: string) => {
    try {
      const draftKey = recordingId
        ? `${DRAFT_STORAGE_KEY}:${recordingId}`
        : DRAFT_STORAGE_KEY;

      const draftData: DraftData = {
        text: textToSave,
        timestamp: Date.now(),
        wordCount,
        characterCount,
      };

      await AsyncStorage.setItem(draftKey, JSON.stringify(draftData));
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save draft:', error);
    }
  }, [recordingId, wordCount, characterCount]);

  /**
   * Load draft from AsyncStorage
   */
  const loadDraft = useCallback(async () => {
    try {
      const draftKey = recordingId
        ? `${DRAFT_STORAGE_KEY}:${recordingId}`
        : DRAFT_STORAGE_KEY;

      const draftJson = await AsyncStorage.getItem(draftKey);

      if (draftJson) {
        const draft: DraftData = JSON.parse(draftJson);

        // Only load draft if it's more recent than initial text
        if (draft.text.length > initialText.length) {
          Alert.alert(
            language === 'hi' ? 'ड्राफ्ट मिला' : 'Draft Found',
            language === 'hi'
              ? 'क्या आप पिछला ड्राफ्ट लोड करना चाहते हैं?'
              : 'Would you like to load the previous draft?',
            [
              {
                text: language === 'hi' ? 'नहीं' : 'No',
                style: 'cancel',
              },
              {
                text: language === 'hi' ? 'हां' : 'Yes',
                onPress: () => {
                  setText(draft.text);
                  calculateCounts(draft.text);
                  setLastSaved(new Date(draft.timestamp));
                },
              },
            ]
          );
        }
      }
    } catch (error) {
      console.error('Failed to load draft:', error);
    }
  }, [recordingId, initialText, language, calculateCounts]);

  /**
   * Clear draft from storage
   */
  const clearDraft = useCallback(async () => {
    try {
      const draftKey = recordingId
        ? `${DRAFT_STORAGE_KEY}:${recordingId}`
        : DRAFT_STORAGE_KEY;

      await AsyncStorage.removeItem(draftKey);
    } catch (error) {
      console.error('Failed to clear draft:', error);
    }
  }, [recordingId]);

  /**
   * Handle save action
   */
  const handleSave = useCallback(async () => {
    if (text.trim().length === 0) {
      Alert.alert(
        language === 'hi' ? 'खाली टेक्स्ट' : 'Empty Text',
        language === 'hi'
          ? 'कृपया कुछ टेक्स्ट दर्ज करें।'
          : 'Please enter some text.'
      );
      return;
    }

    setIsSaving(true);

    try {
      // Clear draft and save
      await clearDraft();
      onSave(text.trim());
    } catch (error) {
      console.error('Failed to save transcription:', error);
      Alert.alert(
        language === 'hi' ? 'त्रुटि' : 'Error',
        language === 'hi'
          ? 'ट्रांसक्रिप्शन सहेजने में विफल।'
          : 'Failed to save transcription.'
      );
    } finally {
      setIsSaving(false);
    }
  }, [text, language, clearDraft, onSave]);

  /**
   * Handle cancel action
   */
  const handleCancel = useCallback(() => {
    if (hasUnsavedChanges) {
      Alert.alert(
        language === 'hi' ? 'बिना सहेजे बाहर निकलें?' : 'Exit Without Saving?',
        language === 'hi'
          ? 'आपके पास बिना सहेजे बदलाव हैं। क्या आप वाकई बाहर निकलना चाहते हैं?'
          : 'You have unsaved changes. Are you sure you want to exit?',
        [
          {
            text: language === 'hi' ? 'रहें' : 'Stay',
            style: 'cancel',
          },
          {
            text: language === 'hi' ? 'बाहर निकलें' : 'Exit',
            style: 'destructive',
            onPress: onCancel,
          },
        ]
      );
    } else {
      onCancel();
    }
  }, [hasUnsavedChanges, language, onCancel]);

  /**
   * Initialize component
   */
  useEffect(() => {
    if (visible) {
      setText(initialText);
      calculateCounts(initialText);
      loadDraft();

      // Focus text input
      setTimeout(() => {
        textInputRef.current?.focus();
      }, 300);
    }
  }, [visible, initialText, calculateCounts, loadDraft]);

  /**
   * Auto-save timer
   */
  useEffect(() => {
    if (visible && hasUnsavedChanges) {
      // Clear existing timer
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }

      // Set new timer
      autoSaveTimerRef.current = setTimeout(() => {
        saveDraft(text);
      }, AUTO_SAVE_INTERVAL);
    }

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [visible, text, hasUnsavedChanges, saveDraft]);

  /**
   * Format last saved time
   */
  const formatLastSaved = (): string => {
    if (!lastSaved) return '';

    const now = new Date();
    const diff = Math.floor((now.getTime() - lastSaved.getTime()) / 1000);

    if (diff < 60) {
      return language === 'hi' ? 'अभी सहेजा गया' : 'Just now';
    } else if (diff < 3600) {
      const mins = Math.floor(diff / 60);
      return language === 'hi'
        ? `${mins} मिनट पहले सहेजा गया`
        : `Saved ${mins} min ago`;
    } else {
      return lastSaved.toLocaleTimeString();
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      onRequestClose={handleCancel}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={handleCancel}
            disabled={isSaving}
          >
            <Text style={styles.cancelButtonText}>
              {language === 'hi' ? 'रद्द करें' : 'Cancel'}
            </Text>
          </TouchableOpacity>

          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle}>
              {language === 'hi' ? 'ट्रांसक्रिप्शन संपादित करें' : 'Edit Transcription'}
            </Text>
            {lastSaved && (
              <Text style={styles.lastSavedText}>
                {formatLastSaved()}
              </Text>
            )}
          </View>

          <TouchableOpacity
            style={[styles.saveButton, isSaving && styles.saveButtonDisabled]}
            onPress={handleSave}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.saveButtonText}>
                {language === 'hi' ? 'सहेजें' : 'Save'}
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Stats Bar */}
        <View style={styles.statsBar}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>
              {language === 'hi' ? 'शब्द' : 'Words'}
            </Text>
            <Text style={styles.statValue}>{wordCount}</Text>
          </View>

          <View style={styles.statDivider} />

          <View style={styles.statItem}>
            <Text style={styles.statLabel}>
              {language === 'hi' ? 'अक्षर' : 'Characters'}
            </Text>
            <Text style={styles.statValue}>{characterCount}</Text>
          </View>

          {hasUnsavedChanges && (
            <>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <View style={styles.unsavedIndicator} />
                <Text style={styles.unsavedText}>
                  {language === 'hi' ? 'बिना सहेजे' : 'Unsaved'}
                </Text>
              </View>
            </>
          )}
        </View>

        {/* Editor */}
        <ScrollView
          style={styles.editorContainer}
          keyboardShouldPersistTaps="handled"
        >
          <TextInput
            ref={textInputRef}
            style={styles.textInput}
            value={text}
            onChangeText={handleTextChange}
            multiline
            placeholder={
              language === 'hi'
                ? 'यहां ट्रांसक्रिप्शन संपादित करें...'
                : 'Edit transcription here...'
            }
            placeholderTextColor="#999"
            textAlignVertical="top"
            autoFocus
            editable={!isSaving}
          />
        </ScrollView>

        {/* Keyboard Hint */}
        <View style={styles.keyboardHint}>
          <Text style={styles.keyboardHintText}>
            {language === 'hi'
              ? '💡 हिन्दी टाइप करने के लिए अपना कीबोर्ड स्विच करें'
              : '💡 Switch your keyboard to type in Hindi'}
          </Text>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    backgroundColor: '#F8F9FA',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  lastSavedText: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  cancelButton: {
    padding: 8,
    minWidth: 60,
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#007AFF',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 60,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    backgroundColor: '#B0B0B0',
  },
  saveButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    backgroundColor: '#F8F9FA',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 6,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  statDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#D0D0D0',
  },
  unsavedIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF9500',
    marginRight: 6,
  },
  unsavedText: {
    fontSize: 14,
    color: '#FF9500',
    fontWeight: '500',
  },
  editorContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  textInput: {
    flex: 1,
    padding: 16,
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
    minHeight: 500,
  },
  keyboardHint: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#FFF9E6',
    borderTopWidth: 1,
    borderTopColor: '#FFE082',
  },
  keyboardHintText: {
    fontSize: 13,
    color: '#F57C00',
    textAlign: 'center',
  },
});

export default TranscriptionEditor;
