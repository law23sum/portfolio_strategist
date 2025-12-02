import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import AppIcon from '../../components/AppIcon';

/**
 * Test screen to verify all icons are loading correctly
 * Add this to your navigation to test: navigation.navigate('IconTest')
 */
export default function IconTestScreen() {
  const icons = [
    { name: 'dashboard', label: 'Dashboard' },
    { name: 'records', label: 'Records' },
    { name: 'stocks', label: 'Stocks' },
    { name: 'solutions', label: 'Solutions' },
    { name: 'chat', label: 'Chat' },
    { name: 'profile', label: 'Profile' },
    { name: 'upload', label: 'Upload' },
    { name: 'search', label: 'Search' },
    { name: 'person', label: 'Person' },
    { name: 'add', label: 'Add' },
    { name: 'edit', label: 'Edit' },
    { name: 'delete', label: 'Delete' },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Icon Test Screen</Text>
        <Text style={styles.subtitle}>Verify all icons are loading</Text>
      </View>
      
      <View style={styles.grid}>
        {icons.map((icon) => (
          <View key={icon.name} style={styles.iconItem}>
            <AppIcon name={icon.name} size={48} />
            <Text style={styles.label}>{icon.label}</Text>
            <Text style={styles.name}>{icon.name}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    justifyContent: 'space-around',
  },
  iconItem: {
    width: '30%',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  label: {
    marginTop: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  name: {
    marginTop: 4,
    fontSize: 12,
    color: '#666',
  },
});

