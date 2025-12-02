# Icon Images

These are the @2x PNG icon images copied from the iOS asset catalog so that React Native's Metro bundler can bundle them.

## Usage

Icons are loaded via the `AppIcon` component:

```tsx
import AppIcon from '../components/AppIcon';

<AppIcon name="dashboard" size={24} tintColor="#007AFF" />
```

## Available Icons

All 41 icons are available. See `AppIcon.tsx` for the complete list.

## Note

These are @2x resolution images. React Native will automatically scale them appropriately for different screen densities.

