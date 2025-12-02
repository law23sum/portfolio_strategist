# CRITICAL: Blank Screen Debugging

## Current Status
- ✅ Metro bundler is running
- ✅ Bundle URL is accessible
- ✅ Minimal test code is in place
- ❌ Screen is still blank

## What This Means

If even the minimal "Hello World" test is blank, the issue is likely:

1. **JavaScript bundle not executing** - Bundle loads but doesn't run
2. **Native crash** - App crashes before React renders
3. **Metro connection issue** - Simulator can't reach Metro bundler
4. **Bundle root mismatch** - AppDelegate looking for wrong bundle

## IMMEDIATE ACTIONS

### Step 1: Check Console Logs

**CRITICAL:** Look for these log messages in order:

1. **Metro Bundler Terminal:**
   - `[index.js] Starting index.js execution...`
   - `[index.js] Registering app component: mobile`
   - `[TEST APP] App component function called`

2. **Xcode Console:**
   - Open `ios/mobile.xcworkspace` in Xcode
   - Run the app
   - Look for ALL console.log messages
   - Check for RED error messages

**If you DON'T see `[index.js] Starting index.js execution...`:**
- The JavaScript bundle is NOT executing
- Check Metro bundler connection
- Check bundle URL in AppDelegate

**If you see `[index.js]` logs but NOT `[TEST APP]` logs:**
- AppRegistry registration failed
- Check app.json name matches

**If you see both but screen is blank:**
- React Native rendering issue
- Check for native module errors

### Step 2: Test Simplest Version

Try the version WITHOUT gesture-handler and reanimated:

```bash
cd assets/javascript/mobile

# Backup current index.js
cp index.js index.js.backup

# Use simple version
cp index.test-simple.js index.js

# Restart Metro
killall node
npx react-native start --reset-cache

# In another terminal, rebuild
npx react-native run-ios
```

### Step 3: Check Metro Connection from Simulator

**In Simulator Safari:**
1. Open Safari
2. Navigate to: `http://localhost:8081`
3. You should see Metro bundler status page

**If this doesn't work:**
- Metro bundler not accessible from simulator
- Check firewall settings
- Try using your Mac's IP address instead of localhost

### Step 4: Verify Bundle URL

Check what URL the app is trying to load:

**In Xcode Console, look for:**
- `Loading JavaScript bundle from...`
- Any network errors
- Any bundle loading errors

### Step 5: Check for Native Crashes

**In Xcode:**
1. Open `ios/mobile.xcworkspace`
2. Run the app
3. Check the **Issue Navigator** (Cmd+4)
4. Look for any build errors or warnings

**Check Console for:**
- `EXC_BAD_ACCESS` errors
- `SIGABRT` errors
- Any Swift/Objective-C errors

### Step 6: Test Bundle Execution

Add this to verify bundle is executing:

**In App.tsx, add at the very top:**
```typescript
console.log('=== APP.TSX LOADED ===');
console.log('Timestamp:', new Date().toISOString());
```

If you don't see this log, App.tsx isn't being loaded.

## Common Issues & Fixes

### Issue: "Unable to connect to Metro bundler"
**Fix:**
```bash
# Check Metro is running
lsof -i :8081

# If not running:
npx react-native start

# Check firewall allows port 8081
```

### Issue: Bundle loads but doesn't execute
**Fix:**
- Check for syntax errors in index.js
- Check for circular dependencies
- Verify app.json name matches

### Issue: Native crash on startup
**Fix:**
```bash
cd ios
pod deintegrate
pod install
cd ..
```

### Issue: Wrong bundle root
**Fix:**
- Verify AppDelegate.swift has correct bundleRoot: `"index"`
- Check Info.plist has correct settings

## What to Share

Please share:

1. **ALL console logs** from:
   - Metro bundler terminal
   - Xcode console
   - Simulator (if any)

2. **Screenshot** of:
   - Simulator screen
   - Xcode console
   - Metro bundler terminal

3. **Which logs you see:**
   - Do you see `[index.js] Starting...`?
   - Do you see `[TEST APP] App component...`?
   - Any error messages?

4. **Build output:**
   - Any Xcode build errors?
   - Any warnings?

## Expected Log Sequence

When working correctly, you should see:

```
[index.js] Starting index.js execution...
[index.js] Timestamp: ...
[index.js] Importing react-native-gesture-handler...
[index.js] ✓ react-native-gesture-handler loaded
[index.js] Importing react-native-reanimated...
[index.js] ✓ react-native-reanimated loaded
[index.js] Importing react-native...
[index.js] ✓ react-native loaded
[index.js] Importing App component...
[index.js] ✓ App component loaded
[index.js] Loading app.json...
[index.js] ✓ app.json loaded, appName: mobile
[index.js] Registering app component: mobile
[index.js] App component factory called
[index.js] ✓ App component registered successfully
[TEST APP] App component function called
[TEST APP] Rendering minimal test app...
[TEST APP] Attempting to render...
[TEST APP] App component mounted (useEffect)
```

If you see a different sequence or missing logs, that tells us where it's failing.

