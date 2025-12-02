# iOS Icon Images Guide

This directory contains image asset sets for all icons used throughout the iOS app. Each icon has its own `.imageset` folder with a `Contents.json` file that defines the image structure.

## Icon Structure

Each icon image set requires two PNG files:
- `icon-name@2x.png` - 2x resolution (e.g., 50x50px for a 25pt icon)
- `icon-name@3x.png` - 3x resolution (e.g., 75x75px for a 25pt icon)

## Tab Bar Icons

These icons are used in the bottom tab navigation. Recommended size: **25x25 points** (50x50px @2x, 75x75px @3x)

- `icon-dashboard.imageset` - Dashboard tab icon
- `icon-records.imageset` - Records tab icon  
- `icon-stocks.imageset` - Stock Analysis tab icon
- `icon-solutions.imageset` - Solutions tab icon
- `icon-chat.imageset` - Chat tab icon
- `icon-profile.imageset` - Profile tab icon

## Dashboard Icons

Recommended size: **32x32 points** (64x64px @2x, 96x96px @3x)

- `icon-upload.imageset` - Upload Document action
- `icon-analyze-stock.imageset` - Analyze Stock action
- `icon-link-account.imageset` - Link Account action
- `icon-insights.imageset` - View Insights action
- `icon-attach-money.imageset` - Total Assets indicator
- `icon-wallet.imageset` - Cash/Wallet indicator
- `icon-credit-card.imageset` - Liabilities indicator
- `icon-arrow-up.imageset` - Credit transaction indicator
- `icon-arrow-down.imageset` - Debit transaction indicator

## Records Screen Icons

Recommended size: **32x32 points** (64x64px @2x, 96x96px @3x)

- `icon-insights.imageset` - Financial Insights
- `icon-explorer.imageset` - Data Explorer
- `icon-upload.imageset` - Upload Document
- `icon-linked-accounts.imageset` - Linked Accounts
- `icon-description.imageset` - Document icon
- `icon-camera.imageset` - Camera icon for photo capture

## Stock Analysis Icons

Recommended size: **32x32 points** (64x64px @2x, 96x96px @3x)

- `icon-search.imageset` - Search/Analyze Stock
- `icon-account-balance.imageset` - Loan Analysis
- `icon-info.imageset` - Information icon
- `icon-loan-analysis.imageset` - Loan Analysis feature

## Chat Screen Icons

Recommended size: **24x24 points** (48x48px @2x, 72x72px @3x)

- `icon-person.imageset` - Human message avatar
- `icon-smart-toy.imageset` - AI message avatar
- `icon-arrow-back.imageset` - Back button
- `icon-delete.imageset` - Delete/Clear chat
- `icon-send.imageset` - Send message button

## Common UI Icons

Recommended size: **24x24 points** (48x48px @2x, 72x72px @3x)

- `icon-chevron-right.imageset` - Navigation chevron
- `icon-edit.imageset` - Edit action
- `icon-lock.imageset` - Security/Password
- `icon-notifications.imageset` - Notifications
- `icon-subscriptions.imageset` - Subscriptions
- `icon-privacy.imageset` - Privacy settings
- `icon-help.imageset` - Help/Support
- `icon-logout.imageset` - Logout action
- `icon-add.imageset` - Add/Plus button
- `icon-sync.imageset` - Sync/Refresh
- `icon-link-off.imageset` - Unlink/Disconnect
- `icon-savings.imageset` - Savings/Retirement
- `icon-download.imageset` - Download action

## How to Add Icons

1. **Generate or obtain PNG images** for each icon at the required resolutions
   - Use design tools like Sketch, Figma, or Adobe Illustrator
   - Export as PNG with transparent backgrounds
   - Ensure icons are properly sized for their use case

2. **Place images in the correct folder**
   - For `icon-dashboard.imageset`, add:
     - `icon-dashboard@2x.png` (50x50px)
     - `icon-dashboard@3x.png` (75x75px)
   - Repeat for all other icons

3. **Design Guidelines**
   - Use consistent stroke width (2pt recommended)
   - Ensure icons are centered in the canvas
   - Use appropriate colors or provide template images that can be tinted
   - Maintain visual consistency across all icons

4. **Testing**
   - After adding images, rebuild the iOS app
   - Verify icons appear correctly at all sizes
   - Check that icons are properly aligned and centered

## Icon Naming Convention

All icons follow the pattern: `icon-{name}.imageset`
- Use lowercase letters
- Separate words with hyphens
- Keep names descriptive and consistent with their usage

## Notes

- The `Contents.json` files are already configured correctly
- Icons should have transparent backgrounds
- Consider providing both filled and outlined versions if needed
- For tab bar icons, ensure they work well in both selected and unselected states

