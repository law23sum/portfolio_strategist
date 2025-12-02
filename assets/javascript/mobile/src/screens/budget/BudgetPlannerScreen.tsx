import React, {useEffect, useState} from 'react';
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function BudgetPlannerScreen({navigation}: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [budgetData, setBudgetData] = useState<any>(null);
  const [debtData, setDebtData] = useState<any>(null);

  // Income & Tax fields
  const [taxYear, setTaxYear] = useState('2024');
  const [annualSalary, setAnnualSalary] = useState('');
  const [paychecksPerYear, setPaychecksPerYear] = useState('26');
  const [hsaContribution, setHsaContribution] = useState('');
  const [retirementPercent, setRetirementPercent] = useState('4');
  const [benefitsPerPaycheck, setBenefitsPerPaycheck] = useState('');

  // Expense fields
  const [expenses, setExpenses] = useState<Array<{name: string; amount: string}>>([
    {name: 'Utilities', amount: ''},
  ]);

  // Debt fields
  const [monthlyDebtPayment, setMonthlyDebtPayment] = useState('');
  const [debts, setDebts] = useState<Array<{name: string; total: string; paid: string}>>([
    {name: 'Car Loan', total: '', paid: '0'},
  ]);

  useEffect(() => {
    loadBudgetData();
    loadDebtData();
  }, []);

  const loadBudgetData = async () => {
    try {
      const response = await apiService.getBudgetData(30);
      if (response.data) {
        setBudgetData(response.data);
        // Pre-populate fields if available from Plaid data
        if (response.data.plaid_data) {
          const plaid = response.data.plaid_data;
          if (plaid.annual_salary) {
            setAnnualSalary(plaid.annual_salary.toString());
          }
          if (plaid.monthly_income) {
            const calculatedAnnual = parseFloat(plaid.monthly_income) * 12;
            if (!annualSalary) {
              setAnnualSalary(calculatedAnnual.toString());
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading budget data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadDebtData = async () => {
    try {
      const response = await apiService.getDebtData();
      if (response.data) {
        setDebtData(response.data);
        // Pre-populate debt fields if available
        if (response.data.total_monthly_payment) {
          setMonthlyDebtPayment(response.data.total_monthly_payment.toString());
        }
      }
    } catch (error) {
      console.error('Error loading debt data:', error);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadBudgetData();
    loadDebtData();
  };

  const addExpense = () => {
    setExpenses([...expenses, {name: '', amount: ''}]);
  };

  const removeExpense = (index: number) => {
    if (expenses.length > 1) {
      setExpenses(expenses.filter((_, i) => i !== index));
    }
  };

  const updateExpense = (index: number, field: 'name' | 'amount', value: string) => {
    const updated = [...expenses];
    updated[index][field] = value;
    setExpenses(updated);
  };

  const addDebt = () => {
    setDebts([...debts, {name: '', total: '', paid: '0'}]);
  };

  const removeDebt = (index: number) => {
    if (debts.length > 1) {
      setDebts(debts.filter((_, i) => i !== index));
    }
  };

  const updateDebt = (index: number, field: 'name' | 'total' | 'paid', value: string) => {
    const updated = [...debts];
    updated[index][field] = value;
    setDebts(updated);
  };

  const calculateBudget = () => {
    Alert.alert(
      'Budget Calculator',
      'Budget calculation feature coming soon. This will calculate taxes, net income, and budget breakdown.',
      [{text: 'OK'}],
    );
  };

  const formatCurrency = (value: number | string | undefined): string => {
    if (value === undefined || value === null) {
      return '$0.00';
    }
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num);
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
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>Budget Planner</Text>
        <Text style={styles.heroSubtitle}>
          Track income, expenses, taxes, and debt to manage your financial plan.
        </Text>
      </View>

      {/* Income & Tax Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Income & Tax Information</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Tax Year</Text>
          <View style={styles.pickerContainer}>
            <TouchableOpacity
              style={styles.pickerButton}
              onPress={() => {
                const years = ['2024', '2023', '2022'];
                const currentIndex = years.indexOf(taxYear);
                const nextIndex = (currentIndex + 1) % years.length;
                setTaxYear(years[nextIndex]);
              }}
            >
              <Text style={styles.pickerText}>{taxYear}</Text>
              <Icon name="arrow-drop-down" size={24} color="#666" />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Annual Salary ($)</Text>
          <TextInput
            style={styles.input}
            value={annualSalary}
            onChangeText={setAnnualSalary}
            placeholder="125000"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Paychecks per Year</Text>
          <TextInput
            style={styles.input}
            value={paychecksPerYear}
            onChangeText={setPaychecksPerYear}
            placeholder="26"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>HSA Contribution ($)</Text>
          <TextInput
            style={styles.input}
            value={hsaContribution}
            onChangeText={setHsaContribution}
            placeholder="2300"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>401(k) Contribution (%)</Text>
          <TextInput
            style={styles.input}
            value={retirementPercent}
            onChangeText={setRetirementPercent}
            placeholder="4"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Benefits per Paycheck ($)</Text>
          <TextInput
            style={styles.input}
            value={benefitsPerPaycheck}
            onChangeText={setBenefitsPerPaycheck}
            placeholder="47.10"
            keyboardType="numeric"
          />
        </View>
      </View>

      {/* Expenses Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Monthly Expenses</Text>
        {expenses.map((expense, index) => (
          <View key={index} style={styles.expenseRow}>
            <TextInput
              style={[styles.input, styles.expenseName]}
              value={expense.name}
              onChangeText={(value) => updateExpense(index, 'name', value)}
              placeholder="Expense name"
            />
            <TextInput
              style={[styles.input, styles.expenseAmount]}
              value={expense.amount}
              onChangeText={(value) => updateExpense(index, 'amount', value)}
              placeholder="Amount"
              keyboardType="numeric"
            />
            {expenses.length > 1 && (
              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => removeExpense(index)}
              >
                <Icon name="close" size={20} color="#FF3B30" />
              </TouchableOpacity>
            )}
          </View>
        ))}
        <TouchableOpacity style={styles.addButton} onPress={addExpense}>
          <Icon name="add" size={20} color="#007AFF" />
          <Text style={styles.addButtonText}>Add Expense</Text>
        </TouchableOpacity>
      </View>

      {/* Debt Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Debt Information</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Monthly Debt Payment ($)</Text>
          <TextInput
            style={styles.input}
            value={monthlyDebtPayment}
            onChangeText={setMonthlyDebtPayment}
            placeholder="2000"
            keyboardType="numeric"
          />
        </View>

        {debts.map((debt, index) => (
          <View key={index} style={styles.debtRow}>
            <TextInput
              style={[styles.input, styles.debtName]}
              value={debt.name}
              onChangeText={(value) => updateDebt(index, 'name', value)}
              placeholder="Debt name"
            />
            <TextInput
              style={[styles.input, styles.debtAmount]}
              value={debt.total}
              onChangeText={(value) => updateDebt(index, 'total', value)}
              placeholder="Total debt"
              keyboardType="numeric"
            />
            <TextInput
              style={[styles.input, styles.debtPaid]}
              value={debt.paid}
              onChangeText={(value) => updateDebt(index, 'paid', value)}
              placeholder="Amount paid"
              keyboardType="numeric"
            />
            {debts.length > 1 && (
              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => removeDebt(index)}
              >
                <Icon name="close" size={20} color="#FF3B30" />
              </TouchableOpacity>
            )}
          </View>
        ))}
        <TouchableOpacity style={styles.addButton} onPress={addDebt}>
          <Icon name="add" size={20} color="#007AFF" />
          <Text style={styles.addButtonText}>Add Debt</Text>
        </TouchableOpacity>
      </View>

      {/* Budget Summary */}
      {budgetData && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Summary</Text>
          <View style={styles.summaryCard}>
            {budgetData.account_balances?.map((item: any, index: number) => (
              <View key={index} style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>{item.account.account_name}</Text>
                <Text style={styles.summaryValue}>
                  {formatCurrency(item.balance?.current_balance || 0)}
                </Text>
              </View>
            ))}
            {budgetData.total_cash && (
              <View style={[styles.summaryRow, styles.summaryRowTotal]}>
                <Text style={styles.summaryLabelTotal}>Total Cash</Text>
                <Text style={styles.summaryValueTotal}>
                  {formatCurrency(budgetData.total_cash)}
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Calculate Button */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.calculateButton} onPress={calculateBudget}>
          <Text style={styles.calculateButtonText}>Calculate Budget</Text>
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
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  hero: {
    backgroundColor: '#0A84FF',
    paddingTop: 64,
    paddingBottom: 32,
    paddingHorizontal: 24,
  },
  heroTitle: {
    fontSize: 28,
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
    paddingBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#111',
  },
  pickerContainer: {
    marginBottom: 0,
  },
  pickerButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pickerText: {
    fontSize: 16,
    color: '#111',
  },
  expenseRow: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'center',
    gap: 8,
  },
  expenseName: {
    flex: 1,
    marginBottom: 0,
  },
  expenseAmount: {
    width: 120,
    marginBottom: 0,
  },
  debtRow: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  debtName: {
    flex: 1,
    marginBottom: 0,
  },
  debtAmount: {
    width: 100,
    marginBottom: 0,
  },
  debtPaid: {
    width: 100,
    marginBottom: 0,
  },
  removeButton: {
    padding: 8,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EAF2FF',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  addButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 2},
    shadowRadius: 8,
    elevation: 2,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  summaryRowTotal: {
    borderBottomWidth: 0,
    borderTopWidth: 2,
    borderTopColor: '#0A84FF',
    marginTop: 8,
    paddingTop: 16,
  },
  summaryLabel: {
    fontSize: 15,
    color: '#666',
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
  },
  summaryLabelTotal: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  summaryValueTotal: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0A84FF',
  },
  calculateButton: {
    backgroundColor: '#0A84FF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 32,
  },
  calculateButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});

