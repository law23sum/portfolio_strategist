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

// Navigation cards matching web investment-savings page
const ASSESSMENT_CARDS = [
  {
    title: 'Stocks Assessment',
    description: 'Analyze stocks with GBM, mean reversion and macro-aware models with ratios, AI commentary and exports.',
    icon: 'trending-up',
    route: {screen: 'StocksAssessment'},
  },
  {
    title: 'Savings Assessment',
    description: 'Forecast your savings account growth across multiple time periods.',
    icon: 'savings',
    route: {screen: 'SavingsAssessment'},
  },
  {
    title: 'CD Assessment',
    description: 'Evaluate Certificate of Deposit investments and forecast returns.',
    icon: 'account-balance-wallet',
    route: {screen: 'CDAssessment'},
  },
  {
    title: 'Bond Assessment',
    description: 'Analyze bond investments and calculate yield projections.',
    icon: 'monetization-on',
    route: {screen: 'BondAssessment'},
  },
];

const formatCurrency = (value: number | null | undefined) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '$0.00';
  }
  return `$${Intl.NumberFormat('en-US', {maximumFractionDigits: 2}).format(value)}`;
};

export default function StockAnalysisScreen({navigation}: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [addSymbol, setAddSymbol] = useState('');
  const [addNickname, setAddNickname] = useState('');
  const [addNotes, setAddNotes] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const loadData = async () => {
    try {
      const [summaryRes, watchlistRes] = await Promise.all([
        apiService.getInvestmentSavingsSummary(),
        apiService.getWatchlist(),
      ]);

      // Handle authentication errors
      if (summaryRes.status === 403 || summaryRes.status === 401) {
        console.warn('[StockAnalysisScreen] Authentication required - user may need to login');
        // Don't show error alert here as it's expected if user isn't logged in
        // The screen will just show empty state
      } else if (summaryRes.error) {
        console.error('[StockAnalysisScreen] Error loading summary:', summaryRes.error);
      } else if (summaryRes.data) {
        setSummary(summaryRes.data);
      }

      if (watchlistRes.status === 403 || watchlistRes.status === 401) {
        console.warn('[StockAnalysisScreen] Authentication required for watchlist');
        // Don't show error alert here as it's expected if user isn't logged in
      } else if (watchlistRes.error) {
        console.error('[StockAnalysisScreen] Error loading watchlist:', watchlistRes.error);
      } else if (watchlistRes.data && watchlistRes.data.entries) {
        setWatchlist(watchlistRes.data.entries);
      }
    } catch (error: any) {
      console.error('[StockAnalysisScreen] Error loading data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleAddToWatchlist = async () => {
    if (!addSymbol.trim()) {
      Alert.alert('Error', 'Please enter a stock symbol');
      return;
    }

    setWatchlistLoading(true);
    try {
      const response = await apiService.addToWatchlist(
        addSymbol.toUpperCase(),
        addNickname || undefined,
        addNotes || undefined,
      );

      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        setAddSymbol('');
        setAddNickname('');
        setAddNotes('');
        setShowAddForm(false);
        await loadData();
        Alert.alert('Success', `Added ${addSymbol.toUpperCase()} to watchlist`);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add to watchlist');
    } finally {
      setWatchlistLoading(false);
    }
  };

  const handleRemoveFromWatchlist = async (entryId: number, symbol: string) => {
    Alert.alert('Remove from Watchlist', `Remove ${symbol}?`, [
      {text: 'Cancel', style: 'cancel'},
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            const response = await apiService.removeFromWatchlist(entryId);
            if (response.error) {
              Alert.alert('Error', response.error);
            } else {
              await loadData();
            }
          } catch (error: any) {
            Alert.alert('Error', error.message || 'Failed to remove from watchlist');
          }
        },
      },
    ]);
  };

  const handleRefreshWatchlist = async (entryId: number) => {
    try {
      const response = await apiService.refreshWatchlist(entryId);
      if (response.error) {
        Alert.alert('Error', response.error);
      } else {
        Alert.alert('Success', 'Refresh queued');
        await loadData();
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to refresh');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0A84FF" />
      </View>
    );
  }

  const totalValue =
    (summary?.stocks?.total_value || 0) +
    (summary?.savings?.total_value || 0) +
    (summary?.cds?.total_value || 0) +
    (summary?.bonds?.total_value || 0);

  const totalDecade =
    (summary?.stocks?.total_decade || 0) +
    (summary?.savings?.total_decade || 0) +
    (summary?.cds?.total_decade || 0) +
    (summary?.bonds?.total_decade || 0);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
    >
      <View style={styles.hero}>
        <Text style={styles.heroEyebrow}>Investment & Savings</Text>
        <Text style={styles.heroTitle}>Manage and track your investments</Text>
        <Text style={styles.heroSubtitle}>
          Analyze stocks, savings accounts, CDs, and bonds across multiple time periods.
        </Text>
      </View>

      {/* Portfolio Summary */}
      {summary && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Portfolio Summary</Text>
          <View style={styles.summaryGrid}>
            <View style={styles.summaryCard}>
              <Text style={styles.summaryCardTitle}>Stocks</Text>
              <Text style={styles.summaryValue}>{formatCurrency(summary.stocks?.total_value)}</Text>
              <Text style={styles.summarySubtext}>{summary.stocks?.count || 0} assessment(s)</Text>
            </View>
            <View style={styles.summaryCard}>
              <Text style={styles.summaryCardTitle}>Savings</Text>
              <Text style={styles.summaryValue}>{formatCurrency(summary.savings?.total_value)}</Text>
              <Text style={styles.summarySubtext}>{summary.savings?.count || 0} account(s)</Text>
            </View>
            <View style={styles.summaryCard}>
              <Text style={styles.summaryCardTitle}>CDs</Text>
              <Text style={styles.summaryValue}>{formatCurrency(summary.cds?.total_value)}</Text>
              <Text style={styles.summarySubtext}>{summary.cds?.count || 0} account(s)</Text>
            </View>
            <View style={styles.summaryCard}>
              <Text style={styles.summaryCardTitle}>Bonds</Text>
              <Text style={styles.summaryValue}>{formatCurrency(summary.bonds?.total_value)}</Text>
              <Text style={styles.summarySubtext}>{summary.bonds?.count || 0} investment(s)</Text>
            </View>
          </View>
          <View style={styles.totalCard}>
            <Text style={styles.totalLabel}>Total Portfolio</Text>
            <Text style={styles.totalValue}>{formatCurrency(totalValue)}</Text>
            <Text style={styles.totalSubtext}>10-Year Projection: {formatCurrency(totalDecade)}</Text>
          </View>
        </View>
      )}

      {/* Watchlist Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Watchlist</Text>
          <TouchableOpacity onPress={() => setShowAddForm(!showAddForm)}>
            <Icon name={showAddForm ? 'close' : 'add'} size={24} color="#0A84FF" />
          </TouchableOpacity>
        </View>
        <Text style={styles.sectionSubtitle}>
          Symbols here are refreshed via Yahoo Finance scraping in the background.
        </Text>

        {showAddForm && (
          <View style={styles.addForm}>
            <TextInput
              style={styles.input}
              placeholder="Symbol (e.g., AAPL)"
              value={addSymbol}
              onChangeText={setAddSymbol}
              autoCapitalize="characters"
            />
            <TextInput
              style={styles.input}
              placeholder="Nickname (optional)"
              value={addNickname}
              onChangeText={setAddNickname}
            />
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Notes (optional)"
              value={addNotes}
              onChangeText={setAddNotes}
              multiline
              numberOfLines={3}
            />
            <TouchableOpacity
              style={[styles.addButton, watchlistLoading && styles.buttonDisabled]}
              onPress={handleAddToWatchlist}
              disabled={watchlistLoading}
            >
              {watchlistLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.addButtonText}>Add to Watchlist</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {watchlist.length === 0 ? (
          <View style={styles.emptyCard}>
            <Icon name="watch-later" size={48} color="#999" />
            <Text style={styles.emptyText}>No symbols in watchlist</Text>
            <Text style={styles.emptySubtext}>Add symbols to track their performance</Text>
          </View>
        ) : (
          watchlist.map(entry => (
            <View key={entry.id} style={styles.watchlistCard}>
              <View style={styles.watchlistHeader}>
                <View>
                  <Text style={styles.watchlistSymbol}>{entry.symbol}</Text>
                  {entry.nickname && <Text style={styles.watchlistNickname}>{entry.nickname}</Text>}
                </View>
                <View style={styles.watchlistActions}>
                  <TouchableOpacity
                    onPress={() => handleRefreshWatchlist(entry.id)}
                    style={styles.watchlistActionButton}
                  >
                    <Icon name="refresh" size={20} color="#0A84FF" />
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => handleRemoveFromWatchlist(entry.id, entry.symbol)}
                    style={styles.watchlistActionButton}
                  >
                    <Icon name="delete" size={20} color="#FF3B30" />
                  </TouchableOpacity>
                </View>
              </View>
              {entry.snapshot && (
                <View style={styles.watchlistSnapshot}>
                  <Text style={styles.watchlistPrice}>
                    {formatCurrency(entry.snapshot.current_price)}
                  </Text>
                  {entry.snapshot.change_percent !== null && (
                    <Text
                      style={[
                        styles.watchlistChange,
                        (entry.snapshot.change_percent || 0) >= 0
                          ? styles.watchlistChangePositive
                          : styles.watchlistChangeNegative,
                      ]}
                    >
                      {(entry.snapshot.change_percent || 0) >= 0 ? '+' : ''}
                      {(entry.snapshot.change_percent || 0).toFixed(2)}%
                    </Text>
                  )}
                </View>
              )}
              {entry.notes && <Text style={styles.watchlistNotes}>{entry.notes}</Text>}
            </View>
          ))
        )}
      </View>

      {/* Assessment Tools */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Assessment Tools</Text>
        {ASSESSMENT_CARDS.map(item => (
          <TouchableOpacity
            key={item.title}
            style={styles.card}
            onPress={() => navigation.navigate(item.route.screen, item.route.params || {})}
          >
            <Icon name={item.icon} size={28} color="#0A84FF" style={styles.cardIcon} />
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardDescription}>{item.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#9C9C9C" />
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
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
  heroEyebrow: {
    color: '#D7EAFF',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  heroTitle: {
    fontSize: 26,
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
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#666',
    marginBottom: 16,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
    marginBottom: 16,
  },
  summaryCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: '1%',
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#0A84FF',
  },
  summaryCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0A84FF',
    marginBottom: 8,
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111',
    marginBottom: 4,
  },
  summarySubtext: {
    fontSize: 12,
    color: '#666',
  },
  totalCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  totalValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111',
    marginBottom: 4,
  },
  totalSubtext: {
    fontSize: 13,
    color: '#666',
  },
  addForm: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  addButton: {
    backgroundColor: '#0A84FF',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  watchlistCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 2},
    shadowRadius: 4,
    elevation: 2,
  },
  watchlistHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  watchlistSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
  },
  watchlistNickname: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
  watchlistActions: {
    flexDirection: 'row',
    gap: 12,
  },
  watchlistActionButton: {
    padding: 4,
  },
  watchlistSnapshot: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 8,
  },
  watchlistPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  watchlistChange: {
    fontSize: 14,
    fontWeight: '600',
  },
  watchlistChangePositive: {
    color: '#34C759',
  },
  watchlistChangeNegative: {
    color: '#FF3B30',
  },
  watchlistNotes: {
    fontSize: 13,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 13,
    color: '#999',
    marginTop: 4,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 10,
    elevation: 2,
  },
  cardIcon: {
    marginRight: 16,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  cardDescription: {
    marginTop: 4,
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});
