/**
 * SIMPLEST POSSIBLE VERSION
 * No gesture-handler, no reanimated - just pure React Native
 * 
 * To use: Temporarily rename index.js to index.js.backup
 * and rename this file to index.js
 */

console.log('[index.js] SIMPLE VERSION - Starting...');

const {AppRegistry} = require('react-native');
const App = require('./App').default;
const appJson = require('./app.json');

console.log('[index.js] App name:', appJson.name);
console.log('[index.js] Registering component...');

AppRegistry.registerComponent(appJson.name, () => {
  console.log('[index.js] Component factory called');
  return App;
});

console.log('[index.js] Registration complete');

