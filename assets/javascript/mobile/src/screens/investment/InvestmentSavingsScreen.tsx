import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function InvestmentSavingsScreen({ navigation }: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState<any>(null);

  const loadData = async () => {
    try {
      const response = await apiService.getInvestmentSavingsSummary();
      if (response.data) {
        setSummary(response.data);
      }
    } catch (error) {
      console.error('Error loading investment & savings:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Investment & Savings</Text>
        <Text style={styles.subtitle}>Manage your investment assessments</Text>
      </View>

      <View style={styles.content}>
        {/* Assessment Types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Assessment Types</Text>
          
          <TouchableOpacity
            style={styles.assessmentCard}
            onPress={() => navigation.navigate('StocksAssessment')}
          >
            <View style={[styles.iconContainer, { backgroundColor: '#2196F315' }]}>
              <Icon name="trending-up" size={32} color="#2196F3" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>Stocks Assessment</Text>
              <Text style={styles.cardDescription}>
                Analyze and forecast stock investments
              </Text>
              {summary?.summary?.stocks && (
                <Text style={styles.cardCount}>
                  {summary.summary.stocks.count} assessment{summary.summary.stocks.count !== 1 ? 's' : ''}
                </Text>
              )}
            </View>
            <Icon name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.assessmentCard}
            onPress={() => navigation.navigate('SavingsAssessment')}
          >
            <View style={[styles.iconContainer, { backgroundColor: '#4CAF5015' }]}>
              <Icon name="savings" size={32} color="#4CAF50" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>Savings Assessment</Text>
              <Text style={styles.cardDescription}>
                Forecast savings account growth
              </Text>
              {summary?.summary?.savings && (
                <Text style={styles.cardCount}>
                  {summary.summary.savings.count} assessment{summary.summary.savings.count !== 1 ? 's' : ''}
                </Text>
              )}
            </View>
            <Icon name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.assessmentCard}
            onPress={() => navigation.navigate('CDAssessment')}
          >
            <View style={[styles.iconContainer, { backgroundColor: '#FF980015' }]}>
              <Icon name="account-balance" size={32} color="#FF9800" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>CD Assessment</Text>
              <Text style={styles.cardDescription}>
                Forecast Certificate of Deposit growth
              </Text>
              {summary?.summary?.cds && (
                <Text style={styles.cardCount}>
                  {summary.summary.cds.count} assessment{summary.summary.cds.count !== 1 ? 's' : ''}
                </Text>
              )}
            </View>
            <Icon name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.assessmentCard}
            onPress={() => navigation.navigate('BondAssessment')}
          >
            <View style={[styles.iconContainer, { backgroundColor: '#9C27B015' }]}>
              <Icon name="show-chart" size={32} color="#9C27B0" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>Bond Assessment</Text>
              <Text style={styles.cardDescription}>
                Analyze bond investments and returns
              </Text>
              {summary?.summary?.bonds && (
                <Text style={styles.cardCount}>
                  {summary.summary.bonds.count} assessment{summary.summary.bonds.count !== 1 ? 's' : ''}
                </Text>
              )}
            </View>
            <Icon name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>
        </View>

        {/* Summary Statistics */}
        {summary?.summary && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Summary</Text>
            <View style={styles.summaryCard}>
              <View style={styles.summaryRow}>
                <Icon name="attach-money" size={24} color="#4CAF50" />
                <View style={styles.summaryContent}>
                  <Text style={styles.summaryLabel}>Total Value</Text>
                  <Text style={styles.summaryValue}>
                    {formatCurrency(
                      (summary.summary.stocks?.total_value || 0) +
                      (summary.summary.savings?.total_value || 0) +
                      (summary.summary.cds?.total_value || 0) +
                      (summary.summary.bonds?.total_value || 0)
                    )}
                  </Text>
                </View>
              </View>
              <View style={styles.summaryRow}>
                <Icon name="trending-up" size={24} color="#2196F3" />
                <View style={styles.summaryContent}>
                  <Text style={styles.summaryLabel}>10-Year Forecast</Text>
                  <Text style={styles.summaryValue}>
                    {formatCurrency(
                      (summary.summary.stocks?.total_decade || 0) +
                      (summary.summary.savings?.total_decade || 0) +
                      (summary.summary.cds?.total_decade || 0) +
                      (summary.summary.bonds?.total_decade || 0)
                    )}
                  </Text>
                </View>
              </View>
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  content: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  assessmentCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
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
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  cardCount: {
    fontSize: 12,
    color: '#999',
  },
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  summaryContent: {
    marginLeft: 12,
    flex: 1,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
});

