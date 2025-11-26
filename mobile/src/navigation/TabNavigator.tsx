/**
 * TabNavigator - Bottom tab navigation
 *
 * 5 tabs: Home, Public Feed, My Reports, Help, Profile
 * Hindi-first labels with icons
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/config';
import { View, Text, StyleSheet } from 'react-native';

// Screens
import HomeScreen from '../screens/HomeScreen';
import FeedScreen from '../screens/FeedScreen';
import MyCasesScreen from '../screens/MyCasesScreen';
import HelpScreen from '../screens/HelpScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Tab = createBottomTabNavigator();

export default function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          if (route.name === 'HomeTab') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'FeedTab') {
            iconName = focused ? 'people' : 'people-outline';
          } else if (route.name === 'MyReportsTab') {
            iconName = focused ? 'folder' : 'folder-outline';
          } else if (route.name === 'HelpTab') {
            iconName = focused ? 'help-circle' : 'help-circle-outline';
          } else if (route.name === 'ProfileTab') {
            iconName = focused ? 'person' : 'person-outline';
          } else {
            iconName = 'ellipse-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.gray[500],
        tabBarStyle: {
          height: 65,
          paddingBottom: 8,
          paddingTop: 8,
          borderTopWidth: 1,
          borderTopColor: COLORS.gray[200],
          backgroundColor: COLORS.white,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <View style={styles.labelContainer}>
              <Text style={[styles.labelHindi, focused && styles.labelActive]}>
                होम
              </Text>
              <Text style={[styles.labelEnglish, focused && styles.labelActiveEnglish]}>
                Home
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="FeedTab"
        component={FeedScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <View style={styles.labelContainer}>
              <Text style={[styles.labelHindi, focused && styles.labelActive]}>
                सार्वजनिक फ़ीड
              </Text>
              <Text style={[styles.labelEnglish, focused && styles.labelActiveEnglish]}>
                Public Feed
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="MyReportsTab"
        component={MyCasesScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <View style={styles.labelContainer}>
              <Text style={[styles.labelHindi, focused && styles.labelActive]}>
                मेरी रिपोर्ट्स
              </Text>
              <Text style={[styles.labelEnglish, focused && styles.labelActiveEnglish]}>
                My Reports
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="HelpTab"
        component={HelpScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <View style={styles.labelContainer}>
              <Text style={[styles.labelHindi, focused && styles.labelActive]}>
                सहायता
              </Text>
              <Text style={[styles.labelEnglish, focused && styles.labelActiveEnglish]}>
                Help
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <View style={styles.labelContainer}>
              <Text style={[styles.labelHindi, focused && styles.labelActive]}>
                प्रोफाइल
              </Text>
              <Text style={[styles.labelEnglish, focused && styles.labelActiveEnglish]}>
                Profile
              </Text>
            </View>
          ),
        }}
      />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  labelContainer: {
    alignItems: 'center',
  },
  labelHindi: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.gray[500],
  },
  labelEnglish: {
    fontSize: 9,
    color: COLORS.gray[400],
  },
  labelActive: {
    color: COLORS.primary,
  },
  labelActiveEnglish: {
    color: COLORS.primary + 'CC',
  },
});
