# Automatically Add Imagesets to Xcode

I've created scripts to automate adding the icon imagesets to your Xcode project.

## Quick Start

### Option 1: Use Python Script (Recommended)

```bash
cd assets/javascript/mobile/ios/mobile/Images.xcassets

# Install xcodeproj library (one-time setup)
pip3 install xcodeproj

# Run the script
python3 add_to_xcode.py
```

This will automatically add all 41 icon imagesets to your Xcode project.

### Option 2: Use Shell Script

```bash
cd assets/javascript/mobile/ios/mobile/Images.xcassets
./add_to_xcode.sh
```

This script will:
- Try to use Python xcodeproj library if available
- Fall back to AppleScript automation
- Provide manual instructions if automation fails

## What These Scripts Do

They automate the manual process of:
1. Opening Xcode project
2. Finding Images.xcassets folder
3. Adding all icon-*.imageset folders to the project
4. Ensuring they're added as "groups" (not folder references)

## After Running

1. **Open Xcode:**
   ```bash
   open assets/javascript/mobile/ios/mobile.xcworkspace
   ```

2. **Verify in Xcode:**
   - Navigate to `mobile` → `Images.xcassets`
   - You should see all 41 icon imagesets listed
   - Click on one (e.g., `icon-dashboard`) to see the PNG files

3. **If imagesets don't appear:**
   - Product → Clean Build Folder (Shift+Cmd+K)
   - Close and reopen Xcode
   - Xcode should re-index the asset catalog

## Troubleshooting

### "xcodeproj library not found"
```bash
pip3 install xcodeproj
```

### "Permission denied"
```bash
chmod +x add_to_xcode.sh add_to_xcode.py
```

### Scripts don't work
Use manual method:
1. Open Xcode
2. Right-click `Images.xcassets` → "Add Files to mobile..."
3. Select all icon-*.imageset folders
4. Make sure "Create groups" is selected
5. Click "Add"

## Note

Xcode should automatically discover imagesets that are inside an asset catalog folder. If the imagesets are in `Images.xcassets/`, they should be visible without manual addition. The scripts are helpful if Xcode hasn't indexed them yet.

