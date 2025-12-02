import React from 'react';
import {ScrollView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

const DOCUMENT_TOOLS = [
  {
    title: 'Upload Documents',
    description: 'PDF, images and statements sync with the Records module used on web.',
    icon: 'cloud-upload',
    route: {screen: 'Upload'},
  },
  {
    title: 'Document Explorer',
    description: 'Browse, filter and inspect imported data the same way you do on desktop.',
    icon: 'description',
    route: {screen: 'Explorer'},
  },
  {
    title: 'Insights',
    description: 'AI-generated summaries and KPIs from the Insights experience.',
    icon: 'insights',
    route: {screen: 'Insights'},
  },
];

const LINKED_SERVICES = [
  {
    title: 'Linked Accounts',
    description: 'View and manage Plaid-linked institutions.',
    icon: 'account-balance',
    route: {screen: 'LinkedAccounts'},
  },
  {
    title: 'Link a new account',
    description: 'Kick off Plaid Link directly from mobile.',
    icon: 'link',
    route: {screen: 'LinkedAccounts'},
  },
];

export default function RecordsScreen({navigation}: any) {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.heroEyebrow}>Financial Records</Text>
        <Text style={styles.heroTitle}>Keep every document and connection tidy.</Text>
        <Text style={styles.heroSubtitle}>
          All data-management tools from the Portfolio Strategist web app live here: uploads, explorer,
          AI insights and account aggregation.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Document tools</Text>
        {DOCUMENT_TOOLS.map(item => (
          <TouchableOpacity
            key={item.title}
            style={styles.card}
            onPress={() => navigation.navigate(item.route.screen)}
          >
            <Icon name={item.icon} size={28} color="#0A84FF" style={styles.cardIcon} />
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardDescription}>{item.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#9C9C9C" />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Linked services</Text>
        {LINKED_SERVICES.map(item => (
          <TouchableOpacity
            key={item.title}
            style={styles.card}
            onPress={() => navigation.navigate(item.route.screen)}
          >
            <Icon name={item.icon} size={28} color="#0A84FF" style={styles.cardIcon} />
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardDescription}>{item.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#9C9C9C" />
          </TouchableOpacity>
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
  hero: {
    backgroundColor: '#0A84FF',
    paddingTop: 64,
    paddingBottom: 32,
    paddingHorizontal: 24,
  },
  heroEyebrow: {
    color: '#D7EAFF',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  heroTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
  },
  heroSubtitle: {
    color: '#E6F1FF',
    fontSize: 15,
    lineHeight: 22,
  },
  section: {
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 16,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 10,
    elevation: 2,
  },
  cardIcon: {
    marginRight: 16,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  cardDescription: {
    marginTop: 4,
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});
