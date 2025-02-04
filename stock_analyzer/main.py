import sys
import pandas as pd
import matplotlib.pyplot as plt

from ratio_definitions import RATIO_DEFINITIONS
from pdf_generator import PDFGenerator
from stock_fetcher import StockFetcher
from stock_ratio import StockRatio
from database_handler import DatabaseHandler
from ai_analyzer import analyze_stock_with_news
from stock_statistics import calculate_statistics, forecast_stock_prices

try:
    # Check if PySide6 is installed to determine if GUI is available
    from PySide6.QtWidgets import QApplication

    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class StockApp:
    def __init__(self):
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

    def forecast_stock_prices(self, df):
        """Forecast future stock prices using a stochastic model."""
        if df.empty:
            print("No historical data available for forecasting.")
            return pd.DataFrame()

        try:
            mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
            if mu_daily is None or sigma_daily is None:
                print("Error in calculating stock statistics.")
                return pd.DataFrame()

            recent_price = closing_prices[-1]
            forecast_days = 30
            t_forecast, forecast_prices = forecast_stock_prices(recent_price, mu_daily, sigma_daily, forecast_days)

            last_date = df['Date'].max()
            forecast_dates = [last_date + pd.Timedelta(days = i) for i in range(1, forecast_days + 1)]
            historical_dates = df['Date']

            # Plot forecast
            plt.figure(figsize = (12, 6))
            plt.plot(historical_dates, df['Close'], label = "Historical Prices", color = "blue", lw = 2)
            plt.plot(forecast_dates, forecast_prices, label = "Forecast Prices", color = "red", lw = 2, linestyle = "--")
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

            return forecast_prices
        except Exception as e:
            print(f"Error forecasting stock prices: {e}")
            return pd.DataFrame()

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
            self.forecast_stock_prices(history_df)

        # Use AI to analyze the ratios and news
        combined_articles_html = self.fetch_stock_news(stock_symbol)
        print("\n--- AI Analysis: Overall Stock Assessment ---")
        ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
        print(ai_assessment)

    def prompt_save_pdf(self, stock_symbol, stock_data, ratios_table, ai_assessment, ratio_definitions):
        """
        Prompts the user to decide whether to save the report as a PDF.
        """
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
    """
    Entry point for the application.
    """
    if GUI_AVAILABLE and "--gui" in sys.argv:
        from stock_gui import run_gui
        run_gui()
    else:
        stock_symbol = input("Enter the stock symbol: ").upper()
        app = StockApp()
        app.display_stock_data_terminal(stock_symbol)

if __name__ == "__main__":
    main()