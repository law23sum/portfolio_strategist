/**
 * MINIMAL TEST VERSION
 * 
 * Use this to test if React Native is working at all.
 * If this shows "Hello World", then React Native is working.
 * If this is blank, there's a deeper setup issue.
 * 
 * To use: Temporarily rename App.tsx to App.tsx.backup
 * and rename this file to App.tsx
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function App() {
  console.log('[TEST APP] Rendering minimal test app...');
  
  return (
    <SafeAreaProvider>
      <View style={styles.container}>
        <Text style={styles.text}>Hello World!</Text>
        <Text style={styles.subtext}>If you see this, React Native is working</Text>
        <Text style={styles.debug}>Check console for logs</Text>
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 20,
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtext: {
    fontSize: 16,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  debug: {
    fontSize: 12,
    color: '#999',
    marginTop: 16,
  },
});

