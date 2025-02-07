import json

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

from pykalman import KalmanFilter
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt


def fetch_stock_data(ticker, forecast_days):
    """
    Fetch historical stock data for the given ticker and a period of 'forecast_days'.

    Parameters:
    - ticker (str): Stock ticker symbol.
    - forecast_days (int): Number of days to go back from yesterday's date.

    Returns:
    - pd.DataFrame: Historical stock OHLCV data.
    """
    end_date = (datetime.today() - timedelta(days = 1))  # Up to yesterday
    start_date = end_date - pd.Timedelta(days = forecast_days)
    print(f"Fetching data for {ticker} from {start_date.date()} to {end_date.date()}")

    for _ in range(5):
        try:
            stock_data = yf.download(
                    ticker,
                    start = start_date.strftime('%Y-%m-%d'),
                    end = end_date.strftime('%Y-%m-%d')
                    )
            if not stock_data.empty:
                break
        except:
            print("Ticker data can't be retrieved from yfinance.")
    return stock_data


def calculate_eta_theta(price_series, delta_t = 1):
    """
    Calculate mean-reversion parameters eta (η) and theta (θ) using a discrete-time
    Ornstein-Uhlenbeck process approximation:
        X_(t+1) = alpha * X_t + beta + noise

    For discrete-time OU:
        alpha ~ 1 - k*delta_t
        beta ~ k*delta_t*theta
        => k = (1 - alpha)/delta_t
        => theta = beta / (k * delta_t)

    HOWEVER, if we do a regression of
        ΔX_t = X_(t+1) - X_t = slope*X_t + intercept,
    then
        X_(t+1) = (1 + slope)*X_t + intercept,
    meaning alpha = 1 + slope, beta = intercept.
    We'll convert those properly below.
    """
    price_series = np.asarray(price_series)
    # Differences
    price_changes = np.diff(price_series)
    price_levels = price_series[:-1]

    # Regress ΔX_t on X_t
    X = price_levels.reshape(-1, 1)
    y = price_changes

    lr = LinearRegression()
    lr.fit(X, y)

    # slope from ΔX_t = slope * X_t + intercept
    slope = lr.coef_[0]
    intercept = lr.intercept_

    # So in X_(t+1) = (1 + slope)*X_t + intercept:
    alpha = 1 + slope  # The "alpha" in the OU docstring
    beta = intercept  # The "beta" in the OU docstring

    # Speed of mean reversion: k = (1 - alpha)/delta_t
    eta = (1 - alpha) / delta_t

    # Long-term mean: theta = beta / (k * delta_t)
    # but watch out for dividing by zero if slope ~ -1
    if abs(eta * delta_t) < 1e-12:
        theta = np.nan
    else:
        theta = beta / (eta * delta_t)

    print(f"OU Regression slope: {slope:.6f} => alpha (1+slope) = {alpha:.6f}")
    print(f"Intercept (beta): {beta:.6f}")
    print(f"Speed of mean reversion (eta): {eta:.6f}")
    print(f"Long-term mean (theta): {theta:.6f}")

    return eta, theta


def calculate_market_beta(stock_returns, market_returns):
    """
    Calculate market beta (βₘ) from CAPM:
        stock_return = α + βₘ * market_return + ε
    """
    stock_returns = np.asarray(stock_returns).reshape(-1, 1)
    market_returns = np.asarray(market_returns).reshape(-1, 1)

    # Ensure same length
    min_len = min(len(stock_returns), len(market_returns))
    X = market_returns[:min_len]
    y = stock_returns[:min_len]

    lr = LinearRegression()
    lr.fit(X, y)

    beta_m = lr.coef_[0][0]
    print(f"Market Beta (βₘ) calculation: slope={beta_m:.6f}")
    return beta_m


def calculate_factor_betas(stock_returns, factor_returns):
    """
    Calculate factor betas from a multi-factor model:
        stock_return = α + Σ(β_factor_i * factor_i) + ε
    """
    stock_returns = np.asarray(stock_returns)

    # Align factor data to the same length as stock_returns
    min_len = min(len(stock_returns), len(factor_returns))
    X = factor_returns.iloc[:min_len].values
    y = stock_returns[:min_len].reshape(-1, 1)

    lr = LinearRegression()
    lr.fit(X, y)

    factor_betas = {}
    for factor_name, coef in zip(factor_returns.columns, lr.coef_[0]):
        factor_betas[factor_name] = coef

    print(f"Factor Betas: {factor_betas}")
    return factor_betas


def calculate_interest_rate_beta(stock_returns, interest_rate_changes):
    """
    Calculate interest rate beta (βᵣ):
        stock_return = α + βᵣ * (change in interest rates) + ε
    """
    stock_returns = np.asarray(stock_returns).reshape(-1, 1)
    interest_rate_changes = np.asarray(interest_rate_changes).reshape(-1, 1)

    # Ensure same length
    min_len = min(len(stock_returns), len(interest_rate_changes))
    X = interest_rate_changes[:min_len]
    y = stock_returns[:min_len]

    lr = LinearRegression()
    lr.fit(X, y)

    beta_r = lr.coef_[0][0]
    print(f"Interest Rate Beta (βᵣ): {beta_r:.6f}")
    return beta_r


def calculate_volatility_beta(stock_returns, vix_changes):
    """
    Calculate volatility beta (βᵥ):
        stock_return = α + βᵥ * (change in VIX) + ε
    """
    stock_returns = np.asarray(stock_returns).reshape(-1, 1)
    vix_changes = np.asarray(vix_changes).reshape(-1, 1)

    # Ensure same length
    min_len = min(len(stock_returns), len(vix_changes))
    X = vix_changes[:min_len]
    y = stock_returns[:min_len]

    lr = LinearRegression()
    lr.fit(X, y)

    beta_v = lr.coef_[0][0]
    print(f"Volatility Beta (βᵥ): {beta_v:.6f}")
    return beta_v


def calculate_statistics(df):
    """
    Calculate statistics from the historical stock data at a daily level.

    Parameters:
    - df: DataFrame containing historical stock data with 'Date' and 'Close' columns.

    Returns:
    - mu_daily: Estimated daily drift (float).
    - sigma_daily: Estimated daily volatility (float).
    - closing_prices: Array of closing prices (numpy array).
    - log_returns: Array of daily log returns (numpy array).
    """
    # Ensure 'Close' is numeric by removing any commas and converting to float
    df['Close'] = df['Close'].astype(str).str.replace(',', '').astype(float)

    # Convert 'Date' column to datetime, coercing any errors to NaT
    df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')

    # Sort the DataFrame by date in ascending order (oldest first)
    df = df.sort_values('Date', ascending = True)

    # Extract closing prices as a NumPy array
    closing_prices = df['Close'].values

    # Calculate daily log returns
    log_returns = np.diff(np.log(closing_prices))

    # Estimate daily drift (mu) and volatility (sigma)
    mu_daily = np.mean(log_returns)
    sigma_daily = np.std(log_returns)

    print(f"Calculated daily drift (mu_daily): {mu_daily}, daily volatility (sigma_daily): {sigma_daily}")
    return mu_daily, sigma_daily, closing_prices, log_returns


def forecast_stock_prices(
    equation_type,
    recent_price,
    mu_daily,
    sigma_daily,
    forecast_days,
    stock_interval="1d",
    valuation_metrics=None,
    financial_health_metrics=None,
    mean_reversion_params=None,
    external_factors=None
):
    """
    Forecast future stock prices using different stochastic models,
    now incorporating 'stock_interval' as the size of each time step.

    Parameters:
      - equation_type: 'Geometric Brownian Motion', 'Geometric Brownian Motion with Mean Reversion',
                      or 'Geometric Brownian Motion External Macroeconomic Factors'
      - recent_price: The most recent closing price (float)
      - mu_daily: Estimated daily drift (float)
      - sigma_daily: Estimated daily volatility (float)
      - forecast_days: Total number of calendar days to forecast (int)
      - stock_interval: Interval string (e.g. '1m', '1d', '1wk')
        to determine how small each time step (dt) is.
      - valuation_metrics, financial_health_metrics, mean_reversion_params, external_factors
        are optional dicts to shape the forecast.

    Returns:
      t:   np.array of time points (in days),
      forecast_prices: np.array of forecasted prices (same length as t)
    """

    # ----------------------------------------------------
    # 1) Map interval => fraction of a day (float dt)
    # ----------------------------------------------------
    interval_map = {
        "1m": 1.0 / (24 * 60),   # 1 minute
        "2m": 2.0 / (24 * 60),
        "5m": 5.0 / (24 * 60),
        "15m": 15.0 / (24 * 60),
        "30m": 30.0 / (24 * 60),
        "60m": 1.0 / 24,        # 1 hour
        "90m": 1.5 / 24,
        "1h": 1.0 / 24,         # also 1 hour
        "1d": 1.0,              # 1 day
        "5d": 5.0,              # 5 days
        "1wk": 7.0,             # 7 days
        "1mo": 30.0,            # approximate
        "3mo": 90.0,            # approximate
    }

    stock_interval_str = json.dumps(stock_interval)
    dt_interval = interval_map.get(stock_interval_str.strip(), 1.0)

    # ----------------------------------------------------
    # 2) Number of steps => forecast_days / dt_interval
    # ----------------------------------------------------
    # e.g., if forecast_days=30 and stock_interval='1d',
    # steps => 30 / 1 = 30
    # if stock_interval='60m' => dt=1/24 => steps => 30 / (1/24)=720
    steps_float = forecast_days / dt_interval

    N = int(round(steps_float))
    if N < 1:
        N = 1

    print(
        f"Forecasting ~{forecast_days} days using {equation_type} model with interval {stock_interval} "
        f"=> dt={dt_interval:.4f} days, total steps={N}.")

    # We'll define dt as dt_interval in 'days'
    dt = dt_interval

    # We'll define time array from 0..forecast_days in N steps
    # so it extends from day 0 to day = forecast_days
    t = np.linspace(0, forecast_days, N)

    # ----------------------------------------------------
    # The rest is basically your original code
    # with references to dt replaced by this dt
    # ----------------------------------------------------
    # Initialize adjustments
    valuation_adjustment = 1.0
    financial_health_adjustment = 1.0

    # Adjust mu_daily and sigma_daily based on valuation metrics
    if valuation_metrics:
        pe_ratio = valuation_metrics.get('P/E Ratio', None)
        pb_ratio = valuation_metrics.get('Price-to-Book', None)

        if pe_ratio is not None:
            if pe_ratio > 20:
                # Reduce drift for overvalued stocks using a precise multiplier
                valuation_adjustment *= 0.923456
            elif pe_ratio < 10:
                # Increase drift for undervalued stocks using a precise multiplier
                valuation_adjustment *= 1.123456

        if pb_ratio is not None:
            if pb_ratio > 2.5:
                # Reduce drift for overvalued stocks using a precise multiplier
                valuation_adjustment *= 0.876543
            elif pb_ratio < 1.5:
                # Increase drift for undervalued stocks using a precise multiplier
                valuation_adjustment *= 1.098765

    # Adjust mu_daily and sigma_daily based on financial health metrics
    if financial_health_metrics:
        debt_to_equity = financial_health_metrics.get('Debt to Equity', None)
        current_ratio = financial_health_metrics.get('Current Ratio', None)

        if debt_to_equity is not None:
            if debt_to_equity > 1.5:
                # Increase volatility for high debt using a precise multiplier
                financial_health_adjustment *= 1.234567
            elif debt_to_equity < 0.5:
                # Decrease volatility for low debt using a precise multiplier
                financial_health_adjustment *= 0.812345

        if current_ratio is not None:
            if current_ratio < 1.0:
                # Increase volatility for poor liquidity using a precise multiplier
                financial_health_adjustment *= 1.198765
            elif current_ratio > 2.0:
                # Decrease volatility for strong liquidity using a precise multiplier
                financial_health_adjustment *= 0.823456

    # Apply adjustments to mu_daily and sigma_daily
    mu_daily_adjusted = mu_daily * valuation_adjustment
    sigma_daily_adjusted = sigma_daily * financial_health_adjustment

    # Generate random Brownian motion
    np.random.seed(42)
    W = np.random.standard_normal(size = N)
    W = np.cumsum(W) * np.sqrt(dt)

    print("Random Brownian motion (W) generated.")

    # Initialize forecast_prices array
    forecast_prices = np.zeros(N)
    forecast_prices[0] = recent_price

    # Extract mean-reversion parameters
    eta = mean_reversion_params.get('eta', 0) if mean_reversion_params else 0
    theta = mean_reversion_params.get('theta', recent_price) if mean_reversion_params else recent_price

    print(f"Mean-reversion eta: {eta}, theta: {theta}")

    # Apply selected forecasting model
    if equation_type == 'Geometric Brownian Motion':  # Standard Geometric Brownian Motion
        forecast_prices = recent_price * np.exp((mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * t + sigma_daily_adjusted * W)

    elif equation_type == 'Geometric Brownian Motion with Mean Reversion':  # GBM with Mean Reversion
        for i in range(1, N):
            # mean_reversion_term = eta * (theta - forecast_prices[i - 1]) * dt
            # forecast_prices[i] = forecast_prices[i - 1] * np.exp(
            #         (mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * dt +
            #         sigma_daily_adjusted * (W[i] - W[i - 1]) +
            #         mean_reversion_term
            #         )
            external_adjustment = 1.0
            if external_factors:
                macro_effect = sum(coefficient * external_factors[factor] for factor, coefficient in external_factors.items())
                external_adjustment = np.exp(macro_effect)

            forecast_prices[i] = forecast_prices[i - 1] * np.exp(
                    (mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * dt +
                    sigma_daily_adjusted * (W[i] - W[i - 1])
                    ) * external_adjustment

    elif equation_type == 'Geometric Brownian Motion External Macroeconomic Factors':
        for i in range(1, N):
            mean_reversion_term = eta * (theta - forecast_prices[i - 1]) * dt

            macro_adjustment = 0
            if external_factors:
                macro_adjustment = sum(coefficient * external_factors[factor] for factor, coefficient in external_factors.items())

            forecast_prices[i] = forecast_prices[i - 1] * np.exp(
                    (mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * dt +
                    sigma_daily_adjusted * (W[i] - W[i - 1]) +
                    mean_reversion_term +
                    macro_adjustment
                    )

    else:
        raise ValueError(
                "Invalid equation_type. Choose 'Geometric Brownian Motion', 'Geometric Brownian Motion with Mean Reversion', "
                "or 'Geometric Brownian Motion External Macroeconomic Factors'.")

    print(f"Stock price forecast using {equation_type} model completed.")
    return t, forecast_prices


def get_trading_dates(start_date, forecast_days):
    """
    Generate a list of valid trading dates (weekdays only) starting from start_date.

    Parameters:
    - start_date: The starting date as a pandas Timestamp.
    - forecast_days: Number of trading days to generate (int).

    Returns:
    - A list of pandas Timestamps representing valid trading days.
    """
    trading_dates = []
    current_date = start_date

    while len(trading_dates) < forecast_days:
        if current_date.weekday() < 5:  # Only consider weekdays (Monday=0, Sunday=6)
            trading_dates.append(current_date)
        current_date += pd.Timedelta(days = 1)

    print(f"Generated {len(trading_dates)} trading dates.")
    return trading_dates[:forecast_days]


def shift_forecast_to_actual_dates(df, forecast_prices, forecast_days):
    """
    Align forecasted prices with actual trading dates.

    Parameters:
    - df: Historical data DataFrame containing 'Date'.
    - forecast_prices: Array of forecasted prices (numpy array).
    - forecast_days: Number of forecast days (int).

    Returns:
    - forecast_df: DataFrame with 'Date' and 'Forecasted_Close'.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
    most_recent_date = df['Date'].max()

    forecast_dates = get_trading_dates(most_recent_date - pd.Timedelta(days = forecast_days), forecast_days)

    forecast_df = pd.DataFrame({'Date': forecast_dates, 'Forecasted_Close': forecast_prices})
    print("Forecasted prices aligned with trading dates.")
    return forecast_df


def calculate_prediction_errors(df, forecast_df):
    """
    Calculate prediction errors between actual and forecasted stock prices.

    Parameters:
    - df: Historical data DataFrame containing 'Date' and 'Close'.
    - forecast_df: DataFrame with forecasted prices containing 'Date' and 'Forecasted_Close'.

    Returns:
    - merged_df: DataFrame with 'Date', 'Actual_Close', 'Forecasted_Close', and 'Error'.
    """
    merged_df = pd.merge(df[['Date', 'Close']], forecast_df, on = 'Date', how = 'inner')
    merged_df = merged_df.rename(columns = {'Close': 'Actual_Close'})
    merged_df['Error'] = merged_df['Actual_Close'] - merged_df['Forecasted_Close']
    print("Prediction errors calculated.")
    return merged_df


def plot_results(error_df):
    """
    Plot actual versus forecasted stock prices.

    Parameters:
    - error_df: DataFrame containing 'Date', 'Actual_Close', and 'Forecasted_Close'.
    """
    plt.figure(figsize = (12, 6))
    plt.plot(error_df['Date'], error_df['Actual_Close'], label = 'Actual Prices', marker = 'o', linestyle = '-')
    plt.plot(error_df['Date'], error_df['Forecasted_Close'], label = 'Forecasted Prices', marker = 'x', linestyle = '--')
    plt.title('Stock Price Prediction: Actual vs. Forecasted')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()
    print("Plot generated successfully.")

# if __name__ == "__main__":
#     # Tickers
#     main_ticker = "NVDA"  # Your main ticker
#     market_ticker = "^GSPC"  # S&P 500
#     vix_ticker = "^VIX"  # Volatility Index
#     tnx_ticker = "^TNX"  # 10-Year Treasury Yield
#
#     # Download all tickers in one go (over the past year for demonstration)
#     data = yf.download([main_ticker, market_ticker, vix_ticker, tnx_ticker], period = "1y")
#
#     # -----------------------------------------
#     # 1. Align data by dropping rows that have NA in any of these tickers
#     #    This ensures consistent length across all columns.
#     # -----------------------------------------
#     close_data = data["Close"].dropna(subset = [main_ticker, market_ticker, vix_ticker, tnx_ticker])
#
#     # Extract each series
#     stock_data = close_data[main_ticker]
#     market_data = close_data[market_ticker]
#     vix_data = close_data[vix_ticker]
#     tnx_data = close_data[tnx_ticker]
#
#     # Convert to numpy arrays
#     price_series = stock_data.values
#     market_prices = market_data.values
#     vix_prices = vix_data.values
#     tnx_prices = tnx_data.values
#
#     # -----------------------------------------
#     # 2. Compute daily returns/changes
#     # -----------------------------------------
#     stock_returns = np.diff(price_series) / price_series[:-1]
#     market_returns = np.diff(market_prices) / market_prices[:-1]
#     vix_changes = np.diff(vix_prices) / vix_prices[:-1]
#     interest_rate_changes = np.diff(tnx_prices) / tnx_prices[:-1]
#
#     # -----------------------------------------
#     # 3. Create Factor Returns (Placeholder)
#     #    In real usage, you'd pull actual factor data (SMB, HML, MOM, etc.).
#     #    Must match the length of stock_returns.
#     # -----------------------------------------
#     min_len = len(stock_returns)  # We'll align to stock returns length
#     factor_returns = pd.DataFrame(
#             {
#                 "SMB": np.random.normal(0, 0.01, min_len),
#                 "HML": np.random.normal(0, 0.01, min_len),
#                 "MOM": np.random.normal(0, 0.01, min_len)
#                 })
#
#     # -----------------------------------------
#     # 4. Calculate Parameters and Betas
#     # -----------------------------------------
#     # Ornstein-Uhlenbeck parameters
#     eta, theta = calculate_eta_theta(price_series)
#
#     # Betas
#     beta_m = calculate_market_beta(stock_returns, market_returns)
#     factor_betas = calculate_factor_betas(stock_returns, factor_returns)
#     beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
#     beta_v = calculate_volatility_beta(stock_returns, vix_changes)
#
#     # -----------------------------------------
#     # 5. Show Results
#     # -----------------------------------------
#     print("\n========== RESULTS ==========")
#     print(f"Eta (η): {eta:.6f}")
#     print(f"Theta (θ): {theta:.6f}")
#     print(f"Market Beta (βₘ): {beta_m:.6f}")
#     print(f"Factor Betas: {factor_betas}")
#     print(f"Interest Rate Beta (βᵣ): {beta_r:.6f}")
#     print(f"Volatility Beta (βᵥ): {beta_v:.6f}")