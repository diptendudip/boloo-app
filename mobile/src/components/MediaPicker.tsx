/**
 * MediaPicker Component
 *
 * Handles photo/document selection from camera or gallery
 * Supports image compression for rural connectivity
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';
import { COLORS } from '../constants/config';

interface MediaFile {
  uri: string;
  type: 'image' | 'document';
  name: string;
  size?: number;
}

interface MediaPickerProps {
  onMediaSelected: (files: MediaFile[]) => void;
  maxFiles?: number;
  allowCamera?: boolean;
  allowGallery?: boolean;
  allowDocuments?: boolean;
}

export default function MediaPicker({
  onMediaSelected,
  maxFiles = 5,
  allowCamera = true,
  allowGallery = true,
  allowDocuments = true,
}: MediaPickerProps) {
  const [selectedMedia, setSelectedMedia] = useState<MediaFile[]>([]);

  const requestPermissions = async () => {
    if (allowCamera) {
      const cameraPermission = await ImagePicker.requestCameraPermissionsAsync();
      if (cameraPermission.status !== 'granted') {
        Alert.alert(
          'कैमरा की अनुमति चाहिए',
          'Camera Permission Required',
          [{ text: 'ठीक है / OK' }]
        );
        return false;
      }
    }

    if (allowGallery) {
      const galleryPermission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (galleryPermission.status !== 'granted') {
        Alert.alert(
          'गैलरी की अनुमति चाहिए',
          'Gallery Permission Required',
          [{ text: 'ठीक है / OK' }]
        );
        return false;
      }
    }

    return true;
  };

  const handleTakePhoto = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    if (selectedMedia.length >= maxFiles) {
      Alert.alert(
        `अधिकतम ${maxFiles} फाइलें`,
        `Maximum ${maxFiles} files allowed`,
        [{ text: 'ठीक है / OK' }]
      );
      return;
    }

    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.5, // Compress for rural connectivity (50% quality)
      });

      if (!result.canceled && result.assets[0]) {
        const newMedia: MediaFile = {
          uri: result.assets[0].uri,
          type: 'image',
          name: `photo_${Date.now()}.jpg`,
          size: result.assets[0].fileSize,
        };
        const updatedMedia = [...selectedMedia, newMedia];
        setSelectedMedia(updatedMedia);
        onMediaSelected(updatedMedia);
      }
    } catch (error) {
      console.error('Camera error:', error);
      Alert.alert(
        'कैमरा में समस्या',
        'Camera Error',
        [{ text: 'ठीक है / OK' }]
      );
    }
  };

  const handlePickFromGallery = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    if (selectedMedia.length >= maxFiles) {
      Alert.alert(
        `अधिकतम ${maxFiles} फाइलें`,
        `Maximum ${maxFiles} files allowed`,
        [{ text: 'ठीक है / OK' }]
      );
      return;
    }

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsMultipleSelection: true,
        quality: 0.5, // Compress for rural connectivity
        selectionLimit: maxFiles - selectedMedia.length,
      });

      if (!result.canceled && result.assets.length > 0) {
        const newMedia: MediaFile[] = result.assets.map((asset, index) => ({
          uri: asset.uri,
          type: 'image' as const,
          name: `photo_${Date.now()}_${index}.jpg`,
          size: asset.fileSize,
        }));
        const updatedMedia = [...selectedMedia, ...newMedia];
        setSelectedMedia(updatedMedia);
        onMediaSelected(updatedMedia);
      }
    } catch (error) {
      console.error('Gallery error:', error);
      Alert.alert(
        'गैलरी में समस्या',
        'Gallery Error',
        [{ text: 'ठीक है / OK' }]
      );
    }
  };

  const handlePickDocument = async () => {
    if (selectedMedia.length >= maxFiles) {
      Alert.alert(
        `अधिकतम ${maxFiles} फाइलें`,
        `Maximum ${maxFiles} files allowed`,
        [{ text: 'ठीक है / OK' }]
      );
      return;
    }

    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        multiple: false,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];

        // Check file size (max 10MB)
        if (asset.size && asset.size > 10 * 1024 * 1024) {
          Alert.alert(
            'फाइल बहुत बड़ी है',
            'File too large (max 10MB)',
            [{ text: 'ठीक है / OK' }]
          );
          return;
        }

        const newMedia: MediaFile = {
          uri: asset.uri,
          type: 'document',
          name: asset.name,
          size: asset.size,
        };
        const updatedMedia = [...selectedMedia, newMedia];
        setSelectedMedia(updatedMedia);
        onMediaSelected(updatedMedia);
      }
    } catch (error) {
      console.error('Document picker error:', error);
      Alert.alert(
        'डॉक्यूमेंट में समस्या',
        'Document Error',
        [{ text: 'ठीक है / OK' }]
      );
    }
  };

  const handleRemoveMedia = (index: number) => {
    const updatedMedia = selectedMedia.filter((_, i) => i !== index);
    setSelectedMedia(updatedMedia);
    onMediaSelected(updatedMedia);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <View style={styles.container}>
      {/* Action Buttons */}
      <View style={styles.buttonsContainer}>
        {allowCamera && (
          <TouchableOpacity style={styles.actionButton} onPress={handleTakePhoto}>
            <Ionicons name="camera-outline" size={24} color={COLORS.primary} />
            <Text style={styles.buttonTextHindi}>फोटो लें</Text>
            <Text style={styles.buttonTextEnglish}>Take Photo</Text>
          </TouchableOpacity>
        )}

        {allowGallery && (
          <TouchableOpacity style={styles.actionButton} onPress={handlePickFromGallery}>
            <Ionicons name="images-outline" size={24} color={COLORS.primary} />
            <Text style={styles.buttonTextHindi}>गैलरी</Text>
            <Text style={styles.buttonTextEnglish}>Gallery</Text>
          </TouchableOpacity>
        )}

        {allowDocuments && (
          <TouchableOpacity style={styles.actionButton} onPress={handlePickDocument}>
            <Ionicons name="document-outline" size={24} color={COLORS.primary} />
            <Text style={styles.buttonTextHindi}>डॉक्यूमेंट</Text>
            <Text style={styles.buttonTextEnglish}>Document</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Selected Media */}
      {selectedMedia.length > 0 && (
        <ScrollView horizontal style={styles.mediaPreview} showsHorizontalScrollIndicator={false}>
          {selectedMedia.map((media, index) => (
            <View key={index} style={styles.mediaItem}>
              {media.type === 'image' ? (
                <Image source={{ uri: media.uri }} style={styles.thumbnail} />
              ) : (
                <View style={styles.documentThumbnail}>
                  <Ionicons name="document-text" size={40} color={COLORS.gray[400]} />
                </View>
              )}

              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => handleRemoveMedia(index)}
              >
                <Ionicons name="close-circle" size={24} color={COLORS.error} />
              </TouchableOpacity>

              <Text style={styles.fileName} numberOfLines={1}>
                {media.name}
              </Text>
              {media.size && (
                <Text style={styles.fileSize}>{formatFileSize(media.size)}</Text>
              )}
            </View>
          ))}
        </ScrollView>
      )}

      {/* Info Text */}
      <Text style={styles.infoText}>
        💡 {maxFiles - selectedMedia.length} और फाइलें जोड़ सकते हैं (अधिकतम {maxFiles})
      </Text>
      <Text style={styles.infoTextEnglish}>
        You can add {maxFiles - selectedMedia.length} more files (max {maxFiles})
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.white,
    borderRadius: 12,
  },
  buttonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  actionButton: {
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.primary + '10',
    borderRadius: 8,
    minWidth: 100,
  },
  buttonTextHindi: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginTop: 8,
  },
  buttonTextEnglish: {
    fontSize: 11,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  mediaPreview: {
    marginBottom: 12,
  },
  mediaItem: {
    marginRight: 12,
    width: 100,
  },
  thumbnail: {
    width: 100,
    height: 100,
    borderRadius: 8,
    backgroundColor: COLORS.gray[200],
  },
  documentThumbnail: {
    width: 100,
    height: 100,
    borderRadius: 8,
    backgroundColor: COLORS.gray[200],
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: COLORS.white,
    borderRadius: 12,
  },
  fileName: {
    fontSize: 11,
    color: COLORS.gray[700],
    marginTop: 4,
  },
  fileSize: {
    fontSize: 10,
    color: COLORS.gray[500],
  },
  infoText: {
    fontSize: 13,
    color: COLORS.gray[700],
    textAlign: 'center',
  },
  infoTextEnglish: {
    fontSize: 11,
    color: COLORS.gray[500],
    textAlign: 'center',
    marginTop: 2,
  },
});
