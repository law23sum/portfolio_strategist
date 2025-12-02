import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Picker,
} from 'react-native';
import apiService from '../../services/api';

export default function AnalyzeStockScreen({ navigation }: any) {
  const [symbol, setSymbol] = useState('');
  const [forecastDays, setForecastDays] = useState('365');
  const [equationType, setEquationType] = useState(
    'Geometric Brownian Motion External Macroeconomic Factors'
  );
  const [analyzing, setAnalyzing] = useState(false);

  const equationTypes = [
    'Geometric Brownian Motion',
    'Geometric Brownian Motion with Mean Reversion',
    'Geometric Brownian Motion External Macroeconomic Factors',
  ];

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      Alert.alert('Error', 'Please enter a stock symbol');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await apiService.analyzeStock(
        symbol.toUpperCase(),
        parseInt(forecastDays, 10),
        equationType
      );

      if (response.error) {
        Alert.alert('Analysis Failed', response.error);
      } else if (response.data) {
        // Navigate to results screen with analysis data
        navigation.navigate('Results', { analysisId: response.data.id || 1, data: response.data });
      }
    } catch (error: any) {
      Alert.alert('Analysis Failed', error.message || 'Failed to analyze stock');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Analyze Stock</Text>
        <Text style={styles.subtitle}>
          Enter a stock symbol to get comprehensive analysis
        </Text>

        <View style={styles.form}>
          <Text style={styles.label}>Stock Symbol</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., AAPL, NVDA, MSFT"
            value={symbol}
            onChangeText={setSymbol}
            autoCapitalize="characters"
            autoFocus
            editable={!analyzing}
          />

          <Text style={styles.label}>Forecast Days (1-1825)</Text>
          <TextInput
            style={styles.input}
            placeholder="365"
            value={forecastDays}
            onChangeText={setForecastDays}
            keyboardType="number-pad"
            editable={!analyzing}
          />

          <Text style={styles.label}>Analysis Model</Text>
          <View style={styles.pickerContainer}>
            {equationTypes.map((type, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.pickerOption,
                  equationType === type && styles.pickerOptionSelected,
                ]}
                onPress={() => setEquationType(type)}
                disabled={analyzing}
              >
                <Text
                  style={[
                    styles.pickerOptionText,
                    equationType === type && styles.pickerOptionTextSelected,
                  ]}
                >
                  {type}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {analyzing ? (
            <View style={styles.analyzingContainer}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.analyzingText}>Analyzing stock...</Text>
              <Text style={styles.analyzingSubtext}>This may take a few moments</Text>
            </View>
          ) : (
            <TouchableOpacity
              style={styles.analyzeButton}
              onPress={handleAnalyze}
              disabled={analyzing}
            >
              <Text style={styles.analyzeButtonText}>Analyze Stock</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>What you'll get:</Text>
          <Text style={styles.infoText}>• Stock price forecasts</Text>
          <Text style={styles.infoText}>• Financial ratios analysis</Text>
          <Text style={styles.infoText}>• AI-powered assessments</Text>
          <Text style={styles.infoText}>• Market news and insights</Text>
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
  form: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  pickerContainer: {
    marginTop: 8,
  },
  pickerOption: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  pickerOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  pickerOptionText: {
    fontSize: 14,
    color: '#333',
  },
  pickerOptionTextSelected: {
    color: '#007AFF',
    fontWeight: '600',
  },
  analyzeButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
  },
  analyzeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  analyzingContainer: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 32,
    alignItems: 'center',
    marginTop: 24,
  },
  analyzingText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
  },
  analyzingSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
  infoCard: {
    backgroundColor: '#E3F2FD',
    borderRadius: 8,
    padding: 16,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#1976D2',
    marginBottom: 8,
  },
});




