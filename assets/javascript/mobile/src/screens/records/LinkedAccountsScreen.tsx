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

interface LinkedAccountsScreenProps {
  navigation: any;
}

export default function LinkedAccountsScreen({ navigation }: LinkedAccountsScreenProps) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [accounts, setAccounts] = useState<any[]>([]);

  const loadAccounts = async () => {
    try {
      const response = await apiService.getLinkedAccounts();
      if (response.data) {
        setAccounts(Array.isArray(response.data) ? response.data : []);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadAccounts();
  };

  const handleLinkAccount = async () => {
    try {
      const response = await apiService.createLinkToken();
      if (response.data) {
        Alert.alert(
          'Link Account',
          'Account linking functionality would open here. In a real app, this would integrate with Plaid or similar service.',
          [{ text: 'OK' }]
        );
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to create link token');
    }
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
      <View style={styles.content}>
        <Text style={styles.title}>Linked Accounts</Text>
        <Text style={styles.subtitle}>Manage your connected financial accounts</Text>

        <TouchableOpacity
          style={styles.linkButton}
          onPress={handleLinkAccount}
        >
          <Icon name="add" size={24} color="#007AFF" />
          <Text style={styles.linkButtonText}>Link New Account</Text>
        </TouchableOpacity>

        {accounts.length > 0 ? (
          <View style={styles.accountsList}>
            {accounts.map((account: any, index: number) => {
              const accountId = account.id || account.account_id;
              const accountName = account.account_name || account.name || 'Account';
              const accountType = account.account_type || account.type || 'Bank Account';
              const latestBalance = account.latest_balance || account.balance;
              const balance = latestBalance?.current_balance || account.balance || 0;

              return (
                <TouchableOpacity
                  key={index}
                  style={styles.accountCard}
                  onPress={() => {
                    if (accountId) {
                      navigation.navigate('AccountDetail', { accountId });
                    }
                  }}
                >
                  <Icon name="account-balance" size={32} color="#007AFF" />
                  <View style={styles.accountInfo}>
                    <Text style={styles.accountName}>{accountName}</Text>
                    <Text style={styles.accountType}>{accountType}</Text>
                    {balance && (
                      <Text style={styles.accountBalance}>
                        ${parseFloat(balance).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </Text>
                    )}
                  </View>
                  <Icon name="chevron-right" size={24} color="#999" />
                </TouchableOpacity>
              );
            })}
          </View>
        ) : (
          <View style={styles.emptyContainer}>
            <Icon name="account-balance" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No linked accounts</Text>
            <Text style={styles.emptySubtext}>
              Link your bank or investment accounts to automatically sync your financial data
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
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  linkButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  accountsList: {
    marginTop: 8,
  },
  accountCard: {
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
  accountInfo: {
    flex: 1,
    marginLeft: 16,
  },
  accountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  accountType: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  accountBalance: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginTop: 4,
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
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});



