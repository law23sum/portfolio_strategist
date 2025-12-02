# Stock Analysis Templates - Financia Reference Comparison

This document compares the web templates with the financia reference implementation to ensure alignment.

## Template Structure Overview

All templates follow a consistent pattern:
1. Extend `web/app/app_base.html`
2. Include Chart.js for visualizations (where needed)
3. Provide "Back" navigation with `return_url` support
4. Display page title and symbol
5. Render data sections conditionally

---

## 1. Detailed Reports Template

### Financia Reference (`DetailedPage`)
- **Layout**: Two-column (left: tables, right: AI analysis)
- **Left Column**:
  - Stock Overview table (key-value pairs)
  - Stock Ratios table
  - Save PDF button
  - Home Page button
- **Right Column**:
  - AI Analysis text display

### Web Template (`stocks_detailed_reports.html`)
- **Layout**: Single column, stacked sections
- **Sections**:
  - ✅ Back navigation button
  - ✅ Stock Fundamentals table (matches Stock Overview)
  - ✅ Financial Ratios table
  - ✅ News section (matches AI Analysis)
- **Missing**:
  - ⚠️ PDF export button (not implemented in view)

### Alignment Status: ✅ Good (PDF export pending)

---

## 2. Analysis/Predictions Template

### Financia Reference (`AnalysisPredictionsPage`)
- **Layout**: Vertical stack
- **Top**: Two charts side-by-side
  - Historical vs Forecast Prices (left)
  - Prediction Error Chart (right)
- **Bottom**: Two tables side-by-side
  - Error Table (left): Date, Actual, Forecasted, Error
  - Forecast Table (right): Date, Predicted Price

### Web Template (`stocks_analysis_predictions.html`)
- **Layout**: Vertical stack
- **Sections**:
  - ✅ Back navigation button
  - ✅ Analysis Configuration box
  - ✅ Forecast Chart (Historical vs Forecasted)
  - ✅ Forecast Data table
- **Missing**:
  - ⚠️ Error Chart (separate chart for prediction errors)
  - ⚠️ Error Table (showing actual vs forecasted with errors)

### Alignment Status: ⚠️ Partial (Error analysis missing)

**Recommendation**: Add error chart and error table sections

---

## 3. Market Overview Template

### Financia Reference (`MarketOverviewPage`)
- **Layout**: Vertical stack
- **Components**:
  - Price comparison plot (stock vs benchmark)
  - Relative performance plot (indexed to 100)
  - Metrics table:
    - Latest Close
    - Period Performance
    - Benchmark Performance
    - Relative vs Benchmark
    - Last Daily Return
- **Home Page button**

### Web Template (`stocks_market_overview.html`)
- **Layout**: Vertical stack
- **Sections**:
  - ✅ Back navigation button
  - ✅ Performance Comparison chart
- **Missing**:
  - ⚠️ Metrics table (Latest Close, Performance %, etc.)
  - ⚠️ Separate relative performance visualization

### Alignment Status: ⚠️ Partial (Metrics table missing)

**Recommendation**: Add metrics table showing key comparison statistics

---

## 4. Risk Dashboard Template

### Financia Reference (`RiskAnalysisPage`)
- **Layout**: Vertical stack
- **Components**:
  - Title: "Risk & Reward Insights"
  - Summary label
  - Key Risk Metrics group:
    - Annual Return (%)
    - Annual Volatility (%)
    - Sharpe Ratio
    - Sortino Ratio
    - Maximum Drawdown (%)
    - Value at Risk (95%) (%)
    - Beta (vs benchmark)
  - Risk Insights (text list)
  - Charts for price action, volatility, drawdown
- **Home Page button**

### Web Template (`stocks_risk_dashboard.html`)
- **Layout**: Vertical stack
- **Sections**:
  - ✅ Back navigation button
  - ✅ Risk Metrics display (all key metrics)
  - ✅ Risk Insights section
- **Missing**:
  - ⚠️ Charts for price action, volatility, drawdown visualizations

### Alignment Status: ✅ Good (Charts optional enhancement)

---

## 5. Decision Support Template

### Financia Reference (`DecisionSupportPage`)
- **Layout**: Vertical stack
- **Components**:
  - Title: "Decision Support Matrix"
  - Summary label
  - Pros Group (list of positive factors)
  - Cons Group (list of risk flags)
  - Overall Stance (Bullish/Bearish/Neutral)
  - Additional context/disclaimers
- **Home Page button**

### Web Template (`stocks_decision_support.html`)
- **Layout**: Vertical stack
- **Sections**:
  - ✅ Back navigation button
  - ✅ Investment Recommendation card
  - ✅ Key Factors list (matches Pros)
  - ✅ Risks to Consider list (matches Cons)
- **Structure**: Uses recommendation card with color coding

### Alignment Status: ✅ Good (Structure matches, styling differs)

---

## 6. Investment Planner Alerts Template

### Financia Reference (`InvestmentPlannerPage`)
- **Layout**: Vertical stack
- **Components**:
  - Title: "Investment Planner & Alerts"
  - Status label
  - Investment Inputs group:
    - Stock Symbol (display)
    - Latest Close (display)
    - Investment Amount ($) input
    - Share Quantity input
    - Biweekly Contribution ($) input
    - Number of phases input
  - Forecast Results Table:
    - Phase number
    - Start date
    - End date
    - Shares accumulated
    - Investment value
  - Alerts Configuration
  - Activity Log
- **Home Page button**

### Web Template (`stocks_investment_planner_alerts.html`)
- **Status**: Template exists, needs verification
- **Expected**: Should match financia structure

### Alignment Status: ⚠️ Needs Review

**Recommendation**: Verify template matches financia structure

---

## 7. Financial Definitions Template

### Financia Reference (`DefinitionsPage`)
- **Layout**: Vertical stack
- **Components**:
  - Title: "Financial Definitions"
  - Definitions table (Term, Definition, Formula)
- **Home Page button**

### Web Template (`financial_definitions.html`)
- **Layout**: Vertical stack
- **Sections**:
  - ✅ Back navigation button
  - ✅ Definition cards (Term, Definition, Formula)
- **Structure**: Uses card-based layout instead of table

### Alignment Status: ✅ Good (Content matches, presentation differs)

---

## Common Template Patterns

### Navigation
All templates include:
```django
{% if request.GET.return_url %}
    <a href="{{ request.GET.return_url }}" class="button">Back</a>
{% else %}
    <a href="{% url 'web:stocks_assessment' %}" class="button">Back to Stocks Assessment</a>
{% endif %}
```

### Page Headers
All templates include:
- Page title with symbol
- Subtitle describing the page
- Consistent styling

### Data Display
- Conditional rendering: `{% if data %}...{% endif %}`
- Table formatting using Bulma CSS
- Chart.js integration for visualizations

---

## Recommendations for Template Improvements

### High Priority
1. **Analysis/Predictions**: Add error chart and error table
2. **Market Overview**: Add metrics table with comparison statistics
3. **Investment Planner**: Verify and complete template structure

### Medium Priority
1. **Detailed Reports**: Add PDF export button (when backend is ready)
2. **Risk Dashboard**: Add visualization charts (price action, volatility, drawdown)

### Low Priority
1. **All Templates**: Consider adding loading states
2. **All Templates**: Add error handling UI for missing data
3. **All Templates**: Add print-friendly CSS

---

## Template Consistency Checklist

- [x] All templates extend `app_base.html`
- [x] All templates include back navigation
- [x] All templates display symbol in title
- [x] All templates handle missing data gracefully
- [x] All templates use consistent styling (Bulma CSS)
- [ ] All templates include Chart.js where needed (verify)
- [ ] All templates match financia reference structure (partial)

---

## Notes

- Web templates use HTML/CSS/JavaScript instead of PyQt5 widgets
- Chart rendering uses Chart.js instead of PyQtGraph
- Layout adapts to web (single column) vs desktop (multi-column) differences
- Overall structure and content align well with financia reference
- Minor enhancements needed for full feature parity

