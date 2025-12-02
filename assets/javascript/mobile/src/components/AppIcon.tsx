import React from 'react';
import { Image, ImageStyle, StyleProp, Platform } from 'react-native';

interface AppIconProps {
  name: string;
  size?: number;
  style?: StyleProp<ImageStyle>;
  tintColor?: string;
}

/**
 * AppIcon component for using iOS asset catalog images
 * 
 * Usage: <AppIcon name="dashboard" size={24} />
 * 
 * In React Native, iOS asset catalog images need to be referenced using require()
 * with the full path to the image file. This component handles that mapping.
 */
export default function AppIcon({ name, size = 24, style, tintColor }: AppIconProps) {
  // Map icon names to their image file paths
  // These paths are relative to the ios/mobile/Images.xcassets folder
  const iconMap: Record<string, () => any> = {
    // Tab bar icons
    dashboard: () => require('../../ios/mobile/Images.xcassets/icon-dashboard.imageset/icon-dashboard@2x.png'),
    records: () => require('../../ios/mobile/Images.xcassets/icon-records.imageset/icon-records@2x.png'),
    stocks: () => require('../../ios/mobile/Images.xcassets/icon-stocks.imageset/icon-stocks@2x.png'),
    solutions: () => require('../../ios/mobile/Images.xcassets/icon-solutions.imageset/icon-solutions@2x.png'),
    chat: () => require('../../ios/mobile/Images.xcassets/icon-chat.imageset/icon-chat@2x.png'),
    profile: () => require('../../ios/mobile/Images.xcassets/icon-profile.imageset/icon-profile@2x.png'),
    
    // Dashboard icons
    upload: () => require('../../ios/mobile/Images.xcassets/icon-upload.imageset/icon-upload@2x.png'),
    'analyze-stock': () => require('../../ios/mobile/Images.xcassets/icon-analyze-stock.imageset/icon-analyze-stock@2x.png'),
    'link-account': () => require('../../ios/mobile/Images.xcassets/icon-link-account.imageset/icon-link-account@2x.png'),
    insights: () => require('../../ios/mobile/Images.xcassets/icon-insights.imageset/icon-insights@2x.png'),
    'attach-money': () => require('../../ios/mobile/Images.xcassets/icon-attach-money.imageset/icon-attach-money@2x.png'),
    wallet: () => require('../../ios/mobile/Images.xcassets/icon-wallet.imageset/icon-wallet@2x.png'),
    'credit-card': () => require('../../ios/mobile/Images.xcassets/icon-credit-card.imageset/icon-credit-card@2x.png'),
    'arrow-up': () => require('../../ios/mobile/Images.xcassets/icon-arrow-up.imageset/icon-arrow-up@2x.png'),
    'arrow-down': () => require('../../ios/mobile/Images.xcassets/icon-arrow-down.imageset/icon-arrow-down@2x.png'),
    
    // Records icons
    explorer: () => require('../../ios/mobile/Images.xcassets/icon-explorer.imageset/icon-explorer@2x.png'),
    'linked-accounts': () => require('../../ios/mobile/Images.xcassets/icon-linked-accounts.imageset/icon-linked-accounts@2x.png'),
    description: () => require('../../ios/mobile/Images.xcassets/icon-description.imageset/icon-description@2x.png'),
    camera: () => require('../../ios/mobile/Images.xcassets/icon-camera.imageset/icon-camera@2x.png'),
    
    // Stock analysis icons
    search: () => require('../../ios/mobile/Images.xcassets/icon-search.imageset/icon-search@2x.png'),
    'account-balance': () => require('../../ios/mobile/Images.xcassets/icon-account-balance.imageset/icon-account-balance@2x.png'),
    info: () => require('../../ios/mobile/Images.xcassets/icon-info.imageset/icon-info@2x.png'),
    'loan-analysis': () => require('../../ios/mobile/Images.xcassets/icon-loan-analysis.imageset/icon-loan-analysis@2x.png'),
    
    // Chat icons
    person: () => require('../../ios/mobile/Images.xcassets/icon-person.imageset/icon-person@2x.png'),
    'smart-toy': () => require('../../ios/mobile/Images.xcassets/icon-smart-toy.imageset/icon-smart-toy@2x.png'),
    'arrow-back': () => require('../../ios/mobile/Images.xcassets/icon-arrow-back.imageset/icon-arrow-back@2x.png'),
    delete: () => require('../../ios/mobile/Images.xcassets/icon-delete.imageset/icon-delete@2x.png'),
    send: () => require('../../ios/mobile/Images.xcassets/icon-send.imageset/icon-send@2x.png'),
    
    // Common UI icons
    'chevron-right': () => require('../../ios/mobile/Images.xcassets/icon-chevron-right.imageset/icon-chevron-right@2x.png'),
    edit: () => require('../../ios/mobile/Images.xcassets/icon-edit.imageset/icon-edit@2x.png'),
    lock: () => require('../../ios/mobile/Images.xcassets/icon-lock.imageset/icon-lock@2x.png'),
    notifications: () => require('../../ios/mobile/Images.xcassets/icon-notifications.imageset/icon-notifications@2x.png'),
    subscriptions: () => require('../../ios/mobile/Images.xcassets/icon-subscriptions.imageset/icon-subscriptions@2x.png'),
    privacy: () => require('../../ios/mobile/Images.xcassets/icon-privacy.imageset/icon-privacy@2x.png'),
    help: () => require('../../ios/mobile/Images.xcassets/icon-help.imageset/icon-help@2x.png'),
    logout: () => require('../../ios/mobile/Images.xcassets/icon-logout.imageset/icon-logout@2x.png'),
    add: () => require('../../ios/mobile/Images.xcassets/icon-add.imageset/icon-add@2x.png'),
    sync: () => require('../../ios/mobile/Images.xcassets/icon-sync.imageset/icon-sync@2x.png'),
    'link-off': () => require('../../ios/mobile/Images.xcassets/icon-link-off.imageset/icon-link-off@2x.png'),
    savings: () => require('../../ios/mobile/Images.xcassets/icon-savings.imageset/icon-savings@2x.png'),
    download: () => require('../../ios/mobile/Images.xcassets/icon-download.imageset/icon-download@2x.png'),
  };

  // Get the image loader function
  const imageLoader = iconMap[name];
  
  if (!imageLoader) {
    console.warn(`Icon "${name}" not found in iconMap`);
    return null;
  }

  let imageSource;
  try {
    imageSource = imageLoader();
  } catch (e) {
    console.warn(`Failed to load icon "${name}":`, e);
    return null;
  }

  return (
    <Image
      source={imageSource}
      style={[
        {
          width: size,
          height: size,
          tintColor: tintColor,
        },
        style,
      ]}
      resizeMode="contain"
    />
  );
}

