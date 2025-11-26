/**
 * OnboardingScreen Component
 *
 * 4-slide onboarding flow for first-time users
 * Hindi-first with visual illustrations
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  FlatList,
  ViewToken,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/config';

const { width, height } = Dimensions.get('window');

interface OnboardingSlide {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  titleHindi: string;
  titleEnglish: string;
  descriptionHindi: string;
  descriptionEnglish: string;
  color: string;
}

const SLIDES: OnboardingSlide[] = [
  {
    id: '1',
    icon: 'megaphone-outline',
    titleHindi: 'अपनी समस्या बताएं',
    titleEnglish: 'Report Your Issues',
    descriptionHindi: 'अपनी समस्याओं को आसानी से बोलकर या लिखकर रिपोर्ट करें',
    descriptionEnglish: 'Easily report your grievances by speaking or typing',
    color: COLORS.primary,
  },
  {
    id: '2',
    icon: 'mic-outline',
    titleHindi: 'हिंदी में बोलें',
    titleEnglish: 'Speak in Hindi',
    descriptionHindi: 'आप अपनी भाषा में बात कर सकते हैं - लिखना जरूरी नहीं',
    descriptionEnglish: 'Speak in your language - no need to type',
    color: '#FF6B6B',
  },
  {
    id: '3',
    icon: 'time-outline',
    titleHindi: 'स्टेटस देखें',
    titleEnglish: 'Track Status',
    descriptionHindi: 'अपनी शिकायत का स्टेटस हर समय देख सकते हैं',
    descriptionEnglish: 'Track your complaint status anytime',
    color: '#4ECDC4',
  },
  {
    id: '4',
    icon: 'checkmark-circle-outline',
    titleHindi: 'समाधान पाएं',
    titleEnglish: 'Get Solutions',
    descriptionHindi: 'सरकार आपकी समस्या का तुरंत समाधान करेगी',
    descriptionEnglish: 'Government will resolve your issues promptly',
    color: '#95E1D3',
  },
];

interface OnboardingScreenProps {
  onComplete: () => void;
}

export default function OnboardingScreen({ onComplete }: OnboardingScreenProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  const onViewableItemsChanged = useRef(({ viewableItems }: { viewableItems: ViewToken[] }) => {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index || 0);
    }
  }).current;

  const viewabilityConfig = useRef({
    itemVisiblePercentThreshold: 50,
  }).current;

  const handleNext = () => {
    if (currentIndex < SLIDES.length - 1) {
      flatListRef.current?.scrollToIndex({ index: currentIndex + 1 });
    } else {
      onComplete();
    }
  };

  const handleSkip = () => {
    onComplete();
  };

  const renderSlide = ({ item }: { item: OnboardingSlide }) => (
    <View style={[styles.slide, { backgroundColor: item.color + '10' }]}>
      <View style={[styles.iconContainer, { backgroundColor: item.color }]}>
        <Ionicons name={item.icon} size={80} color={COLORS.white} />
      </View>

      <View style={styles.textContainer}>
        <Text style={styles.titleHindi}>{item.titleHindi}</Text>
        <Text style={styles.titleEnglish}>{item.titleEnglish}</Text>
        <Text style={styles.descriptionHindi}>{item.descriptionHindi}</Text>
        <Text style={styles.descriptionEnglish}>{item.descriptionEnglish}</Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Skip Button */}
      <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
        <Text style={styles.skipText}>
          छोड़ें / Skip
        </Text>
      </TouchableOpacity>

      {/* Slides */}
      <FlatList
        ref={flatListRef}
        data={SLIDES}
        renderItem={renderSlide}
        keyExtractor={(item) => item.id}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
      />

      {/* Pagination Dots */}
      <View style={styles.pagination}>
        {SLIDES.map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              index === currentIndex && styles.dotActive,
            ]}
          />
        ))}
      </View>

      {/* Next/Done Button */}
      <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
        <Text style={styles.nextTextHindi}>
          {currentIndex === SLIDES.length - 1 ? 'शुरू करें' : 'आगे'}
        </Text>
        <Text style={styles.nextTextEnglish}>
          {currentIndex === SLIDES.length - 1 ? 'Get Started' : 'Next'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  skipButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    zIndex: 10,
    paddingHorizontal: 20,
    paddingVertical: 14,
    minWidth: 48,
    minHeight: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  skipText: {
    fontSize: 14,
    color: COLORS.gray[600],
    fontWeight: '500',
  },
  slide: {
    width: width,
    height: height - 200,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  iconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  textContainer: {
    alignItems: 'center',
  },
  titleHindi: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    textAlign: 'center',
    marginBottom: 8,
  },
  titleEnglish: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.gray[700],
    textAlign: 'center',
    marginBottom: 20,
  },
  descriptionHindi: {
    fontSize: 16,
    color: COLORS.gray[700],
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 8,
  },
  descriptionEnglish: {
    fontSize: 14,
    color: COLORS.gray[500],
    textAlign: 'center',
    lineHeight: 20,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.gray[300],
    marginHorizontal: 4,
  },
  dotActive: {
    width: 24,
    backgroundColor: COLORS.primary,
  },
  nextButton: {
    backgroundColor: COLORS.primary,
    marginHorizontal: 20,
    marginBottom: 40,
    borderRadius: 12,
    paddingVertical: 18,
    minHeight: 56,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  nextTextHindi: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 2,
  },
  nextTextEnglish: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
  },
});
