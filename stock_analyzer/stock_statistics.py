import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


forecast_days = 80


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


def forecast_stock_prices(recent_price, mu_daily, sigma_daily, forecast_days, num_simulations = 1000):
    """
    Forecast future stock prices using an enhanced Geometric Brownian Motion model.

    Parameters:
    - recent_price: The most recent closing price.
    - mu_daily: Estimated daily drift.
    - sigma_daily: Estimated daily volatility.
    - forecast_days: Number of days to forecast (default is 90).
    - num_simulations: Number of Monte Carlo simulations (default is 1000).

    Returns:
    - t: Array of time points (in days).
    - forecast_prices: Array of forecasted stock prices (mean of simulations).
    - confidence_intervals: Confidence intervals for the forecasted prices.
    """
    dt = 1  # one day per step
    N = forecast_days
    t = np.linspace(0, N, N)

    # Generate a Wiener process (Brownian motion increments)
    np.random.seed(42)  # for reproducibility
    W = np.random.standard_normal(size=N)
    W = np.cumsum(W) * np.sqrt(dt)

    # Simulate the forecast using the GBM formula:
    # S(t) = S0 * exp((mu_daily - 0.5 * sigma_daily**2) * t + sigma_daily * W(t))
    forecast_prices = recent_price * np.exp((mu_daily - 0.5 * sigma_daily**2) * t + sigma_daily * W)
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

    # Generate trading dates starting 45 days before the most recent date to cover both past and future
    forecast_dates = get_trading_dates(most_recent_date - pd.Timedelta(days = 40), forecast_days)

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