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

export default function BondAssessmentScreen({navigation}: any) {
  const [saving, setSaving] = useState(false);
  const [accountName, setAccountName] = useState('Bond Investment');
  const [faceValue, setFaceValue] = useState('');
  const [couponRate, setCouponRate] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [yearsToMaturity, setYearsToMaturity] = useState('');
  const [paymentFreq, setPaymentFreq] = useState('2');
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');

  useEffect(() => {
    loadLinkedAccounts();
  }, []);

  const loadLinkedAccounts = async () => {
    try {
      const response = await apiService.getLinkedAccounts();
      if (response.data) {
        const investmentAccounts = (response.data || []).filter(
          (acc: any) => acc.account_type === 'investment' || acc.account_type === 'brokerage',
        );
        setLinkedAccounts(investmentAccounts);
      }
    } catch (error) {
      console.error('Error loading linked accounts:', error);
    }
  };

  const calculateForecast = () => {
    const fv = parseFloat(faceValue) || 0;
    const cr = parseFloat(couponRate) || 0;
    const pp = parseFloat(purchasePrice) || 0;
    const ytm = parseFloat(yearsToMaturity) || 0;
    const freq = parseInt(paymentFreq) || 2;

    if (fv === 0 || cr === 0 || pp === 0 || ytm === 0) {
      return null;
    }

    const forecastData: any = {
      current: {
        face_value: fv,
        purchase_price: pp,
        coupon_rate: cr,
        years_to_maturity: ytm,
      },
    };

    // Calculate annual coupon payment
    const annualCoupon = fv * (cr / 100);
    const couponPerPeriod = annualCoupon / freq;
    const totalPeriods = ytm * freq;

    // Calculate yield to maturity approximation
    const totalCoupons = annualCoupon * ytm;
    const capitalGain = fv - pp;
    const totalReturn = totalCoupons + capitalGain;
    const yieldToMaturity = (totalReturn / pp / ytm) * 100;

    forecastData.maturity = {
      face_value: fv,
      purchase_price: pp,
      total_coupons: totalCoupons,
      capital_gain: capitalGain,
      total_return: totalReturn,
      yield_to_maturity: yieldToMaturity,
    };

    return forecastData;
  };

  const handleSave = async () => {
    if (!faceValue || !couponRate || !purchasePrice || !yearsToMaturity) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSaving(true);
    try {
      const forecastData = calculateForecast();
      const response = await apiService.saveBondAssessment({
        account_name: accountName,
        face_value: parseFloat(faceValue),
        coupon_rate: parseFloat(couponRate),
        purchase_price: parseFloat(purchasePrice),
        years_to_maturity: parseFloat(yearsToMaturity),
        payment_frequency: parseInt(paymentFreq) || 2,
        forecast_data: forecastData,
        linked_account_id: selectedAccountId ? parseInt(selectedAccountId) : undefined,
      });

      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        Alert.alert('Success', 'Bond assessment saved successfully!', [
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
        <Text style={styles.title}>Bond Assessment</Text>
        <Text style={styles.subtitle}>Analyze bond investments and calculate yield projections</Text>

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
                onPress={() => setSelectedAccountId(String(account.id))}
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
          <Text style={styles.sectionTitle}>Bond Details</Text>

          <Text style={styles.label}>Account Name</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., Corporate Bond"
            value={accountName}
            onChangeText={setAccountName}
          />

          <Text style={styles.label}>Face Value ($) *</Text>
          <TextInput
            style={styles.input}
            placeholder="10000"
            value={faceValue}
            onChangeText={setFaceValue}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>Coupon Rate (%) *</Text>
          <TextInput
            style={styles.input}
            placeholder="5.0"
            value={couponRate}
            onChangeText={setCouponRate}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>Purchase Price ($) *</Text>
          <TextInput
            style={styles.input}
            placeholder="9500"
            value={purchasePrice}
            onChangeText={setPurchasePrice}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>Years to Maturity *</Text>
          <TextInput
            style={styles.input}
            placeholder="10"
            value={yearsToMaturity}
            onChangeText={setYearsToMaturity}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>Payment Frequency</Text>
          <View style={styles.frequencyOptions}>
            {['1', '2', '4'].map(freq => (
              <TouchableOpacity
                key={freq}
                style={[
                  styles.frequencyOption,
                  paymentFreq === freq && styles.frequencyOptionSelected,
                ]}
                onPress={() => setPaymentFreq(freq)}
              >
                <Text
                  style={[
                    styles.frequencyOptionText,
                    paymentFreq === freq && styles.frequencyOptionTextSelected,
                  ]}
                >
                  {freq === '1' ? 'Annually' : freq === '2' ? 'Semi-annually' : 'Quarterly'}
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

