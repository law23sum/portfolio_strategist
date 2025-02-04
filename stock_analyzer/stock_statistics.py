import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


forecast_days = 120
prior_days = 60


def calculate_statistics(df):
    """
    Calculate statistics from the historical stock data at a daily level.

    Parameters:
    - df: DataFrame containing historical stock data with 'Date' and 'Close' columns.

    Returns:
    - mu_daily: Estimated daily drift.
    - sigma_daily: Estimated daily volatility.
    - closing_prices: Array of closing prices.
    - log_returns: Array of daily log returns.
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

    return mu_daily, sigma_daily, closing_prices, log_returns


def forecast_stock_prices(
        recent_price, mu_daily, sigma_daily, forecast_days, valuation_metrics = None, financial_health_metrics = None,
        mean_reversion_params = None, external_factors = None
        ):
    """
    Forecast future stock prices using an enhanced Geometric Brownian Motion model,
    adjusted for valuation measures, financial health, mean-reversion, and external factors.

    Parameters:
    - recent_price: The most recent closing price.
    - mu_daily: Estimated daily drift.
    - sigma_daily: Estimated daily volatility.
    - forecast_days: Number of days to forecast (default is 90).
    - valuation_metrics: A dictionary containing valuation metrics (e.g., P/E ratio, P/B ratio).
    - financial_health_metrics: A dictionary containing financial health metrics (e.g., debt-to-equity, current ratio).
    - mean_reversion_params: A dictionary containing mean-reversion parameters (e.g., eta, theta).
    - external_factors: A dictionary containing external factors and their coefficients (e.g., {'factor1': beta1, 'factor2': beta2}).

    Returns:
    - t: Array of time points (in days).
    - forecast_prices: Array of forecasted stock prices (mean of simulations).
    """
    dt = 1  # one day per step
    N = forecast_days
    t = np.linspace(0, N, N)

    # Default adjustment factors
    valuation_adjustment = 1.0
    financial_health_adjustment = 1.0

    # Adjust mu_daily based on valuation metrics
    if valuation_metrics:
        pe_ratio = valuation_metrics.get('P/E Ratio', None)
        pb_ratio = valuation_metrics.get('Price-to-Book', None)

        if pe_ratio is not None:
            # Example logic: If P/E ratio is high, reduce expected returns
            if pe_ratio > 20:  # Assuming 20 is the industry average
                valuation_adjustment *= 0.9  # Reduce expected returns by 10%
            elif pe_ratio < 10:  # If P/E is low, increase expected returns
                valuation_adjustment *= 1.1  # Increase expected returns by 10%

        if pb_ratio is not None:
            # Example logic: If P/B ratio is high, reduce expected returns
            if pb_ratio > 2.5:  # Assuming 2.5 is the industry average
                valuation_adjustment *= 0.9  # Reduce expected returns by 10%
            elif pb_ratio < 1.5:  # If P/B is low, increase expected returns
                valuation_adjustment *= 1.1  # Increase expected returns by 10%

    # Adjust sigma_daily based on financial health metrics
    if financial_health_metrics:
        debt_to_equity = financial_health_metrics.get('Debt to Equity', None)
        current_ratio = financial_health_metrics.get('Current Ratio', None)

        if debt_to_equity is not None:
            # Example logic: If debt-to-equity is high, increase volatility
            if debt_to_equity > 1.5:  # Assuming 1.5 is a threshold for high debt
                financial_health_adjustment *= 1.2  # Increase volatility by 20%
            elif debt_to_equity < 0.5:  # If debt-to-equity is low, decrease volatility
                financial_health_adjustment *= 0.8  # Decrease volatility by 20%

        if current_ratio is not None:
            # Example logic: If current ratio is low, increase volatility
            if current_ratio < 1.0:  # Assuming 1.0 is a threshold for low liquidity
                financial_health_adjustment *= 1.2  # Increase volatility by 20%
            elif current_ratio > 2.0:  # If current ratio is high, decrease volatility
                financial_health_adjustment *= 0.8  # Decrease volatility by 20%

    # Adjust mu_daily and sigma_daily based on valuation and financial health
    mu_daily_adjusted = mu_daily * valuation_adjustment
    sigma_daily_adjusted = sigma_daily * financial_health_adjustment

    # Generate a Wiener process (Brownian motion increments)
    np.random.seed(42)  # for reproducibility
    W = np.random.standard_normal(size = N)
    W = np.cumsum(W) * np.sqrt(dt)

    # Initialize the price array
    forecast_prices = np.zeros(N)
    forecast_prices[0] = recent_price

    # Mean-reversion parameters
    eta = mean_reversion_params.get('eta', 0) if mean_reversion_params else 0
    theta = mean_reversion_params.get('theta', recent_price) if mean_reversion_params else recent_price

    # External factors
    external_factors_sum = np.zeros(N)
    if external_factors:
        for factor, beta in external_factors.items():
            # Assuming external factors are provided as arrays of length N
            external_factors_sum += beta * factor

    # Simulate the forecast using the enhanced GBM formula
    for i in range(1, N):
        mean_reversion_term = eta * (theta - forecast_prices[i - 1]) * dt
        forecast_prices[i] = forecast_prices[i - 1] * np.exp(
                (mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * dt +
                sigma_daily_adjusted * (W[i] - W[i - 1]) +
                mean_reversion_term +
                external_factors_sum[i]
                )

    return t, forecast_prices


def get_trading_dates(start_date, forecast_days):
    """
    Generate a list of valid trading dates (weekdays only) starting from start_date.

    Parameters:
    - start_date: The starting date as a pandas Timestamp.
    - days: Number of trading days to generate.

    Returns:
    - A list of pandas Timestamps representing valid trading days.
    """
    trading_dates = []
    current_date = start_date

    while len(trading_dates) < forecast_days:
        # Only consider weekdays (Monday=0, Sunday=6)
        if current_date.weekday() < 5:
            trading_dates.append(current_date)
        current_date += pd.Timedelta(days = 1)

    return trading_dates[:forecast_days]


def shift_forecast_to_actual_dates(df, forecast_prices, forecast_days):
    """
    Align forecasted prices with actual trading dates.

    Parameters:
    - df: Historical data DataFrame containing 'Date'.
    - forecast_prices: Array of forecasted prices.
    - forecast_days: Number of forecast days (default 90).

    Returns:
    - forecast_df: DataFrame with 'Date' and 'Forecasted_Close'.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
    most_recent_date = df['Date'].max()

    # Generate trading dates starting 60 days before the most recent date to cover both past and future
    forecast_dates = get_trading_dates(most_recent_date - pd.Timedelta(prior_days), forecast_days)

    forecast_df = pd.DataFrame({'Date': forecast_dates, 'Forecasted_Close': forecast_prices})
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
    plt.title('Stock Price Prediction: Actual vs. Forecasted (Past 45 Days + Future 45 Days)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()