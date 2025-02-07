#!/usr/bin/env python3
"""
StockApp - Terminal-Only Edition

This merges the latest forecasting and ratio logic from the 'bottom code'
into a single script for terminal execution only.

Install Requirements:
    pip install pandas numpy matplotlib yfinance mplcursors
    (and, optionally, whatever your pdf_generator, ai_analyzer, etc. require)
"""

import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplcursors
import yfinance as yf

# Local module imports (you must have these modules in the same directory or installed)
from pdf_generator import PDFGenerator
from stock_definitions import RATIO_DEFINITIONS, MACRO_ECONOMIC_INDICATORS
from stock_fetcher import StockFetcher
from stock_ratio import StockRatio
from ai_analyzer import analyze_stock_with_news
from stock_statistics import (
    calculate_eta_theta, calculate_factor_betas, calculate_interest_rate_beta,
    calculate_market_beta, calculate_statistics, calculate_volatility_beta,
    forecast_stock_prices, shift_forecast_to_actual_dates,
    calculate_prediction_errors
    )


try:
    from PySide6.QtWidgets import QApplication


    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class StockApp:
    """
    A terminal-only stock analysis and forecasting application.
    Fetches data, analyzes ratios, forecasts prices with advanced
    mean-reversion and external factor betas, prints results, and optionally
    saves reports to PDF.
    """

    def __init__(self):
        """Initialize StockApp components (fetchers, ratio analyzer, etc.)."""
        print("Initializing StockApp components...")
        self.fetcher = StockFetcher()
        self.analyzer = StockRatio()
        print("StockApp components initialized.\n")

    def fetch_stock_data(self, stock_symbol):
        """
        Fetch stock details from Yahoo Finance (via StockFetcher).
        Return a dictionary containing the stock data.
        """
        print(f"Fetching stock data for symbol: {stock_symbol}...")
        if not stock_symbol:
            print("No stock symbol provided. Aborting fetch.\n")
            return None
        try:
            stock_data = self.fetcher.fetch_stock_details(stock_symbol)
            if stock_data:
                # Remove extraneous "upgrade" text if present
                upgrade_text = (
                    "Upgrade to begin using 40 years of earnings data and get so much more.  "
                    "Build financial models with decades of earnings stats, ratios, and "
                    "valuation data — all exportable — to power your trade ideas. Upgrade"
                )
                if upgrade_text in stock_data:
                    del stock_data[upgrade_text]
                print(f"Successfully fetched fundamental data for {stock_symbol}.\n")
            else:
                print(f"Unable to fetch fundamental data for {stock_symbol}.\n")
            return stock_data
        except Exception as e:
            print(f"Failed to fetch stock details for {stock_symbol}: {e}\n")
            return None

    def fetch_stock_news(self, stock_symbol):
        """
        Fetch the latest news articles for the given stock symbol.
        Returns combined HTML for all articles or an empty string on failure.
        """
        print(f"Fetching news for {stock_symbol}...")
        if not stock_symbol:
            print("No stock symbol provided for news. Aborting.\n")
            return ""
        try:
            combined_html = self.fetcher.fetch_stock_news(stock_symbol)
            print(f"Successfully fetched news for {stock_symbol}.\n")
            return combined_html
        except Exception as e:
            print(f"Failed to fetch news for {stock_symbol}: {e}\n")
            return ""

    def analyze_stock(self, stock_data):
        """
        Analyze the stock data to compute financial ratios
        and produce a DataFrame of ratio results.
        """
        print("Analyzing stock data to compute ratios...\n")
        if not stock_data:
            print("No stock data available for analysis.\n")
            return pd.DataFrame()

        # Calculate ratios and performance
        ratios = self.analyzer.calculate_ratios(stock_data)
        performance = self.analyzer.evaluate_performance(ratios)
        ratios_table = self.analyzer.build_ratios_table(ratios, performance)

        if ratios_table is not None and not ratios_table.empty:
            print("Ratios successfully generated.\n")
        else:
            print("Ratios could not be generated or are empty.\n")
        return ratios_table

    def fetch_stock_history(self, stock_symbol, period, interval):
        """
        Fetch historical price data (typically from Yahoo Finance),
        return as a pandas DataFrame with columns [Date, Open, High, Low, Close, Volume].
        """
        print(f"Fetching historical data for {stock_symbol}...\n")
        try:
            history_df = self.fetcher.fetch_stock_history(stock_symbol, period, interval)
            if not history_df.empty:
                # Basic cleaning if needed
                history_df['Date'] = pd.to_datetime(history_df['Date'], errors = 'coerce')
                history_df['Close'] = pd.to_numeric(
                        history_df['Close'].astype(str).str.replace(',', ''),
                        errors = 'coerce'
                        )
                history_df = history_df.dropna(subset = ['Date', 'Close'])
                history_df = history_df.sort_values(by = 'Date')
                print(f"Historical data retrieved. Sample:\n{history_df.head()}\n")
            else:
                print("No historical data returned.\n")
            return history_df
        except Exception as e:
            print(f"Error fetching historical data for {stock_symbol}: {e}\n")
            return pd.DataFrame()

    def forecast_prices_advanced(
            self,
            df,
            stock_symbol,
            ratios_table,
            stock_interval,
            equation_type = "Geometric Brownian Motion External Macroeconomic Factors",
            market_ticker = "^GSPC",
            vix_ticker = "^VIX",
            tnx_ticker = "^TNX",
            forecast_days = 365
            ):
        """
        Forecast future stock prices with an advanced approach that
        includes mean reversion and external factor betas (market, interest rate, volatility).

        :param df: Historical DataFrame with columns [Date, Close]
        :param stock_symbol: The main stock symbol for fetching additional data
        :param ratios_table: DataFrame containing ratio info
        :param equation_type: Type of model (GBM, GBM with MR, or External Macro)
        :param market_ticker: Ticker for the market index (e.g., S&P 500)
        :param vix_ticker: Ticker for a volatility index (e.g., ^VIX)
        :param tnx_ticker: Ticker for interest rates (e.g., ^TNX)
        :param forecast_days: How many days out to forecast
        :return: forecast_df (DataFrame with forecasted dates and prices)
        """
        if df.empty:
            print("No historical data available for forecast.\n")
            return pd.DataFrame()

        print(f"Preparing advanced forecast for {stock_symbol} with {equation_type}...\n")

        # Calculate historical stats
        mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
        recent_price = closing_prices[-1]

        # Attempt to fetch extra data from yfinance for external factor betas
        main_ticker = stock_symbol
        total_ticker_data = None
        for _ in range(10):
            try:
                total_ticker_data = yf.download([main_ticker, market_ticker, vix_ticker, tnx_ticker], period = "1y")
                if not total_ticker_data.empty:
                    break
            except Exception:
                time.sleep(1)
                print("Retrying yfinance data download...")

        if total_ticker_data is None or total_ticker_data.empty:
            print("Could not retrieve external tickers from yfinance. Forecast will be incomplete.\n")
            return pd.DataFrame()

        # Clean the multi-level columns from yfinance
        close_data = total_ticker_data["Close"].dropna(subset = [main_ticker, market_ticker, vix_ticker, tnx_ticker])

        # Extract each series
        stock_data = close_data[main_ticker].values
        market_data = close_data[market_ticker].values
        vix_data = close_data[vix_ticker].values
        tnx_data = close_data[tnx_ticker].values

        # Compute daily returns/changes
        stock_returns = np.diff(stock_data) / stock_data[:-1]
        market_returns = np.diff(market_data) / market_data[:-1]
        vix_changes = np.diff(vix_data) / vix_data[:-1]
        interest_rate_changes = np.diff(tnx_data) / tnx_data[:-1]

        # Create Factor Returns (fake placeholders for SMB, HML, MOM)
        min_len = min(len(stock_returns), len(market_returns), len(vix_changes), len(interest_rate_changes))
        stock_returns = stock_returns[:min_len]
        market_returns = market_returns[:min_len]
        vix_changes = vix_changes[:min_len]
        interest_rate_changes = interest_rate_changes[:min_len]

        factor_returns = pd.DataFrame(
                {
                    "SMB": np.random.normal(0, 0.01, min_len),
                    "HML": np.random.normal(0, 0.01, min_len),
                    "MOM": np.random.normal(0, 0.01, min_len)
                    }
                )

        # Calculate mean reversion and betas
        eta, theta = calculate_eta_theta(stock_data[:min_len])
        beta_m = calculate_market_beta(stock_returns, market_returns)
        factor_betas = calculate_factor_betas(stock_returns, factor_returns)
        beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
        beta_v = calculate_volatility_beta(stock_returns, vix_changes)

        mean_reversion_params = {
            "eta"  : eta,
            "theta": theta
            }
        external_factors = {
            "market_beta"       : beta_m,
            "factor_betas"      : factor_betas,
            "interest_rate_beta": beta_r,
            "volatility_beta"   : beta_v
            }

        # Break out ratio subsets
        valuation_ratios = [
            'Earnings Per Share', 'P/E Ratio', 'Price-to-Sales', 'Price-to-Book',
            'EV/EBITDA', 'Revenue Per Share', 'Book Value Per Share',
            'Free Cash Flow Per Share', 'Dividend Yield'
            ]
        financial_health_ratios = [
            'Return on Equity', 'Return on Assets', 'Gross Margin', 'Operating Margin',
            'Net Profit Margin', 'Free Cash Flow Yield', 'Debt to Equity', 'Debt to Assets',
            'Cash Flow to Debt', 'Current Ratio'
            ]

        if ratios_table is None or ratios_table.empty:
            print("Ratios table is empty or not provided; forecast will ignore ratio-based adjustments.\n")
            valuation_metrics = {}
            financial_health_metrics = {}
        else:
            valuation_metrics = (
                ratios_table[ratios_table['Ratio Name'].isin(valuation_ratios)]
                .set_index('Ratio Name')['Ratio Value']
                .to_dict()
            )
            financial_health_metrics = (
                ratios_table[ratios_table['Ratio Name'].isin(financial_health_ratios)]
                .set_index('Ratio Name')['Ratio Value']
                .to_dict()
            )

            # Use mu_daily & sigma_daily as initial guesses and refine them
            n_trim = int(len(df['Close']) * 1)
            # In case 7% is too small, default to all data
            if n_trim < 1:
                n_trim = len(df['Close'])

            trimmed_closing_prices = df['Close'][-n_trim:]
            print(f"Trimming data to the last {n_trim} points (~7% of total).")

        # Generate forecast
        t_forecast, forecast_prices = forecast_stock_prices(
                equation_type,
                recent_price,
                mu_daily,
                sigma_daily,
                forecast_days,
                trimmed_closing_prices,
                stock_interval,
                valuation_metrics,
                financial_health_metrics,
                mean_reversion_params,
                external_factors,
                )
        forecast_df = shift_forecast_to_actual_dates(df, forecast_prices, forecast_days)
        print("Forecast generation complete.\n")

        return forecast_df

    def plot_forecast_results(self, df, forecast_df):
        """
        Plot historical vs. forecast data. Also calculate & plot
        prediction errors on overlapping dates. Uses mplcursors for
        interactive data tooltips if a graphical environment is present.
        """
        if df.empty or forecast_df.empty:
            print("Nothing to plot. One of the datasets is empty.\n")
            return

        # Calculate prediction errors on overlapping dates
        error_df = calculate_prediction_errors(df, forecast_df)

        # Plot original chart
        fig, (ax_price, ax_error) = plt.subplots(1, 2, figsize = (14, 5))

        # Left side: Price forecast
        ax_price.plot(df['Date'], df['Close'], label = "Historical", color = "blue")
        ax_price.plot(
                forecast_df['Date'], forecast_df['Forecasted_Close'],
                label = "Forecast", color = "red", linestyle = "--")
        ax_price.set_title("Stock Price: Historical vs. Forecast")
        ax_price.set_xlabel("Date")
        ax_price.set_ylabel("Price")
        ax_price.legend()
        ax_price.grid(True)

        if not error_df.empty:
            # Right side: Error plot
            ax_error.plot(error_df['Date'], error_df['Error'], color = "purple", lw = 2)
            ax_error.set_title("Prediction Errors")
            ax_error.set_xlabel("Date")
            ax_error.set_ylabel("Error")
            ax_error.grid(True)
        else:
            ax_error.text(
                    0.5, 0.5,
                    "No overlapping dates,\nno prediction errors to plot.",
                    horizontalalignment = 'center',
                    verticalalignment = 'center',
                    transform = ax_error.transAxes,
                    fontsize = 14
                    )

        # Optional: set up mplcursors for interactive hover
        try:
            cursor1 = mplcursors.cursor(ax_price.lines, hover = True)

            @cursor1.connect("add")
            def _(sel):
                x, y = sel.target
                sel.annotation.set_text(
                        f"Date: {pd.to_datetime(x).strftime('%Y-%m-%d')}\nPrice: {y:.2f}"
                        )

            if not error_df.empty:
                cursor2 = mplcursors.cursor(ax_error.lines, hover = True)

                @cursor2.connect("add")
                def _(sel):
                    x, y = sel.target
                    sel.annotation.set_text(
                            f"Date: {pd.to_datetime(x).strftime('%Y-%m-%d')}\nError: {y:.2f}"
                            )

        except Exception:
            print("mplcursors not available or an error occurred with interactive cursor.\n")

        # Display errors in the terminal
        if not error_df.empty:
            print("\n--- Prediction Errors ---")
            for _, row in error_df.iterrows():
                date_str = row['Date'].strftime("%Y-%m-%d")
                actual_str = f"{row['Actual_Close']:.2f}"
                forecasted_str = f"{row['Forecasted_Close']:.2f}"
                error_str = f"{row['Error']:.2f}"
                print(
                        f"Date: {date_str}, Actual: {actual_str}, "
                        f"Forecasted: {forecasted_str}, Error: {error_str}")
            print("")

        plt.tight_layout()
        plt.show()


    def display_stock_data_terminal(self, stock_symbol, stock_period, stock_interval):
        """
        Fetch fundamental data, news, analyze ratios, fetch historical,
        forecast (with advanced approach), plot results, do AI analysis,
        and optionally save PDF — all from the terminal, baby!
        """
        # 1) Fetch fundamental data
        stock_data = self.fetch_stock_data(stock_symbol)
        if not stock_data:
            print("Could not retrieve fundamental data. Exiting.\n")
            return

        # 2) Analyze
        ratios_table = self.analyze_stock(stock_data)
        if ratios_table.empty:
            print("No ratios to display.\n")
        else:
            print("---- Stock Ratios ----")
            print(ratios_table.to_string(index = False), "\n")

        # 3) Fetch historical data
        df_history = self.fetch_stock_history(stock_symbol, stock_period, stock_interval)
        if df_history.empty:
            print("No historical data, so forecasting is not possible.\n")
        else:
            # -------------------------------
            # Prompt user for forecast inputs
            # -------------------------------

            # Let's define some enumerated choices and defaults:
            equation_type_options = {
                "1": "Geometric Brownian Motion",
                "2": "Geometric Brownian Motion with Mean Reversion",
                "3": "Geometric Brownian Motion External Macroeconomic Factors"
                }
            default_eq_type_key = "3"  # index key corresponding to the default type

            # Market ticker examples (common indices)
            market_ticker_options = {
                "1": "^GSPC  (S&P 500)",
                "2": "^DJI   (Dow Jones Industrial)",
                "3": "^IXIC  (Nasdaq Composite)"
                }
            default_market_ticker_key = "1"  # ^GSPC

            # VIX ticker examples
            vix_ticker_options = {
                "1": "^VIX   (CBOE Volatility Index)",
                "2": "^VVIX  (CBOE Volatility of Volatility)"
                }
            default_vix_ticker_key = "1"  # ^VIX

            # Interest rate ticker examples (US Treasury yields)
            tnx_ticker_options = {
                "1": "^TNX   (10-year)",
                "2": "^TYX   (30-year)"
                }
            default_tnx_ticker_key = "1"  # ^TNX

            # Forecast days default
            default_forecast_days = 365

            print("\n--- Forecast Configuration ---")
            print("(Press Enter to accept the default in each category)\n")

            # 1) Equation Type
            print("Available Equation Types:")
            for k, v in equation_type_options.items():
                print(f"  {k}) {v}")
            user_eq_type = input(
                    f"\nPick an equation type [1/2/3] (default: {default_eq_type_key}): "
                    ).strip()
            if user_eq_type not in equation_type_options:
                # Use default if user just presses enter or picks something out-of-range
                user_eq_type = default_eq_type_key
            equation_type = equation_type_options[user_eq_type]
            print(f"Using: {equation_type}\n")

            # 2) Market Ticker
            print("Popular Market Index Tickers:")
            for k, v in market_ticker_options.items():
                print(f"  {k}) {v}")
            user_market_choice = input(
                    f"\nPick a market index [1/2/3] (default: {default_market_ticker_key}): "
                    ).strip()
            if user_market_choice not in market_ticker_options:
                user_market_choice = default_market_ticker_key
            # Ticker value is the first token before whitespace
            market_ticker = market_ticker_options[user_market_choice].split()[0]
            print(f"Using: {market_ticker}\n")

            # 3) Volatility Ticker (VIX)
            print("Popular Volatility Index Tickers:")
            for k, v in vix_ticker_options.items():
                print(f"  {k}) {v}")
            user_vix_choice = input(
                    f"\nPick a volatility ticker [1/2] (default: {default_vix_ticker_key}): "
                    ).strip()
            if user_vix_choice not in vix_ticker_options:
                user_vix_choice = default_vix_ticker_key
            vix_ticker = vix_ticker_options[user_vix_choice].split()[0]
            print(f"Using: {vix_ticker}\n")

            # 4) Interest Rate Ticker
            print("Common Treasury Yield Tickers:")
            for k, v in tnx_ticker_options.items():
                print(f"  {k}) {v}")
            user_tnx_choice = input(
                    f"\nPick an interest rate ticker [1/2] (default: {default_tnx_ticker_key}): "
                    ).strip()
            if user_tnx_choice not in tnx_ticker_options:
                user_tnx_choice = default_tnx_ticker_key
            tnx_ticker = tnx_ticker_options[user_tnx_choice].split()[0]
            print(f"Using: {tnx_ticker}\n")

            # 5) Forecast Days
            user_forecast_days = input(
                    f"Enter number of forecast days (default: {default_forecast_days}): "
                    ).strip()
            try:
                forecast_days = int(user_forecast_days) if user_forecast_days else default_forecast_days
            except ValueError:
                print("Invalid entry. Using default forecast days.\n")
                forecast_days = default_forecast_days

            # Summarize user picks
            print("\n----------------------------------------")
            print("      Forecast Configuration Chosen      ")
            print("----------------------------------------")
            print(f"  Equation Type  : {equation_type}")
            print(f"  Market Ticker  : {market_ticker}")
            print(f"  VIX Ticker     : {vix_ticker}")
            print(f"  Rate Ticker    : {tnx_ticker}")
            print(f"  Forecast Days  : {forecast_days}\n")

            # 4) Forecast
            forecast_df = self.forecast_prices_advanced(
                    df_history,
                    stock_symbol,
                    ratios_table,
                    stock_interval,
                    equation_type = equation_type,
                    market_ticker = market_ticker,
                    vix_ticker = vix_ticker,
                    tnx_ticker = tnx_ticker,
                    forecast_days = forecast_days,

                    )

            if not forecast_df.empty:
                # (A) Print the forecast details in the terminal
                print(f"---- Forecasted Prices for the Next {forecast_days} Days ----")
                print(forecast_df.to_string(index = False))
                print()

                # (B) Plot the forecast results in a popup window
                self.plot_forecast_results(df_history, forecast_df)

        # 5) AI analysis with news
        news_html = self.fetch_stock_news(stock_symbol)
        ai_assessment = analyze_stock_with_news(ratios_table, news_html)
        print("\n----- AI Analysis: Overall Stock Assessment -----")
        print(ai_assessment, "\n")

        # 6) Ask if user wants to save PDF
        self.prompt_save_pdf(
                stock_symbol,
                stock_data,
                ratios_table,
                ai_assessment,
                RATIO_DEFINITIONS
                )

    def prompt_save_pdf(self, stock_symbol, stock_data, ratios_table, ai_assessment, ratio_definitions):
        """Prompt the user whether to save the resulting report as a PDF."""
        while True:
            choice = input("Do you want to save the report as a PDF? (y/n): ").strip().lower()
            if choice == 'y':
                path = input("Enter the file path (e.g., /path/to/report.pdf): ").strip()
                if not path.endswith('.pdf'):
                    path += '.pdf'
                try:
                    pdf = PDFGenerator(
                            stock_symbol,
                            stock_data,
                            ratios_table,
                            ai_assessment,
                            ratio_definitions
                            )
                    pdf.generate_pdf(path)
                    print(f"PDF successfully saved: {path}\n")
                except Exception as e:
                    print(f"Failed to save PDF: {e}\n")
                break
            elif choice == 'n':
                print("Ok, not saving to PDF.\n")
                break
            else:
                print("Please enter 'y' or 'n'.")


def main():
    """
    Terminal-driven main entry point:
    - Asks for a stock symbol
    - Creates StockApp
    - Displays analysis & forecasting from the terminal
    """
    if len(sys.argv) > 1:
        # Symbol via command line argument
        stock_symbol = sys.argv[1].strip().upper()
        stock_period = sys.argv[2].strip()
        stock_interval = sys.argv[3].strip()
        app = StockApp()
        app.display_stock_data_terminal(stock_symbol, stock_period, stock_interval)
    elif GUI_AVAILABLE:
        from stock_gui import run_gui
        run_gui()
    elif "--gui" in sys.argv:
        from stock_gui import run_gui
        run_gui()


if __name__ == "__main__":
    main()