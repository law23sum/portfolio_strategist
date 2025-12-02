import {Platform} from 'react-native';

// For iOS Simulator: Use localhost (simulator shares host network stack)
// For physical iOS device: Use your Mac's IP address
// To find your IP: ifconfig | grep "inet " | grep -v 127.0.0.1
const IOS_SIMULATOR_HOST = 'http://localhost:8000'; // iOS Simulator can use localhost
const IOS_PHYSICAL_DEVICE_HOST = 'http://192.168.254.64:8000'; // Use Mac's IP for physical device
const ANDROID_EMULATOR_HOST = 'http://10.0.2.2:8000';
const DEFAULT_LAN_HOST = 'http://192.168.254.64:8000'; // replace with your Mac/PC IP when using a physical device

const runtimeOverride =
  (typeof globalThis !== 'undefined' && (globalThis as any).__API_URL__) ||
  (typeof process !== 'undefined' && process.env.API_BASE_URL);

const resolvedDevHost = runtimeOverride
  ? runtimeOverride
  : Platform.select({
      ios: IOS_SIMULATOR_HOST,
      android: ANDROID_EMULATOR_HOST,
      default: DEFAULT_LAN_HOST,
    }) ?? IOS_SIMULATOR_HOST;

const sanitizeBaseUrl = (url: string): string => url.replace(/[~\/\s]+$/, '').trim();

export const API_BASE_URL = sanitizeBaseUrl(
  __DEV__ ? resolvedDevHost : 'https://your-production-url.com',
);

export const setApiBaseUrl = (url: string) => {
  if (typeof url === 'string' && url.trim().length > 0) {
    (globalThis as any).__API_URL__ = sanitizeBaseUrl(url);
  }
};

if (__DEV__) {
  console.log('[API Config] Platform:', Platform.OS);
  console.log('[API Config] Base URL:', API_BASE_URL);
  console.log(
    '[API Config] Override via process.env.API_BASE_URL or calling setApiBaseUrl("http://YOUR_IP:8000")',
  );
}

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login/',
    REGISTER: '/api/auth/register/',
    LOGOUT: '/api/auth/logout/',
    VERIFY_OTP: '/api/auth/verify-otp/',
    TOKEN_REFRESH: '/api/auth/token/refresh/',
    TOKEN_VERIFY: '/api/auth/token/verify/',
    USER_DETAILS: '/api/auth/user/',
    PASSWORD_CHANGE: '/api/auth/password/change/',
    PLAID_LINK_TOKEN: '/api/auth/plaid/link-token/',
    PLAID_EXCHANGE: '/api/auth/plaid/exchange/',
  },
  DASHBOARD: {
    STATS: '/dashboard/api/signups/',
    SUMMARY: '/api/dashboard/summary/',
  },
  RECORDS: {
    INSIGHTS: '/records/insights/',
    EXPLORER: '/records/explorer/',
    UPLOAD: '/records/upload/',
    DOCUMENTS: '/records/documents/partial/',
    DELETE_DOCUMENT: (id: number) => `/records/delete/${id}/`,
    DOCUMENT_DETAILS: (id: number) => `/records/details/${id}/`,
    LINK_ACCOUNT: '/records/link-account/',
    LINKED_ACCOUNTS: '/records/linked-accounts/',
    ACCOUNT_DETAIL: (id: number) => `/records/account/${id}/`,
    CREATE_LINK_TOKEN: '/records/api/create-link-token/',
    EXCHANGE_TOKEN: '/records/api/exchange-token/',
    SYNC_ACCOUNT: (id: number) => `/records/api/sync-account/${id}/`,
    DISCONNECT_ACCOUNT: (id: number) => `/records/api/disconnect-account/${id}/`,
  },
  STOCK_ANALYSIS: {
    HOME: '/stock-analysis/',
    ANALYZE: '/stock-analysis/api/analyze/', // API endpoint (CSRF exempt)
    RESULTS: (id: number) => `/stock-analysis/results/${id}/`,
    DOWNLOAD_PDF: (id: number) => `/stock-analysis/download-pdf/${id}/`,
    LOAN: '/stock-analysis/loan/',
    LOAN_RESULTS: (id: number) => `/stock-analysis/loan/results/${id}/`,
    PLANNER: (analysisPk: number) => `/stock-analysis/planner/${analysisPk}/`,
    INVESTMENT_FORECAST: '/stock-analysis/api/investment-forecast/',
  },
  INVESTMENT_SAVINGS: {
    SUMMARY: '/investment-savings/',
    STOCKS_ASSESSMENT: '/investment-savings/stocks-assessment/',
    SAVINGS_ASSESSMENT: '/investment-savings/savings-assessment/',
    CD_ASSESSMENT: '/investment-savings/cd-assessment/',
    BOND_ASSESSMENT: '/investment-savings/bond-assessment/',
    SAVE_STOCKS: '/api/investment-savings/save-stocks/',
    SAVE_SAVINGS: '/api/investment-savings/save-savings/',
    SAVE_CD: '/api/investment-savings/save-cd/',
    SAVE_BOND: '/api/investment-savings/save-bond/',
  },
  BUDGET_PLANNER: '/budget-planner/',
  SUBSCRIPTIONS: {
    PLANS: '/subscriptions/plans/',
    CURRENT: '/subscriptions/current/',
    CANCEL: '/subscriptions/cancel/',
  },
  USERS: {
    PROFILE: '/users/profile/',
    UPLOAD_IMAGE: '/users/profile/upload-image/',
  },
  SOLUTIONS: '/solutions/',
  CATEGORIES: '/categories/',
  CHAT: {
    HOME: '/chat/',
    START: '/chat/chat/start/',
    SINGLE: (id: number) => `/chat/chat/${id}/`,
    NEW_MESSAGE: (id: number) => `/chat/chat/${id}/new_message/`,
    GET_RESPONSE: (id: number, taskId: string) => `/chat/chat/${id}/get_response/${taskId}/`,
  },
};
