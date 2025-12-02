# Stock Analysis Pages - Quick Reference Guide

Quick reference for developers working on stock analysis pages.

## Navigation URLs

```python
# Base pattern
/investment-savings/stocks-assessment/<symbol>/<page>/

# Pages
detailed-reports/          # Stock overview, ratios, AI analysis
analysis-predictions/      # Forecast charts and error analysis
market-overview/           # Stock vs benchmark comparison
risk-dashboard/            # Risk metrics and insights
decision-support/          # Pros/cons and recommendations
investment-planner-alerts/ # Multi-phase planning and alerts
financial-definitions/     # Financial term definitions (no symbol)
```

## View Functions (apps/web/views.py)

| Function | Symbol Required | Key Parameters |
|----------|----------------|----------------|
| `stocks_detailed_reports` | ✅ | `period`, `interval` |
| `stocks_analysis_predictions` | ✅ | `period`, `interval`, `model`, `market`, `vix`, `tnx` |
| `stocks_market_overview` | ✅ | `market` |
| `stocks_risk_dashboard` | ✅ | `period`, `market` |
| `stocks_decision_support` | ✅ | None |
| `stocks_investment_planner_alerts` | ✅ | None |
| `financial_definitions` | ❌ | `return_url` (optional) |

## JavaScript Navigation Functions

Located in `templates/web/stocks_assessment.html`:

```javascript
navigateToDetailedReports()
navigateToAnalysisPredictions()
navigateToMarketOverview()
navigateToRiskDashboard()
navigateToDecisionSupport()
navigateToInvestmentPlannerAlerts()
```

## Service Usage Pattern

All views follow this pattern:

```python
from apps.stock_analysis.services import StockAnalysisService

service = StockAnalysisService()
stock_data = service.stock_app.fetch_stock_data(symbol.upper())
history_df = service.stock_app.fetch_stock_history(symbol.upper(), period, interval)
ratios_table = service.stock_app.analyze_stock(stock_data)
```

## Common Context Variables

All views include:
- `active_tab`: `"investment_savings"`
- `page_title`: Translated page title
- `symbol`: Uppercase stock symbol

## Template Locations

All templates in `templates/web/`:
- `stocks_detailed_reports.html`
- `stocks_analysis_predictions.html`
- `stocks_market_overview.html`
- `stocks_risk_dashboard.html`
- `stocks_decision_support.html`
- `stocks_investment_planner_alerts.html`
- `financial_definitions.html`

## Data Structures

### Stock Data
```python
{
    'symbol': str,
    'current_price': float,
    'market_cap': float,
    # ... other stock metrics
}
```

### Ratios Table
```python
# DataFrame with columns: Ratio Name, Value, etc.
# Converted to list of dicts for templates
ratios_dict = ratios_table.to_dict('records')
```

### Risk Metrics
```python
{
    'annual_return': float,
    'annual_volatility': float,
    'sharpe_ratio': float,
    'sortino_ratio': float,
    'max_drawdown': float,
    'value_at_risk_95': float,
    'beta': float,
}
```

### Decision Support
```python
{
    'pros': [str, ...],
    'cons': [str, ...],
    'stance': 'Bullish' | 'Bearish' | 'Neutral',
    'summary': str,
}
```

## URL Parameter Patterns

### Detailed Reports
```
?period=1y&interval=1d&return_url=<encoded>
```

### Analysis/Predictions
```
?period=1y&interval=1d&model=<encoded>&market=^GSPC&vix=^VIX&tnx=^TNX&return_url=<encoded>
```

### Market Overview
```
?market=^GSPC&return_url=<encoded>
```

### Risk Dashboard
```
?period=1y&market=^GSPC&return_url=<encoded>
```

### Decision Support
```
?return_url=<encoded>
```

### Investment Planner Alerts
```
?return_url=<encoded>
```

## Button Enable/Disable Logic

Buttons are enabled when:
1. Stock symbol is entered (`stockSymbol` input has value)
2. Current price is populated (`currentPrice` input has value > 0)

Function: `enableButtons()` in `stocks_assessment.html`

## Common Utilities

### Risk Calculations
```python
from apps.stock_analysis.lib.analysis_utils import (
    calculate_risk_statistics,
    generate_risk_insights,
)
```

### Decision Support
```python
from apps.stock_analysis.lib.analysis_utils import build_decision_support
```

### Definitions
```python
from apps.stock_analysis.lib.stock_definitions import RATIO_DEFINITIONS
```

## Financia Reference Mapping

| Web Page | Financia Class | File Location |
|----------|---------------|---------------|
| Detailed Reports | `DetailedPage` | `reference/financia/stock_analyzer/stock_gui.py:2469` |
| Analysis/Predictions | `AnalysisPredictionsPage` | `reference/financia/stock_analyzer/stock_gui.py:767` |
| Market Overview | `MarketOverviewPage` | `reference/financia/stock_analyzer/stock_gui.py:1875` |
| Risk Dashboard | `RiskAnalysisPage` | `reference/financia/stock_analyzer/stock_gui.py:2028` |
| Decision Support | `DecisionSupportPage` | `reference/financia/stock_analyzer/stock_gui.py:2271` |
| Investment Planner | `InvestmentPlannerPage` | `reference/financia/stock_analyzer/stock_gui.py:1464` |
| Financial Definitions | `DefinitionsPage` | `reference/financia/stock_analyzer/stock_gui.py:726` |

## Common Issues & Solutions

### Issue: Buttons remain disabled
**Solution**: Ensure `populateInformation()` is called and `currentPrice` is set

### Issue: Missing data on detail pages
**Solution**: Verify `StockAnalysisService` is properly initialized and API keys are set

### Issue: Charts not rendering
**Solution**: Check that Chart.js is loaded and data is properly serialized to JSON

### Issue: Return URL not working
**Solution**: Ensure `return_url` parameter is URL-encoded and passed correctly

## Related Documentation

- `stock_analysis_button_mappings.md` - Detailed button/link mappings
- `stock_analysis_implementation_status.md` - Implementation status and comparison

