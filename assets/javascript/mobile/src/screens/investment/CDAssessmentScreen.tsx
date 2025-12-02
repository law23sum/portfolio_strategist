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

export default function CDAssessmentScreen({navigation}: any) {
  const [saving, setSaving] = useState(false);
  const [accountName, setAccountName] = useState('CD Account');
  const [cdAmount, setCdAmount] = useState('');
  const [annualRate, setAnnualRate] = useState('');
  const [termMonths, setTermMonths] = useState('36');
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
        const depositoryAccounts = (response.data || []).filter(
          (acc: any) => acc.account_type === 'depository',
        );
        setLinkedAccounts(depositoryAccounts);
      }
    } catch (error) {
      console.error('Error loading linked accounts:', error);
    }
  };

  const calculateForecast = () => {
    const principal = parseFloat(cdAmount) || 0;
    const rate = parseFloat(annualRate) || 0;
    const contrib = parseFloat(biweeklyContrib) || 0;
    const freq = parseInt(compoundingFreq) || 12;
    const months = parseInt(termMonths) || 36;

    if (principal === 0 || rate === 0) {
      return null;
    }

    const forecastData: any = {
      current: {
        value: principal,
        principal: principal,
        interest: 0,
        growth_percent: 0,
      },
    };

    const ratePerPeriod = rate / 100 / freq;
    const periods = months * (freq / 12);
    const contributions = contrib * (months / (12 / 26));

    let amount = principal;
    for (let i = 0; i < periods; i++) {
      amount = amount * (1 + ratePerPeriod) + (contrib / freq);
    }

    forecastData.maturity = {
      value: amount,
      principal: principal + contributions,
      interest: amount - principal - contributions,
      growth_percent: ((amount - principal) / principal) * 100,
    };

    return forecastData;
  };

  const handleSave = async () => {
    if (!cdAmount || !annualRate) {
      Alert.alert('Error', 'Please enter CD amount and annual rate');
      return;
    }

    setSaving(true);
    try {
      const forecastData = calculateForecast();
      const response = await apiService.saveCDAssessment({
        account_name: accountName,
        amount: parseFloat(cdAmount),
        annual_interest_rate: parseFloat(annualRate),
        term_months: parseInt(termMonths) || 36,
        biweekly_contribution: parseFloat(biweeklyContrib) || 0,
        compounding_frequency: parseInt(compoundingFreq) || 12,
        forecast_data: forecastData,
        linked_account_id: selectedAccountId ? parseInt(selectedAccountId) : undefined,
      });

      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        Alert.alert('Success', 'CD assessment saved successfully!', [
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
        <Text style={styles.title}>CD Assessment</Text>
        <Text style={styles.subtitle}>Evaluate Certificate of Deposit investments and forecast returns</Text>

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
                  setCdAmount(String(balance));
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
          <Text style={styles.sectionTitle}>CD Details</Text>

          <Text style={styles.label}>Account Name</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., 3-Year CD"
            value={accountName}
            onChangeText={setAccountName}
          />

          <Text style={styles.label}>CD Amount ($) *</Text>
          <TextInput
            style={styles.input}
            placeholder="10000"
            value={cdAmount}
            onChangeText={setCdAmount}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>APY (%) *</Text>
          <TextInput
            style={styles.input}
            placeholder="5.0"
            value={annualRate}
            onChangeText={setAnnualRate}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>Term (Months) *</Text>
          <View style={styles.termOptions}>
            {['12', '24', '36', '48', '60'].map(term => (
              <TouchableOpacity
                key={term}
                style={[styles.termOption, termMonths === term && styles.termOptionSelected]}
                onPress={() => setTermMonths(term)}
              >
                <Text
                  style={[
                    styles.termOptionText,
                    termMonths === term && styles.termOptionTextSelected,
                  ]}
                >
                  {term} mo
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Biweekly Contribution ($)</Text>
          <TextInput
            style={styles.input}
            placeholder="0"
            value={biweeklyContrib}
            onChangeText={setBiweeklyContrib}
            keyboardType="decimal-pad"
          />

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
  termOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  termOption: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    marginRight: 8,
    marginBottom: 8,
  },
  termOptionSelected: {
    borderColor: '#0A84FF',
    backgroundColor: '#E9F3FF',
  },
  termOptionText: {
    fontSize: 14,
    color: '#333',
  },
  termOptionTextSelected: {
    color: '#0A84FF',
    fontWeight: '600',
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
  saveButton: {
    backgroundColor: '#0A84FF',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 24,
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

