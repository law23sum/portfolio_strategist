#!/bin/bash
echo "Quick Build Script"
echo "=================="
echo ""
echo "This will try to build the app using different methods..."
echo ""

echo "Method 1: Build for simulator SDK (no device specified)..."
cd ios
xcodebuild -workspace mobile.xcworkspace -scheme mobile -sdk iphonesimulator -configuration Debug build CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO 2>&1 | tail -20
echo ""

echo "If that failed, try building from Xcode:"
echo "1. Open ios/mobile.xcworkspace in Xcode"
echo "2. Select iPhone 16 Pro simulator"
echo "3. Press Cmd+R"
echo ""
