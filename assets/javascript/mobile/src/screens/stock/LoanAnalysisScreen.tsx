import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import DocumentPicker from 'react-native-document-picker';
import apiService from '../../services/api';

export default function LoanAnalysisScreen({ navigation }: any) {
  const [loading, setLoading] = useState(false);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    setLoading(true);
    try {
      // Note: The backend doesn't have a list endpoint, so we'll show upload functionality
      // Users can upload and then view results
    } catch (error) {
      console.error('Error loading analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.csv],
      });

      if (result && result.length > 0) {
        await uploadCSV(result[0]);
      }
    } catch (err) {
      if (DocumentPicker.isCancel(err)) {
        // User cancelled
      } else {
        Alert.alert('Error', 'Failed to pick document');
      }
    }
  };

  const uploadCSV = async (file: any) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('csv_file', {
        uri: file.uri,
        type: 'text/csv',
        name: file.name || 'loan_data.csv',
      });

      const token = await apiService['getToken']();
      const response = await fetch(
        `${apiService['baseURL']}/stock-analysis/loan/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
          body: formData,
        }
      );

      const data = await response.json();
      
      if (response.ok && data.id) {
        Alert.alert('Success', 'Loan analysis completed!', [
          {
            text: 'View Results',
            onPress: () => navigation.navigate('LoanResults', { analysisId: data.id }),
          },
          { text: 'OK' },
        ]);
      } else {
        Alert.alert('Error', data.error || 'Failed to analyze loan data');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to upload file');
    } finally {
      setUploading(false);
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
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Personal Loan Analysis</Text>
        <Text style={styles.subtitle}>
          Upload a CSV file to analyze personal loan data
        </Text>

        <View style={styles.uploadCard}>
          <Icon name="cloud-upload" size={48} color="#007AFF" />
          <Text style={styles.uploadTitle}>Upload CSV File</Text>
          <Text style={styles.uploadDescription}>
            Upload a CSV file with columns: Account, Direction, Amount
          </Text>
          
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={pickDocument}
            disabled={uploading}
          >
            {uploading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Icon name="file-upload" size={20} color="#fff" />
                <Text style={styles.uploadButtonText}>Choose CSV File</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        <View style={styles.infoCard}>
          <Icon name="info" size={24} color="#007AFF" />
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>CSV Format</Text>
            <Text style={styles.infoText}>
              Your CSV file should have the following columns:{'\n'}
              • Account: The account name{'\n'}
              • Direction: IN or OUT{'\n'}
              • Amount: The transaction amount
            </Text>
          </View>
        </View>

        {analyses.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Previous Analyses</Text>
            {analyses.map((analysis, index) => (
              <TouchableOpacity
                key={index}
                style={styles.analysisCard}
                onPress={() => navigation.navigate('LoanResults', { analysisId: analysis.id })}
              >
                <View style={styles.analysisContent}>
                  <Text style={styles.analysisDate}>
                    {new Date(analysis.analysis_date).toLocaleDateString()}
                  </Text>
                </View>
                <Icon name="chevron-right" size={24} color="#999" />
              </TouchableOpacity>
            ))}
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
  uploadCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  uploadTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  uploadDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  uploadButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 200,
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    alignItems: 'flex-start',
  },
  infoContent: {
    flex: 1,
    marginLeft: 12,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
  section: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  analysisCard: {
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
  analysisContent: {
    flex: 1,
  },
  analysisDate: {
    fontSize: 16,
    color: '#333',
  },
});



