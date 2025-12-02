// Test if bundle is actually being executed
console.log('=== BUNDLE LOAD TEST ===');
console.log('Timestamp:', new Date().toISOString());
console.log('Platform:', typeof Platform !== 'undefined' ? Platform.OS : 'unknown');
console.log('React Native version:', require('react-native/package.json').version);
console.log('=== END TEST ===');
