# Setup Instructions for React Native Mobile App

## Prerequisites

1. Node.js (>= 18)
2. React Native development environment setup
   - For iOS: Xcode, CocoaPods
   - For Android: Android Studio, JDK

## Installation Steps

### 1. Install Dependencies

```bash
cd assets/javascript/mobile
npm install
```

### 2. Install Native Dependencies

#### iOS
```bash
cd ios
pod install
cd ..
```

#### Android
No additional steps needed - Gradle will handle dependencies

### 3. Configure Google Sign-In

1. Get your Google Client IDs from Google Cloud Console:
   - **Web Client ID**: Used for OAuth token exchange
   - **iOS Client ID**: Required for iOS authentication (create an iOS OAuth 2.0 client in Google Cloud Console)
   
2. Update `App.tsx`:
   ```typescript
   GoogleSignin.configure({
     webClientId: 'YOUR_GOOGLE_WEB_CLIENT_ID_HERE',
     iosClientId: 'YOUR_GOOGLE_IOS_CLIENT_ID_HERE', // Required for iOS
   });
   ```
   
   **Note**: The iOS Client ID is different from the Web Client ID. You need to create a separate iOS OAuth 2.0 client in Google Cloud Console with your app's bundle identifier.

### 4. Configure API Base URL

Edit `src/config/api.ts` and update the `API_BASE_URL`:

```typescript
export const API_BASE_URL = __DEV__ 
  ? 'http://YOUR_LOCAL_IP:8000' // Replace with your local IP address
  : 'https://your-production-url.com';
```

**To find your local IP:**
- macOS/Linux: `ifconfig | grep "inet " | grep -v 127.0.0.1`
- Windows: `ipconfig`

### 5. Update Backend CORS Settings

Ensure your Django backend allows requests from your mobile device IP. Update `portfolio_strategist/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://YOUR_LOCAL_IP:8000",
    # Add your mobile device IP if testing on physical device
]
```

### 6. Run the App

#### Start Metro Bundler
```bash
npm start
```

#### iOS
```bash
npm run ios
# or
npx react-native run-ios
```

#### Android
```bash
npm run android
# or
npx react-native run-android
```

## Additional Configuration

### iOS Permissions

Add to `ios/mobile/Info.plist`:
```xml
<key>NSCameraUsageDescription</key>
<string>We need access to your camera to upload financial documents</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>We need access to your photos to upload financial documents</string>
```

### Android Permissions

Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

## Troubleshooting

### Common Issues

1. **Metro bundler won't start**
   - Clear cache: `npm start -- --reset-cache`
   - Delete `node_modules` and reinstall

2. **iOS build fails**
   - Run `pod install` in `ios/` directory
   - Clean build: `cd ios && xcodebuild clean`

3. **Android build fails**
   - Clean Gradle: `cd android && ./gradlew clean`
   - Check Java version (should be JDK 11 or higher)

4. **API connection issues**
   - Verify backend server is running
   - Check API_BASE_URL matches your server
   - Ensure CORS is configured correctly
   - For physical device, use your computer's IP (not localhost)

5. **Module not found errors**
   - Run `npm install` again
   - For native modules, rebuild the app

## Testing

### Test Authentication
- Login with valid credentials
- Test OTP flow if 2FA is enabled
- Test registration

### Test Features
- Upload documents
- View financial insights
- Analyze stocks
- Navigate between screens

## Development Notes

- All API calls are in `src/services/api.ts`
- Navigation structure is in `src/navigation/AppNavigator.tsx`
- Token refresh is automatic
- Error handling is built into API service

## Next Steps

1. Customize the app theme/colors
2. Add more detailed error messages
3. Implement offline mode with local caching
4. Add push notifications
5. Implement biometric authentication

