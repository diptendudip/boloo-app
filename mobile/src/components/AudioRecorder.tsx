/**
 * AudioRecorder.tsx
 *
 * Audio recording component with automatic compression
 * Optimized for rural connectivity and low-bandwidth networks
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { useAudioRecorder, useAudioPlayer, AudioModule, RecordingPresets, setAudioModeAsync } from 'expo-audio';
import * as FileSystem from 'expo-file-system';
import {
  AudioCompressor,
  CompressionProgress,
  CompressionResult,
  formatCompressionRatio,
  estimateBandwidthSavings,
} from '../utils/AudioCompressor';
import TranscriptionEditor from './TranscriptionEditor';

interface AudioRecorderProps {
  onRecordingComplete?: (uri: string, fileSize: number, transcription?: string) => void;
  maxDurationSeconds?: number;
  autoCompress?: boolean;
  enableTranscription?: boolean;
  apiBaseUrl?: string;
}

interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  uri?: string;
}

interface TranscriptionState {
  text: string;
  isTranscribing: boolean;
  confidence?: number;
  newWords: string[];
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onRecordingComplete,
  maxDurationSeconds = 300, // 5 minutes default
  autoCompress = true,
  enableTranscription = true,
  apiBaseUrl = 'http://localhost:3000',
}) => {
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const audioPlayer = useAudioPlayer();
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
  });
  const [compressionProgress, setCompressionProgress] = useState<CompressionProgress | null>(null);
  const [compressionResult, setCompressionResult] = useState<CompressionResult | null>(null);
  const [isCompressing, setIsCompressing] = useState(false);

  // Transcription state
  const [transcription, setTranscription] = useState<TranscriptionState>({
    text: '',
    isTranscribing: false,
    newWords: [],
  });
  const [showEditor, setShowEditor] = useState(false);
  const [finalTranscription, setFinalTranscription] = useState('');

  // Refs for transcription
  const transcriptionTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastTranscriptionTime = useRef(0);
  const typingAnimation = useRef(new Animated.Value(0)).current;

  // Initialize audio mode
  useEffect(() => {
    const initializeAudio = async () => {
      try {
        await AudioModule.requestRecordingPermissionsAsync();
        await setAudioModeAsync({
          playsInSilentMode: true,
          allowsRecording: true,
        });
      } catch (error) {
        console.error('Failed to initialize audio:', error);
        Alert.alert('Error', 'Failed to initialize audio recording');
      }
    };

    initializeAudio();

    // Cleanup handled automatically by expo-audio
  }, []);

  // Update duration timer and trigger transcription
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (recordingState.isRecording && !recordingState.isPaused) {
      interval = setInterval(() => {
        setRecordingState(prev => ({
          ...prev,
          duration: prev.duration + 1,
        }));

        // Trigger transcription every 2 seconds
        if (enableTranscription && recordingState.duration % 2 === 0) {
          transcribeAudioChunk();
        }

        // Auto-stop at max duration
        if (recordingState.duration >= maxDurationSeconds) {
          stopRecording();
        }
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [recordingState.isRecording, recordingState.isPaused, recordingState.duration, enableTranscription]);

  // Typing animation for transcription
  useEffect(() => {
    if (transcription.isTranscribing) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(typingAnimation, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(typingAnimation, {
            toValue: 0,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      typingAnimation.setValue(0);
    }
  }, [transcription.isTranscribing]);

  /**
   * Transcribe audio chunk during recording
   */
  const transcribeAudioChunk = async () => {
    if (!audioRecorder.isRecording || !enableTranscription) return;

    try {
      const currentTime = Date.now();

      // Avoid too frequent requests
      if (currentTime - lastTranscriptionTime.current < 1500) {
        return;
      }

      lastTranscriptionTime.current = currentTime;
      setTranscription(prev => ({ ...prev, isTranscribing: true }));

      // Get current recording URI
      if (audioRecorder.uri) {
        const uri = audioRecorder.uri;

        // Read audio file
        const audioData = await FileSystem.readAsStringAsync(uri!, {
          encoding: FileSystem.EncodingType.Base64,
        });

        // Call transcription API
        const response = await fetch(`${apiBaseUrl}/v1/ai/transcribe`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio: audioData,
            language: 'hi',
            partial: true,
          }),
        });

        if (response.ok) {
          const result = await response.json();

          // Extract new words
          const previousWords = transcription.text.split(' ');
          const newText = result.text || '';
          const allWords = newText.split(' ');
          const newWords = allWords.slice(previousWords.length);

          setTranscription(prev => ({
            ...prev,
            text: newText,
            confidence: result.confidence,
            newWords: newWords,
            isTranscribing: false,
          }));

          // Fade out new words highlighting after 3 seconds
          setTimeout(() => {
            setTranscription(prev => ({
              ...prev,
              newWords: [],
            }));
          }, 3000);
        }
      }
    } catch (error) {
      console.error('Transcription error:', error);
      setTranscription(prev => ({ ...prev, isTranscribing: false }));
    }
  };

  /**
   * Start audio recording with optimized settings
   */
  const startRecording = async () => {
    try {
      // Request permissions
      const { granted } = await AudioModule.requestRecordingPermissionsAsync();
      if (!granted) {
        Alert.alert('Permission Denied', 'Please enable microphone access');
        return;
      }

      // Configure audio mode
      await setAudioModeAsync({
        playsInSilentMode: true,
        allowsRecording: true,
      });

      // Start recording with preset options
      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();

      setRecordingState({
        isRecording: true,
        isPaused: false,
        duration: 0,
      });
      setCompressionResult(null);

      // Reset transcription
      setTranscription({
        text: '',
        isTranscribing: false,
        newWords: [],
      });
      setFinalTranscription('');

    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Error', 'Failed to start recording. Please try again.');
    }
  };

  /**
   * Pause recording
   */
  const pauseRecording = async () => {
    if (!audioRecorder.isRecording) return;

    try {
      await audioRecorder.pause();
      setRecordingState(prev => ({ ...prev, isPaused: true }));
    } catch (error) {
      console.error('Failed to pause recording:', error);
    }
  };

  /**
   * Resume recording
   */
  const resumeRecording = async () => {
    if (!audioRecorder.isPaused) return;

    try {
      audioRecorder.record();
      setRecordingState(prev => ({ ...prev, isPaused: false }));
    } catch (error) {
      console.error('Failed to resume recording:', error);
    }
  };

  /**
   * Stop recording and optionally compress
   */
  const stopRecording = async () => {
    if (!audioRecorder.isRecording) return;

    try {
      await audioRecorder.stop();
      const uri = audioRecorder.uri;

      setRecordingState(prev => ({
        ...prev,
        isRecording: false,
        uri,
      }));

      // Clear transcription timer
      if (transcriptionTimerRef.current) {
        clearTimeout(transcriptionTimerRef.current);
      }

      // Set final transcription
      setFinalTranscription(transcription.text);

      if (uri) {
        if (autoCompress) {
          await compressAudio(uri);
        } else {
          // Use original file
          const fileSize = 0; // Will be calculated in compression if needed
          onRecordingComplete?.(uri, fileSize, transcription.text);
        }
      }

    } catch (error) {
      console.error('Failed to stop recording:', error);
      Alert.alert('Error', 'Failed to save recording');
    }
  };

  /**
   * Compress recorded audio
   */
  const compressAudio = async (uri: string) => {
    setIsCompressing(true);
    setCompressionProgress(null);

    const compressor = new AudioCompressor((progress) => {
      setCompressionProgress(progress);
    });

    try {
      const result = await compressor.compressAudio(uri);
      setCompressionResult(result);

      if (result.success && result.compressedUri) {
        // Show compression results
        showCompressionResults(result);

        // Use compressed file with transcription
        onRecordingComplete?.(
          result.compressedUri,
          result.compressedSize || 0,
          finalTranscription
        );
      } else {
        // Fallback to original file on compression failure
        Alert.alert(
          'Compression Warning',
          'Audio compression failed. Using original file.',
          [
            {
              text: 'OK',
              onPress: () => onRecordingComplete?.(uri, result.originalSize, finalTranscription),
            },
          ]
        );
      }
    } catch (error) {
      console.error('Compression error:', error);
      Alert.alert(
        'Compression Error',
        'Failed to compress audio. Using original file.',
        [
          {
            text: 'OK',
            onPress: () => onRecordingComplete?.(uri, 0, finalTranscription),
          },
        ]
      );
    } finally {
      setIsCompressing(false);
    }
  };

  /**
   * Show compression results to user
   */
  const showCompressionResults = (result: CompressionResult) => {
    if (!result.success || !result.compressionRatio) return;

    const savings = estimateBandwidthSavings(
      result.originalSize,
      result.compressedSize || result.originalSize,
      '2g'
    );

    const message = [
      `Original: ${formatBytes(result.originalSize)}`,
      `Compressed: ${formatBytes(result.compressedSize || 0)}`,
      `Saved: ${formatCompressionRatio(result.compressionRatio)}`,
      ``,
      `Upload time on 2G:`,
      `Before: ${savings.originalTime}s`,
      `After: ${savings.compressedTime}s`,
      `Saved: ${savings.timeSaved}s`,
    ].join('\n');

    Alert.alert('Compression Complete', message);
  };

  /**
   * Format duration as MM:SS
   */
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  /**
   * Format bytes to human-readable size
   */
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  /**
   * Estimate file size based on current duration
   */
  const estimateFileSize = (): string => {
    const size = AudioCompressor.estimateCompressedSize(recordingState.duration);
    return formatBytes(size);
  };

  /**
   * Handle transcription edit
   */
  const handleEditTranscription = () => {
    setShowEditor(true);
  };

  /**
   * Handle transcription save
   */
  const handleSaveTranscription = (editedText: string) => {
    setFinalTranscription(editedText);
    setTranscription(prev => ({
      ...prev,
      text: editedText,
    }));
    setShowEditor(false);
  };

  /**
   * Render highlighted transcription text
   */
  const renderTranscriptionText = () => {
    const words = transcription.text.split(' ');

    return (
      <Text style={styles.transcriptionText}>
        {words.map((word, index) => {
          const isNew = transcription.newWords.includes(word);
          return (
            <Text
              key={index}
              style={[
                styles.transcriptionWord,
                isNew && styles.transcriptionWordNew,
              ]}
            >
              {word}{' '}
            </Text>
          );
        })}
      </Text>
    );
  };

  return (
    <View style={styles.container}>
      {/* Recording Status */}
      <View style={styles.statusContainer}>
        <View style={styles.statusHeader}>
          <Text style={styles.statusText}>
            {recordingState.isRecording
              ? recordingState.isPaused
                ? 'Paused'
                : 'Recording...'
              : 'Ready to Record'}
          </Text>
          {recordingState.isRecording && (
            <Text style={styles.durationText}>
              {formatDuration(recordingState.duration)} / {formatDuration(maxDurationSeconds)}
            </Text>
          )}
        </View>
        {recordingState.isRecording && (
          <Text style={styles.sizeText}>
            Estimated Size: {estimateFileSize()}
          </Text>
        )}
      </View>

      {/* Transcription Display */}
      {enableTranscription && (recordingState.isRecording || transcription.text.length > 0) && (
        <View style={styles.transcriptionContainer}>
          <View style={styles.transcriptionHeader}>
            <Text style={styles.transcriptionTitle}>
              Live Transcription
            </Text>
            {transcription.isTranscribing && (
              <View style={styles.typingIndicator}>
                <Animated.View
                  style={[
                    styles.typingDot,
                    {
                      opacity: typingAnimation,
                    },
                  ]}
                />
                <Animated.View
                  style={[
                    styles.typingDot,
                    {
                      opacity: typingAnimation,
                    },
                  ]}
                />
                <Animated.View
                  style={[
                    styles.typingDot,
                    {
                      opacity: typingAnimation,
                    },
                  ]}
                />
              </View>
            )}
            {transcription.confidence && (
              <Text style={styles.confidenceText}>
                {Math.round(transcription.confidence * 100)}% confident
              </Text>
            )}
          </View>

          <View style={styles.transcriptionBox}>
            {transcription.text.length > 0 ? (
              renderTranscriptionText()
            ) : (
              <Text style={styles.transcriptionPlaceholder}>
                Transcription will appear here...
              </Text>
            )}
          </View>

          {!recordingState.isRecording && transcription.text.length > 0 && (
            <TouchableOpacity
              style={styles.editTranscriptionButton}
              onPress={handleEditTranscription}
            >
              <Text style={styles.editTranscriptionButtonText}>
                ✏️ Edit Transcription / संपादित करें
              </Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Compression Progress */}
      {isCompressing && compressionProgress && (
        <View style={styles.compressionContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.compressionText}>
            {compressionProgress.message}
          </Text>
          <Text style={styles.compressionProgress}>
            {compressionProgress.progress}%
          </Text>
        </View>
      )}

      {/* Recording Controls */}
      <View style={styles.controlsContainer}>
        {!recordingState.isRecording ? (
          <TouchableOpacity
            style={[styles.button, styles.recordButton]}
            onPress={startRecording}
          >
            <Text style={styles.buttonText}>Start Recording</Text>
          </TouchableOpacity>
        ) : (
          <>
            <TouchableOpacity
              style={[styles.button, styles.pauseButton]}
              onPress={recordingState.isPaused ? resumeRecording : pauseRecording}
            >
              <Text style={styles.buttonText}>
                {recordingState.isPaused ? 'Resume' : 'Pause'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.stopButton]}
              onPress={stopRecording}
              disabled={isCompressing}
            >
              <Text style={styles.buttonText}>Stop</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Compression Info */}
      {compressionResult && compressionResult.success && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>Compression Results:</Text>
          <Text style={styles.resultText}>
            Original: {formatBytes(compressionResult.originalSize)}
          </Text>
          <Text style={styles.resultText}>
            Compressed: {formatBytes(compressionResult.compressedSize || 0)}
          </Text>
          {compressionResult.compressionRatio && (
            <Text style={styles.resultText}>
              Saved: {formatCompressionRatio(compressionResult.compressionRatio)}
            </Text>
          )}
        </View>
      )}

      {/* Transcription Editor Modal */}
      <TranscriptionEditor
        visible={showEditor}
        initialText={finalTranscription || transcription.text}
        recordingId={recordingState.uri}
        onSave={handleSaveTranscription}
        onCancel={() => setShowEditor(false)}
        language="hi"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusContainer: {
    marginBottom: 20,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  durationText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
    fontVariant: ['tabular-nums'],
  },
  sizeText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  transcriptionContainer: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  transcriptionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  transcriptionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  typingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#007AFF',
  },
  confidenceText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '500',
  },
  transcriptionBox: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    maxHeight: 200,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  transcriptionText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  transcriptionWord: {
    color: '#333',
  },
  transcriptionWordNew: {
    backgroundColor: '#FFE082',
    color: '#F57C00',
    fontWeight: '600',
  },
  transcriptionPlaceholder: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
  },
  editTranscriptionButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginTop: 12,
    alignItems: 'center',
  },
  editTranscriptionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  compressionContainer: {
    backgroundColor: '#F5F5F5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  compressionText: {
    fontSize: 14,
    color: '#333',
    marginTop: 8,
  },
  compressionProgress: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 4,
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    minWidth: 120,
    alignItems: 'center',
  },
  recordButton: {
    backgroundColor: '#007AFF',
  },
  pauseButton: {
    backgroundColor: '#FF9500',
  },
  stopButton: {
    backgroundColor: '#FF3B30',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultContainer: {
    marginTop: 20,
    padding: 12,
    backgroundColor: '#E8F5E9',
    borderRadius: 8,
  },
  resultTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2E7D32',
    marginBottom: 8,
  },
  resultText: {
    fontSize: 12,
    color: '#2E7D32',
    marginBottom: 4,
  },
});

export default AudioRecorder;
