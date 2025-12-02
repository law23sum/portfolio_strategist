/**
 * @format
 */

import React from 'react';
import {act, create} from 'react-test-renderer';
import App from '../App';

jest.mock('../src/navigation/AppNavigator', () => () => null);
jest.useFakeTimers();

test('renders correctly', async () => {
  await act(async () => {
    create(<App />);
    jest.runAllTimers();
    await Promise.resolve();
  });
});
