import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QDialog, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit, QFileDialog, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont

from pdf_generator import PDFGenerator
from ratio_definitions import RATIO_DEFINITIONS
from stock_analyzer.stock_statistics import calculate_statistics
from stock_fetcher import StockFetcher
from stock_ratio import StockRatio
from database_handler import DatabaseHandler
from ai_analyzer import analyze_stock_with_news
from stock_statistics import (
    calculate_statistics, forecast_stock_prices, shift_forecast_to_actual_dates,
    calculate_prediction_errors, plot_results
)
# calculate_eta_theta, calculate_factor_betas, calculate_interest_rate_beta, calculate_market_beta,
#     calculate_statistics, calculate_volatility_beta, fetch_stock_data,

# Check if PySide6 is installed to determine if GUI is available
try:
    from PySide6.QtWidgets import QApplication
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class StockApp:
    def __init__(self):
        """Initialize StockApp components."""
        print("Initializing StockApp components.")
        self.fetcher = StockFetcher()
        self.analyzer = StockRatio()
        self.db_handler = DatabaseHandler()
        print("StockApp components initialized.")

    def fetch_stock_data(self, stock_symbol):
        """Fetch stock details from DB if available, otherwise from Yahoo Finance, then save."""
        print(f"Starting stock data fetch for symbol: {stock_symbol}.")
        if not stock_symbol:
            print("No stock symbol provided. Aborting fetch.")
            return None

        # Check if data is already in the DB
        db_data = self.db_handler.fetch_stock_data(stock_symbol)
        if db_data:
            print(f"Fetched stock data for {stock_symbol} from the database.")
            return db_data

        # If not in DB, pull from Yahoo Finance
        try:
            print(f"Fetching stock data for {stock_symbol} from Yahoo Finance.")
            stock_data = self.fetcher.fetch_stock_details(stock_symbol)
            if stock_data:
                upgrade_text = ("Upgrade to begin using 40 years of earnings data and get so much more.  "
                               "Build financial models with decades of earnings stats, ratios, and "
                               "valuation data — all exportable — to power your trade ideas. Upgrade")
                for key in list(stock_data.keys()):
                    if key == upgrade_text:
                        del stock_data[key]
                self.db_handler.save_stock_data(stock_symbol, stock_data)
                print(f"Stock data for {stock_symbol} fetched from Yahoo Finance and saved to DB.")
            return stock_data
        except Exception as e:
            print(f"Failed to fetch stock details: {e}")
            return None

    def fetch_stock_news(self, stock_symbol):
        """Fetch the latest news articles for the given stock symbol from Yahoo Finance."""
        print(f"Starting news fetch for symbol: {stock_symbol}.")
        if not stock_symbol:
            print("No stock symbol provided for news fetch. Aborting.")
            return ""
        try:
            combined_html = self.fetcher.fetch_stock_news(stock_symbol)
            print(f"News articles fetched for {stock_symbol}.")
            return combined_html
        except Exception as e:
            print(f"Failed to fetch news for {stock_symbol}: {e}")
            return ""

    def analyze_stock(self, stock_data):
        """Analyze stock data and return a table of ratios."""
        print("Starting stock analysis.")
        if not stock_data:
            print("No stock data available for analysis.")
            return None
        ratios = self.analyzer.calculate_ratios(stock_data)
        print("Calculated stock ratios.")
        performance = self.analyzer.evaluate_performance(ratios)
        print("Evaluated stock performance based on ratios.")
        ratios_table = self.analyzer.build_ratios_table(ratios, performance)
        print("Built the ratios table.")
        return ratios_table

    def fetch_stock_history(self, stock_symbol):
        """Fetch historical stock data."""
        print(f"Fetching historical data for {stock_symbol}...")
        try:
            history_df = self.fetcher.fetch_stock_history(stock_symbol)
            if history_df.empty:
                print("No historical data available.")
            else:
                print("Historical data (first few rows):")
                print(history_df.head())
            return history_df
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return pd.DataFrame()

    def forecast_stock_prices(self, df, stock_symbol, ratios_table):
        """Forecast future stock prices using a stochastic model."""
        forecast_days = 120

        stock_data = fetch_stock_data(stock_symbol, forecast_days)
        price_series = stock_data['Close'].values

        # Ensure price_series is a 1D array
        if len(price_series.shape) > 1:
            price_series = price_series.flatten()

        # Calculate stock returns
        stock_returns = np.diff(price_series) / price_series[:-1]

        market_data = fetch_stock_data(stock_symbol, forecast_days)
        market_returns = np.diff(market_data['Close'].values.flatten()) / market_data['Close'].values[:-1].flatten()

        factor_returns = pd.DataFrame(
            {
                'SMB': np.random.normal(0, 0.01, len(stock_returns)),
                'HML': np.random.normal(0, 0.01, len(stock_returns)),
                'MOM': np.random.normal(0, 0.01, len(stock_returns))
            }
        )

        interest_rate_data = fetch_stock_data(stock_symbol, forecast_days)
        interest_rate_changes = np.diff(interest_rate_data['Close'].values.flatten()) / interest_rate_data['Close'].values[:-1].flatten()

        vix_data = fetch_stock_data(stock_symbol, forecast_days)
        vix_changes = np.diff(vix_data['Close'].values.flatten()) / vix_data['Close'].values[:-1].flatten()

        if df.empty:
            print("No historical data available for forecasting.")
            return pd.DataFrame()

        try:
            mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
            if mu_daily is None or sigma_daily is None:
                print("Error in calculating stock statistics.")
                return pd.DataFrame()

            recent_price = closing_prices[-1]
            forecast_days = 120

            # Define categories
            valuation_ratios = [
                'Earnings Per Share', 'P/E Ratio', 'Price-to-Sales', 'Price-to-Book',
                'EV/EBITDA', 'Revenue Per Share', 'Book Value Per Share', 'Free Cash Flow Per Share', 'Dividend Yield'
            ]

            financial_health_ratios = [
                'Return on Equity', 'Return on Assets', 'Gross Margin', 'Operating Margin',
                'Net Profit Margin', 'Free Cash Flow Yield', 'Debt to Equity', 'Debt to Assets',
                'Cash Flow to Debt', 'Current Ratio'
            ]

            # Filter the DataFrame and convert to dictionaries
            valuation_metrics = ratios_table[ratios_table['Ratio Name'].isin(valuation_ratios)].set_index('Ratio Name')['Ratio Value'].to_dict()
            financial_health_metrics = ratios_table[ratios_table['Ratio Name'].isin(financial_health_ratios)].set_index('Ratio Name')['Ratio Value'].to_dict()

            # Calculate necessary parameters
            eta, theta = calculate_eta_theta(price_series)
            beta_m = calculate_market_beta(stock_returns, market_returns)
            factor_betas = calculate_factor_betas(stock_returns, factor_returns)
            beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
            beta_v = calculate_volatility_beta(stock_returns, vix_changes)

            # Assign calculated values to structured variables
            mean_reversion_params = {
                "eta": eta,
                "theta": theta
            }

            external_factors = {
                "market_beta": beta_m,
                "factor_betas": factor_betas,
                "interest_rate_beta": beta_r,
                "volatility_beta": beta_v
            }

            t_forecast, forecast_prices = forecast_stock_prices(
                recent_price, mu_daily, sigma_daily, forecast_days, valuation_metrics,
                financial_health_metrics, mean_reversion_params, external_factors
            )

            forecast_df = shift_forecast_to_actual_dates(df, forecast_prices, forecast_days)
            forecast_dates = forecast_df['Date'].tolist()

            # Plot forecast
            plt.figure(figsize=(12, 6))
            plt.plot(df['Date'], df['Close'], label="Historical Prices", color="blue", lw=2)
            plt.plot(forecast_dates, forecast_prices, label="Forecast Prices", color="red", lw=2, linestyle="--")
            plt.title("Stock Price Forecast")
            plt.xlabel("Date")
            plt.ylabel("Stock Price")
            plt.legend()
            plt.grid(True)
            plt.gcf().autofmt_xdate()
            plt.tight_layout()
            plt.show()

            print("\nForecasted Prices:")
            for day, price in zip(range(1, forecast_days + 1), forecast_prices):
                print(f"Day {day}: {price:.2f}")

            self.display_prediction_errors(calculate_prediction_errors(df, forecast_df))
            return forecast_prices
        except Exception as e:
            print(f"Error forecasting stock prices: {e}")
            return pd.DataFrame()

    def display_prediction_errors(self, error_df):
        """Display the prediction errors in a formatted table in the terminal."""
        if not error_df.empty:
            print("\n--- Prediction Errors ---")
            print(f"{'Date':<15}{'Actual Price':<15}{'Forecasted Price':<20}{'Error':<10}")
            print("-" * 60)
            for _, row in error_df.iterrows():
                date_str = row['Date'].strftime("%Y-%m-%d")
                actual_str = f"{row['Actual_Close']:.2f}"
                forecasted_str = f"{row['Forecasted_Close']:.2f}"
                error_str = f"{row['Error']:.2f}"
                print(f"{date_str:<15}{actual_str:<15}{forecasted_str:<20}{error_str:<10}")
        else:
            print("\nNo prediction errors to show.")

    def display_stock_data_terminal(self, stock_symbol):
        """Fetch and display stock data in the terminal, including historical and forecast analysis."""
        print(f"Displaying stock data for symbol: {stock_symbol} in terminal mode.")
        stock_data = self.fetch_stock_data(stock_symbol)
        if not stock_data:
            print("Unable to retrieve stock data. Ensure VPN is ON.")
            return

        # Print raw stock data
        print("\n--- Stock Details ---")
        for key, value in stock_data.items():
            print(f"{key}: {value}")

        # Analyze the stock
        ratios_table = self.analyze_stock(stock_data)
        if ratios_table is not None and not ratios_table.empty:
            print("\n--- Stock Ratios Ordered by Importance ---")
            print(ratios_table)

        # Fetch and display stock history
        history_df = self.fetch_stock_history(stock_symbol)
        if not history_df.empty:
            self.forecast_stock_prices(history_df, stock_symbol, ratios_table)

        # Use AI to analyze the ratios and news
        combined_articles_html = self.fetch_stock_news(stock_symbol)
        print("\n--- AI Analysis: Overall Stock Assessment ---")
        ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
        print(ai_assessment)

        self.prompt_save_pdf(stock_symbol, stock_data, ratios_table, ai_assessment, RATIO_DEFINITIONS)

    def prompt_save_pdf(self, stock_symbol, stock_data, ratios_table, ai_assessment, ratio_definitions):
        """Prompts the user to decide whether to save the report as a PDF."""
        while True:
            choice = input("\nDo you want to save the report as a PDF? (y/n): ").strip().lower()
            if choice == 'y':
                save_path = input("Enter the full path where you want to save the PDF (e.g., /path/to/report.pdf): ").strip()
                if not save_path.endswith('.pdf'):
                    save_path += '.pdf'
                try:
                    pdf = PDFGenerator(stock_symbol, stock_data, ratios_table, ai_assessment, ratio_definitions)
                    pdf.generate_pdf(save_path)
                    print(f"Report successfully saved as '{save_path}'.")
                except Exception as e:
                    print(f"Failed to save PDF: {e}")
                break
            elif choice == 'n':
                print("User opted not to save the report as a PDF.")
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")


def main():
    """Entry point for the application."""
    if GUI_AVAILABLE and "--gui" in sys.argv:
        from stock_gui import run_gui
        run_gui()
    else:
        stock_symbol = input("Enter the stock symbol: ").upper()
        app = StockApp()
        app.display_stock_data_terminal(stock_symbol)


if __name__ == "__main__":
    main()