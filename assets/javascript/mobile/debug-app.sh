#!/bin/bash

echo "🔍 iOS App Debug Script"
echo "======================"
echo ""

cd "$(dirname "$0")"

echo "1. Checking Metro bundler..."
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null ; then
    echo "   ✅ Metro bundler is running"
    echo "   Testing Metro connection..."
    STATUS=$(curl -s http://localhost:8081/status)
    echo "   Metro status: $STATUS"
else
    echo "   ❌ Metro bundler is NOT running"
    echo "   Start it with: npx react-native start"
    exit 1
fi

echo ""
echo "2. Testing bundle URL..."
BUNDLE_URL="http://localhost:8081/index.bundle?platform=ios&dev=true"
echo "   Testing: $BUNDLE_URL"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BUNDLE_URL")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Bundle URL is accessible (HTTP $HTTP_CODE)"
else
    echo "   ❌ Bundle URL returned HTTP $HTTP_CODE"
    echo "   This might indicate a bundling error"
fi

echo ""
echo "3. Checking for JavaScript errors in Metro..."
echo "   Look at your Metro bundler terminal for red error messages"
echo "   Common issues:"
echo "   - Module not found"
echo "   - Syntax errors"
echo "   - Type errors"

echo ""
echo "4. Checking React/React Native versions..."
echo "   React: $(grep '"react":' package.json | head -1)"
echo "   React Native: $(grep '"react-native":' package.json | head -1)"
echo ""
echo "   ⚠️  WARNING: React 19 may not be compatible with React Native 0.78"
echo "   React Native 0.78 typically requires React 18.x"

echo ""
echo "5. Next steps:"
echo "   a) Check Xcode console for native errors"
echo "   b) Check Metro bundler terminal for JS errors"
echo "   c) Shake simulator (Cmd+Ctrl+Z) and select 'Debug'"
echo "   d) Try opening http://localhost:8081/debugger-ui in Safari"
echo ""
echo "6. To test with minimal app:"
echo "   Temporarily replace App.tsx content with App.test.tsx"
echo "   Then rebuild: npx react-native run-ios"

