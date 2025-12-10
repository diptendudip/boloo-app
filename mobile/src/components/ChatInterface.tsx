/**
 * ChatInterface Component - WhatsApp-style chat UI
 *
 * Features:
 * - Chat bubbles for user and AI messages
 * - Text input + voice recording
 * - Real-time conversation flow
 * - Completeness indicator
 * - Summary confirmation dialog
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
  Animated,
} from 'react-native';
import { useAudioRecorder, RecordingPresets, AudioModule, setAudioModeAsync } from 'expo-audio';
import * as FileSystem from 'expo-file-system/legacy';
import { Ionicons } from '@expo/vector-icons';
import { chatService, ChatMessage, ChatTurnResponse } from '../services/chat';
import { offlineManager } from '../utils/OfflineManager';
import { useAuth } from '../context/AuthContext';
import { PreviewCard } from './PreviewCard';
import { ConfirmationModal, showAlert } from './ConfirmationModal';
import { webAudioRecorder } from '../utils/webAudioRecorder';

interface ChatInterfaceProps {
  userId: string;
  onSubmitComplete?: (result: any) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId, onSubmitComplete }) => {
  const { isOnline } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [completenessScore, setCompletenessScore] = useState(0);
  const [displayedProgress, setDisplayedProgress] = useState(0); // Monotonic progress (never decreases)
  const [readyForSubmission, setReadyForSubmission] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);

  // Option B: Early submission support
  const [showSubmitButton, setShowSubmitButton] = useState(false);
  const [showSkipButton, setShowSkipButton] = useState(false);
  const [previewCard, setPreviewCard] = useState<any>(null);

  // Web-compatible confirmation modal state
  const [confirmModalVisible, setConfirmModalVisible] = useState(false);
  const [confirmModalData, setConfirmModalData] = useState({
    title: '',
    message: '',
    buttons: [] as Array<{ text: string; onPress?: () => void; style?: 'default' | 'cancel' | 'destructive' }>,
  });

  const scrollViewRef = useRef<ScrollView>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const meteringIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const recordingUriRef = useRef<string | null>(null);

  // Initialize expo-audio recorder hook
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  // Audio-reactive pulsing animation (responds to voice intensity)
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Start conversation on mount
  useEffect(() => {
    initializeConversation();
  }, []);

  // Set audio mode for iOS recording on mount
  useEffect(() => {
    const setupAudioMode = async () => {
      try {
        // Configure audio session for recording (iOS & Android)
        await setAudioModeAsync({
          allowsRecording: true,
          playsInSilentMode: true,
        });
        console.log('✅ Audio mode configured for recording');
      } catch (error) {
        console.error('Error setting audio mode:', error);
      }
    };
    setupAudioMode();
  }, []);

  // Audio-reactive animation - responds to voice intensity
  useEffect(() => {
    if (isRecording && audioRecorder.isRecording) {
      // Poll audio levels every 100ms
      meteringIntervalRef.current = setInterval(() => {
        try {
          const metering = audioRecorder.currentTime; // expo-audio provides metering through recording state
          // Note: expo-audio's metering API may be different, adjust if needed
          if (metering !== undefined && metering !== null) {
            // For now, use a simple pulsing animation
            // expo-audio's metering API might need adjustment based on actual implementation
            const targetScale = 1.2; // Simple pulse effect

            // Smooth animation to new scale
            Animated.spring(pulseAnim, {
              toValue: targetScale,
              friction: 8,
              tension: 100,
              useNativeDriver: true,
            }).start();

            // Spring back
            setTimeout(() => {
              Animated.spring(pulseAnim, {
                toValue: 1,
                friction: 8,
                tension: 100,
                useNativeDriver: true,
              }).start();
            }, 150);
          }
        } catch (error) {
          console.log('Error reading audio level:', error);
        }
      }, 300);
    } else {
      // Reset when not recording
      if (meteringIntervalRef.current) {
        clearInterval(meteringIntervalRef.current);
        meteringIntervalRef.current = null;
      }
      pulseAnim.setValue(1);
    }

    return () => {
      if (meteringIntervalRef.current) {
        clearInterval(meteringIntervalRef.current);
      }
    };
  }, [isRecording, audioRecorder.isRecording]);

  const initializeConversation = async () => {
    try {
      setIsLoading(true);
      const response = await chatService.startConversation(userId, 'hi');

      if (response.success) {
        setConversationId(response.conversation_id);

        // Add greeting as first message
        const greetingMessage: ChatMessage = {
          role: 'assistant',
          content: response.greeting_hi,
          timestamp: new Date(),
        };
        setMessages([greetingMessage]);
      }
    } catch (error) {
      console.error('Error initializing conversation:', error);
      Alert.alert('त्रुटि', 'बातचीत शुरू करने में समस्या। कृपया पुनः प्रयास करें।');
    } finally {
      setIsLoading(false);
    }
  };

  const sendTextMessage = async () => {
    if (!inputText.trim() || !conversationId) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await chatService.sendTextMessage(
        conversationId,
        userId,
        inputText
      );

      handleChatResponse(response);
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('त्रुटि', 'संदेश भेजने में समस्या। कृपया पुनः प्रयास करें।');
    } finally {
      setIsLoading(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (meteringIntervalRef.current) {
        clearInterval(meteringIntervalRef.current);
      }
      // Web audio recorder cleanup
      if (Platform.OS === 'web') {
        webAudioRecorder.cleanup();
      }
      // expo-audio cleanup is handled automatically by the hook
    };
  }, []);

  const startRecording = async () => {
    try {
      // WEB: Use native MediaRecorder API for reliable recording
      if (Platform.OS === 'web') {
        console.log('[Recording] Using web MediaRecorder');

        // Request permissions
        const hasPermission = await webAudioRecorder.requestPermission();
        if (!hasPermission) {
          setConfirmModalData({
            title: 'अनुमति आवश्यक',
            message: 'कृपया माइक्रोफोन की अनुमति दें।',
            buttons: [{ text: 'ठीक है', style: 'default' }],
          });
          setConfirmModalVisible(true);
          return;
        }

        // Prepare and start recording
        await webAudioRecorder.prepareToRecordAsync();
        webAudioRecorder.record();

        setIsRecording(true);
        setRecordingDuration(0);

        // Start duration counter
        durationIntervalRef.current = setInterval(() => {
          setRecordingDuration(prev => prev + 1);
        }, 1000);

        console.log('[Recording] Web recording started successfully');
        return;
      }

      // NATIVE: Use expo-audio
      console.log('[Recording] Using expo-audio for native');

      // Request permissions
      const permission = await AudioModule.requestRecordingPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('अनुमति आवश्यक', 'कृपया माइक्रोफोन की अनुमति दें।');
        return;
      }

      // CRITICAL: Prepare recorder before starting (required for file to be saved)
      await audioRecorder.prepareToRecordAsync();
      console.log('Recorder prepared');

      // Start recording using expo-audio hook
      audioRecorder.record();

      setIsRecording(true);
      setRecordingDuration(0);

      // Start duration counter
      durationIntervalRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);

      console.log('Recording started successfully');
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsRecording(false);
      setRecordingDuration(0);
      if (Platform.OS === 'web') {
        setConfirmModalData({
          title: 'त्रुटि',
          message: 'रिकॉर्डिंग शुरू करने में समस्या। कृपया पुनः प्रयास करें।',
          buttons: [{ text: 'ठीक है', style: 'default' }],
        });
        setConfirmModalVisible(true);
      } else {
        Alert.alert('त्रुटि', 'रिकॉर्डिंग शुरू करने में समस्या। कृपया पुनः प्रयास करें।');
      }
    }
  };

  const stopRecording = async () => {
    // Clear duration counter
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }

    // Clear metering interval
    if (meteringIntervalRef.current) {
      clearInterval(meteringIntervalRef.current);
      meteringIntervalRef.current = null;
    }

    if (!isRecording || !conversationId) {
      console.log('No active recording to stop');
      setIsRecording(false);
      setRecordingDuration(0);
      return;
    }

    // Get actual recording time - different sources for web vs native
    const actualDuration = Platform.OS === 'web'
      ? webAudioRecorder.currentTime || recordingDuration
      : audioRecorder.currentTime || recordingDuration;
    console.log(`[Recording] State duration: ${recordingDuration}s, Actual duration: ${actualDuration}s`);

    // Check minimum duration (1 second minimum)
    // FIX: Use actual duration from recorder, not state (web timing issues)
    if (actualDuration < 1 && recordingDuration < 1) {
      console.log('Recording too short, minimum 1 second required');
      // Clean up the recording
      try {
        if (Platform.OS === 'web') {
          await webAudioRecorder.stop();
          webAudioRecorder.cleanup();
        } else {
          await audioRecorder.stop();
        }
      } catch (e) {
        console.log('Error cleaning up short recording:', e);
      }
      setIsRecording(false);
      setRecordingDuration(0);

      // FIX: Use web-compatible modal instead of Alert.alert
      if (Platform.OS === 'web') {
        setConfirmModalData({
          title: 'रिकॉर्डिंग बहुत छोटी',
          message: 'कम से कम 1 सेकंड बोलें।',
          buttons: [{ text: 'ठीक है', style: 'default' }],
        });
        setConfirmModalVisible(true);
      } else {
        Alert.alert('रिकॉर्डिंग बहुत छोटी', 'कम से कम 1 सेकंड बोलें।');
      }
      return;
    }

    // Clear state immediately to prevent double-stop
    setIsRecording(false);
    const finalDuration = Math.max(recordingDuration, actualDuration);
    setRecordingDuration(0);

    try {
      // Stop the recording - different for web vs native
      let uri: string | null = null;

      if (Platform.OS === 'web') {
        console.log('[Recording] Stopping web MediaRecorder...');
        uri = await webAudioRecorder.stop();
        console.log('[Recording] Web recording stopped, URI:', uri);
      } else {
        await audioRecorder.stop();
        uri = audioRecorder.uri;
      }

      if (!uri) {
        console.error('No recording URI found');
        // FIX: Use web-compatible modal
        if (Platform.OS === 'web') {
          setConfirmModalData({
            title: 'त्रुटि',
            message: 'रिकॉर्डिंग फ़ाइल नहीं मिली। कृपया पुनः प्रयास करें।',
            buttons: [{ text: 'ठीक है', style: 'default' }],
          });
          setConfirmModalVisible(true);
        } else {
          Alert.alert('त्रुटि', 'रिकॉर्डिंग फ़ाइल नहीं मिली।');
        }
        return;
      }

      console.log(`Recording stopped. Duration: ${finalDuration}s, URI: ${uri}`);

      // Wait a moment for file to be finalized
      await new Promise(resolve => setTimeout(resolve, 500));

      // FIX: Skip file verification on web (FileSystem API works differently)
      if (Platform.OS !== 'web') {
        // Verify file exists (native only)
        const fileInfo = await FileSystem.getInfoAsync(uri);
        if (!fileInfo.exists) {
          console.error('Recording file does not exist:', uri);
          Alert.alert('त्रुटि', 'रिकॉर्डिंग फ़ाइल सेव नहीं हुई। कृपया पुनः प्रयास करें।');
          return;
        }
        console.log(`File verified. Size: ${fileInfo.size} bytes`);
      } else {
        console.log(`[Web] Skipping file verification, URI: ${uri}`);
      }

      // Add placeholder user message
      const userMessage: ChatMessage = {
        role: 'user',
        content: '🎤 [वॉइस मैसेज]',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      setIsLoading(true);

      // Send voice message
      const response = await chatService.sendVoiceMessage(
        conversationId,
        userId,
        uri
      );

      handleChatResponse(response);
      setIsLoading(false);
    } catch (error) {
      console.error('Error stopping recording:', error);
      setIsLoading(false);
      // FIX: Use web-compatible modal
      if (Platform.OS === 'web') {
        setConfirmModalData({
          title: 'त्रुटि',
          message: 'रिकॉर्डिंग रोकने में समस्या। कृपया पुनः प्रयास करें।',
          buttons: [{ text: 'ठीक है', style: 'default' }],
        });
        setConfirmModalVisible(true);
      } else {
        Alert.alert('त्रुटि', 'रिकॉर्डिंग रोकने में समस्या। कृपया पुनः प्रयास करें।');
      }
    }
  };

  // Toggle recording on/off with single tap
  const toggleRecording = async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  };

  const handleChatResponse = (response: ChatTurnResponse) => {
    // Update user message with transcribed text if voice
    // ONLY update if it's a voice message placeholder, don't duplicate
    if (response.user_message !== inputText) {
      setMessages(prev => {
        const updated = [...prev];
        const lastMessage = updated[updated.length - 1];

        // Only update if the last message is the voice placeholder
        if (lastMessage && lastMessage.role === 'user' && lastMessage.content === '🎤 [वॉइस मैसेज]') {
          updated[updated.length - 1].content = response.user_message;
        }
        // Otherwise, don't modify - prevents duplication

        return updated;
      });
    }

    // Add AI response (NOT user message)
    const aiMessage: ChatMessage = {
      role: 'assistant',
      content: response.ai_response_hi,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, aiMessage]);

    // Update completeness
    setCompletenessScore(response.completeness_score);
    setReadyForSubmission(response.ready_for_submission);

    // MONOTONIC PROGRESS: Only increase, never decrease (fixes confusing progress jumps)
    setDisplayedProgress(prev => Math.max(prev, response.completeness_score));

    // Option B: Update UX enhancement flags
    setShowSubmitButton(response.show_submit_button || false);
    setShowSkipButton(response.show_skip_button || false);
    setPreviewCard(response.preview_card || null);

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const showSummaryAndSubmit = async () => {
    if (!conversationId) return;

    try {
      setIsLoading(true);
      const summary = await chatService.getConversationSummary(conversationId, userId);

      // Use journalist-style narrative from API (natural, like news reporting)
      // Falls back to old format if narrative not available (backwards compatibility)
      let displaySummary = '📋 आपकी रिपोर्ट:\n\n';

      if (summary.narrative_summary_hi) {
        // NEW: Use journalist narrative (natural Hindi paragraph)
        displaySummary += summary.narrative_summary_hi;
      } else {
        // FALLBACK: Build from extracted_data (old bullet-point format)
        const fieldLabels: Record<string, string> = {
          issue_description: 'समस्या का विवरण',
          location: 'स्थान',
          when_started: 'कब से',
          affected_people: 'प्रभावित लोग',
          previous_action: 'पहले की गई कार्रवाई'
        };

        Object.entries(summary.extracted_data || {}).forEach(([key, value]) => {
          if (value && value !== null && value !== '') {
            const label = fieldLabels[key] || key;
            displaySummary += `✓ ${label}: ${value}\n\n`;
          }
        });
      }

      // Add missing fields warning if any
      if (summary.missing_fields && summary.missing_fields.length > 0) {
        displaySummary += '\n\n⚠️ कुछ जानकारी अभी भी गायब है:\n';

        // BUG FIX #10D: missing_fields is an array of objects, not strings
        // Each object has: {field, name_hi, name_en, importance, prompt_hi, prompt_en}
        summary.missing_fields.forEach((fieldObj: any) => {
          // Use the Hindi name provided by the backend
          const label = fieldObj.name_hi || fieldObj.field || 'अज्ञात फील्ड';
          displaySummary += `  • ${label}\n`;
        });

        displaySummary += '\nलेकिन आप इसे अभी जमा कर सकते हैं।';
      }

      // Use web-compatible confirmation (works on iOS, Android, AND Web)
      if (Platform.OS === 'web') {
        // Web: Use custom modal for better UX
        setConfirmModalData({
          title: 'सारांश की पुष्टि करें',
          message: displaySummary,
          buttons: [
            { text: 'संपादित करें', style: 'cancel' },
            { text: 'जमा करें', onPress: () => submitReport() },
          ],
        });
        setConfirmModalVisible(true);
      } else {
        // Native: Use Alert.alert
        Alert.alert(
          'सारांश की पुष्टि करें',
          displaySummary,
          [
            { text: 'संपादित करें', style: 'cancel' },
            { text: 'जमा करें', onPress: () => submitReport() },
          ]
        );
      }
    } catch (error) {
      console.error('Error getting summary:', error);
      showAlert('त्रुटि', 'सारांश प्राप्त करने में समस्या।');
    } finally {
      setIsLoading(false);
    }
  };

  const submitReport = async () => {
    if (!conversationId) return;

    try {
      setIsLoading(true);

      // Check if online
      if (!isOnline) {
        // Get summary for offline queueing
        const summary = await chatService.getConversationSummary(conversationId, userId);

        // Queue the report for later submission
        const queueId = await offlineManager.addToQueue({
          userId,
          description: summary.narrative_summary_hi || summary.extracted_data?.issue_description || 'रिपोर्ट विवरण',
          location: summary.extracted_data?.location,
          category: 'general', // Default category
        });

        showAlert(
          'ऑफलाइन मोड',
          'आपकी रिपोर्ट सहेज ली गई है। जब इंटरनेट कनेक्शन उपलब्ध होगा, तो यह स्वचालित रूप से भेज दी जाएगी।',
          [
            {
              text: 'ठीक है',
              onPress: () => {
                if (onSubmitComplete) {
                  onSubmitComplete({ case_id: queueId, offline: true });
                }
              },
            },
          ]
        );
        return;
      }

      // Online submission
      const result = await chatService.submitConversation(conversationId, userId);

      showAlert(
        'सफल!',
        result.message_hi,
        [
          {
            text: 'ठीक है',
            onPress: () => {
              if (onSubmitComplete) {
                onSubmitComplete(result);
              }
            },
          },
        ]
      );
    } catch (error) {
      console.error('Error submitting report:', error);

      // If submission fails, offer to queue it offline
      if (Platform.OS === 'web') {
        // Web: Use custom modal for save option
        setConfirmModalData({
          title: 'त्रुटि',
          message: 'रिपोर्ट जमा करने में समस्या। क्या आप इसे बाद में भेजने के लिए सहेजना चाहते हैं?',
          buttons: [
            { text: 'रद्द करें', style: 'cancel' },
            {
              text: 'सहेजें',
              onPress: async () => {
                try {
                  const summary = await chatService.getConversationSummary(conversationId!, userId);
                  const queueId = await offlineManager.addToQueue({
                    userId,
                    description: summary.narrative_summary_hi || summary.extracted_data?.issue_description || 'रिपोर्ट विवरण',
                    location: summary.extracted_data?.location,
                    category: 'general',
                  });

                  showAlert('सहेजा गया', 'रिपोर्ट बाद में भेजने के लिए सहेज ली गई है।');
                  if (onSubmitComplete) {
                    onSubmitComplete({ case_id: queueId, offline: true });
                  }
                } catch (e) {
                  console.error('Error queueing report:', e);
                  showAlert('त्रुटि', 'रिपोर्ट सहेजने में समस्या।');
                }
              },
            },
          ],
        });
        setConfirmModalVisible(true);
      } else {
        // Native: Use Alert.alert
        Alert.alert(
          'त्रुटि',
          'रिपोर्ट जमा करने में समस्या। क्या आप इसे बाद में भेजने के लिए सहेजना चाहते हैं?',
          [
            { text: 'रद्द करें', style: 'cancel' },
            {
              text: 'सहेजें',
              onPress: async () => {
                try {
                  const summary = await chatService.getConversationSummary(conversationId!, userId);
                  const queueId = await offlineManager.addToQueue({
                    userId,
                    description: summary.narrative_summary_hi || summary.extracted_data?.issue_description || 'रिपोर्ट विवरण',
                    location: summary.extracted_data?.location,
                    category: 'general',
                  });

                  Alert.alert('सहेजा गया', 'रिपोर्ट बाद में भेजने के लिए सहेज ली गई है।');
                  if (onSubmitComplete) {
                    onSubmitComplete({ case_id: queueId, offline: true });
                  }
                } catch (e) {
                  console.error('Error queueing report:', e);
                  Alert.alert('त्रुटि', 'रिपोर्ट सहेजने में समस्या।');
                }
              },
            },
          ]
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      {/* Web-compatible Confirmation Modal */}
      <ConfirmationModal
        visible={confirmModalVisible}
        title={confirmModalData.title}
        message={confirmModalData.message}
        buttons={confirmModalData.buttons}
        onClose={() => setConfirmModalVisible(false)}
      />
      {/* Completeness indicator */}
      <View style={styles.completenessBar}>
        <View style={styles.completenessProgress}>
          <View
            style={[
              styles.completenessProgressFill,
              { width: `${displayedProgress * 100}%` },
            ]}
          />
        </View>
        <Text style={styles.completenessText}>
          {Math.round(displayedProgress * 100)}% पूर्ण
        </Text>
      </View>

      {/* Messages */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.map((message, index) => (
          <View
            key={index}
            style={[
              styles.messageBubble,
              message.role === 'user' ? styles.userBubble : styles.aiBubble,
            ]}
          >
            <Text
              style={[
                styles.messageText,
                message.role === 'user' ? styles.userText : styles.aiText,
              ]}
            >
              {message.content}
            </Text>
          </View>
        ))}

        {isLoading && (
          <View style={styles.loadingBubble}>
            <ActivityIndicator size="small" color="#666" />
            <Text style={styles.loadingText}>टाइप कर रहे हैं...</Text>
          </View>
        )}

        {/* Option B: Preview Card (shows extracted data) */}
        {showSubmitButton && previewCard && (
          <View style={styles.previewSection}>
            <PreviewCard
              location={previewCard.location}
              issue={previewCard.issue_description}
              reporter={previewCard.reporter_name}
              phone={previewCard.phone}
              actions={previewCard.actions_taken}
            />
          </View>
        )}
      </ScrollView>

      {/* Option B: Early Submit Button (minimum fields present) */}
      {showSubmitButton && (
        <View style={styles.optionBActionsContainer}>
          <TouchableOpacity
            style={styles.optionBSubmitButton}
            onPress={showSummaryAndSubmit}
            disabled={isLoading}
          >
            <Ionicons name="checkmark-circle" size={24} color="#fff" />
            <Text style={styles.optionBSubmitButtonText}>✓ रिपोर्ट सबमिट करें</Text>
          </TouchableOpacity>

          {showSkipButton && (
            <TouchableOpacity
              style={styles.skipButton}
              onPress={() => {
                // Skip to next question or allow adding more details
                setInputText('और जानकारी जोड़ें');
              }}
            >
              <Text style={styles.skipButtonText}>या फिर और जानकारी जोड़ें →</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Submit button (when fully complete - old behavior) */}
      {readyForSubmission && !showSubmitButton && (
        <TouchableOpacity
          style={styles.submitButton}
          onPress={showSummaryAndSubmit}
          disabled={isLoading}
        >
          <Ionicons name="checkmark-circle" size={24} color="#fff" />
          <Text style={styles.submitButtonText}>सारांश देखें और जमा करें</Text>
        </TouchableOpacity>
      )}

      {/* Recording indicator with pulsing animation (shows when recording) */}
      {isRecording && (
        <View style={styles.recordingIndicator}>
          {/* Pulsing circles - breathing effect */}
          <View style={styles.pulseContainer}>
            <Animated.View
              style={[
                styles.pulseCircle,
                styles.pulseCircleOuter,
                {
                  transform: [{ scale: pulseAnim }],
                  opacity: pulseAnim.interpolate({
                    inputRange: [1, 1.3],
                    outputRange: [0.3, 0.1],
                  }),
                },
              ]}
            />
            <Animated.View
              style={[
                styles.pulseCircle,
                styles.pulseCircleMiddle,
                {
                  transform: [{ scale: pulseAnim }],
                  opacity: pulseAnim.interpolate({
                    inputRange: [1, 1.3],
                    outputRange: [0.5, 0.2],
                  }),
                },
              ]}
            />
            <View style={[styles.pulseCircle, styles.pulseCircleInner]} />
          </View>

          <Text style={styles.recordingText}>
            रिकॉर्डिंग चल रही है... {recordingDuration}s
          </Text>
          <Text style={styles.recordingHint}>
            रुकने के लिए फिर से दबाएँ
          </Text>
        </View>
      )}

      {/* Input area */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="अपना संदेश लिखें..."
          placeholderTextColor="#999"
          multiline
          maxLength={500}
          editable={!isRecording}
        />

        {inputText.trim() ? (
          <TouchableOpacity
            style={styles.sendButton}
            onPress={sendTextMessage}
            disabled={isLoading}
          >
            <Ionicons name="send" size={24} color="#fff" />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[
              styles.voiceButton,
              isRecording && styles.voiceButtonRecording
            ]}
            onPress={toggleRecording}
            disabled={isLoading}
          >
            <Ionicons
              name={isRecording ? 'stop' : 'mic'}
              size={28}
              color="#fff"
            />
          </TouchableOpacity>
        )}
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  completenessBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  completenessProgress: {
    flex: 1,
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    marginRight: 12,
    overflow: 'hidden',
  },
  completenessProgressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 4,
  },
  completenessText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#fff',
  },
  aiText: {
    color: '#333',
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4CAF50',
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    backgroundColor: '#f5f5f5',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    marginRight: 8,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FF3B30',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButtonRecording: {
    backgroundColor: '#FF3B30',
  },
  recordingIndicator: {
    backgroundColor: '#FFF3CD',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#FFE69C',
    padding: 16,
    alignItems: 'center',
  },
  pulseContainer: {
    width: 80,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  pulseCircle: {
    position: 'absolute',
    borderRadius: 100,
    backgroundColor: '#FF3B30',
  },
  pulseCircleOuter: {
    width: 80,
    height: 80,
  },
  pulseCircleMiddle: {
    width: 56,
    height: 56,
  },
  pulseCircleInner: {
    width: 32,
    height: 32,
    opacity: 1,
  },
  recordingText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#856404',
    marginBottom: 4,
  },
  recordingHint: {
    fontSize: 14,
    color: '#856404',
  },
  previewSection: {
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  optionBActionsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  optionBSubmitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  optionBSubmitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginLeft: 8,
  },
  skipButton: {
    alignItems: 'center',
    padding: 12,
    marginTop: 8,
  },
  skipButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
