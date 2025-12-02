import React from 'react';
import {ScrollView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

const SOLUTION_GROUPS = [
  {
    title: 'Budget Planner',
    description:
      'The same budgeting, tax, expense and debt worksheets from the web experience, optimized for touch.',
    icon: 'account-balance-wallet',
    route: 'BudgetPlanner',
  },
  {
    title: 'Investment & Savings',
    description:
      'Stocks, savings, CD and bond assessments with portfolio forecasts, matching the desktop workflows.',
    icon: 'savings',
    route: 'InvestmentSavings',
  },
  {
    title: 'AI Solutions',
    description:
      'AI assistant mirrors the site-wide chat experience for financial planning and answering “what-if” questions.',
    icon: 'smart-toy',
    route: 'Chat',
  },
];

const SECONDARY = [
  {
    title: 'Portfolio Management',
    description: 'Review allocations, rebalance suggestions and strategy notes.',
    icon: 'pie-chart',
  },
  {
    title: 'Retirement Planning',
    description: 'Project scenarios and track milestones consistent with the web portal.',
    icon: 'timeline',
  },
];

export default function SolutionsScreen({navigation}: any) {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.heroEyebrow}>Solutions Hub</Text>
        <Text style={styles.heroTitle}>Strategic tools, same as the web.</Text>
        <Text style={styles.heroSubtitle}>
          Budget planning, investment planners, retirement projections and AI support are available in one tidy mobile hub.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Primary solutions</Text>
        {SOLUTION_GROUPS.map(group => (
          <TouchableOpacity
            key={group.title}
            style={styles.card}
            onPress={() => navigation.navigate(group.route as never)}
          >
            <Icon name={group.icon} size={28} color="#0A84FF" style={styles.cardIcon} />
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>{group.title}</Text>
              <Text style={styles.cardDescription}>{group.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#9C9C9C" />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Supporting experiences</Text>
        {SECONDARY.map(item => (
          <View key={item.title} style={styles.secondaryCard}>
            <Icon name={item.icon} size={24} color="#0A84FF" />
            <View style={styles.secondaryContent}>
              <Text style={styles.secondaryTitle}>{item.title}</Text>
              <Text style={styles.secondaryDescription}>{item.description}</Text>
            </View>
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
  secondaryCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 10,
    elevation: 1,
  },
  secondaryContent: {
    marginLeft: 12,
    flex: 1,
  },
  secondaryTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
  },
  secondaryDescription: {
    marginTop: 4,
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
  },
});
