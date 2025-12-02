// Navigation type definitions
export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Dashboard: undefined;
  Records: undefined;
  InvestmentSavings: undefined;
  Profile: undefined;
};

export type RecordsStackParamList = {
  RecordsMain: undefined;
  Insights: undefined;
  Explorer: undefined;
  Upload: undefined;
  LinkedAccounts: undefined;
  AccountDetail: {accountId: string};
};

export type StockStackParamList = {
  InvestmentSavings: undefined;
  StocksAssessment: undefined;
  AnalysisResults: { analysisId?: number; data?: any };
  SavingsAssessment?: undefined;
  CDAssessment?: undefined;
  BondAssessment?: undefined;
};

export type MainStackParamList = {
  MainTabs: undefined;
  Chat: undefined;
  Solutions: undefined;
  BudgetPlanner: undefined;
};

