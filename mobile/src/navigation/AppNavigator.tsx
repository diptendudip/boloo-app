import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../types';
import { COLORS } from '../constants/config';

// Screens
import LoginScreen from '../screens/LoginScreen';
import VerifyOTPScreen from '../screens/VerifyOTPScreen';
import OnboardingScreen from '../components/OnboardingScreen';
import SplashScreen from '../components/SplashScreen';
import TabNavigator from './TabNavigator';
import IssueSelectionScreen from '../screens/IssueSelectionScreen';
import VoiceRecordScreen from '../screens/VoiceRecordScreen';
import MyCasesScreen from '../screens/MyCasesScreen';
import CaseSubmittedScreen from '../screens/CaseSubmittedScreen';
import UpdateAddressScreen from '../screens/UpdateAddressScreen';
import ChangePhoneScreen from '../screens/ChangePhoneScreen';

const Stack = createStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  const { isAuthenticated, isLoading, user, completeOnboarding } = useAuth();

  // Show splash screen while checking authentication
  if (isLoading) {
    return <SplashScreen message="Restoring session..." />;
  }

  const shouldShowOnboarding = isAuthenticated && user?.is_first_timer === true;

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: COLORS.primary,
          },
          headerTintColor: COLORS.white,
          headerTitleStyle: {
            fontWeight: '600',
          },
        }}
      >
        {!isAuthenticated ? (
          // Auth Stack
          <>
            <Stack.Screen
              name="Login"
              component={LoginScreen}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="VerifyOTP"
              component={VerifyOTPScreen}
              options={{
                title: 'Verify OTP',
                headerBackTitleVisible: false,
              }}
            />
          </>
        ) : shouldShowOnboarding ? (
          // Onboarding for first-time users
          <Stack.Screen
            name="Onboarding"
            options={{ headerShown: false }}
          >
            {() => <OnboardingScreen onComplete={completeOnboarding} />}
          </Stack.Screen>
        ) : (
          // Main App Stack
          <>
            <Stack.Screen
              name="Tabs"
              component={TabNavigator}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="IssueSelection"
              component={IssueSelectionScreen}
              options={{
                title: 'Select Issue',
                headerBackTitleVisible: false,
              }}
            />
            <Stack.Screen
              name="VoiceRecord"
              component={VoiceRecordScreen}
              options={{
                title: 'Record Grievance',
                headerBackTitleVisible: false,
              }}
            />
            <Stack.Screen
              name="CaseSubmitted"
              component={CaseSubmittedScreen}
              options={{
                title: 'शिकायत दर्ज',
                headerBackTitleVisible: false,
              }}
            />
            <Stack.Screen
              name="MyCases"
              component={MyCasesScreen}
              options={{
                title: 'मेरी रिपोर्ट्स',
                headerBackTitleVisible: false,
              }}
            />
            <Stack.Screen
              name="UpdateAddress"
              component={UpdateAddressScreen}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="ChangePhone"
              component={ChangePhoneScreen}
              options={{ headerShown: false }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
