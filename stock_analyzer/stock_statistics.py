import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def calculate_statistics(df):
    """
    Calculate statistics from the historical stock data.

    :param df: DataFrame containing historical data with at least a 'Date' and 'Close' column.
    :return: A tuple containing estimated daily drift (mu_daily), daily volatility (sigma_daily),
             closing prices, and log returns.
    """
    # Ensure the 'Close' column is numeric
    if df['Close'].dtype != np.float64:
        df['Close'] = df['Close'].str.replace(',', '').astype(float)

    # Ensure the 'Date' column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Sort the DataFrame by date in ascending order
    df = df.sort_values('Date', ascending=True)

    # Extract closing prices
    closing_prices = df['Close'].values

    # Calculate daily log returns
    log_returns = np.diff(np.log(closing_prices))

    # Estimate drift (mu) and volatility (sigma)
    mu_daily = np.mean(log_returns)
    sigma_daily = np.std(log_returns)

    return mu_daily, sigma_daily, closing_prices, log_returns


def forecast_stock_prices(recent_price, mu_daily, sigma_daily, forecast_days=30):
    """
    Forecast future stock prices using a geometric Brownian motion model.

    :param recent_price: Most recent closing price.
    :param mu_daily: Estimated daily drift.
    :param sigma_daily: Estimated daily volatility.
    :param forecast_days: Number of days to forecast into the future.
    :return: Tuple of (time array, forecasted price path)
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