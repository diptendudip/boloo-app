import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAudioRecorder, useAudioPlayer, AudioModule, RecordingPresets } from 'expo-audio';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, APP_CONFIG } from '../constants/config';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';
import { triageService } from '../services/triage';
import { transcriptionService } from '../services/transcription';

type VoiceRecordScreenNavigationProp = StackNavigationProp<RootStackParamList, 'VoiceRecord'>;
type VoiceRecordScreenRouteProp = RouteProp<RootStackParamList, 'VoiceRecord'>;

interface Props {
  navigation: VoiceRecordScreenNavigationProp;
  route: VoiceRecordScreenRouteProp;
}

export default function VoiceRecordScreen({ navigation, route }: Props) {
  const { taxonomyId } = route.params;
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const audioPlayer = useAudioPlayer();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingUri, setRecordingUri] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    requestPermissions();
    return () => {
      // Cleanup on unmount - expo-audio handles cleanup automatically
    };
  }, []);

  const requestPermissions = async () => {
    try {
      const { granted } = await AudioModule.requestRecordingPermissionsAsync();
      setPermissionGranted(granted);

      if (!granted) {
        Alert.alert(
          'Permission Required',
          'Microphone permission is required to record audio',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Permission error:', error);
    }
  };

  const startRecording = async () => {
    if (!permissionGranted) {
      await requestPermissions();
      return;
    }

    try {
      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();

      setIsRecording(true);
      setDuration(0);

      // Update duration every second
      const interval = setInterval(() => {
        setDuration(prev => {
          if (prev >= APP_CONFIG.maxAudioDuration) {
            stopRecording();
            clearInterval(interval);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (error) {
      console.error('Failed to start recording', error);
      Alert.alert('Error', 'Failed to start recording. Please try again.');
    }
  };

  const stopRecording = async () => {
    if (!audioRecorder.isRecording) return;

    try {
      setIsRecording(false);
      await audioRecorder.stop();
      const uri = audioRecorder.uri;

      setRecordingUri(uri || null);

    } catch (error) {
      console.error('Failed to stop recording', error);
      Alert.alert('Error', 'Failed to stop recording. Please try again.');
    }
  };

  const playRecording = async () => {
    if (!recordingUri) return;

    try {
      if (isPlaying) {
        audioPlayer.pause();
        setIsPlaying(false);
      } else {
        // If audio finished, seek to beginning before playing
        if (audioPlayer.currentTime >= audioPlayer.duration) {
          audioPlayer.seekTo(0);
        }

        // Load audio if not already loaded
        if (!audioPlayer.isLoaded) {
          audioPlayer.replace({ uri: recordingUri });
        }

        audioPlayer.play();
        setIsPlaying(true);

        // Listen for playback completion
        const checkPlayback = setInterval(() => {
          if (audioPlayer.currentTime >= audioPlayer.duration && audioPlayer.paused) {
            setIsPlaying(false);
            clearInterval(checkPlayback);
          }
        }, 500);
      }
    } catch (error) {
      console.error('Failed to play recording', error);
      Alert.alert('Error', 'Failed to play recording');
    }
  };

  const deleteRecording = () => {
    // expo-audio handles cleanup automatically
    setRecordingUri(null);
    setDuration(0);
    setIsPlaying(false);
  };

  const handleContinue = async () => {
    if (!recordingUri) {
      Alert.alert('No Recording', 'Please record your grievance first');
      return;
    }

    try {
      setIsLoading(true);

      console.log('[VoiceRecord] Uploading and transcribing audio...');

      // Call backend: Upload → Transcribe (Azure) → Classify (Claude)
      const result = await transcriptionService.transcribeAndClassify(
        recordingUri,
        'Raipur, Chhattisgarh' // Location hint
      );

      console.log('[VoiceRecord] Transcription result:', result);

      if (!result.success) {
        throw new Error(result.error || 'Transcription failed');
      }

      // Show transcription result
      const transcript = result.transcript;
      const triageResult = result.triage_result;

      if (triageResult) {
        // Show classification result
        const intentLabel =
          triageResult.intent === 'grievance'
            ? '📢 Grievance (शिकायत)'
            : triageResult.intent === 'community'
            ? '📰 Community (समुदाय)'
            : '📝 Personal (व्यक्तिगत)';

        const confidencePercent = Math.round(triageResult.confidence * 100);

        Alert.alert(
          '🎯 Voice Transcribed & Classified',
          `Transcript: "${transcript.substring(0, 100)}..."\n\nIntent: ${intentLabel}\nConfidence: ${confidencePercent}%\n\n${triageResult.reasoning}`,
          [
            {
              text: 'Cancel',
              style: 'cancel',
            },
            {
              text: 'Submit Case',
              onPress: () => handleRealSubmit(transcript, triageResult),
            },
          ]
        );
      } else {
        // Transcription succeeded but no classification
        Alert.alert(
          '✅ Voice Transcribed',
          `Transcript: "${transcript}"\n\nClassification unavailable. Continue anyway?`,
          [
            {
              text: 'Cancel',
              style: 'cancel',
            },
            {
              text: 'Submit Anyway',
              onPress: () => handleRealSubmit(transcript, null),
            },
          ]
        );
      }
    } catch (error: any) {
      console.error('[VoiceRecord] Real recording error:', error);
      Alert.alert(
        'Error',
        error.message || 'Failed to process recording. Please try again or use test mode.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestMode = () => {
    Alert.alert(
      '🧪 Testing Mode',
      'Skip recording and use dummy transcript for testing?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Test Water Complaint',
          onPress: () => handleTestComplaint(
            'हमारे क्षेत्र में पानी की समस्या है 2 हफ्ते से। कृपया जल्दी ध्यान दें।',
            'Water supply issue in our area for 2 weeks.'
          ),
        },
        {
          text: 'Test Road Complaint',
          onPress: () => handleTestComplaint(
            'सड़क बहुत खराब हो गई है। गड्ढे बहुत हैं। बारिश में पानी भर जाता है।',
            'The road has become very bad. There are many potholes.'
          ),
        },
      ]
    );
  };

  const handleTestComplaint = async (transcriptHindi: string, transcriptEnglish: string) => {
    try {
      setIsLoading(true);

      // Show transcript first
      console.log('[VoiceRecord] Test transcript:', transcriptHindi);

      // Call triage service for classification
      console.log('[VoiceRecord] Classifying complaint...');
      const result = await triageService.classifyIntent({
        transcript_text: transcriptHindi,
        location_hint: 'Raipur, Chhattisgarh',
      });

      console.log('[VoiceRecord] Classification result:', result);

      // Show classification result
      const intentLabel =
        result.intent === 'grievance'
          ? '📢 Grievance (शिकायत)'
          : result.intent === 'community'
          ? '📰 Community (समुदाय)'
          : '📝 Personal (व्यक्तिगत)';

      const confidencePercent = Math.round(result.confidence * 100);

      Alert.alert(
        '🎯 Classification Result',
        `Intent: ${intentLabel}\nConfidence: ${confidencePercent}%\n\n${result.reasoning}`,
        [
          {
            text: 'Cancel',
            style: 'cancel',
          },
          {
            text: 'Submit Case',
            onPress: () => handleTestSubmit(transcriptHindi, transcriptEnglish, result),
          },
        ]
      );
    } catch (error) {
      console.error('[VoiceRecord] Test complaint error:', error);
      Alert.alert('Error', 'Failed to classify complaint. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestSubmit = async (
    transcriptHindi: string,
    transcriptEnglish: string,
    triageResult: any
  ) => {
    try {
      setIsLoading(true);

      // Create dummy case and save locally
      const caseId = `test-case-${Date.now()}`;
      const caseReference = `BOL${Date.now().toString().slice(-8)}`;

      const dummyCase = {
        id: caseId,
        reference: caseReference,
        title: transcriptEnglish.substring(0, 50),
        description: transcriptHindi,
        taxonomy_id: taxonomyId,
        status: 'pending',
        triage_intent: triageResult.intent,
        triage_confidence: triageResult.confidence,
        location: {
          latitude: 21.2514,
          longitude: 81.6296,
          address: 'Raipur, Chhattisgarh',
        },
        created_at: new Date().toISOString(),
      };

      // Save to local storage
      const casesKey = 'boloo:offline_cases';
      const existingCases = await AsyncStorage.getItem(casesKey);
      const cases = existingCases ? JSON.parse(existingCases) : [];
      cases.unshift(dummyCase);
      await AsyncStorage.setItem(casesKey, JSON.stringify(cases));

      console.log('[VoiceRecord] Case saved offline:', dummyCase);

      // Navigate to success screen
      navigation.reset({
        index: 0,
        routes: [
          { name: 'Home' },
          {
            name: 'CaseSubmitted',
            params: { caseId, caseReference },
          },
        ],
      });
    } catch (error) {
      console.error('[VoiceRecord] Submit error:', error);
      Alert.alert('Error', 'Failed to submit case. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRealSubmit = async (
    transcript: string,
    triageResult: any
  ) => {
    try {
      setIsLoading(true);

      // Create case from real transcription and save locally
      const caseId = `real-case-${Date.now()}`;
      const caseReference = `BOL${Date.now().toString().slice(-8)}`;

      const realCase = {
        id: caseId,
        reference: caseReference,
        title: transcript.substring(0, 50),
        description: transcript,
        taxonomy_id: taxonomyId,
        status: 'pending',
        triage_intent: triageResult?.intent || 'unknown',
        triage_confidence: triageResult?.confidence || 0,
        location: {
          latitude: 21.2514,
          longitude: 81.6296,
          address: 'Raipur, Chhattisgarh',
        },
        created_at: new Date().toISOString(),
        audio_uri: recordingUri, // Save reference to audio file
      };

      // Save to local storage
      const casesKey = 'boloo:offline_cases';
      const existingCases = await AsyncStorage.getItem(casesKey);
      const cases = existingCases ? JSON.parse(existingCases) : [];
      cases.unshift(realCase);
      await AsyncStorage.setItem(casesKey, JSON.stringify(cases));

      console.log('[VoiceRecord] Real case saved offline:', realCase);

      // Navigate to success screen
      navigation.reset({
        index: 0,
        routes: [
          { name: 'Home' },
          {
            name: 'CaseSubmitted',
            params: { caseId, caseReference },
          },
        ],
      });
    } catch (error) {
      console.error('[VoiceRecord] Real submit error:', error);
      Alert.alert('Error', 'Failed to submit case. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Loading Overlay */}
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingCard}>
            <ActivityIndicator size="large" color={COLORS.primary} />
            <Text style={styles.loadingText}>
              {recordingUri && !isRecording ? 'Uploading & Transcribing...' : 'Processing complaint...'}
            </Text>
            <Text style={styles.loadingSubtext}>
              {recordingUri && !isRecording ? 'Speech-to-Text + AI Classification' : 'Classifying and submitting'}
            </Text>
          </View>
        </View>
      )}

      <View style={styles.content}>
        <Text style={styles.title}>Record Your Grievance</Text>
        <Text style={styles.subtitle}>
          Describe your issue in Hindi or English
        </Text>

        {/* Recording Status */}
        <View style={styles.recordingArea}>
          {isRecording && (
            <View style={styles.recordingIndicator}>
              <View style={styles.recordingDot} />
              <Text style={styles.recordingText}>Recording...</Text>
            </View>
          )}

          {/* Timer */}
          <Text style={styles.timer}>{formatTime(duration)}</Text>
          <Text style={styles.maxDuration}>
            Max: {formatTime(APP_CONFIG.maxAudioDuration)}
          </Text>

          {/* Record Button */}
          {!recordingUri && (
            <TouchableOpacity
              style={[
                styles.recordButton,
                isRecording && styles.recordButtonActive
              ]}
              onPress={isRecording ? stopRecording : startRecording}
              disabled={!permissionGranted}
            >
              <View style={[
                styles.recordButtonInner,
                isRecording && styles.recordButtonInnerActive
              ]} />
            </TouchableOpacity>
          )}

          {/* Playback Controls */}
          {recordingUri && !isRecording && (
            <View style={styles.playbackControls}>
              <TouchableOpacity
                style={styles.iconButton}
                onPress={playRecording}
              >
                <Text style={styles.iconButtonText}>
                  {isPlaying ? '⏸️' : '▶️'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.iconButton}
                onPress={deleteRecording}
              >
                <Text style={styles.iconButtonText}>🗑️</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Instructions */}
        {!recordingUri && !isRecording && (
          <Text style={styles.instructions}>
            Tap the button to start recording
          </Text>
        )}

        {isRecording && (
          <Text style={styles.instructions}>
            Tap again to stop recording
          </Text>
        )}

        {recordingUri && (
          <Text style={styles.instructions}>
            Play to review or continue
          </Text>
        )}

        {/* Continue Button */}
        {recordingUri && (
          <TouchableOpacity style={styles.button} onPress={handleContinue}>
            <Text style={styles.buttonText}>Continue</Text>
          </TouchableOpacity>
        )}

        {/* Test Mode Button */}
        {!recordingUri && !isRecording && (
          <TouchableOpacity
            style={styles.testModeButton}
            onPress={handleTestMode}
          >
            <Text style={styles.testModeText}>
              🧪 Test Without Recording
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.gray[600],
    textAlign: 'center',
    marginBottom: 48,
  },
  recordingArea: {
    alignItems: 'center',
    marginBottom: 32,
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: COLORS.error,
    marginRight: 8,
  },
  recordingText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.error,
  },
  timer: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: 8,
  },
  maxDuration: {
    fontSize: 14,
    color: COLORS.gray[500],
    marginBottom: 32,
  },
  recordButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: COLORS.white,
    borderWidth: 4,
    borderColor: COLORS.error,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  recordButtonActive: {
    backgroundColor: COLORS.error,
    borderColor: COLORS.error,
  },
  recordButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.error,
  },
  recordButtonInnerActive: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: COLORS.white,
  },
  playbackControls: {
    flexDirection: 'row',
    gap: 16,
  },
  iconButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  iconButtonText: {
    fontSize: 32,
  },
  instructions: {
    fontSize: 16,
    color: COLORS.gray[600],
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 48,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  testModeButton: {
    backgroundColor: COLORS.warning + '20',
    borderWidth: 2,
    borderColor: COLORS.warning,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
    marginTop: 16,
  },
  testModeText: {
    color: COLORS.warning,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  loadingCard: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    minWidth: 200,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginTop: 16,
    textAlign: 'center',
  },
  loadingSubtext: {
    fontSize: 14,
    color: COLORS.gray[600],
    marginTop: 8,
    textAlign: 'center',
  },
});
