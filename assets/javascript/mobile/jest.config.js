module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['./jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|@react-navigation|@react-native-async-storage|@react-native-google-signin|react-native-gesture-handler|react-native-safe-area-context|react-native-reanimated|react-native-vector-icons|react-native-chart-kit|react-native-webview)/)',
  ],
};
