import yfinance as yf
import pandas as pd
import numpy as np
import logging


# Configure logging for debugging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')

# List of tickers for multi-stock analysis
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# Create Ticker object for AAPL
stock = yf.Ticker("AAPL")

# 🔹 1. Download historical market data for multiple stocks
try:
    historical_data = yf.download(tickers, start = "2023-01-01", end = "2023-12-31", interval = "1d")
    logging.info("1. Historical Market Data for Multiple Stocks downloaded successfully.")
    print("\n1. Historical Market Data for Multiple Stocks:")
    print(historical_data.head())
except Exception as e:
    logging.error(f"Failed to download historical market data: {e}")

# 🔹 2. Extended historical data (Weekly, 5 Years)
try:
    history = stock.history(period = "5y", interval = "1wk")
    logging.info("2. Extended Historical Data (Weekly, 5 Years) downloaded successfully.")
    print("\n2. Extended Historical Data (Weekly, 5 Years):")
    print(history.head())
except Exception as e:
    logging.error(f"Failed to download extended historical data: {e}")

# 🔹 3. Real-time Stock Info
try:
    info = stock.info
    logging.info("3. Stock Information (Extended Metrics) retrieved successfully.")
    print("\n3. Stock Information (Extended Metrics):")
    print({k: info.get(k, 'N/A') for k in ['sector', 'industry', 'marketCap', 'beta', 'trailingPE', 'forwardPE', 'enterpriseValue']})
except Exception as e:
    logging.error(f"Failed to retrieve stock information: {e}")

# 🔹 4. Fetch real-time stock price dynamically
try:
    logging.info("4. Live Market Price retrieved successfully.")
    print("\n4. Live Market Price:")
    print(f"AAPL Last Price: {stock.fast_info['last_price']}")
except Exception as e:
    logging.error(f"Failed to fetch live market price: {e}")

# 🔹 5. Dividends & Payout Ratios
try:
    logging.info("5. Dividend Yield & History retrieved successfully.")
    print("\n5. Dividend Yield & History:")
    print(f"Dividend Yield: {info.get('dividendYield', 'N/A')}")
    print(f"Payout Ratio: {info.get('payoutRatio', 'N/A')}")
    print(stock.dividends.tail())
except Exception as e:
    logging.error(f"Failed to retrieve dividend data: {e}")

# 🔹 6. Stock Splits
try:
    logging.info("6. Stock Splits retrieved successfully.")
    print("\n6. Stock Splits:")
    print(stock.splits)
except Exception as e:
    logging.error(f"Failed to retrieve stock splits: {e}")

# 🔹 7. Trading Volume Trends (Last 3 Months)
try:
    volume = stock.history(period = "3mo", interval = "1d")["Volume"]
    logging.info("7. Trading Volume Trends retrieved successfully.")
    print("\n7. Trading Volume Trends:")
    print(volume.tail())
except Exception as e:
    logging.error(f"Failed to retrieve trading volume trends: {e}")

# 🔹 8. Earnings Data
try:
    logging.info("8. Earnings Data retrieved successfully.")
    print("\n8. Earnings Data:")
    print(stock.earnings)
except Exception as e:
    logging.error(f"Failed to retrieve earnings data: {e}")

# 🔹 9. Revenue Growth Trend
try:
    revenue_trend = stock.financials.loc["Total Revenue"]
    logging.info("9. Revenue Growth Trend retrieved successfully.")
    print("\n9. Revenue Growth Trend:")
    print(revenue_trend.head())
except Exception as e:
    logging.error(f"Failed to retrieve revenue growth trend: {e}")

# 🔹 10. Balance Sheet (Assets & Liabilities)
try:
    balance_sheet = stock.balance_sheet
    logging.info("10. Balance Sheet retrieved successfully.")
    print("\n10. Balance Sheet:")
    print(balance_sheet.loc[['Total Assets', 'Total Liabilities']].head())
except Exception as e:
    logging.error(f"Failed to retrieve balance sheet: {e}")

# 🔹 11. Options Expiration Dates & Option Chain
try:
    options = stock.options
    if options:
        logging.info("11. Options Expiration Dates retrieved successfully.")
        print("\n11. Options Expiration Dates:")
        print(options)

        option_chain = stock.option_chain(options[0])
        logging.info("12. Option Chain retrieved successfully.")
        print("\n12. Option Chain (Calls):")
        print(option_chain.calls.head())
        print("\n12. Option Chain (Puts):")
        print(option_chain.puts.head())
except Exception as e:
    logging.error(f"Failed to retrieve options data: {e}")

# 🔹 13. Major Shareholders
try:
    logging.info("13. Major Shareholders retrieved successfully.")
    print("\n13. Major Shareholders:")
    print(stock.major_holders)
except Exception as e:
    logging.error(f"Failed to retrieve major shareholders: {e}")

# 🔹 14. Institutional & Mutual Fund Holders
try:
    logging.info("14. Institutional Holders retrieved successfully.")
    print("\n14. Institutional Holders:")
    print(stock.institutional_holders)
    logging.info("14. Mutual Fund Holders retrieved successfully.")
    print("\n14. Mutual Fund Holders:")
    print(stock.mutualfund_holders)
except Exception as e:
    logging.error(f"Failed to retrieve institutional/mutual fund holders: {e}")

# 🔹 15. Latest Stock News
try:
    logging.info("15. Latest Stock News retrieved successfully.")
    print("\n15. Latest Stock News:")
    news = stock.news
    for n in news[:5]:
        print(f"{n['title']} - {n['link']}")
except Exception as e:
    logging.error(f"Failed to retrieve stock news: {e}")

# 🔹 16. Sustainability (ESG Scores)
try:
    logging.info("16. Sustainability Metrics (ESG Scores) retrieved successfully.")
    print("\n16. Sustainability Metrics (ESG Scores):")
    print(stock.sustainability)
except Exception as e:
    logging.error(f"Failed to retrieve sustainability metrics: {e}")

# 🔹 17. Short Interest Data
try:
    logging.info("17. Short Interest retrieved successfully.")
    print("\n17. Short Interest:")
    print(stock.get_shares_short())
except Exception as e:
    logging.error(f"17. Short Interest data unavailable: {e}")

# 🔹 18. Financial Ratios
try:
    logging.info("18. Financial Ratios retrieved successfully.")
    print("\n18. Financial Ratios:")
    print(f"P/E Ratio: {info.get('trailingPE', 'N/A')}")
    print(f"Forward P/E Ratio: {info.get('forwardPE', 'N/A')}")
    print(f"PEG Ratio: {info.get('pegRatio', 'N/A')}")
    print(f"Price-to-Book Ratio: {info.get('priceToBook', 'N/A')}")
except Exception as e:
    logging.error(f"Failed to retrieve financial ratios: {e}")

# 🔹 19. Outstanding Shares & Market Cap
try:
    logging.info("19. Outstanding Shares retrieved successfully.")
    print("\n19. Outstanding Shares:")
    print(info.get("sharesOutstanding", "N/A"))
    logging.info("20. Market Capitalization retrieved successfully.")
    print("\n20. Market Capitalization:")
    print(info.get("marketCap", "N/A"))
except Exception as e:
    logging.error(f"Failed to retrieve outstanding shares/market cap: {e}")

# 🔹 21. Sector Performance Comparison (S&P 500, NASDAQ, Dow Jones)
try:
    sector_tickers = ["^GSPC", "^IXIC", "^DJI"]
    sector_data = yf.download(sector_tickers, period = "1y", interval = "1mo")
    logging.info("21. Sector Performance (S&P 500, NASDAQ, Dow Jones) retrieved successfully.")
    print("\n21. Sector Performance (S&P 500, NASDAQ, Dow Jones):")
    print(sector_data["Close"].tail())
except Exception as e:
    logging.error(f"Failed to retrieve sector performance data: {e}")

# 🔹 22. Stock Correlation Matrix
try:
    closing_prices = yf.download(tickers, period = "6mo")["Close"]
    correlation = closing_prices.corr()
    logging.info("22. Stock Correlation Matrix computed successfully.")
    print("\n22. Stock Correlation Matrix:")
    print(correlation)
except Exception as e:
    logging.error(f"Failed to compute stock correlation matrix: {e}")

# 🔹 23. Stock Trend Detection (Moving Averages)
try:
    sma_50 = stock.history(period = "6mo", interval = "1d")["Close"].rolling(window = 50).mean()
    sma_200 = stock.history(period = "6mo", interval = "1d")["Close"].rolling(window = 200).mean()
    logging.info("23. Simple Moving Averages (50-day vs 200-day) computed successfully.")
    print("\n23. Simple Moving Averages (50-day vs 200-day):")
    print(f"50-Day SMA: {sma_50.tail()}")
    print(f"200-Day SMA: {sma_200.tail()}")
except Exception as e:
    logging.error(f"Failed to compute moving averages: {e}")


# 🔹 24. Relative Strength Index (RSI)
def compute_rsi(data, window = 14):
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window = window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window = window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


try:
    rsi = compute_rsi(stock.history(period = "6mo")["Close"])
    logging.info("24. Relative Strength Index (RSI) computed successfully.")
    print("\n24. Relative Strength Index (RSI):")
    print(rsi.tail())
except Exception as e:
    logging.error(f"Failed to compute RSI: {e}")


# 🔹 25. Bollinger Bands
def compute_bollinger_bands(data, window = 20, num_std = 2):
    rolling_mean = data.rolling(window = window).mean()
    rolling_std = data.rolling(window = window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return rolling_mean, upper_band, lower_band


try:
    bb_middle, bb_upper, bb_lower = compute_bollinger_bands(stock.history(period = "6mo")["Close"])
    logging.info("25. Bollinger Bands computed successfully.")
    print("\n25. Bollinger Bands:")
    print(f"Middle Band: {bb_middle.tail()}")
    print(f"Upper Band: {bb_upper.tail()}")
    print(f"Lower Band: {bb_lower.tail()}")
except Exception as e:
    logging.error(f"Failed to compute Bollinger Bands: {e}")


# 🔹 26. MACD (Moving Average Convergence Divergence)
def compute_macd(data, short_window = 12, long_window = 26, signal_window = 9):
    short_ema = data.ewm(span = short_window, adjust = False).mean()
    long_ema = data.ewm(span = long_window, adjust = False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span = signal_window, adjust = False).mean()
    return macd, signal


try:
    macd, signal = compute_macd(stock.history(period = "6mo")["Close"])
    logging.info("26. MACD computed successfully.")
    print("\n26. MACD:")
    print(f"MACD: {macd.tail()}")
    print(f"Signal: {signal.tail()}")
except Exception as e:
    logging.error(f"Failed to compute MACD: {e}")

# 🔹 27. Beta Calculation (Volatility)
try:
    beta = info.get('beta', 'N/A')
    logging.info("27. Beta (Volatility) retrieved successfully.")
    print("\n27. Beta (Volatility):")
    print(f"Beta: {beta}")
except Exception as e:
    logging.error(f"Failed to retrieve beta: {e}")

# 🔹 28. Dividend Growth Rate
try:
    dividends = stock.dividends
    dividend_growth_rate = dividends.pct_change().dropna().mean() * 100
    logging.info("28. Dividend Growth Rate computed successfully.")
    print("\n28. Dividend Growth Rate:")
    print(f"Dividend Growth Rate: {dividend_growth_rate:.2f}%")
except Exception as e:
    logging.error(f"Failed to compute dividend growth rate: {e}")

# 🔹 29. Free Cash Flow Analysis
try:
    cash_flow = stock.cashflow
    free_cash_flow = cash_flow.loc["Free Cash Flow"]
    logging.info("29. Free Cash Flow Analysis retrieved successfully.")
    print("\n29. Free Cash Flow Analysis:")
    print(free_cash_flow.head())
except Exception as e:
    logging.error(f"Failed to retrieve free cash flow data: {e}")

# 🔹 30. Debt-to-Equity Ratio
try:
    balance_sheet = stock.balance_sheet
    total_liabilities = balance_sheet.loc["Total Liabilities"]
    total_equity = balance_sheet.loc["Total Stockholder Equity"]
    debt_to_equity = total_liabilities / total_equity
    logging.info("30. Debt-to-Equity Ratio computed successfully.")
    print("\n30. Debt-to-Equity Ratio:")
    print(f"Debt-to-Equity Ratio: {debt_to_equity.iloc[-1]:.2f}")
except Exception as e:
    logging.error(f"Failed to compute debt-to-equity ratio: {e}")