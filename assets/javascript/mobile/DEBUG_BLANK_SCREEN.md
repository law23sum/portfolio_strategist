# Debugging Blank Screen - Step by Step

## Current Status
✅ Metro bundler is running and accessible
✅ Bundle is loading correctly  
✅ SafeAreaProvider is present
✅ Dependencies installed

## Most Likely Causes

Since Metro is working but the screen is blank, the issue is likely:

1. **JavaScript Error in Screen Component** - One of the imported screens has an error
2. **NavigationContainer Failing** - Navigation setup issue
3. **AsyncStorage Error** - Token check failing silently
4. **Vector Icons Issue** - Icons not loading causing silent failure

## Debugging Steps

### Step 1: Check Console Logs

**In Metro Bundler Terminal:**
Look for:
- `[index.js] Registering app component: mobile`
- `[App] App component rendering...`
- `[AppNavigator] Initializing...`
- Any RED error messages

**In Xcode Console:**
- Open `ios/mobile.xcworkspace` in Xcode
- Run the app
- Look for red error messages
- Check if you see the console.log messages above

### Step 2: Test Minimal Version

Try the minimal test to see if React Native works at all:

```bash
cd assets/javascript/mobile

# Backup current App.tsx
cp App.tsx App.tsx.backup

# Use minimal test
cp App.test-minimal.tsx App.tsx

# Rebuild
npx react-native run-ios
```

**If minimal test works:**
- React Native setup is fine
- Issue is in navigation or screen components
- Proceed to Step 3

**If minimal test is blank:**
- React Native setup issue
- Check Xcode build errors
- Check Metro bundler connection
- Verify Info.plist settings

### Step 3: Test Navigation Only

If minimal test worked, try navigation test:

```bash
# Use navigation test
cp App.test-navigation.tsx App.tsx

# Rebuild
npx react-native run-ios
```

**If navigation test works:**
- Navigation setup is fine
- Issue is in one of the screen components
- Proceed to Step 4

**If navigation test is blank:**
- Navigation setup issue
- Check NavigationContainer configuration
- Check screen imports

### Step 4: Identify Problematic Screen

The issue is likely in one of these screens. Check each:

1. **LoginScreen** - Most likely, it's the first screen shown
2. **DashboardScreen** - If userToken exists, this loads first
3. **One of the tab screens** - Check if MainTabs is failing

To test, temporarily comment out screens in `AppNavigator.tsx`:

```typescript
// Comment out all screens except LoginScreen
// import DashboardScreen from '../screens/main/DashboardScreen';
// import RecordsScreen from '../screens/main/RecordsScreen';
// ... etc
```

Then rebuild and see if LoginScreen shows.

### Step 5: Check Specific Issues

**Vector Icons:**
If you see errors about MaterialIcons, check:
- Fonts are linked (should be automatic in RN 0.78)
- Try removing icon usage temporarily

**AsyncStorage:**
If token check is failing:
- Check if AsyncStorage is properly installed
- Try commenting out AsyncStorage.getItem() temporarily

**API Calls:**
If screens make API calls on mount:
- Check if API_BASE_URL is correct
- Check if backend is running
- Check network errors in console

## Quick Fixes to Try

### Fix 1: Clear All Caches
```bash
cd assets/javascript/mobile
rm -rf node_modules
npm install
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
npx react-native start --reset-cache
```

### Fix 2: Reset Simulator
```bash
xcrun simctl erase all
```

### Fix 3: Check for Import Errors
Look for any screen files that might have syntax errors:
```bash
cd assets/javascript/mobile/src/screens
# Check each screen file for export default
```

### Fix 4: Temporarily Disable Error Boundary
Comment out ErrorBoundary to see raw errors:
```typescript
// In App.tsx, temporarily:
return (
  <SafeAreaProvider>
    {/* <ErrorBoundary> */}
      <AppNavigator />
    {/* </ErrorBoundary> */}
  </SafeAreaProvider>
);
```

## What to Share

If still stuck, share:
1. **Metro bundler output** (full terminal output)
2. **Xcode console output** (all messages)
3. **Screenshot** of simulator
4. **Which test worked** (minimal, navigation, or none)
5. **Any error messages** you see

## Expected Console Output

When working correctly, you should see:
```
[index.js] Registering app component: mobile
[App] App component rendering...
[App] App component mounted
[AppNavigator] Initializing...
[AppNavigator] Checking for stored token...
[AppNavigator] Token found: No
[AppNavigator] Initialization complete
[AppNavigator] Rendering navigation, userToken: null
[AppNavigator] Navigation container ready
```

If you don't see these messages, the app is failing before rendering.

