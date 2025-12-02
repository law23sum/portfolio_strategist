import React, {useEffect, useState} from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function SavingsAssessmentScreen({navigation}: any) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [accountName, setAccountName] = useState('Savings Account');
  const [initialDeposit, setInitialDeposit] = useState('');
  const [annualRate, setAnnualRate] = useState('');
  const [biweeklyContrib, setBiweeklyContrib] = useState('');
  const [compoundingFreq, setCompoundingFreq] = useState('12');
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');

  useEffect(() => {
    loadLinkedAccounts();
  }, []);

  const loadLinkedAccounts = async () => {
    try {
      const response = await apiService.getLinkedAccounts();
      if (response.data) {
        const savingsAccounts = (response.data || []).filter(
          (acc: any) => acc.account_type === 'depository',
        );
        setLinkedAccounts(savingsAccounts);
      }
    } catch (error) {
      console.error('Error loading linked accounts:', error);
    }
  };

  const calculateForecast = () => {
    const principal = parseFloat(initialDeposit) || 0;
    const rate = parseFloat(annualRate) || 0;
    const contrib = parseFloat(biweeklyContrib) || 0;
    const freq = parseInt(compoundingFreq) || 12;

    if (principal === 0 || rate === 0) {
      return null;
    }

    const forecastData: any = {
      current: {
        value: principal,
        contributions: principal,
        interest: 0,
        growth_percent: 0,
      },
    };

    // Calculate for different time periods
    const periods = [
      {key: 'monthly', months: 1},
      {key: 'quarterly', months: 3},
      {key: 'yearly', months: 12},
      {key: 'decade', months: 120},
    ];

    periods.forEach(period => {
      const months = period.months;
      const periodsPerYear = freq;
      const ratePerPeriod = rate / 100 / periodsPerYear;
      const contributions = contrib * (months / (12 / 26)); // Biweekly contributions

      let amount = principal;
      for (let i = 0; i < months * (periodsPerYear / 12); i++) {
        amount = amount * (1 + ratePerPeriod) + (contrib / periodsPerYear);
      }

      forecastData[period.key] = {
        value: amount,
        contributions: principal + contributions,
        interest: amount - principal - contributions,
        growth_percent: ((amount - principal) / principal) * 100,
      };
    });

    return forecastData;
  };

  const handleCalculate = () => {
    if (!initialDeposit || !annualRate) {
      Alert.alert('Error', 'Please enter initial deposit and annual rate');
      return;
    }

    const forecast = calculateForecast();
    if (forecast) {
      Alert.alert('Forecast Calculated', 'Forecast data has been calculated. Save to store results.');
    }
  };

  const handleSave = async () => {
    if (!initialDeposit || !annualRate) {
      Alert.alert('Error', 'Please enter initial deposit and annual rate');
      return;
    }

    setSaving(true);
    try {
      const forecastData = calculateForecast();
      const response = await apiService.saveSavingsAssessment({
        account_name: accountName,
        initial_deposit: parseFloat(initialDeposit),
        annual_interest_rate: parseFloat(annualRate),
        biweekly_contribution: parseFloat(biweeklyContrib) || 0,
        compounding_frequency: parseInt(compoundingFreq) || 12,
        forecast_data: forecastData,
        linked_account_id: selectedAccountId ? parseInt(selectedAccountId) : undefined,
      });

      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        Alert.alert('Success', 'Savings assessment saved successfully!', [
          {text: 'OK', onPress: () => navigation.goBack()},
        ]);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save assessment');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Savings Assessment</Text>
        <Text style={styles.subtitle}>Forecast your savings account growth across multiple time periods</Text>

        {linkedAccounts.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Linked Accounts</Text>
            {linkedAccounts.map(account => (
              <TouchableOpacity
                key={account.id}
                style={[
                  styles.accountCard,
                  selectedAccountId === String(account.id) && styles.accountCardSelected,
                ]}
                onPress={() => {
                  setSelectedAccountId(String(account.id));
                  const balance = account.balances?.[0]?.current_balance || 0;
                  setInitialDeposit(String(balance));
                }}
              >
                <View style={styles.accountInfo}>
                  <Text style={styles.accountName}>{account.account_name}</Text>
                  <Text style={styles.accountInstitution}>{account.institution_name}</Text>
                </View>
                <Text style={styles.accountBalance}>
                  ${parseFloat(account.balances?.[0]?.current_balance || 0).toFixed(2)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Details</Text>

          <Text style={styles.label}>Account Name</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., High-Yield Savings Account"
            value={accountName}
            onChangeText={setAccountName}
          />

          <Text style={styles.label}>Initial Deposit ($) *</Text>
          <TextInput
            style={styles.input}
            placeholder="25000"
            value={initialDeposit}
            onChangeText={setInitialDeposit}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>APY (%) *</Text>
          <TextInput
            style={styles.input}
            placeholder="4.5"
            value={annualRate}
            onChangeText={setAnnualRate}
            keyboardType="decimal-pad"
          />
          <Text style={styles.helpText}>Annual Percentage Yield</Text>

          <Text style={styles.label}>Biweekly Contribution ($)</Text>
          <TextInput
            style={styles.input}
            placeholder="200"
            value={biweeklyContrib}
            onChangeText={setBiweeklyContrib}
            keyboardType="decimal-pad"
          />
          <Text style={styles.helpText}>26 biweekly periods × 3 years = 78 contributions per phase</Text>

          <Text style={styles.label}>Compounding Frequency</Text>
          <View style={styles.frequencyOptions}>
            {['1', '2', '4', '12', '365'].map(freq => (
              <TouchableOpacity
                key={freq}
                style={[
                  styles.frequencyOption,
                  compoundingFreq === freq && styles.frequencyOptionSelected,
                ]}
                onPress={() => setCompoundingFreq(freq)}
              >
                <Text
                  style={[
                    styles.frequencyOptionText,
                    compoundingFreq === freq && styles.frequencyOptionTextSelected,
                  ]}
                >
                  {freq === '1' ? 'Annually' : freq === '2' ? 'Semi-annually' : freq === '4' ? 'Quarterly' : freq === '12' ? 'Monthly' : 'Daily'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.calculateButton} onPress={handleCalculate}>
            <Text style={styles.calculateButtonText}>Calculate Forecast</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.saveButton, saving && styles.buttonDisabled]}
            onPress={handleSave}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.saveButtonText}>Save Assessment</Text>
            )}
          </TouchableOpacity>
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
    color: '#111',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
    color: '#555',
    marginBottom: 24,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 16,
  },
  accountCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    marginBottom: 8,
  },
  accountCardSelected: {
    borderColor: '#0A84FF',
    backgroundColor: '#E9F3FF',
  },
  accountInfo: {
    flex: 1,
  },
  accountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  accountInstitution: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
  accountBalance: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0A84FF',
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  helpText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    marginBottom: 8,
  },
  frequencyOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  frequencyOption: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    marginRight: 8,
    marginBottom: 8,
  },
  frequencyOptionSelected: {
    borderColor: '#0A84FF',
    backgroundColor: '#E9F3FF',
  },
  frequencyOptionText: {
    fontSize: 14,
    color: '#333',
  },
  frequencyOptionTextSelected: {
    color: '#0A84FF',
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
    marginBottom: 24,
  },
  calculateButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#0A84FF',
    alignItems: 'center',
  },
  calculateButtonText: {
    color: '#0A84FF',
    fontWeight: '600',
    fontSize: 16,
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#0A84FF',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});

