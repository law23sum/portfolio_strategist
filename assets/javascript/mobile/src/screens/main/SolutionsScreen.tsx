import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

export default function SolutionsScreen({ navigation }: any) {
  const solutions = [
    {
      title: 'Budget Planning',
      description: 'Create and manage your budget with tax, expense, and debt calculations',
      icon: 'account-balance-wallet',
      color: '#4CAF50',
      onPress: () => navigation.navigate('BudgetPlanner'),
    },
    {
      title: 'Investment & Savings',
      description: 'Assess stocks, savings, CDs, and bonds with detailed forecasts',
      icon: 'savings',
      color: '#2196F3',
      onPress: () => navigation.navigate('InvestmentSavings', { screen: 'InvestmentSavingsMain' }),
    },
    {
      title: 'Stock Analysis',
      description: 'Analyze stocks and create investment plans with forecasts',
      icon: 'trending-up',
      color: '#FF9800',
      onPress: () => navigation.navigate('StockAnalysis', { screen: 'StockMain' }),
    },
    {
      title: 'Loan Analysis',
      description: 'Analyze personal loans and compare loan options',
      icon: 'account-balance',
      color: '#9C27B0',
      onPress: () => navigation.navigate('StockAnalysis', { screen: 'Loan' }),
    },
    {
      title: 'Financial Records',
      description: 'Upload documents, view insights, and explore your financial data',
      icon: 'description',
      color: '#00BCD4',
      onPress: () => navigation.navigate('Records', { screen: 'RecordsMain' }),
    },
    {
      title: 'AI Financial Services',
      description: 'Get personalized financial advice from our AI assistant',
      icon: 'chat',
      color: '#E91E63',
      onPress: () => navigation.navigate('Chat'),
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Solutions</Text>
        <Text style={styles.subtitle}>
          Comprehensive financial solutions tailored for you
        </Text>

        {solutions.map((solution, index) => (
          <TouchableOpacity
            key={index}
            style={styles.solutionCard}
            onPress={solution.onPress}
            activeOpacity={0.7}
          >
            <View style={[styles.iconContainer, { backgroundColor: `${solution.color}15` }]}>
              <Icon name={solution.icon} size={32} color={solution.color} />
            </View>
            <View style={styles.solutionContent}>
              <Text style={styles.solutionTitle}>{solution.title}</Text>
              <Text style={styles.solutionDescription}>{solution.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>
        ))}

        <View style={styles.infoCard}>
          <Icon name="info" size={24} color="#007AFF" />
          <Text style={styles.infoText}>
            Our solutions help you create, aggregate, report, and predict your financial future
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
  content: {
    padding: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
  },
  solutionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  solutionContent: {
    flex: 1,
  },
  solutionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  solutionDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
  },
  infoText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
});



