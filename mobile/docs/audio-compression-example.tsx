/**
 * Audio Compression Usage Example
 *
 * This file demonstrates how to use the AudioRecorder component
 * with automatic compression in the Boloo app
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { AudioRecorder } from '../src/components/AudioRecorder';

/**
 * Example Screen: Farmer Voice Message
 */
export function FarmerMessageScreen() {
  const [uploadStatus, setUploadStatus] = useState<string>('Ready');

  const handleRecordingComplete = async (uri: string, fileSize: number) => {
    setUploadStatus('Uploading...');

    try {
      // Upload compressed audio to server
      const formData = new FormData();
      formData.append('audio', {
        uri,
        type: 'audio/m4a',
        name: 'farmer_message.m4a',
      } as any);

      const response = await fetch('https://api.boloo.app/messages/upload', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        setUploadStatus('Upload complete!');
        Alert.alert('Success', 'Your message has been sent!');
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      setUploadStatus('Upload failed');
      Alert.alert('Error', 'Failed to upload message. Please try again.');
      console.error('Upload error:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Record Farm Update</Text>
      <Text style={styles.subtitle}>
        Optimized for 2G/3G networks
      </Text>

      <AudioRecorder
        onRecordingComplete={handleRecordingComplete}
        maxDurationSeconds={300} // 5 minutes
        autoCompress={true} // Enable compression
      />

      <Text style={styles.status}>{uploadStatus}</Text>

      <View style={styles.infoBox}>
        <Text style={styles.infoTitle}>Benefits:</Text>
        <Text style={styles.infoText}>✓ 10x smaller file size</Text>
        <Text style={styles.infoText}>✓ Faster uploads on 2G/3G</Text>
        <Text style={styles.infoText}>✓ Reduced data costs</Text>
        <Text style={styles.infoText}>✓ Better battery life</Text>
      </View>
    </View>
  );
}

/**
 * Example: Custom Compression with Progress
 */
export function CustomCompressionExample() {
  const [compressionProgress, setCompressionProgress] = useState<string>('');

  const compressExistingAudio = async (audioUri: string) => {
    const { AudioCompressor, CompressionProgress } = require('../src/utils/AudioCompressor');

    const compressor = new AudioCompressor((progress: CompressionProgress) => {
      setCompressionProgress(
        `${progress.stage}: ${progress.progress}% - ${progress.message}`
      );
    });

    const result = await compressor.compressAudio(audioUri, {
      targetBitrate: 16000,
      sampleRate: 16000,
      numberOfChannels: 1,
      maxFileSizeMB: 1,
    });

    if (result.success && result.compressionRatio) {
      Alert.alert(
        'Compression Complete',
        `Original: ${result.originalSize} bytes\n` +
        `Compressed: ${result.compressedSize} bytes\n` +
        `Saved: ${Math.round((1 - result.compressionRatio) * 100)}%`
      );
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.progress}>{compressionProgress}</Text>
    </View>
  );
}

/**
 * Example: File Size Estimation
 */
export function FileSizeEstimationExample() {
  const { AudioCompressor } = require('../src/utils/AudioCompressor');

  const [duration, setDuration] = useState(60); // 1 minute

  const estimatedSize = AudioCompressor.estimateCompressedSize(duration);
  const formattedSize = formatBytes(estimatedSize);

  return (
    <View style={styles.container}>
      <Text style={styles.text}>
        Estimated size for {duration}s recording: {formattedSize}
      </Text>
    </View>
  );
}

/**
 * Example: Bandwidth Savings Calculator
 */
export function BandwidthSavingsExample() {
  const { estimateBandwidthSavings } = require('../src/utils/AudioCompressor');

  const originalSize = 5 * 1024 * 1024; // 5MB
  const compressedSize = 500 * 1024; // 500KB

  const savings = estimateBandwidthSavings(originalSize, compressedSize, '2g');

  return (
    <View style={styles.container}>
      <Text style={styles.infoTitle}>Upload Time on 2G:</Text>
      <Text style={styles.infoText}>Original: {savings.originalTime}s</Text>
      <Text style={styles.infoText}>Compressed: {savings.compressedTime}s</Text>
      <Text style={styles.infoText}>Time Saved: {savings.timeSaved}s</Text>
    </View>
  );
}

/**
 * Example: Cleanup Temporary Files
 */
export function CleanupExample() {
  const cleanupTempFiles = async () => {
    const { AudioCompressor } = require('../src/utils/AudioCompressor');

    try {
      await AudioCompressor.cleanupTempFiles();
      Alert.alert('Success', 'Temporary audio files cleaned up');
    } catch (error) {
      Alert.alert('Error', 'Failed to cleanup files');
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={cleanupTempFiles}>
        <Text>Clean Up Temp Files</Text>
      </TouchableOpacity>
    </View>
  );
}

// Helper function
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 24,
  },
  status: {
    fontSize: 16,
    color: '#007AFF',
    marginTop: 20,
    textAlign: 'center',
  },
  infoBox: {
    marginTop: 24,
    padding: 16,
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  progress: {
    fontSize: 14,
    color: '#007AFF',
    textAlign: 'center',
  },
  text: {
    fontSize: 16,
    color: '#333',
  },
});

export default FarmerMessageScreen;
