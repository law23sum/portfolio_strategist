#!/bin/bash

# Simple script to refresh Xcode and make imagesets visible
# This is often all that's needed since Xcode should auto-discover imagesets

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE="$IOS_DIR/mobile.xcworkspace"

echo "🔄 Refreshing Xcode project to show icon imagesets..."
echo ""

# Check if workspace exists
if [ ! -d "$WORKSPACE" ]; then
    echo "❌ Error: Xcode workspace not found at $WORKSPACE"
    exit 1
fi

echo "📂 Workspace: $WORKSPACE"
echo "📁 Images directory: $SCRIPT_DIR"
echo ""

# Count imagesets
IMAGESET_COUNT=$(find "$SCRIPT_DIR" -maxdepth 1 -type d -name "icon-*.imageset" | wc -l | tr -d ' ')
echo "✅ Found $IMAGESET_COUNT icon imagesets"
echo ""

# Open Xcode workspace
echo "🚀 Opening Xcode workspace..."
open "$WORKSPACE"

echo ""
echo "⏳ Waiting for Xcode to open..."
sleep 3

# Use AppleScript to clean build folder (forces refresh)
echo "🧹 Cleaning build folder in Xcode..."
osascript << 'APPLESCRIPT'
tell application "Xcode"
    activate
    delay 2
    
    -- Try to clean build folder
    try
        tell application "System Events"
            tell process "Xcode"
                -- Press Cmd+Shift+K to clean build folder
                key code 40 using {command down, shift down}
                delay 1
            end tell
        end tell
        return "Cleaned build folder"
    on error
        return "Could not clean automatically - please do it manually: Product → Clean Build Folder (Shift+Cmd+K)"
    end try
end tell
APPLESCRIPT

echo ""
echo "✅ Done!"
echo ""
echo "📋 Next steps:"
echo "1. In Xcode, navigate to: mobile → Images.xcassets"
echo "2. You should see all $IMAGESET_COUNT icon imagesets"
echo "3. If not visible, try: Product → Clean Build Folder (Shift+Cmd+K)"
echo "4. Then close and reopen Xcode"
echo ""
echo "💡 Tip: Xcode should automatically discover imagesets in asset catalogs."
echo "   If they don't appear, they may need to be manually added (see AUTO_ADD_GUIDE.md)"

