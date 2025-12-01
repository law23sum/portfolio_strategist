// API Configuration
export const API_BASE_URL = __DEV__ 
  ? 'http://10.23.49.129:8000' // Development URL - update with your local IP
  : 'https://your-production-url.com'; // Production URL

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
  },
  DASHBOARD: {
    STATS: '/dashboard/api/signups/',
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
    ANALYZE: '/stock-analysis/analyze/',
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

