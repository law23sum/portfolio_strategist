// Minimal test app to verify React Native is working
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function TestApp() {
  console.log('[TestApp] Rendering test app');
  
  return (
    <View style={styles.container}>
      <Text style={styles.text}>React Native is Working!</Text>
      <Text style={styles.subtext}>If you see this, the app is loading correctly.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#007AFF',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  subtext: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
});

