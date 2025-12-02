import React from 'react';
import {ScrollView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

const PRIMARY_TASKS = [
  {
    title: 'Run Stock Analysis',
    description:
      'GBM, mean reversion and macro-aware models with ratios, AI commentary and exports.',
    icon: 'analytics',
    route: {screen: 'Analyze'},
  },
  {
    title: 'Loan Analysis',
    description: 'Evaluate stock-backed loans just like on the desktop suite.',
    icon: 'account-balance',
    route: {screen: 'Loan'},
  },
  {
    title: 'Saved Results',
    description: 'Jump to prior analyses and PDF-ready reporting.',
    icon: 'folder',
    route: {screen: 'Results'},
  },
];

const PLANNING_TOOLS = [
  {
    title: 'Investment Planner',
    description: 'Scenario planning and projections mirror the Investment Planner web workflow.',
    icon: 'timeline',
    route: {screen: 'InvestmentPlanner'},
  },
  {
    title: 'AI Assistance',
    description: 'Use the Chat tab for strategy questions mid-analysis.',
    icon: 'smart-toy',
    route: {screen: 'Chat'},
  },
];

export default function StockAnalysisScreen({navigation}: any) {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.heroEyebrow}>Stock Analysis</Text>
        <Text style={styles.heroTitle}>Full analytics from the desktop app, optimized for mobile.</Text>
        <Text style={styles.heroSubtitle}>
          Every forecast engine, ratio table, AI explanation and PDF export available on web is accessible here.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Core workflows</Text>
        {PRIMARY_TASKS.map(item => (
          <TouchableOpacity
            key={item.title}
            style={styles.card}
            onPress={() => navigation.navigate(item.route.screen, item.route.params)}
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
        <Text style={styles.sectionTitle}>Planning & guidance</Text>
        {PLANNING_TOOLS.map(item => (
          <TouchableOpacity
            key={item.title}
            style={styles.card}
            onPress={() => navigation.navigate(item.route.screen, item.route.params)}
          >
            <Icon name={item.icon} size={28} color="#0A84FF" style={styles.cardIcon} />
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardDescription}>{item.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#9C9C9C" />
          </TouchableOpacity>
        ))}
        <View style={styles.noteCard}>
          <Icon name="info" size={22} color="#0A84FF" />
          <Text style={styles.noteText}>
            Need the exact same ratios, Monte Carlo output or AI commentary as desktop? Start an analysis and the
            data pipeline matches the web app one-to-one.
          </Text>
        </View>
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
  noteCard: {
    flexDirection: 'row',
    backgroundColor: '#EAF2FF',
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
  },
  noteText: {
    marginLeft: 12,
    color: '#0A2F66',
    flex: 1,
    lineHeight: 20,
    fontSize: 14,
  },
});
