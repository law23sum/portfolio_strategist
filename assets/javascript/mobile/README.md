# The Portfolio Strategist - React Native Mobile App

A comprehensive React Native mobile application that provides all the features of the Portfolio Strategist web application.

## Features

### Authentication
- Login with username/password
- Registration
- Two-factor authentication (OTP)
- Google Sign-In support
- Token-based authentication with automatic refresh

### Dashboard
- Financial overview
- Quick action buttons
- Recent activity
- Statistics and insights

### Financial Records
- **Insights**: View financial insights and analytics
- **Explorer**: Explore financial data
- **Upload**: Upload financial documents (PDF, images)
- **Linked Accounts**: Manage connected financial accounts (Plaid integration ready)

### Stock Analysis
- **Analyze Stock**: Analyze stock symbols with multiple forecasting models
- **Results**: View detailed analysis results including forecasts, ratios, and AI assessments
- **Loan Analysis**: Personal loan analysis and comparison (coming soon)

### Solutions
- Budget Planning
- Investment Retirement planning
- Portfolio Management

### Profile
- User profile management
- Password change
- Subscription management
- Settings

## Setup

1. Install dependencies:
```bash
npm install
```

2. For iOS, install pods:
```bash
cd ios && pod install && cd ..
```

3. Configure Google Sign-In:
   - Update the `webClientId` in `App.tsx` with your Google Web Client ID
   - Update the `iosClientId` in `App.tsx` with your Google iOS Client ID (required for iOS)
   - Configure Google Sign-In in your Google Cloud Console (create separate iOS OAuth 2.0 client)

4. Update API Base URL:
   - Edit `src/config/api.ts` and update `API_BASE_URL` with your backend server URL

## Running the App

### iOS
```bash
npx react-native run-ios
```

### Android
```bash
npx react-native run-android
```

### Start Metro Bundler
```bash
npx react-native start
```

## Project Structure

```
src/
├── config/
│   └── api.ts              # API configuration and endpoints
├── navigation/
│   ├── AppNavigator.tsx    # Main navigation setup
│   └── types.ts            # Navigation types
├── screens/
│   ├── auth/               # Authentication screens
│   │   ├── LoginScreen.tsx
│   │   └── RegisterScreen.tsx
│   ├── main/               # Main feature screens
│   │   ├── DashboardScreen.tsx
│   │   ├── RecordsScreen.tsx
│   │   ├── StockAnalysisScreen.tsx
│   │   ├── SolutionsScreen.tsx
│   │   └── ProfileScreen.tsx
│   ├── records/            # Records sub-screens
│   │   ├── InsightsScreen.tsx
│   │   ├── ExplorerScreen.tsx
│   │   ├── UploadScreen.tsx
│   │   └── LinkedAccountsScreen.tsx
│   └── stock/              # Stock analysis screens
│       ├── AnalyzeStockScreen.tsx
│       ├── AnalysisResultsScreen.tsx
│       └── LoanAnalysisScreen.tsx
└── services/
    └── api.ts              # API service layer with token management
```

## API Integration

The app connects to the Django backend API. Ensure:
- Backend server is running
- CORS is properly configured for mobile IP addresses
- API endpoints match the backend routes

## Notes

- Token refresh is handled automatically
- All API calls include error handling
- The app uses AsyncStorage for local token storage
- Image/document pickers require proper permissions setup

## Dependencies

Key dependencies include:
- React Navigation for navigation
- React Native Vector Icons for icons
- AsyncStorage for local storage
- Google Sign-In for authentication
- Image Picker and Document Picker for file uploads
