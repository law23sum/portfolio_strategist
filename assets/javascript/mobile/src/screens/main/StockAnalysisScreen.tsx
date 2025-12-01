import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

export default function StockAnalysisScreen({ navigation }: any) {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Stock Analysis</Text>
        <Text style={styles.subtitle}>Analyze stocks and create investment plans</Text>
      </View>

      <View style={styles.content}>
        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigation.navigate('Analyze')}
        >
          <Icon name="search" size={32} color="#007AFF" />
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Analyze Stock</Text>
            <Text style={styles.actionDescription}>
              Analyze a stock symbol and get detailed insights
            </Text>
          </View>
          <Icon name="chevron-right" size={24} color="#999" />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigation.navigate('Loan')}
        >
          <Icon name="account-balance" size={32} color="#007AFF" />
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Loan Analysis</Text>
            <Text style={styles.actionDescription}>
              Analyze personal loan options and rates
            </Text>
          </View>
          <Icon name="chevron-right" size={24} color="#999" />
        </TouchableOpacity>

        <View style={styles.infoCard}>
          <Icon name="info" size={24} color="#007AFF" />
          <Text style={styles.infoText}>
            Get comprehensive stock analysis including forecasts, ratios, and AI-powered insights
          </Text>
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
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  content: {
    padding: 16,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionContent: {
    flex: 1,
    marginLeft: 16,
  },
  actionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 14,
    color: '#666',
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
  },
  infoText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
});



