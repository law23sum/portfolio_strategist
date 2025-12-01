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
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

const PHASES = [
  { phase: 1, years: 3, label: 'Phase 1: Years 1-3' },
  { phase: 2, years: 3, label: 'Phase 2: Years 4-6' },
  { phase: 3, years: 3, label: 'Phase 3: Years 7-9' },
  { phase: 4, years: 1, label: 'Phase 4: Year 10' },
];

export default function SavingsAssessmentScreen({ navigation, route }: any) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([]);
  
  const [accountName, setAccountName] = useState('Savings Account');
  const [initialDeposit, setInitialDeposit] = useState('');
  const [annualRate, setAnnualRate] = useState('');
  const [biweeklyContribution, setBiweeklyContribution] = useState('');
  const [compoundingFrequency, setCompoundingFrequency] = useState(12);
  const [notes, setNotes] = useState('');
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  
  const [forecastResults, setForecastResults] = useState<any[]>([]);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    loadLinkedAccounts();
  }, []);

  const loadLinkedAccounts = async () => {
    try {
      const response = await apiService.getLinkedAccounts();
      if (response.data) {
        const savingsAccounts = response.data.filter(
          (acc: any) => acc.account_type === 'depository'
        );
        setLinkedAccounts(savingsAccounts);
      }
    } catch (error) {
      console.error('Error loading linked accounts:', error);
    }
  };

  const calculateSavingsPhase = (
    startingAmount: number,
    apy: number,
    biweeklyContrib: number,
    compoundFreq: number,
    phaseNumber: number,
    totalYears: number
  ) => {
    const periodsPerYear = compoundFreq;
    const ratePerPeriod = apy / periodsPerYear;
    const totalPeriods = totalYears * periodsPerYear;
    const biweeklyPeriodsPerYear = 26;
    const contributionPerPeriod = (biweeklyContrib * biweeklyPeriodsPerYear) / periodsPerYear;
    
    let balance = startingAmount;
    let totalContributions = 0;
    
    for (let period = 0; period < totalPeriods; period++) {
      balance += contributionPerPeriod;
      totalContributions += contributionPerPeriod;
      balance *= (1 + ratePerPeriod);
    }
    
    const interestEarned = balance - startingAmount - totalContributions;
    
    return {
      phase: phaseNumber,
      startingAmount,
      totalAmount: balance,
      interestEarned,
      totalContributions,
      apy: apy * 100,
      years: totalYears,
    };
  };

  const calculateForecast = () => {
    const deposit = parseFloat(initialDeposit) || 0;
    const rate = parseFloat(annualRate) / 100 || 0;
    const biweeklyContrib = parseFloat(biweeklyContribution) || 0;
    
    if (deposit <= 0 || rate <= 0) {
      Alert.alert('Error', 'Please enter valid initial deposit and APY.');
      return;
    }
    
    const phases = [];
    let startingAmount = deposit;
    
    for (const phaseInfo of PHASES) {
      const phaseResult = calculateSavingsPhase(
        startingAmount,
        rate,
        biweeklyContrib,
        compoundingFrequency,
        phaseInfo.phase,
        phaseInfo.years
      );
      phases.push(phaseResult);
      startingAmount = phaseResult.totalAmount;
    }
    
    setForecastResults(phases);
    setShowResults(true);
  };

  const saveAssessment = async () => {
    if (!showResults) {
      Alert.alert('Error', 'Please calculate forecast first.');
      return;
    }
    
    setSaving(true);
    try {
      const deposit = parseFloat(initialDeposit) || 0;
      const rate = parseFloat(annualRate) || 0;
      const biweeklyContrib = parseFloat(biweeklyContribution) || 0;
      
      const forecastData: any = {
        current: {
          value: deposit,
          contributions: deposit,
          interest: 0,
          growth_percent: 0,
        },
      };
      
      let startingAmount = deposit;
      for (const phaseInfo of PHASES) {
        const phase = calculateSavingsPhase(
          startingAmount,
          rate / 100,
          biweeklyContrib,
          compoundingFrequency,
          phaseInfo.phase,
          phaseInfo.years
        );
        forecastData[`phase_${phaseInfo.phase}`] = {
          value: phase.totalAmount,
          starting_amount: phase.startingAmount,
          interest: phase.interestEarned,
          total_contributions: phase.totalContributions,
          apy: phase.apy,
        };
        startingAmount = phase.totalAmount;
      }
      
      const data: any = {
        account_name: accountName,
        initial_deposit: deposit,
        annual_interest_rate: rate,
        biweekly_contribution: biweeklyContrib,
        compounding_frequency: compoundingFrequency,
        forecast_data: forecastData,
        notes: notes,
      };
      
      if (selectedAccountId) {
        data.linked_account_id = selectedAccountId;
      }
      
      const response = await apiService.saveSavingsAssessment(data);
      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        Alert.alert('Success', 'Assessment saved successfully!', [
          { text: 'OK', onPress: () => navigation.goBack() },
        ]);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save assessment');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Savings Assessment</Text>
        <Text style={styles.subtitle}>Forecast your savings account growth</Text>

        {/* Linked Account Selection */}
        {linkedAccounts.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.label}>Import from Linked Account (Optional)</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={selectedAccountId}
                onValueChange={(value) => {
                  setSelectedAccountId(value);
                  if (value) {
                    const account = linkedAccounts.find((acc: any) => acc.id === value);
                    if (account) {
                      setAccountName(account.account_name);
                      setInitialDeposit(account.current_balance?.toString() || '');
                    }
                  }
                }}
                style={styles.picker}
              >
                <Picker.Item label="Select a linked account (optional)" value={null} />
                {linkedAccounts.map((account: any) => (
                  <Picker.Item
                    key={account.id}
                    label={`${account.institution_name} - ${account.account_name}`}
                    value={account.id}
                  />
                ))}
              </Picker>
            </View>
          </View>
        )}

        {/* Form Fields */}
        <View style={styles.section}>
          <Text style={styles.label}>Account Name *</Text>
          <TextInput
            style={styles.input}
            value={accountName}
            onChangeText={setAccountName}
            placeholder="e.g., High-Yield Savings Account"
          />
        </View>

        <View style={styles.row}>
          <View style={styles.halfWidth}>
            <Text style={styles.label}>Initial Deposit ($) *</Text>
            <TextInput
              style={styles.input}
              value={initialDeposit}
              onChangeText={setInitialDeposit}
              placeholder="25000"
              keyboardType="numeric"
            />
          </View>
          <View style={styles.halfWidth}>
            <Text style={styles.label}>APY (%) *</Text>
            <TextInput
              style={styles.input}
              value={annualRate}
              onChangeText={setAnnualRate}
              placeholder="4.5"
              keyboardType="numeric"
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Biweekly Contribution ($)</Text>
          <TextInput
            style={styles.input}
            value={biweeklyContribution}
            onChangeText={setBiweeklyContribution}
            placeholder="200"
            keyboardType="numeric"
          />
          <Text style={styles.helpText}>
            26 biweekly periods × 3 years = 78 contributions per phase
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Compounding Frequency</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={compoundingFrequency}
              onValueChange={setCompoundingFrequency}
              style={styles.picker}
            >
              <Picker.Item label="Daily" value={365} />
              <Picker.Item label="Monthly" value={12} />
              <Picker.Item label="Quarterly" value={4} />
              <Picker.Item label="Semi-Annually" value={2} />
              <Picker.Item label="Annually" value={1} />
            </Picker>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Notes</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={notes}
            onChangeText={setNotes}
            placeholder="Optional notes about this savings account"
            multiline
            numberOfLines={4}
          />
        </View>

        <TouchableOpacity
          style={styles.calculateButton}
          onPress={calculateForecast}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="calculate" size={20} color="#fff" />
              <Text style={styles.buttonText}>Calculate Forecast</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Forecast Results */}
        {showResults && forecastResults.length > 0 && (
          <View style={styles.resultsSection}>
            <Text style={styles.resultsTitle}>Forecast Results</Text>
            {forecastResults.map((phase, index) => (
              <View key={index} style={styles.resultCard}>
                <Text style={styles.phaseTitle}>{PHASES[index].label}</Text>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Starting Amount:</Text>
                  <Text style={styles.resultValue}>
                    {formatCurrency(phase.startingAmount)}
                  </Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Total Contributions:</Text>
                  <Text style={styles.resultValue}>
                    {formatCurrency(phase.totalContributions)}
                  </Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Interest Earned:</Text>
                  <Text style={styles.resultValue}>
                    {formatCurrency(phase.interestEarned)}
                  </Text>
                </View>
                <View style={[styles.resultRow, styles.totalRow]}>
                  <Text style={styles.totalLabel}>Total Amount:</Text>
                  <Text style={styles.totalValue}>
                    {formatCurrency(phase.totalAmount)}
                  </Text>
                </View>
              </View>
            ))}
            
            <TouchableOpacity
              style={styles.saveButton}
              onPress={saveAssessment}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Icon name="save" size={20} color="#fff" />
                  <Text style={styles.buttonText}>Save Assessment</Text>
                </>
              )}
            </TouchableOpacity>
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
  section: {
    marginBottom: 20,
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
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  halfWidth: {
    width: '48%',
  },
  pickerContainer: {
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  helpText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  calculateButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  saveButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  resultsSection: {
    marginTop: 24,
  },
  resultsTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  phaseTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 12,
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  totalRow: {
    borderBottomWidth: 0,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 2,
    borderTopColor: '#007AFF',
  },
  resultLabel: {
    fontSize: 14,
    color: '#666',
  },
  resultValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
});

