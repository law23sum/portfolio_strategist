#!/usr/bin/env python3
"""
Python script to add icon imagesets to Xcode project.
This automates the manual process of adding files to Xcode.

Usage:
    python3 add_to_xcode.py
    
Or install xcodeproj library first:
    pip3 install xcodeproj
    python3 add_to_xcode.py
"""

import os
import sys
from pathlib import Path

def add_imagesets_with_xcodeproj():
    """Add imagesets using xcodeproj library."""
    try:
        from xcodeproj import XcodeProject
    except ImportError:
        print("❌ xcodeproj library not installed")
        print("Install with: pip3 install xcodeproj")
        return False
    
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent.parent.parent
    project_path = project_dir / 'mobile.xcodeproj' / 'project.pbxproj'
    images_dir = script_dir
    
    if not project_path.exists():
        print(f"❌ Project file not found: {project_path}")
        return False
    
    print(f"📂 Opening project: {project_path}")
    project = XcodeProject.load(str(project_path))
    
    # Find Images.xcassets group
    images_group = None
    for group in project.groups:
        if hasattr(group, 'name') and group.name == 'Images.xcassets':
            images_group = group
            break
        elif hasattr(group, 'path') and 'Images.xcassets' in str(group.path):
            images_group = group
            break
    
    if not images_group:
        print("❌ Images.xcassets group not found in project")
        print("Available groups:")
        for group in project.groups[:10]:  # Show first 10
            print(f"  - {getattr(group, 'name', 'unnamed')}")
        return False
    
    print("✅ Found Images.xcassets group")
    
    # Get all imagesets
    imagesets = [d for d in os.listdir(images_dir) if d.endswith('.imageset')]
    print(f"📦 Found {len(imagesets)} imagesets")
    
    added_count = 0
    skipped_count = 0
    
    for imageset in sorted(imagesets):
        imageset_path = images_dir / imageset
        
        if not imageset_path.is_dir():
            continue
        
        # Check if already added
        already_added = False
        if hasattr(images_group, 'file_refs'):
            for file_ref in images_group.file_refs:
                if imageset in str(file_ref.path):
                    already_added = True
                    break
        
        if not already_added:
            try:
                images_group.add_file(str(imageset_path))
                added_count += 1
                print(f"✅ Added: {imageset}")
            except Exception as e:
                print(f"⚠️  Could not add {imageset}: {e}")
        else:
            skipped_count += 1
            print(f"⏭️  Already added: {imageset}")
    
    # Save project
    try:
        project.save()
        print(f"\n✅ Successfully processed {len(imagesets)} imagesets")
        print(f"   Added: {added_count}")
        print(f"   Skipped: {skipped_count}")
        return True
    except Exception as e:
        print(f"❌ Error saving project: {e}")
        return False

def main():
    """Main function."""
    print("🔧 Adding icon imagesets to Xcode project...")
    print("")
    
    if add_imagesets_with_xcodeproj():
        print("")
        print("✅ Done! Please open Xcode and verify:")
        print("   1. Open mobile.xcworkspace")
        print("   2. Check Images.xcassets in Project Navigator")
        print("   3. Verify all icon-* imagesets are visible")
        print("")
        print("If imagesets don't appear:")
        print("   - Product → Clean Build Folder (Shift+Cmd+K)")
        print("   - Close and reopen Xcode")
    else:
        print("")
        print("⚠️  Could not automatically add imagesets.")
        print("")
        print("Manual steps:")
        print("1. Open Xcode: open ../mobile.xcworkspace")
        print("2. Right-click 'Images.xcassets' → 'Add Files to mobile...'")
        print("3. Navigate to this folder and select all icon-*.imageset folders")
        print("4. Make sure 'Create groups' is selected")
        print("5. Click 'Add'")
        print("")
        print("Note: Xcode should automatically discover imagesets in asset catalogs.")
        print("Try cleaning the build folder first: Product → Clean Build Folder")

if __name__ == '__main__':
    main()

