import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function BudgetPlannerScreen({ navigation }: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [budgetData, setBudgetData] = useState<any>(null);
  const [debtData, setDebtData] = useState<any>(null);

  const loadData = async () => {
    try {
      const response = await apiService.getBudgetPlannerData();
      if (response.data) {
        // The backend returns HTML, so we'll need to parse or display a simplified view
        // For now, we'll show a placeholder that indicates the feature is available
        setBudgetData(response.data);
      }
    } catch (error) {
      console.error('Error loading budget planner:', error);
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
    if (!value) return '$0.00';
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
        <Text style={styles.title}>Budget Planner</Text>
        <Text style={styles.subtitle}>Plan your budget with tax, expense, and debt calculations</Text>
      </View>

      <View style={styles.content}>
        {/* Budget Overview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Budget Overview</Text>
          <View style={styles.infoCard}>
            <Icon name="info" size={24} color="#007AFF" />
            <Text style={styles.infoText}>
              Budget Planner helps you calculate taxes, track expenses, and manage debt.
              Use the web app for full functionality with interactive forms and charts.
            </Text>
          </View>
        </View>

        {/* Budget Data Display */}
        {budgetData && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Budget Data</Text>
            <View style={styles.dataCard}>
              <Text style={styles.dataText}>
                Budget data is available. For detailed calculations and interactive features,
                please use the web application.
              </Text>
            </View>
          </View>
        )}

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          
          <View style={styles.actionCard}>
            <Icon name="account-balance-wallet" size={32} color="#4CAF50" />
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>View Records</Text>
              <Text style={styles.actionDescription}>
                Access your financial records and documents
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => navigation.navigate('Records', { screen: 'RecordsMain' })}
            >
              <Icon name="chevron-right" size={24} color="#999" />
            </TouchableOpacity>
          </View>

          <View style={styles.actionCard}>
            <Icon name="trending-up" size={32} color="#2196F3" />
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Investment & Savings</Text>
              <Text style={styles.actionDescription}>
                Plan your investments and savings
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => navigation.navigate('InvestmentSavings')}
            >
              <Icon name="chevron-right" size={24} color="#999" />
            </TouchableOpacity>
          </View>

          <View style={styles.actionCard}>
            <Icon name="account-balance" size={32} color="#FF9800" />
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Link Accounts</Text>
              <Text style={styles.actionDescription}>
                Connect your financial accounts via Plaid
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => navigation.navigate('Records', { screen: 'LinkedAccounts' })}
            >
              <Icon name="chevron-right" size={24} color="#999" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Note */}
        <View style={styles.noteCard}>
          <Icon name="lightbulb" size={24} color="#FF9800" />
          <Text style={styles.noteText}>
            For the full Budget Planner experience with tax calculations, expense tracking,
            and debt management, please visit the web application.
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
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    alignItems: 'flex-start',
  },
  infoText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
  dataCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  dataText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  actionCard: {
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
  actionContent: {
    flex: 1,
    marginLeft: 16,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 14,
    color: '#666',
  },
  noteCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    alignItems: 'flex-start',
  },
  noteText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#E65100',
    lineHeight: 20,
  },
});

