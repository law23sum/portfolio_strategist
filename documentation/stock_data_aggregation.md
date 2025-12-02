# Stock Data Aggregation System

## Overview

The Stock Data Aggregation System fetches stock data from multiple sources, removes redundant data, and intelligently merges it for use across different web pages.

## Architecture

### Components

1. **StockDataAggregator** (`apps/stock_analysis/lib/data_aggregator.py`)
   - Main aggregation service
   - Fetches from multiple sources
   - Deduplicates and merges data
   - Provides page-specific data methods

2. **Data Sources**
   - **Yahoo Finance** (Priority: 1) - Web scraping via headless Chrome
   - **Cached Celery/DB** (Priority: 1b) - StockWatchSnapshot cached data (checked after web scraping fails)
   - **Polygon.io** (Priority: 2) - API-based financial data
   - **Alpha Vantage** (Priority: 3) - API-based financial data

### Source Priority

Data fetching follows this priority order:
1. **Yahoo Finance Web Scraping** - Headless Chrome scraping (tried first)
2. **Cached Celery/DB Data** - StockWatchSnapshot from database (checked if web scraping fails)
3. **Polygon.io API** - Reliable API data (fallback)
4. **Alpha Vantage API** - Fallback API data
5. **Offline Cache** - Local cached files (last resort)

When merging data from multiple sources, higher priority sources take precedence:
- Yahoo Finance (Priority 3) - Most comprehensive, includes scraping
- Polygon.io (Priority 2) - Reliable API data
- Alpha Vantage (Priority 1) - Fallback API data

## Data Flow

```
User Request
    ↓
StockDataAggregator.aggregate_all()
    ↓
Fetch from sources in priority order:
    1. Yahoo Finance Web Scraping (headless Chrome)
       └─ If fails → Check Cached Celery/DB (StockWatchSnapshot)
    2. Polygon.io API (if API key available and web scraping failed)
    3. Alpha Vantage API (if API key available and previous sources failed)
    ↓
Merge and Deduplicate:
    ├─ Fundamentals (by field, prefer higher priority)
    ├─ News (by URL, remove duplicates)
    └─ Statistics (merge all available)
    ↓
Cache result (5 minutes)
    ↓
Return aggregated data
```

## Page-Specific Data Methods

Each page has a dedicated method that returns optimized data:

### 1. Detailed Reports
```python
aggregator.get_data_for_detailed_reports(symbol)
```
Returns:
- `stock_data`: Aggregated fundamentals
- `statistics`: Merged statistics
- `yahoo_profile`: Company profile from Yahoo
- `news`: Deduplicated news articles

### 2. Market Overview
```python
aggregator.get_data_for_market_overview(symbol, benchmark='^GSPC')
```
Returns:
- `stock_history`: Historical price data
- `benchmark_history`: Benchmark historical data
- `fundamentals`: Aggregated fundamentals
- `statistics`: Merged statistics

### 3. Risk Dashboard
```python
aggregator.get_data_for_risk_dashboard(symbol, benchmark='^GSPC')
```
Returns:
- `stock_history`: Historical price data for risk calculations
- `benchmark`: Benchmark symbol
- `fundamentals`: Aggregated fundamentals
- `statistics`: Merged statistics
- `yahoo_statistics`: Additional Yahoo Finance statistics

### 4. Decision Support
```python
aggregator.get_data_for_decision_support(symbol)
```
Returns:
- `fundamentals`: Aggregated fundamentals
- `statistics`: Merged statistics
- `yahoo_profile`: Company profile
- `yahoo_holders`: Institutional/mutual fund holders
- `news`: Deduplicated news
- `stock_history`: Historical data

### 5. Analysis/Predictions
```python
aggregator.get_data_for_analysis_predictions(symbol)
```
Returns:
- `fundamentals`: Aggregated fundamentals
- `statistics`: Merged statistics
- `stock_history`: Historical data for forecasting
- `yahoo_chart_details`: Chart type information

### 6. Investment Planner
```python
aggregator.get_data_for_investment_planner(symbol)
```
Returns:
- `fundamentals`: Aggregated fundamentals
- `statistics`: Merged statistics
- `stock_history`: Extended historical data (2 years)
- `yahoo_options`: Options chain data
- `yahoo_holders`: Holders information

## Deduplication Logic

### Fundamentals
- Fields are merged by key
- Higher priority sources overwrite lower priority values
- `None` values are skipped
- Numeric strings are converted to floats

### News
- Deduplicated by URL
- All unique articles are preserved
- Source information is maintained

### Statistics
- All statistics are merged
- Yahoo Finance statistics are most comprehensive
- Additional statistics from other sources supplement

## Caching

- Results are cached per symbol for 5 minutes
- Cache key: `symbol.upper()`
- Cache includes timestamp for expiration checking

## Error Handling

- If aggregator fails, views fall back to original single-source methods
- Each source failure is logged but doesn't stop aggregation
- Missing sources are gracefully handled

## Usage in Views

### Example: Detailed Reports View

```python
from apps.stock_analysis.lib.data_aggregator import StockDataAggregator

service = StockAnalysisService()
aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)

try:
    page_data = aggregator.get_data_for_detailed_reports(symbol.upper())
    stock_data = page_data.get('stock_data', {})
    # ... use aggregated data
except Exception as e:
    # Fallback to original method
    stock_data = service.stock_app.fetch_stock_data(symbol.upper())
```

## API Endpoint

The `stock_details_api` endpoint uses the aggregator:

```python
aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
comprehensive_data = aggregator.get_comprehensive_data(symbol)
```

Returns all aggregated data including:
- Fundamentals (merged from all sources)
- Statistics (merged)
- News (deduplicated)
- Yahoo Finance comprehensive data
- Stock history
- Sources used

## Benefits

1. **Comprehensive Data**: Combines data from multiple sources for complete coverage
2. **Redundancy Removal**: Eliminates duplicate information
3. **Source Priority**: Uses best available data when conflicts exist
4. **Page Optimization**: Each page gets exactly the data it needs
5. **Resilience**: Falls back gracefully if sources fail
6. **Performance**: Caching reduces redundant API calls

## Future Enhancements

- Add more data sources (e.g., IEX Cloud, Finnhub)
- Implement source reliability scoring
- Add data freshness tracking
- Create data quality metrics
- Implement parallel fetching for faster aggregation

