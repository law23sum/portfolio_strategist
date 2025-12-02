#!/bin/bash
echo "=== iOS Blank Screen Diagnostic ==="
echo ""

echo "1. Checking Metro Bundler..."
if lsof -i :8081 > /dev/null 2>&1; then
    echo "   ✓ Metro bundler is running on port 8081"
else
    echo "   ✗ Metro bundler is NOT running"
    echo "   Run: npx react-native start"
fi
echo ""

echo "2. Testing Metro connection..."
if curl -s http://localhost:8081/status > /dev/null 2>&1; then
    echo "   ✓ Metro bundler is accessible"
else
    echo "   ✗ Metro bundler is NOT accessible"
    echo "   Try: curl http://localhost:8081/status"
fi
echo ""

echo "3. Checking bundle URL..."
BUNDLE=$(curl -s "http://localhost:8081/index.bundle?platform=ios" 2>&1 | head -5)
if echo "$BUNDLE" | grep -q "React\|__d\|require"; then
    echo "   ✓ Bundle is loading (contains React code)"
else
    echo "   ✗ Bundle may not be loading correctly"
    echo "   Output: $BUNDLE"
fi
echo ""

echo "4. Checking for common issues..."
if [ -f "App.tsx" ]; then
    if grep -q "SafeAreaProvider" App.tsx; then
        echo "   ✓ SafeAreaProvider is present"
    else
        echo "   ✗ SafeAreaProvider is MISSING"
    fi
else
    echo "   ✗ App.tsx not found"
fi
echo ""

echo "5. Checking node_modules..."
if [ -d "node_modules" ]; then
    echo "   ✓ node_modules exists"
    if [ -d "node_modules/react-native-safe-area-context" ]; then
        echo "   ✓ react-native-safe-area-context installed"
    else
        echo "   ✗ react-native-safe-area-context MISSING"
    fi
else
    echo "   ✗ node_modules not found - run npm install"
fi
echo ""

echo "=== Next Steps ==="
echo "1. Check Xcode console for errors"
echo "2. Check Metro bundler terminal for JavaScript errors"
echo "3. Shake simulator (Cmd+Ctrl+Z) and select 'Debug'"
echo "4. Try minimal test: Use App.test-minimal.tsx"
