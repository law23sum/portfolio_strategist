import React, {useEffect, useMemo, useState} from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

type QuickAction = {
  title: string;
  subtitle: string;
  icon: string;
  route: string;
  params?: Record<string, any>;
};

type FeatureBlock = {
  title: string;
  description: string;
  icon: string;
  route: string;
};

const QUICK_ACTIONS: QuickAction[] = [
  {
    title: 'Upload Documents',
    subtitle: 'Statements, invoices, receipts',
    icon: 'cloud-upload',
    route: 'Records',
    params: {screen: 'Upload'},
  },
  {
    title: 'Analyze Stock',
    subtitle: 'Forecasts & ratios',
    icon: 'show-chart',
    route: 'StockAnalysis',
    params: {screen: 'Analyze'},
  },
  {
    title: 'Link Accounts',
    subtitle: 'Plaid-ready accounts',
    icon: 'account-balance',
    route: 'Records',
    params: {screen: 'LinkedAccounts'},
  },
  {
    title: 'Budget Planner',
    subtitle: 'Taxes, expenses, debt',
    icon: 'account-balance-wallet',
    route: 'BudgetPlanner',
  },
  {
    title: 'AI Chat',
    subtitle: 'Ask for guidance',
    icon: 'chat-bubble',
    route: 'Chat',
  },
  {
    title: 'Investment & Savings',
    subtitle: 'Stocks, CDs, bonds',
    icon: 'savings',
    route: 'InvestmentSavings',
  },
];

const FEATURE_BLOCKS: FeatureBlock[] = [
  {
    title: 'Financial Records',
    description:
      'Insights, Explorer, Uploads and Linked Accounts mirror the full Portfolio Strategist web workflow.',
    icon: 'folder-shared',
    route: 'Records',
  },
  {
    title: 'Stock Analysis Suite',
    description:
      'Geometric Brownian Motion models, AI commentary, PDF exports and loan analysis available on mobile.',
    icon: 'trending-up',
    route: 'StockAnalysis',
  },
  {
    title: 'Solutions Hub',
    description:
      'Budget planner, retirement planning, portfolio management and AI solutions from the web experience.',
    icon: 'lightbulb',
    route: 'Solutions',
  },
];

const STAT_FIELDS = [
  {key: 'total_documents', label: 'Documents'},
  {key: 'total_accounts', label: 'Linked Accounts'},
  {key: 'total_analyses', label: 'Analyses'},
];

export default function DashboardScreen({navigation}: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [userDetails, setUserDetails] = useState<any>(null);

  const loadData = async () => {
    try {
      const [statsResponse, userResponse] = await Promise.all([
        apiService.getDashboardSummary(),
        apiService.getUserDetails(),
      ]);

      if (statsResponse.data) {
        setStats(statsResponse.data);
      }
      if (userResponse.data) {
        setUserDetails(userResponse.data);
      }
    } catch (error) {
      console.error('Error loading dashboard', error);
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

  const statCards = useMemo(() => {
    if (!stats) {
      return [];
    }
    return STAT_FIELDS.map(item => ({
      label: item.label,
      value: formatNumber(stats[item.key]),
    }));
  }, [stats]);

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
        <Text style={styles.heroEyebrow}>The Portfolio Strategist</Text>
        <Text style={styles.heroTitle}>
          {`Welcome${userDetails?.username ? `, ${userDetails.username}` : ''}`}
        </Text>
        <Text style={styles.heroSubtitle}>
          Organize records, run analytics, plan solutions and chat with AI — exactly like the web app.
        </Text>
        {stats?.last_login && (
          <Text style={styles.heroMeta}>
            Last synced {new Date(stats.last_login).toLocaleString()}
          </Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick actions</Text>
        <View style={styles.actionGrid}>
          {QUICK_ACTIONS.map(action => (
            <TouchableOpacity
              key={action.title}
              style={styles.actionTile}
              onPress={() => navigation.navigate(action.route, action.params)}
            >
              <View style={styles.actionIconWrap}>
                <Icon name={action.icon} size={22} color="#0A84FF" />
              </View>
              <Text style={styles.actionTileTitle}>{action.title}</Text>
              <Text style={styles.actionTileSubtitle}>{action.subtitle}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Web parity modules</Text>
        {FEATURE_BLOCKS.map(block => (
          <TouchableOpacity
            key={block.title}
            style={styles.featureCard}
            onPress={() => navigation.navigate(block.route)}
          >
            <Icon name={block.icon} size={28} color="#0A84FF" style={styles.featureIcon} />
            <View style={styles.featureContent}>
              <Text style={styles.featureTitle}>{block.title}</Text>
              <Text style={styles.featureDescription}>{block.description}</Text>
            </View>
            <Icon name="chevron-right" size={24} color="#8E8E93" />
          </TouchableOpacity>
        ))}
      </View>

      {statCards.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>At a glance</Text>
          <View style={styles.statsRow}>
            {statCards.map(card => (
              <View key={card.label} style={styles.statCard}>
                <Text style={styles.statLabel}>{card.label}</Text>
                <Text style={styles.statValue}>{card.value}</Text>
              </View>
            ))}
          </View>
          <Text style={styles.statFootnote}>
            These values mirror the Portfolio Strategist web dashboard in real-time.
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

function formatNumber(value: number | string | undefined): string {
  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-US').format(value);
  }
  if (typeof value === 'string' && value.trim().length > 0) {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return new Intl.NumberFormat('en-US').format(parsed);
    }
  }
  return '—';
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
  heroEyebrow: {
    color: '#D7EAFF',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#fff',
  },
  heroSubtitle: {
    marginTop: 8,
    color: '#E6F1FF',
    fontSize: 15,
    lineHeight: 22,
  },
  heroMeta: {
    marginTop: 12,
    color: '#BEDBFF',
    fontSize: 13,
  },
  section: {
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 16,
  },
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionTile: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 10,
    elevation: 2,
  },
  actionIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#EAF2FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  actionTileTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
  },
  actionTileSubtitle: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
  },
  featureCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 10,
    elevation: 2,
  },
  featureIcon: {
    marginRight: 16,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
    marginBottom: 4,
  },
  featureDescription: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    marginRight: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 8,
    elevation: 1,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0A84FF',
    marginTop: 8,
  },
  statFootnote: {
    fontSize: 13,
    color: '#777',
    marginTop: 12,
  },
});
