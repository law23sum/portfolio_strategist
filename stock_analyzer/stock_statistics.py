import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Sort the DataFrame by date in ascending order (oldest first)
    df = df.sort_values('Date', ascending=True)

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
    recent_price, mu_daily, sigma_daily, forecast_days,
    valuation_metrics=None, financial_health_metrics=None,
    mean_reversion_params=None, external_factors=None
):
    """
    Forecast future stock prices using an enhanced Geometric Brownian Motion model.

    Parameters:
    - recent_price: The most recent closing price (float).
    - mu_daily: Estimated daily drift (float).
    - sigma_daily: Estimated daily volatility (float).
    - forecast_days: Number of days to forecast (int).
    - valuation_metrics: A dictionary containing valuation metrics (dict, optional).
    - financial_health_metrics: A dictionary containing financial health metrics (dict, optional).
    - mean_reversion_params: A dictionary containing mean-reversion parameters (dict, optional).
    - external_factors: A dictionary containing external factors and their coefficients (dict, optional).

    Returns:
    - t: Array of time points (in days) (numpy array).
    - forecast_prices: Array of forecasted stock prices (numpy array).
    """
    dt = 1  # Time step (1 day)
    N = forecast_days  # Number of days to forecast
    t = np.linspace(0, N, N)  # Time array

    print(f"Forecasting {N} days with time step (dt): {dt}")

    # Initialize adjustments for valuation and financial health metrics
    valuation_adjustment = 1.0
    financial_health_adjustment = 1.0

    # Adjust mu_daily and sigma_daily based on valuation metrics
    if valuation_metrics:
        pe_ratio = valuation_metrics.get('P/E Ratio', None)
        pb_ratio = valuation_metrics.get('Price-to-Book', None)

        if pe_ratio is not None:
            print(f"P/E Ratio detected: {pe_ratio}")
            if pe_ratio > 20:
                valuation_adjustment *= 0.923456
            elif pe_ratio < 10:
                valuation_adjustment *= 1.123456

        if pb_ratio is not None:
            print(f"Price-to-Book detected: {pb_ratio}")
            if pb_ratio > 2.5:
                valuation_adjustment *= 0.876543
            elif pb_ratio < 1.5:
                valuation_adjustment *= 1.098765

    # Adjust mu_daily and sigma_daily based on financial health metrics
    if financial_health_metrics:
        debt_to_equity = financial_health_metrics.get('Debt to Equity', None)
        current_ratio = financial_health_metrics.get('Current Ratio', None)

        if debt_to_equity is not None:
            print(f"Debt to Equity detected: {debt_to_equity}")
            if debt_to_equity > 1.5:
                financial_health_adjustment *= 1.234567
            elif debt_to_equity < 0.5:
                financial_health_adjustment *= 0.812345

        if current_ratio is not None:
            print(f"Current Ratio detected: {current_ratio}")
            if current_ratio < 1.0:
                financial_health_adjustment *= 1.198765
            elif current_ratio > 2.0:
                financial_health_adjustment *= 0.823456

    mu_daily_adjusted = mu_daily * valuation_adjustment
    sigma_daily_adjusted = sigma_daily * financial_health_adjustment

    # Generate random Brownian motion
    np.random.seed(None)
    W = np.random.standard_normal(size=N)
    W = np.cumsum(W) * np.sqrt(dt)
    print("Random Brownian motion (W) generated and cumulatively summed.")

    # Initialize forecast_prices array
    forecast_prices = np.zeros(N)
    forecast_prices[0] = recent_price
    print(f"Starting forecast at recent price: {recent_price}")

    # Extract mean-reversion parameters (eta and theta)
    eta = mean_reversion_params.get('eta', 0) if mean_reversion_params else 0
    theta = mean_reversion_params.get('theta', recent_price) if mean_reversion_params else recent_price
    print(f"Mean-reversion parameter eta: {eta}, theta: {theta}")

    # Simulate stock prices using the enhanced Geometric Brownian Motion model
    for i in range(1, N):
        mean_reversion_term = eta * (theta - forecast_prices[i - 1]) * dt
        forecast_prices[i] = forecast_prices[i - 1] * np.exp(
            (mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * dt +
            sigma_daily_adjusted * (W[i] - W[i - 1]) +
            mean_reversion_term
        )

    print("Stock price forecast simulation completed.")
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
        current_date += pd.Timedelta(days=1)

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
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    most_recent_date = df['Date'].max()

    forecast_dates = get_trading_dates(most_recent_date - pd.Timedelta(days=forecast_days), forecast_days)

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
    merged_df = pd.merge(df[['Date', 'Close']], forecast_df, on='Date', how='inner')
    merged_df = merged_df.rename(columns={'Close': 'Actual_Close'})
    merged_df['Error'] = merged_df['Actual_Close'] - merged_df['Forecasted_Close']
    print("Prediction errors calculated.")
    return merged_df


def plot_results(error_df):
    """
    Plot actual versus forecasted stock prices.

    Parameters:
    - error_df: DataFrame containing 'Date', 'Actual_Close', and 'Forecasted_Close'.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(error_df['Date'], error_df['Actual_Close'], label='Actual Prices', marker='o', linestyle='-')
    plt.plot(error_df['Date'], error_df['Forecasted_Close'], label='Forecasted Prices', marker='x', linestyle='--')
    plt.title('Stock Price Prediction: Actual vs. Forecasted')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()
    print("Plot generated successfully.")