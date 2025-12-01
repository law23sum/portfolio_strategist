import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import apiService from '../../services/api';

interface LoginScreenProps {
  navigation: any;
  onLoginSuccess: () => void;
}

export default function LoginScreen({ navigation, onLoginSuccess }: LoginScreenProps) {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showOTP, setShowOTP] = useState(false);
  const [otp, setOtp] = useState('');
  const [tempOtpToken, setTempOtpToken] = useState('');

  const handleLogin = async () => {
    if (!usernameOrEmail.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter both email/username and password.');
      return;
    }

    setLoading(true);
    try {
      console.log('[LoginScreen] Attempting login...');
      const response = await apiService.login(usernameOrEmail, password);
      console.log('[LoginScreen] Login response received:', response);
      
      if (response.error) {
        console.error('[LoginScreen] Login error:', response.error);
        Alert.alert('Login Failed', response.error);
      } else if (response.data) {
        // Check if 2FA is required
        if (response.data.status === 'otp_required' && response.data.temp_otp_token) {
          console.log('[LoginScreen] 2FA required');
          setTempOtpToken(response.data.temp_otp_token);
          setShowOTP(true);
        } else if (response.data.access && response.data.refresh) {
          // Login successful without 2FA
          console.log('[LoginScreen] Login successful');
          onLoginSuccess();
        } else {
          console.warn('[LoginScreen] Unexpected response format:', response.data);
          Alert.alert('Login Failed', 'Unexpected response from server. Please try again.');
        }
      } else {
        console.error('[LoginScreen] No data or error in response:', response);
        Alert.alert('Login Failed', 'No response from server. Please check your connection.');
      }
    } catch (error: any) {
      console.error('[LoginScreen] Exception during login:', error);
      Alert.alert('Login Failed', error.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOTPVerification = async () => {
    if (!otp.trim()) {
      Alert.alert('Error', 'Please enter the OTP code.');
      return;
    }

    if (!tempOtpToken.trim()) {
      Alert.alert('Error', 'Session expired. Please login again.');
      setShowOTP(false);
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.verifyOTP(otp, tempOtpToken);
      if (response.error) {
        Alert.alert('Verification Failed', response.error);
      } else if (response.data && response.data.access && response.data.refresh) {
        onLoginSuccess();
      }
    } catch (error: any) {
      Alert.alert('Verification Failed', error.message || 'Invalid OTP code.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      // Handle Google sign-in - you'll need to send the token to your backend
      Alert.alert('Success', 'Google Sign-In completed. Backend integration needed.');
    } catch (error: any) {
      Alert.alert('Google Sign-In Error', error.message);
    }
  };

  if (showOTP) {
    return (
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.title}>Enter OTP</Text>
          <Text style={styles.subtitle}>Please enter the OTP code sent to your email</Text>

          <TextInput
            style={styles.input}
            placeholder="OTP Code"
            value={otp}
            onChangeText={setOtp}
            keyboardType="number-pad"
            maxLength={6}
            autoFocus
            editable={!loading}
          />

          {loading ? (
            <ActivityIndicator size="large" color="#007AFF" style={styles.loader} />
          ) : (
            <>
              <TouchableOpacity
                style={styles.button}
                onPress={handleOTPVerification}
                disabled={loading}
              >
                <Text style={styles.buttonText}>Verify OTP</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => setShowOTP(false)}
                disabled={loading}
              >
                <Text style={styles.secondaryButtonText}>Back to Login</Text>
              </TouchableOpacity>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>The Portfolio Strategist</Text>
        <Text style={styles.subtitle}>Welcome back! Please login to continue.</Text>

        <TextInput
          style={styles.input}
          placeholder="Email or Username"
          autoCapitalize="none"
          keyboardType="email-address"
          value={usernameOrEmail}
          onChangeText={setUsernameOrEmail}
          autoCorrect={false}
          editable={!loading}
        />

        <TextInput
          style={styles.input}
          placeholder="Password"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          editable={!loading}
          onSubmitEditing={handleLogin}
        />

        {loading ? (
          <ActivityIndicator size="large" color="#007AFF" style={styles.loader} />
        ) : (
          <>
            <TouchableOpacity
              style={styles.button}
              onPress={handleLogin}
              disabled={loading}
            >
              <Text style={styles.buttonText}>Sign In</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.googleButton}
              onPress={handleGoogleSignIn}
              disabled={loading}
            >
              <Text style={styles.googleButtonText}>Sign in with Google</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.linkButton}
              onPress={() => navigation.navigate('Register')}
              disabled={loading}
            >
              <Text style={styles.linkText}>
                Don't have an account? <Text style={styles.linkTextBold}>Sign Up</Text>
              </Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 32,
    textAlign: 'center',
    color: '#666',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 15,
    marginBottom: 16,
    borderRadius: 8,
    backgroundColor: '#f9f9f9',
    fontSize: 16,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  googleButton: {
    backgroundColor: '#4285F4',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  googleButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 20,
    alignItems: 'center',
  },
  linkText: {
    color: '#666',
    fontSize: 14,
  },
  linkTextBold: {
    color: '#007AFF',
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#f0f0f0',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  secondaryButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  loader: {
    marginTop: 20,
  },
});

