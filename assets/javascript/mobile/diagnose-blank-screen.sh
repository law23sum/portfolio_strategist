#!/bin/bash
echo "=========================================="
echo "iOS Blank Screen Diagnostic"
echo "=========================================="
echo ""

echo "1. Checking Metro Bundler..."
if lsof -i :8081 > /dev/null 2>&1; then
    echo "   ✓ Metro is running on port 8081"
    METRO_PID=$(lsof -ti :8081)
    echo "   PID: $METRO_PID"
else
    echo "   ✗ Metro is NOT running"
    echo "   Start with: npx react-native start"
    exit 1
fi
echo ""

echo "2. Testing Metro accessibility..."
if curl -s http://localhost:8081/status > /dev/null 2>&1; then
    echo "   ✓ Metro status endpoint accessible"
else
    echo "   ✗ Metro status endpoint NOT accessible"
fi
echo ""

echo "3. Testing bundle URL..."
BUNDLE_TEST=$(curl -s "http://localhost:8081/index.bundle?platform=ios&dev=true" 2>&1 | head -5)
if echo "$BUNDLE_TEST" | grep -q "index.js\|SIMPLE\|__d"; then
    echo "   ✓ Bundle URL returns JavaScript code"
    echo "   First few lines:"
    echo "$BUNDLE_TEST" | head -3 | sed 's/^/      /'
else
    echo "   ✗ Bundle URL may not be working"
    echo "   Response: $BUNDLE_TEST"
fi
echo ""

echo "4. Checking for index.js..."
if [ -f "index.js" ]; then
    echo "   ✓ index.js exists"
    if grep -q "SIMPLE VERSION" index.js; then
        echo "   ✓ Using simple version (no gesture-handler)"
    else
        echo "   ⚠ Not using simple version"
    fi
else
    echo "   ✗ index.js NOT FOUND"
fi
echo ""

echo "5. Checking for App.tsx..."
if [ -f "App.tsx" ]; then
    echo "   ✓ App.tsx exists"
    if grep -q "TEST APP" App.tsx; then
        echo "   ✓ Using test version"
    else
        echo "   ⚠ Not using test version"
    fi
else
    echo "   ✗ App.tsx NOT FOUND"
fi
echo ""

echo "6. Checking app.json..."
if [ -f "app.json" ]; then
    echo "   ✓ app.json exists"
    APP_NAME=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' app.json | cut -d'"' -f4)
    echo "   App name: $APP_NAME"
else
    echo "   ✗ app.json NOT FOUND"
fi
echo ""

echo "7. Checking iOS build setup..."
if [ -d "ios" ]; then
    echo "   ✓ ios directory exists"
    if [ -f "ios/mobile.xcworkspace/contents.xcworkspacedata" ]; then
        echo "   ✓ Xcode workspace exists"
    else
        echo "   ✗ Xcode workspace NOT FOUND"
    fi
    if [ -f "ios/Podfile.lock" ]; then
        echo "   ✓ Pods installed (Podfile.lock exists)"
    else
        echo "   ⚠ Pods may not be installed (no Podfile.lock)"
    fi
else
    echo "   ✗ ios directory NOT FOUND"
fi
echo ""

echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. Rebuild the app:"
echo "   cd ios && xcodebuild clean -workspace mobile.xcworkspace -scheme mobile"
echo "   cd .. && npx react-native run-ios"
echo ""
echo "2. Check Xcode console for:"
echo "   - [AppDelegate] logs"
echo "   - [index.js] logs"
echo "   - [TEST APP] logs"
echo ""
echo "3. Check Metro terminal for:"
echo "   - Bundle requests"
echo "   - JavaScript logs"
echo ""
echo "4. If still blank, share:"
echo "   - ALL Xcode console output"
echo "   - Metro bundler output"
echo "   - Screenshot of simulator"
echo ""
