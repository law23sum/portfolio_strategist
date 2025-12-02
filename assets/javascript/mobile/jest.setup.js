import 'react-native-gesture-handler/jestSetup';

jest.mock('react-native-gesture-handler', () => {
  const React = require('react');
  return {
    GestureHandlerRootView: ({children}) => React.createElement(React.Fragment, null, children),
  };
});

jest.mock('react-native-reanimated', () => require('react-native-reanimated/mock'));

jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  return {
    SafeAreaProvider: ({children}) => React.createElement(React.Fragment, null, children),
    SafeAreaView: ({children}) => React.createElement(React.Fragment, null, children),
    useSafeAreaInsets: () => ({top: 0, bottom: 0, left: 0, right: 0}),
  };
});

jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    configure: jest.fn(),
    hasPlayServices: jest.fn().mockResolvedValue(true),
    signIn: jest.fn().mockResolvedValue({}),
    signOut: jest.fn().mockResolvedValue(undefined),
  },
}));

jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);

jest.mock(
  'react-native-webview',
  () => ({
    WebView: ({children}) => children ?? null,
  }),
  {virtual: true},
);

jest.mock('react-native-vector-icons/MaterialIcons', () => 'Icon');

jest.mock('react-native-image-picker', () => ({
  launchCamera: jest.fn(),
  launchImageLibrary: jest.fn(),
  MediaType: {photo: 'photo', video: 'video'},
}));

jest.mock('react-native-document-picker', () => ({
  __esModule: true,
  default: {
    pick: jest.fn(),
    types: {},
  },
}));

jest.mock('react-native-svg', () => {
  const React = require('react');
  const mock = (name) => {
    const Component = (props) => React.createElement(name, props, props.children);
    Component.displayName = name;
    return Component;
  };
  return {
    __esModule: true,
    default: mock('Svg'),
    Circle: mock('Circle'),
    ClipPath: mock('ClipPath'),
    Defs: mock('Defs'),
    Ellipse: mock('Ellipse'),
    G: mock('G'),
    Line: mock('Line'),
    LinearGradient: mock('LinearGradient'),
    Path: mock('Path'),
    Polygon: mock('Polygon'),
    Polyline: mock('Polyline'),
    RadialGradient: mock('RadialGradient'),
    Rect: mock('Rect'),
    Stop: mock('Stop'),
    Symbol: mock('Symbol'),
    Text: mock('Text'),
    TSpan: mock('TSpan'),
    Use: mock('Use'),
  };
});
