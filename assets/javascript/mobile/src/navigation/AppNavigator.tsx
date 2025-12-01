import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Auth Screens
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';

// Main Screens
import DashboardScreen from '../screens/main/DashboardScreen';
import RecordsScreen from '../screens/main/RecordsScreen';
import StockAnalysisScreen from '../screens/main/StockAnalysisScreen';
import SolutionsScreen from '../screens/main/SolutionsScreen';
import ProfileScreen from '../screens/main/ProfileScreen';

// Records Sub-screens
import InsightsScreen from '../screens/records/InsightsScreen';
import ExplorerScreen from '../screens/records/ExplorerScreen';
import UploadScreen from '../screens/records/UploadScreen';
import LinkedAccountsScreen from '../screens/records/LinkedAccountsScreen';

// Stock Analysis Sub-screens
import AnalyzeStockScreen from '../screens/stock/AnalyzeStockScreen';
import AnalysisResultsScreen from '../screens/stock/AnalysisResultsScreen';
import LoanAnalysisScreen from '../screens/stock/LoanAnalysisScreen';
import InvestmentPlannerScreen from '../screens/stock/InvestmentPlannerScreen';

// Investment & Savings Screens
import InvestmentSavingsScreen from '../screens/investment/InvestmentSavingsScreen';
import SavingsAssessmentScreen from '../screens/investment/SavingsAssessmentScreen';
import CDAssessmentScreen from '../screens/investment/CDAssessmentScreen';
import BondAssessmentScreen from '../screens/investment/BondAssessmentScreen';

// Budget Planner
import BudgetPlannerScreen from '../screens/main/BudgetPlannerScreen';

// Chat Screen
import ChatScreen from '../screens/chat/ChatScreen';

import AsyncStorage from '@react-native-async-storage/async-storage';
import { ActivityIndicator, View } from 'react-native';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();
const AuthStack = createStackNavigator();
const RecordsStack = createStackNavigator();
const StockStack = createStackNavigator();
const InvestmentStack = createStackNavigator();

function RecordsNavigator() {
  return (
    <RecordsStack.Navigator>
      <RecordsStack.Screen 
        name="RecordsMain" 
        component={RecordsScreen}
        options={{ headerShown: false }}
      />
      <RecordsStack.Screen 
        name="Insights" 
        component={InsightsScreen}
        options={{ title: 'Financial Insights' }}
      />
      <RecordsStack.Screen 
        name="Explorer" 
        component={ExplorerScreen}
        options={{ title: 'Data Explorer' }}
      />
      <RecordsStack.Screen 
        name="Upload" 
        component={UploadScreen}
        options={{ title: 'Upload Document' }}
      />
      <RecordsStack.Screen 
        name="LinkedAccounts" 
        component={LinkedAccountsScreen}
        options={{ title: 'Linked Accounts' }}
      />
    </RecordsStack.Navigator>
  );
}

function StockNavigator() {
  return (
    <StockStack.Navigator>
      <StockStack.Screen 
        name="StockMain" 
        component={StockAnalysisScreen}
        options={{ headerShown: false }}
      />
      <StockStack.Screen 
        name="Analyze" 
        component={AnalyzeStockScreen}
        options={{ title: 'Analyze Stock' }}
      />
      <StockStack.Screen 
        name="Results" 
        component={AnalysisResultsScreen}
        options={{ title: 'Analysis Results' }}
      />
      <StockStack.Screen 
        name="Loan" 
        component={LoanAnalysisScreen}
        options={{ title: 'Loan Analysis' }}
      />
      <StockStack.Screen 
        name="InvestmentPlanner" 
        component={InvestmentPlannerScreen}
        options={{ title: 'Investment Planner' }}
      />
    </StockStack.Navigator>
  );
}

function InvestmentNavigator() {
  return (
    <InvestmentStack.Navigator>
      <InvestmentStack.Screen 
        name="InvestmentSavingsMain" 
        component={InvestmentSavingsScreen}
        options={{ headerShown: false }}
      />
      <InvestmentStack.Screen 
        name="SavingsAssessment" 
        component={SavingsAssessmentScreen}
        options={{ title: 'Savings Assessment' }}
      />
      <InvestmentStack.Screen 
        name="CDAssessment" 
        component={CDAssessmentScreen}
        options={{ title: 'CD Assessment' }}
      />
      <InvestmentStack.Screen 
        name="BondAssessment" 
        component={BondAssessmentScreen}
        options={{ title: 'Bond Assessment' }}
      />
    </InvestmentStack.Navigator>
  );
}

function MainTabs({ onLogout }: { onLogout: () => void }) {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#666',
        headerShown: true,
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="dashboard" size={size} color={color} />
          ),
          headerTitle: 'Dashboard',
        }}
      />
      <Tab.Screen
        name="Records"
        component={RecordsNavigator}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="description" size={size} color={color} />
          ),
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="StockAnalysis"
        component={StockNavigator}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="trending-up" size={size} color={color} />
          ),
          headerShown: false,
          tabBarLabel: 'Stocks',
        }}
      />
      <Tab.Screen
        name="InvestmentSavings"
        component={InvestmentNavigator}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="savings" size={size} color={color} />
          ),
          headerShown: false,
          tabBarLabel: 'Investments',
        }}
      />
      <Tab.Screen
        name="Solutions"
        component={SolutionsScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="lightbulb" size={size} color={color} />
          ),
          headerTitle: 'Solutions',
        }}
      />
      <Tab.Screen
        name="BudgetPlanner"
        component={BudgetPlannerScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="account-balance-wallet" size={size} color={color} />
          ),
          headerTitle: 'Budget Planner',
        }}
      />
      <Tab.Screen
        name="Chat"
        component={ChatScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="chat" size={size} color={color} />
          ),
          headerTitle: 'Chat Assistant',
        }}
      />
      <Tab.Screen
        name="Profile"
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="person" size={size} color={color} />
          ),
          headerTitle: 'Profile',
        }}
      >
        {(props) => <ProfileScreen {...props} onLogout={onLogout} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

function AuthNavigator({ onLoginSuccess }: { onLoginSuccess: () => void }) {
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}>
      <AuthStack.Screen name="Login">
        {(props) => <LoginScreen {...props} onLoginSuccess={onLoginSuccess} />}
      </AuthStack.Screen>
      <AuthStack.Screen name="Register">
        {(props) => <RegisterScreen {...props} onRegisterSuccess={onLoginSuccess} />}
      </AuthStack.Screen>
    </AuthStack.Navigator>
  );
}

export default function AppNavigator() {
  const [isLoading, setIsLoading] = React.useState(true);
  const [userToken, setUserToken] = React.useState<string | null>(null);

  React.useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        const token = await AsyncStorage.getItem('accessToken');
        setUserToken(token);
      } catch (e) {
        console.error('Restoring token failed', e);
      } finally {
        setIsLoading(false);
      }
    };

    bootstrapAsync();
  }, []);

  const handleLoginSuccess = () => {
    setUserToken('authenticated');
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('accessToken');
      await AsyncStorage.removeItem('refreshToken');
      setUserToken(null);
    } catch (e) {
      console.error('Logout error:', e);
    }
  };

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {userToken ? (
        <MainTabs onLogout={handleLogout} />
      ) : (
        <AuthNavigator onLoginSuccess={handleLoginSuccess} />
      )}
    </NavigationContainer>
  );
}

