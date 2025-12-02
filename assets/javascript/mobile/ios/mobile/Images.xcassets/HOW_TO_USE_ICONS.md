# How to Use the Icon Images in Your iOS App

## ✅ Icons Have Been Generated

All placeholder PNG icons have been created successfully! You now have:
- 41 icon sets
- 82 PNG files (@2x and @3x for each icon)

## Current Status

The app is currently using `react-native-vector-icons` which works perfectly fine. The image assets I created are **optional** - they're there if you want to use custom icon images instead of vector icons.

## Two Options:

### Option 1: Keep Using Vector Icons (Current - Recommended)
The app already works with `react-native-vector-icons`. No changes needed!

### Option 2: Use Custom Image Icons

If you want to use the PNG icons I created, you need to:

#### Step 1: Add Images to Xcode Project

1. Open `ios/mobile.xcworkspace` in Xcode
2. In the Project Navigator, find `mobile/Images.xcassets`
3. The icon imagesets should already be there (they're in the folder)
4. **Important**: Make sure Xcode recognizes them:
   - Right-click on `Images.xcassets` → "Add Files to mobile..."
   - Navigate to the `Images.xcassets` folder
   - Select all the `.imageset` folders
   - Make sure "Create groups" is selected
   - Click "Add"

#### Step 2: Verify Images in Asset Catalog

1. In Xcode, click on `Images.xcassets` in the Project Navigator
2. You should see all the icon imagesets listed
3. Click on one (e.g., `icon-dashboard`) to verify it shows @2x and @3x images

#### Step 3: Use Images in React Native Code

To use the images, you have two approaches:

**Approach A: Use Image Component Directly**

```tsx
import { Image } from 'react-native';

// In your component:
<Image 
  source={{ uri: 'icon-dashboard' }} 
  style={{ width: 24, height: 24 }} 
/>
```

**Approach B: Create a Helper Component**

I've created `AppIcon.tsx` component, but it needs the images to be properly registered in Xcode first.

#### Step 4: Rebuild the App

After adding images to Xcode:
```bash
cd assets/javascript/mobile/ios
pod install
cd ..
npx react-native run-ios
```

## Why Images Might Not Show

If you're trying to use the images but they're not showing:

1. **Images not added to Xcode project** - The PNG files exist, but Xcode needs to know about them
2. **Asset catalog not properly configured** - The Contents.json files are correct, but Xcode needs to index them
3. **App not rebuilt** - After adding images, you need to rebuild the app

## Quick Test

To test if images are working:

1. Open Xcode
2. Go to `Images.xcassets`
3. Find `icon-dashboard`
4. You should see two images: `icon-dashboard@2x.png` and `icon-dashboard@3x.png`
5. If you see them, they're ready to use
6. If you don't see them, follow Step 1 above to add them

## Recommendation

**For now, keep using `react-native-vector-icons`** - it's working perfectly and doesn't require any setup. The PNG icons I created are there if you want to customize them later with your own designs.

If you want to replace the placeholder icons with proper designs:
1. Replace the PNG files in each `.imageset` folder with your custom designs
2. Keep the same filenames (`icon-name@2x.png` and `icon-name@3x.png`)
3. Rebuild the app

