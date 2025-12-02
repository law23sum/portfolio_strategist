import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

interface AccountDetailScreenProps {
  route: {
    params: {
      accountId: number;
    };
  };
  navigation: any;
}

export default function AccountDetailScreen({ route, navigation }: AccountDetailScreenProps) {
  const { accountId } = route.params;
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [account, setAccount] = useState<any>(null);

  const loadAccount = async () => {
    try {
      const response = await apiService.getAccountDetail(accountId);
      if (response.data) {
        setAccount(response.data);
      } else if (response.error) {
        Alert.alert('Error', response.error);
      }
    } catch (error: any) {
      console.error('Error loading account:', error);
      Alert.alert('Error', error.message || 'Failed to load account details');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAccount();
  }, [accountId]);

  const onRefresh = () => {
    setRefreshing(true);
    loadAccount();
  };

  const handleSync = async () => {
    try {
      const response = await apiService.syncAccount(accountId);
      if (response.data) {
        Alert.alert('Success', 'Account sync started');
        // Reload after a delay
        setTimeout(() => {
          loadAccount();
        }, 2000);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to sync account');
    }
  };

  const handleDisconnect = () => {
    Alert.alert(
      'Disconnect Account',
      'Are you sure you want to disconnect this account?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disconnect',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await apiService.disconnectAccount(accountId);
              if (response.data) {
                Alert.alert('Success', 'Account disconnected');
                navigation.goBack();
              }
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to disconnect account');
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!account) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Account not found</Text>
      </View>
    );
  }

  const latestBalance = account.latest_balance;
  const recentTransactions = account.recent_transactions || [];
  const holdings = account.holdings || [];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.content}>
        {/* Account Header */}
        <View style={styles.accountHeader}>
          <View style={styles.accountIcon}>
            <Icon name="account-balance" size={32} color="#007AFF" />
          </View>
          <View style={styles.accountInfo}>
            <Text style={styles.accountName}>{account.account?.account_name || 'Account'}</Text>
            <Text style={styles.institutionName}>{account.account?.institution_name || ''}</Text>
            <Text style={styles.accountType}>
              {account.account?.account_type || 'Unknown'} • {account.account?.account_number_masked || ''}
            </Text>
          </View>
        </View>

        {/* Balance Card */}
        {latestBalance && (
          <View style={styles.balanceCard}>
            <Text style={styles.balanceLabel}>Current Balance</Text>
            <Text style={styles.balanceValue}>
              ${parseFloat(latestBalance.current_balance || 0).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>
            {latestBalance.available_balance && (
              <Text style={styles.availableBalance}>
                Available: ${parseFloat(latestBalance.available_balance).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            )}
          </View>
        )}

        {/* Actions */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.actionButton} onPress={handleSync}>
            <Icon name="sync" size={24} color="#007AFF" />
            <Text style={styles.actionButtonText}>Sync Account</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionButton, styles.dangerButton]} onPress={handleDisconnect}>
            <Icon name="link-off" size={24} color="#F44336" />
            <Text style={[styles.actionButtonText, styles.dangerText]}>Disconnect</Text>
          </TouchableOpacity>
        </View>

        {/* Investment Holdings */}
        {holdings.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Holdings</Text>
            {holdings.map((holding: any, index: number) => (
              <View key={index} style={styles.holdingCard}>
                <View style={styles.holdingHeader}>
                  <Text style={styles.holdingName}>
                    {holding.security_name || holding.security_ticker || 'Unknown'}
                  </Text>
                  <Text style={styles.holdingValue}>
                    ${parseFloat(holding.value || 0).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <View style={styles.holdingDetails}>
                  <Text style={styles.holdingDetail}>
                    Quantity: {parseFloat(holding.quantity || 0).toLocaleString()}
                  </Text>
                  {holding.cost_basis && (
                    <Text style={styles.holdingDetail}>
                      Cost Basis: ${parseFloat(holding.cost_basis).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Recent Transactions */}
        {recentTransactions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recent Transactions</Text>
            {recentTransactions.map((transaction: any, index: number) => (
              <View key={index} style={styles.transactionCard}>
                <View style={styles.transactionHeader}>
                  <View style={styles.transactionIcon}>
                    <Icon
                      name={transaction.transaction_type === 'credit' ? 'arrow-downward' : 'arrow-upward'}
                      size={20}
                      color={transaction.transaction_type === 'credit' ? '#4CAF50' : '#F44336'}
                    />
                  </View>
                  <View style={styles.transactionContent}>
                    <Text style={styles.transactionDescription}>
                      {transaction.description || 'Transaction'}
                    </Text>
                    <Text style={styles.transactionDate}>
                      {new Date(transaction.date).toLocaleDateString()}
                    </Text>
                  </View>
                  <Text
                    style={[
                      styles.transactionAmount,
                      { color: transaction.transaction_type === 'credit' ? '#4CAF50' : '#F44336' },
                    ]}
                  >
                    {transaction.transaction_type === 'credit' ? '+' : '-'}$
                    {parseFloat(transaction.amount || 0).toFixed(2)}
                  </Text>
                </View>
                {transaction.category && (
                  <Text style={styles.transactionCategory}>{transaction.category}</Text>
                )}
              </View>
            ))}
          </View>
        )}

        {recentTransactions.length === 0 && holdings.length === 0 && (
          <View style={styles.emptyContainer}>
            <Icon name="info-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No transactions or holdings available</Text>
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
  errorText: {
    fontSize: 16,
    color: '#F44336',
  },
  content: {
    padding: 16,
  },
  accountHeader: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  accountIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  accountInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  accountName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  institutionName: {
    fontSize: 16,
    color: '#666',
    marginBottom: 4,
  },
  accountType: {
    fontSize: 14,
    color: '#999',
  },
  balanceCard: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  balanceLabel: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
    marginBottom: 8,
  },
  balanceValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  availableBalance: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
  },
  actionsContainer: {
    flexDirection: 'row',
    marginBottom: 24,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  dangerButton: {
    borderWidth: 1,
    borderColor: '#F44336',
  },
  actionButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  dangerText: {
    color: '#F44336',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  holdingCard: {
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
  holdingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  holdingName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  holdingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  holdingDetails: {
    flexDirection: 'row',
    gap: 16,
  },
  holdingDetail: {
    fontSize: 14,
    color: '#666',
  },
  transactionCard: {
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
  transactionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  transactionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  transactionContent: {
    flex: 1,
  },
  transactionDescription: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 4,
  },
  transactionDate: {
    fontSize: 12,
    color: '#666',
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: '600',
  },
  transactionCategory: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
    fontStyle: 'italic',
  },
  emptyContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
    textAlign: 'center',
  },
});

