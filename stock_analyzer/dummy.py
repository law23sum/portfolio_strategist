from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt


forecast_days = 120
prior_days = 60


def fetch_stock_data(ticker, forecast_days):
    """
    Fetch historical stock data for the given ticker and date range.

    Parameters:
    - ticker: Stock ticker symbol.
    - start_date_str: Start date in 'YYYY-MM-DD' format.
    - forecast_days: Number of days to go back from the start date.

    Returns:
    - stock_data: DataFrame containing historical stock data.
    """
    end_date = pd.to_datetime((datetime.today() - timedelta(days = 1)).strftime('%Y-%m-%d')) - pd.Timedelta(days = forecast_days)
    stock_data = yf.download(ticker, start = end_date.strftime('%Y-%m-%d'), end = (datetime.today() - timedelta(days = 1)).strftime('%Y-%m-%d'))
    return stock_data


def calculate_eta_theta(price_series, delta_t = 1):
    """
    Calculate mean-reversion parameters eta (η) and theta (θ) using the Ornstein-Uhlenbeck process.

    Inputs:
    - price_series: A pandas Series or numpy array of historical stock prices.
    - delta_t: Time step (default is 1 for daily data).

    Returns:
    - eta: Speed of mean reversion.
    - theta: Long-term equilibrium price.
    """
    price_changes = np.diff(price_series)
    price_levels = price_series[:-1]

    model = LinearRegression()
    model.fit(price_levels.reshape(-1, 1), price_changes)

    alpha = model.coef_[0]
    beta = model.intercept_

    eta = (1 - alpha) / delta_t
    theta = beta / (eta * delta_t)

    return eta, theta


def calculate_market_beta(stock_returns, market_returns):
    """
    Calculate market beta (βₘ) using the CAPM model.

    Inputs:
    - stock_returns: A pandas Series or numpy array of historical stock returns.
    - market_returns: A pandas Series or numpy array of historical market returns (e.g., S&P 500).

    Returns:
    - beta_m: Market beta.
    """
    model = LinearRegression()
    model.fit(market_returns.reshape(-1, 1), stock_returns)

    beta_m = model.coef_[0]

    return beta_m


def calculate_factor_betas(stock_returns, factor_returns):
    """
    Calculate factor betas (e.g., SMB, HML, MOM) using a multi-factor model.

    Inputs:
    - stock_returns: A pandas Series or numpy array of historical stock returns.
    - factor_returns: A pandas DataFrame of historical factor returns (columns: SMB, HML, MOM, etc.).

    Returns:
    - betas: A dictionary of factor betas.
    """
    model = LinearRegression()
    model.fit(factor_returns, stock_returns)

    betas = {factor: coef for factor, coef in zip(factor_returns.columns, model.coef_)}

    return betas


def calculate_interest_rate_beta(stock_returns, interest_rate_changes):
    """
    Calculate interest rate beta (βᵣ).

    Inputs:
    - stock_returns: A pandas Series or numpy array of historical stock returns.
    - interest_rate_changes: A pandas Series or numpy array of historical changes in interest rates.

    Returns:
    - beta_r: Interest rate beta.
    """
    model = LinearRegression()
    model.fit(interest_rate_changes.reshape(-1, 1), stock_returns)

    beta_r = model.coef_[0]

    return beta_r


def calculate_volatility_beta(stock_returns, vix_changes):
    """
    Calculate volatility beta (βᵥ) using changes in the VIX index.

    Inputs:
    - stock_returns: A pandas Series or numpy array of historical stock returns.
    - vix_changes: A pandas Series or numpy array of historical changes in the VIX index.

    Returns:
    - beta_v: Volatility beta.
    """
    model = LinearRegression()
    model.fit(vix_changes.reshape(-1, 1), stock_returns)

    beta_v = model.coef_[0]

    return beta_v


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
    df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')
    if df['Close'].isnull().any():
        print("Warning: Some 'Close' values could not be converted to numeric and were set to NaN.")

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
        recent_price, mu_daily, sigma_daily, forecast_days,
        valuation_metrics=None, financial_health_metrics=None,
        mean_reversion_params=None, external_factors=None
    ):
    """
    Forecast future stock prices using an enhanced Geometric Brownian Motion model.

    Parameters:
    - recent_price: The most recent closing price.
    - mu_daily: Estimated daily drift.
    - sigma_daily: Estimated daily volatility.
    - forecast_days: Number of days to forecast.
    - valuation_metrics: A dictionary containing valuation metrics.
    - financial_health_metrics: A dictionary containing financial health metrics.
    - mean_reversion_params: A dictionary containing mean-reversion parameters (eta, theta).
    - external_factors: A dictionary containing external factors and their coefficients.

    Returns:
    - t: Array of time points (in days).
    - forecast_prices: Array of forecasted stock prices (mean of simulations).
    """

    dt = 1  # Time step (1 day)
    N = forecast_days  # Number of days to forecast
    t = np.linspace(0, N, N)  # Time array

    print(f"Time step (dt) is {dt}, forecasting {N} days.")

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

    # external_factors_sum = np.zeros(N)
    # if external_factors:
    #     for factor_name, beta in external_factors.items():
    #         factor = external_factors[factor_name]
    #         if isinstance(factor, (list, np.ndarray)):
    #             # Ensure factor is a numpy array
    #             factor_array = np.array(factor)
    #             external_factors_sum += beta * factor_array
    #         else:
    #             # If factor is a scalar, multiply directly
    #             external_factors_sum += beta * factor
    #     print("External factors processed and combined.")

    # Simulate stock prices using the enhanced Geometric Brownian Motion model
    for i in range(1, N):
        mean_reversion_term = eta * (theta - forecast_prices[i - 1]) * dt
        forecast_prices[i] = forecast_prices[i - 1] * np.exp(
            (mu_daily_adjusted - 0.5 * sigma_daily_adjusted ** 2) * dt +
            sigma_daily_adjusted * (W[i] - W[i - 1]) +
            mean_reversion_term
            # + external_factors_sum[i]
        )

    print("Stock price forecast simulation completed.")
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
    - forecast_days: Number of forecast days.

    Returns:
    - forecast_df: DataFrame with 'Date' and 'Forecasted_Close'.
    """
    df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
    most_recent_date = df['Date'].max()

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

if __name__ == "__main__":
    ticker = 'AAPL'
    start_date_str = '2023-10-01'
    forecast_days = 120

    stock_data = fetch_stock_data(ticker, forecast_days)
    price_series = stock_data['Close'].values
    price_series = price_series.flatten()
    stock_returns = np.diff(price_series) / price_series[:-1]

    market_data = fetch_stock_data(ticker, forecast_days)
    market_returns = np.diff(market_data['Close'].values.flatten()) / market_data['Close'].values[:-1].flatten()

    factor_returns = pd.DataFrame(
            {
                'SMB': np.random.normal(0, 0.01, len(stock_returns)),
                'HML': np.random.normal(0, 0.01, len(stock_returns)),
                'MOM': np.random.normal(0, 0.01, len(stock_returns))
                })

    interest_rate_data = fetch_stock_data(ticker, forecast_days)
    interest_rate_changes = np.diff(interest_rate_data['Close'].values.flatten()) / interest_rate_data['Close'].values[:-1].flatten()

    vix_data = fetch_stock_data(ticker, forecast_days)
    vix_changes = np.diff(vix_data['Close'].values.flatten()) / vix_data['Close'].values[:-1].flatten()

    eta, theta = calculate_eta_theta(price_series)
    beta_m = calculate_market_beta(stock_returns, market_returns)
    factor_betas = calculate_factor_betas(stock_returns, factor_returns)
    beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
    beta_v = calculate_volatility_beta(stock_returns, vix_changes)

    print(f"Eta (η): {eta}")
    print(f"Theta (θ): {theta}")
    print(f"Market Beta (βₘ): {beta_m}")
    print(f"Factor Betas: {factor_betas}")
    print(f"Interest Rate Beta (βᵣ): {beta_r}")
    print(f"Volatility Beta (βᵥ): {beta_v}")

    mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(stock_data.reset_index())
    t, forecast_prices = forecast_stock_prices(closing_prices[-1], mu_daily, sigma_daily, forecast_days)
    forecast_df = shift_forecast_to_actual_dates(stock_data.reset_index(), forecast_prices, forecast_days)
    error_df = calculate_prediction_errors(stock_data.reset_index(), forecast_df)