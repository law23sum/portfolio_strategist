# Blank Screen Fix - iOS App

## Fixes Applied

### ✅ 1. Added SafeAreaProvider Wrapper
- **File**: `App.tsx`
- **Change**: Wrapped `AppNavigator` with `SafeAreaProvider`
- **Why**: React Navigation requires `SafeAreaProvider` for proper iOS rendering, especially with bottom tabs

### ✅ 2. Enhanced Error Logging
- **File**: `AppNavigator.tsx`
- **Change**: Added console logs to track initialization and navigation state
- **Why**: Helps identify where the app is failing

## Next Steps - Debug the Blank Screen

### Step 1: Restart Metro Bundler with Cache Clear
```bash
cd assets/javascript/mobile

# Kill any existing Metro processes
killall node

# Start Metro with cache cleared
npx react-native start --reset-cache
```

### Step 2: Clean iOS Build
```bash
cd assets/javascript/mobile/ios

# Clean build
rm -rf build
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Reinstall pods (important after code changes)
pod install

cd ..
```

### Step 3: Rebuild and Run
```bash
# In the mobile directory
npx react-native run-ios --simulator="iPhone 16 Pro"
```

### Step 4: Check Console Logs

**In Metro Bundler Terminal:**
- Look for red error messages
- Check if bundle is loading successfully
- Look for any "Unable to resolve module" errors

**In Xcode Console:**
1. Open `ios/mobile.xcworkspace` in Xcode
2. Run the app (Cmd+R)
3. Check the console output for:
   - `[index.js] Registering app component: mobile`
   - `[App] App component rendering...`
   - `[AppNavigator] Initializing...`
   - `[AppNavigator] Navigation container ready`

**In Simulator:**
- Shake device (Cmd+Ctrl+Z) or press Cmd+D
- Select "Debug" to open React Native debugger
- Check for red error screens

### Step 5: Verify Metro Connection

Test if Metro bundler is accessible:
```bash
# Check Metro status
curl http://localhost:8081/status

# Test bundle URL
curl http://localhost:8081/index.bundle?platform=ios | head -20
```

If these fail, Metro bundler isn't running or isn't accessible.

### Step 6: Check for JavaScript Errors

Common causes of blank screens:

1. **Missing Module**
   - Error: "Unable to resolve module"
   - Fix: Run `npm install` and `cd ios && pod install`

2. **Vector Icons Not Configured**
   - Error: Icon components fail to render
   - Fix: Ensure fonts are linked (should be automatic with RN 0.78)

3. **Navigation Error**
   - Error: NavigationContainer fails to initialize
   - Fix: Check that all screen components exist and export correctly

4. **API Configuration Error**
   - Error: Network requests fail during initialization
   - Fix: Check `src/config/api.ts` - API_BASE_URL should be accessible

## Quick Test: Minimal App

If the blank screen persists, test with a minimal app to isolate the issue:

**Temporarily replace `App.tsx` content with:**
```tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function App() {
  return (
    <SafeAreaProvider>
      <View style={styles.container}>
        <Text style={styles.text}>Hello World!</Text>
        <Text style={styles.subtext}>If you see this, React Native is working</Text>
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtext: {
    fontSize: 16,
    color: '#666',
    marginTop: 8,
  },
});
```

If this works, the issue is in your navigation or screen components.
If this doesn't work, the issue is with React Native setup or Metro bundler.

## Still Having Issues?

1. **Check React Native version:**
   ```bash
   npx react-native --version
   ```

2. **Check Xcode version:**
   ```bash
   xcodebuild -version
   ```

3. **Verify all dependencies:**
   ```bash
   cd assets/javascript/mobile
   npm install
   cd ios
   pod install
   ```

4. **Reset Simulator:**
   ```bash
   xcrun simctl erase all
   ```

5. **Check network connectivity:**
   - Ensure backend server is running (if app tries to connect on startup)
   - Verify API_BASE_URL in `src/config/api.ts` is correct
   - Test API endpoint: `curl http://YOUR_API_URL/api/auth/user/`

## What to Share When Asking for Help

- Metro bundler output (full terminal output)
- Xcode console logs
- Screenshot of simulator
- Output of `npx react-native --version`
- Output of `xcodebuild -version`
- Any error messages from console

