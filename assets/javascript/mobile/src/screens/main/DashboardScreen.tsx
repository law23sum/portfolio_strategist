import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { LineChart, BarChart } from 'react-native-chart-kit';
import apiService from '../../services/api';

const screenWidth = Dimensions.get('window').width;

// Helper function to convert data to chart format (similar to web app)
const listToDict = (list: any[]) => {
  return list.reduce((acc: any, item: any) => {
    acc[item.date] = item.count;
    return acc;
  }, {});
};

const toDateString = (dateObj: Date) => {
  return dateObj.toISOString().split('T')[0];
};

const getTimeSeriesData = (start: Date, end: Date, data: any[]) => {
  const dataDict = listToDict(data);
  const chartData: { x: string; y: number }[] = [];
  const current = new Date(start);
  while (current <= end) {
    const curString = toDateString(current);
    chartData.push({
      x: curString,
      y: dataDict[curString] || 0,
    });
    current.setDate(current.getDate() + 1);
  }
  return chartData;
};

export default function DashboardScreen({ navigation }: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [userDetails, setUserDetails] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);

  const loadData = async () => {
    try {
      const [statsResponse, userResponse] = await Promise.all([
        apiService.getDashboardStats(),
        apiService.getUserDetails(),
      ]);

      if (statsResponse.data) {
        setStats(statsResponse.data);
        
        // Process chart data if available
        if (statsResponse.data.signups_by_date) {
          const endDate = new Date();
          const startDate = new Date();
          startDate.setDate(startDate.getDate() - 30); // Last 30 days
          const timeSeriesData = getTimeSeriesData(
            startDate,
            endDate,
            statsResponse.data.signups_by_date
          );
          
          setChartData({
            labels: timeSeriesData.map((d, i) => 
              i % Math.ceil(timeSeriesData.length / 7) === 0 
                ? new Date(d.x).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                : ''
            ),
            datasets: [
              {
                data: timeSeriesData.map(d => d.y),
                color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
                strokeWidth: 2,
              },
            ],
          });
        }
      }
      if (userResponse.data) {
        setUserDetails(userResponse.data);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
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
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome back!</Text>
        {userDetails && (
          <Text style={styles.username}>{userDetails.username || userDetails.email}</Text>
        )}
      </View>

      <View style={styles.cardsContainer}>
        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Records', { screen: 'Upload' })}
            >
              <Icon name="cloud-upload" size={32} color="#007AFF" />
              <Text style={styles.actionText}>Upload Document</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('StockAnalysis', { screen: 'Analyze' })}
            >
              <Icon name="trending-up" size={32} color="#007AFF" />
              <Text style={styles.actionText}>Analyze Stock</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Records', { screen: 'LinkedAccounts' })}
            >
              <Icon name="account-balance" size={32} color="#007AFF" />
              <Text style={styles.actionText}>Link Account</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Records', { screen: 'Insights' })}
            >
              <Icon name="insights" size={32} color="#007AFF" />
              <Text style={styles.actionText}>View Insights</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Chat')}
            >
              <Icon name="chat" size={32} color="#007AFF" />
              <Text style={styles.actionText}>Chat Assistant</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Charts Section */}
        {chartData && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Activity Trends</Text>
            <View style={styles.chartCard}>
              <LineChart
                data={chartData}
                width={screenWidth - 64}
                height={220}
                chartConfig={{
                  backgroundColor: '#ffffff',
                  backgroundGradientFrom: '#ffffff',
                  backgroundGradientTo: '#ffffff',
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  style: {
                    borderRadius: 16,
                  },
                  propsForDots: {
                    r: '4',
                    strokeWidth: '2',
                    stroke: '#007AFF',
                  },
                }}
                bezier
                style={styles.chart}
                withInnerLines={false}
                withOuterLines={true}
                withVerticalLabels={true}
                withHorizontalLabels={true}
              />
            </View>
          </View>
        )}

        {/* Financial Overview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Financial Overview</Text>
          <View style={styles.statsCard}>
            <View style={styles.statRow}>
              <Icon name="attach-money" size={24} color="#4CAF50" />
              <View style={styles.statContent}>
                <Text style={styles.statLabel}>Total Assets</Text>
                <Text style={styles.statValue}>
                  {stats?.total_assets ? `$${stats.total_assets.toLocaleString()}` : 'N/A'}
                </Text>
              </View>
            </View>
            <View style={styles.statRow}>
              <Icon name="trending-up" size={24} color="#2196F3" />
              <View style={styles.statContent}>
                <Text style={styles.statLabel}>Investments</Text>
                <Text style={styles.statValue}>
                  {stats?.investments ? `$${stats.investments.toLocaleString()}` : 'N/A'}
                </Text>
              </View>
            </View>
            <View style={styles.statRow}>
              <Icon name="savings" size={24} color="#FF9800" />
              <View style={styles.statContent}>
                <Text style={styles.statLabel}>Savings</Text>
                <Text style={styles.statValue}>
                  {stats?.savings ? `$${stats.savings.toLocaleString()}` : 'N/A'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Recent Activity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          <View style={styles.activityCard}>
            <Text style={styles.emptyText}>No recent activity</Text>
          </View>
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
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    paddingTop: 60,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  username: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  cardsContainer: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionText: {
    marginTop: 8,
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    textAlign: 'center',
  },
  statsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  statContent: {
    marginLeft: 12,
    flex: 1,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  activityCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  emptyText: {
    color: '#999',
    fontSize: 14,
  },
  chartCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    alignItems: 'center',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
});

