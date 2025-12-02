#!/bin/bash

echo "🔍 Checking iOS App Setup..."
echo ""

# Check Node version
echo "📦 Node.js:"
node --version || echo "❌ Node.js not found"
echo ""

# Check if in correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must run from assets/javascript/mobile directory"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found. Run: npm install"
else
    echo "✅ node_modules exists"
fi

# Check iOS pods
echo ""
echo "🍎 Checking iOS dependencies..."
if [ ! -d "ios/Pods" ]; then
    echo "⚠️  Pods not installed. Run: cd ios && pod install"
else
    echo "✅ Pods installed"
fi

# Check Metro bundler
echo ""
echo "🚇 Checking Metro bundler..."
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Metro bundler is running on port 8081"
else
    echo "⚠️  Metro bundler is NOT running"
    echo "   Start it with: npx react-native start"
fi

# Check available simulators
echo ""
echo "📱 Available iOS Simulators:"
xcrun simctl list devices available | grep -E "iPhone|iPad" | head -5 || echo "⚠️  Could not list simulators"

# Check API config
echo ""
echo "🌐 Checking API configuration..."
if grep -q "YOUR_LOCAL_IP" src/config/api.ts 2>/dev/null; then
    echo "⚠️  API_BASE_URL may need to be updated in src/config/api.ts"
else
    echo "✅ API configuration looks set"
fi

echo ""
echo "✅ Setup check complete!"
echo ""
echo "To start the app:"
echo "  1. Terminal 1: npx react-native start"
echo "  2. Terminal 2: npx react-native run-ios"

