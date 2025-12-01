# Running the iOS App

## Quick Start

### Option 1: Using Xcode (Recommended for first-time setup)
```bash
cd assets/javascript/mobile
open ios/mobile.xcworkspace
```
Then in Xcode:
1. Select a simulator from the device dropdown (top left)
2. Press `Cmd + R` or click the Play button
3. Wait for the build to complete

### Option 2: Using Command Line
```bash
cd assets/javascript/mobile
npx react-native run-ios
```

### Option 3: Specify a Simulator
```bash
cd assets/javascript/mobile
npx react-native run-ios --simulator="iPhone 16 Pro"
```

## Troubleshooting

### Error Code 70
This usually means:
- Code signing issue - Fix in Xcode: Project Settings > Signing & Capabilities > Enable "Automatically manage signing"
- Simulator not available - Check available simulators: `xcrun simctl list devices available`

### Check Available Simulators
```bash
xcrun simctl list devices available
```

### Clean Build
If you encounter build issues:
```bash
cd assets/javascript/mobile/ios
xcodebuild clean -workspace mobile.xcworkspace -scheme mobile
cd ..
npx react-native run-ios
```

### Reinstall Pods
If dependencies are missing:
```bash
cd assets/javascript/mobile/ios
pod install
cd ..
```

### Start Metro Bundler Separately
Sometimes it helps to start Metro first:
```bash
cd assets/javascript/mobile
npx react-native start
```
Then in another terminal:
```bash
npx react-native run-ios
```

## First Time Setup Checklist

- [ ] Node.js installed (>= 18)
- [ ] Xcode installed
- [ ] CocoaPods installed (`pod --version`)
- [ ] Dependencies installed (`npm install`)
- [ ] Pods installed (`cd ios && pod install`)
- [ ] Code signing configured in Xcode

## Common Issues

1. **"Unable to find a destination"** - The simulator ID changed. Use Xcode to select a simulator, or list available ones with `xcrun simctl list devices`

2. **Code signing errors** - Open Xcode, go to Signing & Capabilities, enable automatic signing, and select your Apple ID/Team

3. **Build fails with module errors** - Run `cd ios && pod install && cd ..`

4. **Metro bundler issues** - Clear cache: `npx react-native start --reset-cache`

