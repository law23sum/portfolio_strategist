// Navigation type definitions
export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Dashboard: undefined;
  Records: undefined;
  StockAnalysis: undefined;
  Solutions: undefined;
  Profile: undefined;
};

export type RecordsStackParamList = {
  RecordsMain: undefined;
  Insights: undefined;
  Explorer: undefined;
  Upload: undefined;
  LinkedAccounts: undefined;
};

export type StockStackParamList = {
  StockMain: undefined;
  Analyze: undefined;
  Results: { analysisId?: number; data?: any };
  Loan: undefined;
};



