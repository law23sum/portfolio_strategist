# Stock Analysis & Investment Inputs - Button/Link Web Page Details

This document maps each button and link on the "PLAN BUILDER - Stock Analysis & Investment Inputs" page to its corresponding web page details, based on the financia reference code.

## Action Buttons (Top Section)

### 1. **Populate Information** (Download Icon)
- **Type**: Action Button (triggers data fetch)
- **Function**: `populateInformation()`
- **Purpose**: Fetches stock data from API for both Detailed Reports and Forecast/Analysis pages
- **Behavior**: 
  - Fetches stock overview data, ratios, and AI assessment for Detailed Reports
  - Fetches historical data for forecasting and analysis
  - Updates form fields with fetched data (current price, etc.)
  - Enables navigation buttons once data is loaded
- **No Navigation**: Stays on current page, populates data

### 2. **Calculate & Save Assessment** (Save Icon)
- **Type**: Action Button
- **Function**: `calculateAndSave()`
- **Purpose**: Saves the current stock assessment configuration
- **Behavior**: 
  - Calculates assessment based on current inputs
  - Saves to database via API endpoint
  - Shows success/error notification
- **No Navigation**: Stays on current page after saving

### 3. **Preview Forecast** (Line Chart Icon)
- **Type**: Action Button
- **Function**: `calculateForecast()`
- **Purpose**: Generates and displays forecast visualization on the same page
- **Behavior**: 
  - Calculates forecast using selected model (GBM, Mean Reversion, etc.)
  - Displays forecast chart with confidence bands (±1σ, ±2σ, ±3σ)
  - Shows forecast summary cards (Current Price, Total Cost, Shares Held, Model)
  - Displays detailed forecast table
- **No Navigation**: Shows forecast section on current page

### 4. **Reset Stock** (Refresh Icon)
- **Type**: Action Button
- **Function**: `resetStock()`
- **Purpose**: Resets all form fields to default values
- **Behavior**: 
  - Clears stock symbol
  - Resets period to "1y", interval to "1d"
  - Resets model to "Geometric Brownian Motion External Macroeconomic Factors"
  - Resets market tickers to defaults (^GSPC, ^VIX, ^TNX)
  - Clears investment inputs
- **No Navigation**: Stays on current page

---

## Navigation Buttons (Bottom Section)

### 5. **Stock Detailed Reports** (Document Icon)
- **URL Pattern**: `/investment-savings/stocks-assessment/<symbol>/detailed-reports/`
- **URL Parameters**: 
  - `period`: Stock period (e.g., "1y")
  - `interval`: Stock interval (e.g., "1d")
  - `return_url`: Encoded return URL
- **Django View**: `stocks_detailed_reports`
- **Template**: `templates/web/stocks_detailed_reports.html`
- **Based on Financia Class**: `DetailedPage` (lines 2469-2627)
- **Page Content**:
  - **Left Column**:
    - Stock Overview table (key-value pairs of stock metrics)
    - Stock Ratios table (financial ratios in tabular format)
    - "Save Report as PDF" button
    - "Home Page" navigation button
  - **Right Column**:
    - AI Analysis: Stock Summary Assessment (text display of AI-generated analysis)
- **Requirements**: Stock symbol and price must be populated before navigation
- **Data Sources**: Stock overview data, ratios table, AI assessment

### 6. **Stock Analysis/Predictions** (Line Chart Icon)
- **URL Pattern**: `/investment-savings/stocks-assessment/<symbol>/analysis-predictions/`
- **URL Parameters**: 
  - `period`: Stock period
  - `interval`: Stock interval
  - `model`: Forecasting model (URL encoded)
  - `market`: Market ticker (e.g., "^GSPC")
  - `vix`: Volatility ticker (e.g., "^VIX")
  - `tnx`: Interest rate ticker (e.g., "^TNX")
  - `return_url`: Encoded return URL
- **Django View**: `stocks_analysis_predictions`
- **Template**: `templates/web/stocks_analysis_predictions.html`
- **Based on Financia Class**: `AnalysisPredictionsPage` (lines 767-1017)
- **Page Content**:
  - **Top Section**: Two charts side by side
    - Left: Historical vs. Forecast Prices plot (with legends)
    - Right: Prediction Error Chart
  - **Bottom Section**: Two tables side by side
    - Left: Error Table (Date, Actual Price, Forecasted Price, Error)
    - Right: Forecast Table (Date, Predicted Price for future dates)
  - **Navigation**: "Home Page" button
- **Requirements**: Stock symbol, price, period, interval, and model must be set
- **Data Sources**: Historical stock data, forecast calculations, error metrics

### 7. **Market Overview** (Globe Icon)
- **URL Pattern**: `/investment-savings/stocks-assessment/<symbol>/market-overview/`
- **URL Parameters**: 
  - `market`: Market ticker (e.g., "^GSPC")
  - `return_url`: Encoded return URL
- **Django View**: `stocks_market_overview`
- **Template**: `templates/web/stocks_market_overview.html`
- **Based on Financia Class**: `MarketOverviewPage` (lines 1875-2026)
- **Page Content**:
  - **Title**: "Market Overview & Benchmarks"
  - **Status Label**: Shows comparison status
  - **Price Plot**: Side-by-side comparison of stock price vs. benchmark price
  - **Relative Performance Plot**: Indexed performance comparison (both starting at 100)
  - **Metrics Table**: Key metrics including:
    - Latest Close
    - Period Performance (%)
    - Benchmark Performance (%)
    - Relative vs Benchmark (%)
    - Last Daily Return (%)
  - **Navigation**: "Home Page" button
- **Requirements**: Stock symbol, price, and market ticker must be set
- **Data Sources**: Historical stock data, benchmark historical data

### 8. **Risk Dashboard** (Shield Icon)
- **URL Pattern**: `/investment-savings/stocks-assessment/<symbol>/risk-dashboard/`
- **URL Parameters**: 
  - `period`: Stock period
  - `market`: Market ticker
  - `return_url`: Encoded return URL
- **Django View**: `stocks_risk_dashboard`
- **Template**: `templates/web/stocks_risk_dashboard.html`
- **Based on Financia Class**: `RiskAnalysisPage` (lines 2028-2269)
- **Page Content**:
  - **Title**: "Risk & Reward Insights"
  - **Summary Label**: Risk profile description relative to benchmark
  - **Key Risk Metrics Group**:
    - Annual Return (%)
    - Annual Volatility (%)
    - Sharpe Ratio
    - Sortino Ratio
    - Maximum Drawdown (%)
    - Value at Risk (95%) (%)
    - Beta (vs. benchmark)
  - **Risk Insights**: Text-based insights about risk characteristics
  - **Charts**: Price action, volatility, drawdown visualizations
  - **Navigation**: "Home Page" button
- **Requirements**: Stock symbol, price, period, and market ticker must be set
- **Data Sources**: Historical stock data, benchmark data, risk calculations

### 9. **Decision Support** (Lightbulb Icon)
- **URL Pattern**: `/investment-savings/stocks-assessment/<symbol>/decision-support/`
- **URL Parameters**: 
  - `return_url`: Encoded return URL
- **Django View**: `stocks_decision_support`
- **Template**: `templates/web/stocks_decision_support.html`
- **Based on Financia Class**: `DecisionSupportPage` (lines 2271-2467)
- **Page Content**:
  - **Title**: "Decision Support Matrix"
  - **Summary Label**: Decision support description for the stock
  - **Pros Group**: List of positive factors (e.g., strong Sharpe ratio, good returns)
  - **Risk Flags (Cons) Group**: List of risk warnings (e.g., high volatility, VaR concerns)
  - **Overall Stance**: Bullish/Bearish/Neutral recommendation based on pros vs. cons
  - **Additional Context**: Risk disclaimers and investment guidance
  - **Navigation**: "Home Page" button
- **Requirements**: Stock symbol and price must be set
- **Data Sources**: Risk metrics, financial health metrics, fundamentals analysis

### 10. **Investment Planner Alerts** (Bell Icon)
- **URL Pattern**: `/investment-savings/stocks-assessment/<symbol>/investment-planner-alerts/`
- **URL Parameters**: 
  - `return_url`: Encoded return URL
- **Django View**: `stocks_investment_planner_alerts`
- **Template**: `templates/web/stocks_investment_planner_alerts.html`
- **Based on Financia Class**: `InvestmentPlannerPage` (lines 1464-1873)
- **Page Content**:
  - **Title**: "Investment Planner & Alerts"
  - **Status Label**: Planning status and instructions
  - **Investment Inputs Group**:
    - Stock Symbol (display only)
    - Latest Close (display only)
    - Investment Amount ($) input
    - Share Quantity input
    - Biweekly Contribution ($) input
    - Number of phases input
  - **Forecast Results Table**: Multi-phase forecast showing:
    - Phase number
    - Start date
    - End date
    - Shares accumulated
    - Investment value
  - **Alerts Configuration**: Notification settings for price targets
  - **Log Display**: Activity log for planning operations
  - **Navigation**: "Home Page" button
- **Requirements**: Stock symbol, price, and historical data must be available
- **Data Sources**: Historical stock data, forecast calculations, investment inputs

### 11. **Financial Definitions** (Book Icon)
- **URL Pattern**: `/investment-savings/financial-definitions/`
- **URL Parameters**: 
  - `return_url`: Encoded return URL (optional)
- **Django View**: `financial_definitions`
- **Template**: `templates/web/financial_definitions.html`
- **Based on Financia Class**: `DefinitionsPage` (lines 726-762)
- **Page Content**:
  - **Title**: "Financial Definitions"
  - **Definitions Table**: Table displaying financial terms and their definitions
  - **Table Columns**: Typically includes term name and definition
  - **Data Source**: `RATIO_DEFINITIONS` from financia's `main.py`
  - **Navigation**: "Home Page" button or return to previous page via `return_url`
- **Requirements**: None (always accessible)
- **Data Sources**: Static definitions data

---

## URL Route Mappings

All routes are defined in `apps/web/urls.py`:

```python
# Detailed Reports
path("investment-savings/stocks-assessment/<str:symbol>/detailed-reports/", 
     views.stocks_detailed_reports, name="stocks_detailed_reports")

# Analysis/Predictions
path("investment-savings/stocks-assessment/<str:symbol>/analysis-predictions/", 
     views.stocks_analysis_predictions, name="stocks_analysis_predictions")

# Market Overview
path("investment-savings/stocks-assessment/<str:symbol>/market-overview/", 
     views.stocks_market_overview, name="stocks_market_overview")

# Risk Dashboard
path("investment-savings/stocks-assessment/<str:symbol>/risk-dashboard/", 
     views.stocks_risk_dashboard, name="stocks_risk_dashboard")

# Decision Support
path("investment-savings/stocks-assessment/<str:symbol>/decision-support/", 
     views.stocks_decision_support, name="stocks_decision_support")

# Investment Planner Alerts
path("investment-savings/stocks-assessment/<str:symbol>/investment-planner-alerts/", 
     views.stocks_investment_planner_alerts, name="stocks_investment_planner_alerts")

# Financial Definitions
path("investment-savings/financial-definitions/", 
     views.financial_definitions, name="financial_definitions")
```

---

## Button State Management

### Enabled/Disabled Logic
- All navigation buttons (5-10) are **disabled by default**
- Buttons are **enabled** when:
  - Stock symbol is entered AND
  - Current price is populated (via "Populate Information")
- Function: `enableButtons()` in `stocks_assessment.html`

### Button States
- **Disabled**: `opacity: 0.5`, `pointer-events: none`, `cursor: not-allowed`
- **Enabled**: `opacity: 1`, `pointer-events: auto`, `cursor: pointer`

---

## Data Flow

1. **User enters stock symbol** → Form field updated
2. **User clicks "Populate Information"** → API call fetches:
   - Stock overview data
   - Stock ratios
   - AI assessment
   - Historical price data
   - Current price (populates form)
3. **Form fields populated** → `enableButtons()` called
4. **Navigation buttons enabled** → User can navigate to detail pages
5. **User clicks navigation button** → Redirects to detail page with symbol and parameters
6. **Detail page loads** → Fetches/calculates page-specific data and renders

---

## Notes

- All navigation buttons require stock data to be populated first
- The "Financial Definitions" button is always enabled (no data requirements)
- Each detail page can accept a `return_url` parameter for navigation back
- The financia reference implementation uses PyQt5 widgets, but the web implementation uses Django templates with similar structure and content
- Forecast calculations use the selected model (GBM, Mean Reversion, etc.) with optional macroeconomic factors

