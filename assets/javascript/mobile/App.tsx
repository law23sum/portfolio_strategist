import React from 'react';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import AppNavigator from './src/navigation/AppNavigator';

// Configure Google Sign-In
GoogleSignin.configure({
  webClientId: 'YOUR_WEB_CLIENT_ID', // Replace with your actual Google Web Client ID
  iosClientId: 'YOUR_IOS_CLIENT_ID', // Replace with your actual Google iOS Client ID (required for iOS)
});

export default function App() {
  return <AppNavigator />;
}
