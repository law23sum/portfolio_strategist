import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { launchImageLibrary, launchCamera, ImagePickerResponse, MediaType } from 'react-native-image-picker';
import DocumentPicker, { DocumentPickerResponse } from 'react-native-document-picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import apiService from '../../services/api';

export default function UploadScreen() {
  const [uploading, setUploading] = useState(false);

  const handleFilePicker = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.pdf, DocumentPicker.types.images],
      });

      if (result && result.length > 0) {
        await uploadFile(result[0]);
      }
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to pick document');
      }
    }
  };

  const handleImagePicker = () => {
    Alert.alert(
      'Select Image',
      'Choose an option',
      [
        { text: 'Camera', onPress: () => launchCamera({ mediaType: 'photo' as MediaType }, handleImageResponse) },
        { text: 'Gallery', onPress: () => launchImageLibrary({ mediaType: 'photo' as MediaType }, handleImageResponse) },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const handleImageResponse = async (response: ImagePickerResponse) => {
    if (response.didCancel || response.errorMessage) {
      return;
    }

    if (response.assets && response.assets[0]) {
      const asset = response.assets[0];
      const file = {
        uri: asset.uri || '',
        type: asset.type || 'image/jpeg',
        name: asset.fileName || 'image.jpg',
      };
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: DocumentPickerResponse | { uri?: string; type?: string; name?: string }) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: file.type || 'application/pdf',
        name: file.name || 'document.pdf',
      } as any);
      formData.append('title', file.name || 'Document');

      const response = await apiService.uploadDocument(formData);
      
      if (response.error) {
        Alert.alert('Upload Failed', response.error);
      } else {
        Alert.alert('Success', 'Document uploaded successfully');
      }
    } catch (error: any) {
      Alert.alert('Upload Failed', error.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Upload Document</Text>
        <Text style={styles.subtitle}>
          Upload financial documents, statements, or receipts
        </Text>

        {uploading ? (
          <View style={styles.uploadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.uploadingText}>Uploading...</Text>
          </View>
        ) : (
          <View style={styles.uploadOptions}>
            <TouchableOpacity
              style={styles.uploadButton}
              onPress={handleFilePicker}
            >
              <Icon name="description" size={48} color="#007AFF" />
              <Text style={styles.uploadButtonText}>Upload PDF/Document</Text>
              <Text style={styles.uploadButtonSubtext}>
                Select a file from your device
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.uploadButton}
              onPress={handleImagePicker}
            >
              <Icon name="photo-camera" size={48} color="#007AFF" />
              <Text style={styles.uploadButtonText}>Take Photo</Text>
              <Text style={styles.uploadButtonSubtext}>
                Capture or select an image
              </Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.infoContainer}>
          <Text style={styles.infoTitle}>Supported Formats</Text>
          <Text style={styles.infoText}>• PDF documents</Text>
          <Text style={styles.infoText}>• Images (JPG, PNG)</Text>
          <Text style={styles.infoText}>• Financial statements</Text>
          <Text style={styles.infoText}>• Receipts and invoices</Text>
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
  uploadingContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    marginBottom: 16,
  },
  uploadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  uploadOptions: {
    marginBottom: 24,
  },
  uploadButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  uploadButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
  },
  uploadButtonSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  infoContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
});

