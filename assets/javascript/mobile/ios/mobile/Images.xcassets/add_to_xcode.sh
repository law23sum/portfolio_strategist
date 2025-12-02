#!/bin/bash

# Script to add icon imagesets to Xcode project
# This automates the manual process described in HOW_TO_USE_ICONS.md

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
XCODE_PROJECT="$PROJECT_DIR/mobile.xcodeproj"
WORKSPACE="$PROJECT_DIR/mobile.xcworkspace"
IMAGES_DIR="$SCRIPT_DIR"

echo "🔧 Adding icon imagesets to Xcode project..."
echo ""
echo "Project: $XCODE_PROJECT"
echo "Images directory: $IMAGES_DIR"
echo ""

# Check if Xcode project exists
if [ ! -d "$XCODE_PROJECT" ]; then
    echo "❌ Error: Xcode project not found at $XCODE_PROJECT"
    exit 1
fi

# Check if workspace exists
if [ ! -d "$WORKSPACE" ]; then
    echo "❌ Error: Xcode workspace not found at $WORKSPACE"
    exit 1
fi

# Check if we have Python with xcodeproj library
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found"
    
    # Try to install/use xcodeproj library
    if python3 -c "import xcodeproj" 2>/dev/null; then
        echo "✅ xcodeproj library found"
        USE_PYTHON=true
    else
        echo "⚠️  xcodeproj library not found, will use AppleScript instead"
        USE_PYTHON=false
    fi
else
    USE_PYTHON=false
fi

# Method 1: Use Python xcodeproj library (most reliable)
if [ "$USE_PYTHON" = true ]; then
    echo ""
    echo "Using Python xcodeproj library..."
    python3 << 'PYTHON_SCRIPT'
import sys
import os
from pathlib import Path

try:
    from xcodeproj import XcodeProject
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
    project_path = os.path.join(project_dir, 'mobile.xcodeproj', 'project.pbxproj')
    images_dir = script_dir
    
    if not os.path.exists(project_path):
        print(f"❌ Project file not found: {project_path}")
        sys.exit(1)
    
    # Open project
    project = XcodeProject.load(project_path)
    
    # Find Images.xcassets group
    images_group = None
    for group in project.groups:
        if group.name == 'Images.xcassets' or 'Images.xcassets' in str(group.path):
            images_group = group
            break
    
    if not images_group:
        print("❌ Images.xcassets group not found in project")
        sys.exit(1)
    
    # Add all imagesets
    imagesets = [d for d in os.listdir(images_dir) if d.endswith('.imageset')]
    added_count = 0
    
    for imageset in sorted(imagesets):
        imageset_path = os.path.join(images_dir, imageset)
        if os.path.isdir(imageset_path):
            # Check if already added
            already_added = False
            for file_ref in images_group.file_refs:
                if imageset in str(file_ref.path):
                    already_added = True
                    break
            
            if not already_added:
                images_group.add_file(imageset_path)
                added_count += 1
                print(f"✅ Added: {imageset}")
            else:
                print(f"⏭️  Already added: {imageset}")
    
    # Save project
    project.save()
    print(f"\n✅ Successfully added {added_count} imagesets to Xcode project")
    
except ImportError:
    print("❌ xcodeproj library not installed")
    print("Install with: pip3 install xcodeproj")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Done! Please open Xcode and verify the imagesets are visible."
        echo "   If they don't appear, try: Product → Clean Build Folder"
        exit 0
    fi
fi

# Method 2: Use AppleScript to automate Xcode GUI
echo ""
echo "Using AppleScript to automate Xcode..."
echo "⚠️  This will open Xcode and attempt to add files automatically"
echo ""

# Create AppleScript
osascript << 'APPLESCRIPT'
tell application "Xcode"
    activate
    
    -- Open workspace if not already open
    set workspacePath to POSIX file "/Users/chrisdixon/Projects/portfolio_strategist/assets/javascript/mobile/ios/mobile.xcworkspace"
    
    try
        open workspacePath
        delay 2
    on error
        display dialog "Could not open Xcode workspace. Please open it manually first." buttons {"OK"} default button "OK"
        return
    end try
    
    -- Wait for Xcode to load
    delay 3
    
    -- Note: Full automation of "Add Files" dialog is complex
    -- Instead, we'll provide instructions
    display dialog "To add the imagesets:" & return & return & "1. In Xcode, right-click 'Images.xcassets'" & return & "2. Select 'Add Files to mobile...'" & return & "3. Navigate to the Images.xcassets folder" & return & "4. Select all icon-*.imageset folders" & return & "5. Make sure 'Create groups' is selected" & return & "6. Click 'Add'" buttons {"OK", "Open Finder"} default button "Open Finder"
    
    if button returned of result is "Open Finder" then
        tell application "Finder"
            activate
            open POSIX file "/Users/chrisdixon/Projects/portfolio_strategist/assets/javascript/mobile/ios/mobile/Images.xcassets"
        end tell
    end if
end tell
APPLESCRIPT

echo ""
echo "📝 Manual Steps:"
echo "1. In Xcode, right-click on 'Images.xcassets'"
echo "2. Select 'Add Files to mobile...'"
echo "3. Navigate to: $(pwd)"
echo "4. Select all icon-*.imageset folders"
echo "5. Make sure 'Create groups' is selected (NOT 'Create folder references')"
echo "6. Click 'Add'"
echo ""
echo "Alternatively, Xcode should automatically discover imagesets in the asset catalog."
echo "Try: Product → Clean Build Folder, then check Images.xcassets again."

