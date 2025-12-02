import React, {useEffect, useState} from 'react';
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import apiService from '../../services/api';
import {API_BASE_URL} from '../../config/api';

const ACCOUNT_ACTIONS = [
  {icon: 'edit', label: 'Edit profile'},
  {icon: 'lock', label: 'Change password'},
  {icon: 'subscriptions', label: 'Subscriptions'},
];

const SETTINGS_ACTIONS = [
  {icon: 'notifications', label: 'Notifications'},
  {icon: 'privacy-tip', label: 'Privacy'},
  {icon: 'help', label: 'Help & Support'},
];

interface ProfileScreenProps {
  onLogout: () => void;
}

export default function ProfileScreen({onLogout}: ProfileScreenProps) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>(null);

  const loadProfile = async () => {
    try {
      const response = await apiService.getUserProfile();
      if (response.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.error('Error loading profile', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadProfile();
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      {text: 'Cancel', style: 'cancel'},
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          await apiService.logout();
          onLogout();
        },
      },
    ]);
  };

  const loadDebugInfo = async () => {
    try {
      const accessToken = await AsyncStorage.getItem('accessToken');
      const refreshToken = await AsyncStorage.getItem('refreshToken');
      const tokenPreview = accessToken ? `${accessToken.substring(0, 20)}...` : 'none';
      const refreshPreview = refreshToken ? `${refreshToken.substring(0, 20)}...` : 'none';
      
      // Test token validity
      let tokenValid = false;
      let tokenError = null;
      if (accessToken) {
        try {
          const verifyResponse = await apiService.verifyToken(accessToken);
          tokenValid = verifyResponse.status === 200;
          if (!tokenValid) {
            tokenError = verifyResponse.error || 'Token verification failed';
          }
        } catch (e: any) {
          tokenError = e.message || 'Token verification error';
        }
      }
      
      setDebugInfo({
        apiBaseUrl: API_BASE_URL,
        hasAccessToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
        accessTokenPreview: tokenPreview,
        refreshTokenPreview: refreshPreview,
        tokenValid,
        tokenError,
        userEmail: user?.email || 'Not loaded',
        userId: user?.pk || user?.id || 'Not loaded',
      });
    } catch (error: any) {
      setDebugInfo({
        error: error.message || 'Failed to load debug info',
      });
    }
  };

  const handleDebugPress = () => {
    if (showDebug) {
      setShowDebug(false);
      setDebugInfo(null);
    } else {
      setShowDebug(true);
      loadDebugInfo();
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
      <View style={styles.hero}>
        <View style={styles.avatar}>
          <Icon name="person" size={48} color="#0A84FF" />
        </View>
        <Text style={styles.name}>{user?.username || user?.email || 'User'}</Text>
        {user?.email && <Text style={styles.email}>{user.email}</Text>}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        {ACCOUNT_ACTIONS.map(action => (
          <TouchableOpacity key={action.label} style={styles.menuItem}>
            <Icon name={action.icon} size={22} color="#0A84FF" />
            <Text style={styles.menuText}>{action.label}</Text>
            <Icon name="chevron-right" size={22} color="#9C9C9C" />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>
        {SETTINGS_ACTIONS.map(action => (
          <TouchableOpacity key={action.label} style={styles.menuItem}>
            <Icon name={action.icon} size={22} color="#0A84FF" />
            <Text style={styles.menuText}>{action.label}</Text>
            <Icon name="chevron-right" size={22} color="#9C9C9C" />
          </TouchableOpacity>
        ))}
        <TouchableOpacity style={styles.menuItem} onPress={handleDebugPress}>
          <Icon name="bug-report" size={22} color="#0A84FF" />
          <Text style={styles.menuText}>Debug Info</Text>
          <Icon name={showDebug ? "expand-less" : "expand-more"} size={22} color="#9C9C9C" />
        </TouchableOpacity>
      </View>

      {showDebug && debugInfo && (
        <View style={styles.debugSection}>
          <Text style={styles.debugTitle}>Debug Information</Text>
          <View style={styles.debugItem}>
            <Text style={styles.debugLabel}>API Base URL:</Text>
            <Text style={styles.debugValue}>{debugInfo.apiBaseUrl}</Text>
          </View>
          <View style={styles.debugItem}>
            <Text style={styles.debugLabel}>Has Access Token:</Text>
            <Text style={[styles.debugValue, debugInfo.hasAccessToken ? styles.success : styles.error]}>
              {debugInfo.hasAccessToken ? 'Yes' : 'No'}
            </Text>
          </View>
          <View style={styles.debugItem}>
            <Text style={styles.debugLabel}>Has Refresh Token:</Text>
            <Text style={[styles.debugValue, debugInfo.hasRefreshToken ? styles.success : styles.error]}>
              {debugInfo.hasRefreshToken ? 'Yes' : 'No'}
            </Text>
          </View>
          {debugInfo.hasAccessToken && (
            <>
              <View style={styles.debugItem}>
                <Text style={styles.debugLabel}>Token Preview:</Text>
                <Text style={styles.debugValue} numberOfLines={1}>{debugInfo.accessTokenPreview}</Text>
              </View>
              <View style={styles.debugItem}>
                <Text style={styles.debugLabel}>Token Valid:</Text>
                <Text style={[styles.debugValue, debugInfo.tokenValid ? styles.success : styles.error]}>
                  {debugInfo.tokenValid ? 'Yes' : 'No'}
                </Text>
              </View>
              {debugInfo.tokenError && (
                <View style={styles.debugItem}>
                  <Text style={styles.debugLabel}>Token Error:</Text>
                  <Text style={[styles.debugValue, styles.error]}>{debugInfo.tokenError}</Text>
                </View>
              )}
            </>
          )}
          <View style={styles.debugItem}>
            <Text style={styles.debugLabel}>User Email:</Text>
            <Text style={styles.debugValue}>{debugInfo.userEmail}</Text>
          </View>
          <View style={styles.debugItem}>
            <Text style={styles.debugLabel}>User ID:</Text>
            <Text style={styles.debugValue}>{debugInfo.userId}</Text>
          </View>
          {debugInfo.error && (
            <View style={styles.debugItem}>
              <Text style={styles.debugLabel}>Error:</Text>
              <Text style={[styles.debugValue, styles.error]}>{debugInfo.error}</Text>
            </View>
          )}
          <TouchableOpacity 
            style={styles.debugButton} 
            onPress={async () => {
              Alert.alert(
                'Copy Debug Info',
                'Debug information copied to console. Check Metro bundler terminal for details.',
                [{text: 'OK'}]
              );
              console.log('[DEBUG] Full Debug Info:', JSON.stringify(debugInfo, null, 2));
            }}
          >
            <Text style={styles.debugButtonText}>Copy to Console</Text>
          </TouchableOpacity>
        </View>
      )}

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Icon name="logout" size={22} color="#FF3B30" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
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
  hero: {
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingVertical: 32,
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#EAF2FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  name: {
    fontSize: 22,
    fontWeight: '600',
    color: '#111',
  },
  email: {
    marginTop: 6,
    color: '#666',
  },
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    paddingHorizontal: 4,
    paddingVertical: 8,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 8,
    elevation: 1,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#555',
    marginLeft: 12,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#eee',
  },
  menuText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 15,
    color: '#111',
  },
  logoutButton: {
    marginHorizontal: 16,
    marginBottom: 32,
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 8,
    elevation: 1,
  },
  logoutText: {
    marginLeft: 8,
    color: '#FF3B30',
    fontWeight: '600',
  },
  debugSection: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: {width: 0, height: 4},
    shadowRadius: 8,
    elevation: 1,
  },
  debugTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#555',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  debugItem: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#eee',
  },
  debugLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  debugValue: {
    fontSize: 13,
    color: '#111',
    fontFamily: 'monospace',
  },
  success: {
    color: '#34C759',
  },
  error: {
    color: '#FF3B30',
  },
  debugButton: {
    marginTop: 8,
    padding: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignItems: 'center',
  },
  debugButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
});
