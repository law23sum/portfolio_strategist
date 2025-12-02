/**
 * NAVIGATION TEST VERSION
 * 
 * Use this to test if Navigation is working.
 * This only loads LoginScreen to test if navigation setup works.
 * 
 * To use: Temporarily rename App.tsx to App.tsx.backup
 * and rename this file to App.tsx
 */

import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import LoginScreen from './src/screens/auth/LoginScreen';

const Stack = createStackNavigator();

export default function App() {
  console.log('[TEST APP] Rendering navigation test app...');
  
  return (
    <SafeAreaProvider>
      <NavigationContainer
        onReady={() => console.log('[TEST] Navigation container ready')}
        onError={(error) => console.error('[TEST] Navigation error:', error)}
      >
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen 
            name="Login" 
            component={LoginScreen}
            initialParams={{ onLoginSuccess: () => console.log('Login success') }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

