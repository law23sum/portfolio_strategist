# iOS App Troubleshooting Guide

## App Won't Populate/Show Content on Simulator

If your iOS app launches but shows a blank screen or doesn't display content, follow these steps:

### 1. Check Metro Bundler Connection

The most common issue is that the app can't connect to Metro bundler.

**Solution:**
```bash
cd assets/javascript/mobile

# Kill any existing Metro processes
killall node

# Clear Metro cache and restart
npx react-native start --reset-cache
```

In a **separate terminal**, run:
```bash
cd assets/javascript/mobile
npx react-native run-ios
```

### 2. Check Simulator Network Settings

The iOS simulator needs to be able to reach your development server.

**Verify:**
- Open Safari on the simulator
- Navigate to `http://localhost:8081` (Metro bundler)
- You should see Metro's status page

If it doesn't work, try:
- `http://127.0.0.1:8081`
- Check your Mac's IP address: `ifconfig | grep "inet " | grep -v 127.0.0.1`

### 3. Check Console Logs

**In Xcode:**
1. Open `ios/mobile.xcworkspace` in Xcode
2. Run the app (Cmd+R)
3. Check the console for red error messages

**In Metro Bundler:**
- Look for JavaScript errors in the Metro terminal
- Red error messages indicate what's preventing the app from loading

**In Simulator:**
- Shake the device (Cmd+Ctrl+Z) or press Cmd+D
- Select "Debug" to see React Native debugger
- Check for any red error screens

### 4. Clean Build

Sometimes cached build files cause issues:

```bash
cd assets/javascript/mobile/ios

# Clean Xcode build
xcodebuild clean -workspace mobile.xcworkspace -scheme mobile

# Remove derived data
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Reinstall pods
pod deintegrate
pod install

cd ..
# Clear node modules and reinstall (optional)
# rm -rf node_modules
# npm install

# Clear Metro cache
npx react-native start --reset-cache
```

### 5. Verify Dependencies

Ensure all native dependencies are properly installed:

```bash
cd assets/javascript/mobile

# Check Node modules
npm install

# Reinstall iOS pods
cd ios
pod install
cd ..
```

### 6. Check API Configuration

If the app loads but shows errors, verify your API configuration:

**File:** `src/config/api.ts`

```typescript
export const API_BASE_URL = __DEV__ 
  ? 'http://YOUR_LOCAL_IP:8000' // Make sure this is correct
  : 'https://your-production-url.com';
```

**For iOS Simulator:**
- Use `localhost` or `127.0.0.1` if your backend is on the same machine
- Use your Mac's local IP if backend is on another machine
- Make sure the backend is running and accessible

### 7. Check Info.plist Network Settings

The app's `Info.plist` must allow connections to your development server.

**File:** `ios/mobile/Info.plist`

Ensure your IP address is in the `NSExceptionDomains` section. If your IP changed, update it.

### 8. Verify App Entry Point

Check that the app is properly registered:

**File:** `index.js` should contain:
```javascript
import {AppRegistry} from 'react-native';
import App from './App';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => App);
```

**File:** `app.json` should contain:
```json
{
  "name": "mobile",
  "displayName": "mobile"
}
```

### 9. Check for JavaScript Errors

The app now includes an Error Boundary that will catch JavaScript errors. If you see an error screen:
- Check the console for the full error message
- Common issues:
  - Missing imports
  - Undefined variables
  - Network request failures
  - Missing native module configurations

### 10. Reset Simulator

If nothing else works, reset the simulator:

```bash
# List all simulators
xcrun simctl list devices

# Erase a specific simulator (replace DEVICE_ID)
xcrun simctl erase DEVICE_ID

# Or reset all simulators
xcrun simctl erase all
```

Then rebuild:
```bash
cd assets/javascript/mobile
npx react-native run-ios
```

## Common Error Messages and Solutions

### "Unable to connect to Metro bundler"
- **Solution:** Start Metro bundler first: `npx react-native start`
- Check firewall settings
- Verify port 8081 is not blocked

### "Network request failed"
- **Solution:** Check API_BASE_URL in `src/config/api.ts`
- Verify backend server is running
- Check Info.plist network exceptions

### "Module not found"
- **Solution:** Run `npm install` and `cd ios && pod install`

### "Code signing error"
- **Solution:** Open Xcode, go to Signing & Capabilities, enable automatic signing

### Blank white screen
- **Solution:** Check Metro bundler is running and accessible
- Check console for JavaScript errors
- Verify all imports are correct

## Still Having Issues?

1. **Check React Native version compatibility:**
   ```bash
   npx react-native --version
   ```

2. **Verify Xcode version:**
   ```bash
   xcodebuild -version
   ```

3. **Check CocoaPods version:**
   ```bash
   pod --version
   ```

4. **Review recent changes:**
   - Check git diff for any recent modifications
   - Try reverting to a known working commit

5. **Create a minimal test:**
   - Temporarily replace `App.tsx` with a simple "Hello World" component
   - If that works, the issue is in your app code, not the setup

## Getting Help

When asking for help, provide:
- Error messages from console
- Metro bundler output
- Xcode build log
- Steps you've already tried
- React Native version
- Xcode version
- macOS version

