# Quick Fix: Images Not Showing

## The Problem

The PNG images exist but React Native can't load them because:
1. React Native requires images to be bundled at build time
2. The `require()` paths need to be static (can't use variables)
3. Images need to be accessible from the JavaScript bundle

## Solution: Use require() with Static Paths

I've updated `AppIcon.tsx` to use `require()` with static paths. However, React Native's bundler (Metro) needs to be able to resolve these paths.

## Steps to Fix:

### 1. Verify Images Exist
```bash
cd assets/javascript/mobile/ios/mobile/Images.xcassets
ls icon-dashboard.imageset/
# Should show: Contents.json, icon-dashboard@2x.png, icon-dashboard@3x.png
```

### 2. Rebuild the App
```bash
cd assets/javascript/mobile
npx react-native start --reset-cache
# In another terminal:
npx react-native run-ios
```

### 3. Test Icons
I've created a test screen. Add it to your navigation temporarily:

```tsx
// In AppNavigator.tsx, add:
import IconTestScreen from '../screens/test/IconTestScreen';

// In your stack navigator:
<Stack.Screen name="IconTest" component={IconTestScreen} />
```

Then navigate to it to see if icons load.

## Alternative: Use Vector Icons (Current Working Solution)

The app currently uses `react-native-vector-icons` which works perfectly. If you want to keep using that (recommended), no changes are needed.

## If Images Still Don't Show:

1. **Check Metro bundler logs** - Look for "Unable to resolve module" errors
2. **Verify file paths** - Make sure the require() paths match actual file locations
3. **Check Xcode build** - Ensure Images.xcassets is included in the build
4. **Try a simple test** - Use Image component directly:
   ```tsx
   <Image 
     source={require('../../ios/mobile/Images.xcassets/icon-dashboard.imageset/icon-dashboard@2x.png')} 
     style={{ width: 24, height: 24 }} 
   />
   ```

## Why This Is Complex

React Native's image loading has limitations:
- Images must be statically analyzable at build time
- Dynamic paths don't work with require()
- Asset catalogs work differently than regular images

The `react-native-vector-icons` library handles all this complexity for you, which is why it's the recommended approach.

