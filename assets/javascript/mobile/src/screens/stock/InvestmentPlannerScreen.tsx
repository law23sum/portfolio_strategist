import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function InvestmentPlannerScreen({ navigation, route }: any) {
  const { analysisPk } = route.params || {};
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  
  const [targetPrice, setTargetPrice] = useState('');
  const [investmentAmount, setInvestmentAmount] = useState('');
  const [alertEnabled, setAlertEnabled] = useState(true);

  useEffect(() => {
    if (analysisPk) {
      loadPlannerData();
    }
  }, [analysisPk]);

  const loadPlannerData = async () => {
    setLoading(true);
    try {
      const response = await apiService.getInvestmentPlanner(analysisPk);
      if (response.data) {
        setAnalysis(response.data.analysis);
        setPlans(response.data.plans || []);
        setCurrentPrice(response.data.current_price);
      }
    } catch (error) {
      console.error('Error loading planner:', error);
      Alert.alert('Error', 'Failed to load investment planner data');
    } finally {
      setLoading(false);
    }
  };

  const savePlan = async () => {
    if (!targetPrice || !investmentAmount) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSaving(true);
    try {
      const data = {
        target_price: parseFloat(targetPrice),
        investment_amount: parseFloat(investmentAmount),
        alert_enabled: alertEnabled,
      };

      const response = await apiService.createInvestmentPlan(analysisPk, data);
      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        Alert.alert('Success', 'Investment plan saved!');
        setTargetPrice('');
        setInvestmentAmount('');
        loadPlannerData();
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save plan');
    } finally {
      setSaving(false);
    }
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
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Investment Planner</Text>
        {analysis && (
          <Text style={styles.subtitle}>
            Plan investments for {analysis.symbol}
          </Text>
        )}

        {currentPrice && (
          <View style={styles.priceCard}>
            <Text style={styles.priceLabel}>Current Price</Text>
            <Text style={styles.priceValue}>{formatCurrency(currentPrice)}</Text>
          </View>
        )}

        {/* Create New Plan */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Create Investment Plan</Text>
          
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Target Price ($) *</Text>
            <TextInput
              style={styles.input}
              value={targetPrice}
              onChangeText={setTargetPrice}
              placeholder="Enter target price"
              keyboardType="numeric"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Investment Amount ($) *</Text>
            <TextInput
              style={styles.input}
              value={investmentAmount}
              onChangeText={setInvestmentAmount}
              placeholder="Enter investment amount"
              keyboardType="numeric"
            />
          </View>

          <TouchableOpacity
            style={styles.saveButton}
            onPress={savePlan}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Icon name="save" size={20} color="#fff" />
                <Text style={styles.buttonText}>Save Plan</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Existing Plans */}
        {plans.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Your Investment Plans</Text>
            {plans.map((plan, index) => (
              <View key={index} style={styles.planCard}>
                <View style={styles.planHeader}>
                  <Text style={styles.planTitle}>Plan #{index + 1}</Text>
                  {plan.alert_enabled && (
                    <View style={styles.alertBadge}>
                      <Icon name="notifications" size={16} color="#fff" />
                      <Text style={styles.alertText}>Alerts On</Text>
                    </View>
                  )}
                </View>
                <View style={styles.planRow}>
                  <Text style={styles.planLabel}>Target Price:</Text>
                  <Text style={styles.planValue}>
                    {formatCurrency(plan.target_price)}
                  </Text>
                </View>
                <View style={styles.planRow}>
                  <Text style={styles.planLabel}>Investment Amount:</Text>
                  <Text style={styles.planValue}>
                    {formatCurrency(plan.investment_amount)}
                  </Text>
                </View>
                {plan.created_at && (
                  <Text style={styles.planDate}>
                    Created: {new Date(plan.created_at).toLocaleDateString()}
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}

        {plans.length === 0 && (
          <View style={styles.emptyCard}>
            <Icon name="inbox" size={48} color="#999" />
            <Text style={styles.emptyText}>No investment plans yet</Text>
            <Text style={styles.emptySubtext}>
              Create your first plan above to get started
            </Text>
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
  priceCard: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 24,
  },
  priceLabel: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  saveButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  planCard: {
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
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  alertBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  alertText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  planRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  planLabel: {
    fontSize: 14,
    color: '#666',
  },
  planValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  planDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    marginTop: 24,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
});

