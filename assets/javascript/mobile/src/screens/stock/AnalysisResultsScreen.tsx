import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function AnalysisResultsScreen({ route, navigation }: any) {
  const { analysisId, data: initialData } = route.params || {};
  const [loading, setLoading] = useState(!initialData);
  const [analysisData, setAnalysisData] = useState(initialData);

  useEffect(() => {
    if (analysisId && !initialData) {
      loadResults();
    }
  }, [analysisId]);

  const loadResults = async () => {
    try {
      const response = await apiService.getAnalysisResults(analysisId);
      if (response.data) {
        setAnalysisData(response.data);
      }
    } catch (error) {
      console.error('Error loading results:', error);
    } finally {
      setLoading(false);
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
      contentContainerStyle={styles.scrollContent}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.content}>
        {analysisData ? (
          <>
            <View style={styles.header}>
              <Text style={styles.symbol}>{analysisData.symbol || 'N/A'}</Text>
              <Text style={styles.date}>
                Analyzed on {new Date(analysisData.analysis_date || Date.now()).toLocaleDateString()}
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Forecast</Text>
              <View style={styles.card}>
                <Text style={styles.cardText}>
                  {analysisData.forecast_data
                    ? 'Forecast data available'
                    : 'No forecast data available'}
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Financial Ratios</Text>
              <View style={styles.card}>
                <Text style={styles.cardText}>
                  {analysisData.ratios_table
                    ? 'Ratios analysis available'
                    : 'No ratios data available'}
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>AI Assessment</Text>
              <View style={styles.card}>
                <Text style={styles.cardText}>
                  {analysisData.ai_assessment || 'No assessment available'}
                </Text>
              </View>
            </View>

            <View style={styles.actions}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => {
                  // Handle PDF download
                  console.log('Download PDF');
                }}
              >
                <Icon name="file-download" size={20} color="#007AFF" />
                <Text style={styles.actionButtonText}>Download PDF</Text>
              </TouchableOpacity>
            </View>
          </>
        ) : (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No analysis data available</Text>
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
  scrollContent: {
    paddingBottom: 24,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: 16,
  },
  header: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  symbol: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  date: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  actions: {
    marginTop: 24,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  actionButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  emptyContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
  },
});



