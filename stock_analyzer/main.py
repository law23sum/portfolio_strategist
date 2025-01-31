# main.py

import sys
import pandas as pd


try:
    # Check if PySide6 is installed to determine if GUI is available
    from PySide6.QtWidgets import QApplication


    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from ratio_definitions import RATIO_DEFINITIONS
from stock_fetcher import StockFetcher
from stock_analyzer import StockAnalyzer
from database_handler import DatabaseHandler
from stock_news_fetcher import StockNewsFetcher
from ai_analyzer import analyze_stock_with_news


class StockApp:
    def __init__(self):
        self.fetcher = StockFetcher()
        self.analyzer = StockAnalyzer()
        self.db_handler = DatabaseHandler()
        self.news_fetcher = StockNewsFetcher()  # Initialize your News Fetcher

    def fetch_stock_data(self, stock_symbol):
        """Fetch stock details from DB if available, otherwise from Yahoo Finance, then save."""
        if not stock_symbol:
            return None

        # Check if data is already in the DB
        db_data = self.db_handler.fetch_stock_data(stock_symbol)
        if db_data:
            print(f"Fetched stock data for {stock_symbol} from the database.")
            return db_data

        # If not in DB, pull from Yahoo Finance
        try:
            stock_data = self.fetcher.fetch_stock_details(stock_symbol)
            if stock_data:
                self.db_handler.save_stock_data(stock_symbol, stock_data)
                print(f"Fetched stock data for {stock_symbol} from Yahoo Finance and saved to DB.")
            return stock_data
        except Exception as e:
            print(f"Failed to fetch stock details: {e}")
            return None

    def fetch_stock_news(self, stock_symbol):
        """Fetch the latest news articles for the given stock symbol from Yahoo Finance."""
        if not stock_symbol:
            return ""

        try:
            combined_html = self.news_fetcher.fetch_stock_news(stock_symbol)
            return combined_html
        except Exception as e:
            print(f"Failed to fetch news for {stock_symbol}: {e}")
            return ""

    def analyze_stock(self, stock_data):
        """Analyze stock data and return a table of ratios."""
        if not stock_data:
            return None

        ratios = self.analyzer.calculate_ratios(stock_data)
        performance = self.analyzer.evaluate_performance(ratios)
        return self.analyzer.build_ratios_table(ratios, performance)

    def display_stock_data_terminal(self, stock_symbol):
        """Fetch and display stock data in the terminal, including some fresh news."""
        stock_data = self.fetch_stock_data(stock_symbol)
        if not stock_data:
            print("Unable to retrieve stock data.")
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
        else:
            print("Error: Stock analysis failed.")

        # Display Ratio Definitions
        if ratios_table is not None and 'Ratio Name' in ratios_table.columns:
            print("\n--- Ratio Definitions ---")
            for ratio_name in ratios_table['Ratio Name']:
                definition = RATIO_DEFINITIONS.get(ratio_name, {}).get('Definition', 'N/A')
                formula = RATIO_DEFINITIONS.get(ratio_name, {}).get('Formula', 'N/A')
                print(f"\n🔍 {ratio_name}:")
                print(f"   Definition: {definition}")
                print(f"   Formula: {formula}")

        # Use AI to analyze the ratios and news
        print("\n--- AI Analysis: Overall Stock Assessment ---")
        combined_articles_html = self.fetch_stock_news(stock_symbol)
        ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
        print(ai_assessment)

        # Optionally, display news headlines and links if needed
        # Since the updated fetch_stock_news returns combined_html, you may need to parse it again
        # to extract headlines and links if required.

        # Close Selenium driver for news (optional best practice)
        self.news_fetcher.close()

    def start_terminal_mode(self):
        """Prompt user for a symbol and display data in the terminal."""
        stock_symbol = input("Enter the stock symbol: ").upper()
        self.display_stock_data_terminal(stock_symbol)


def main():
    """
    Entry point for the application.
    If --gui is in sys.argv and GUI_AVAILABLE, launch the GUI. Otherwise, terminal mode.
    """
    if GUI_AVAILABLE and "--gui" in sys.argv:
        # Import and launch GUI
        from stock_gui import run_gui
        run_gui()
    else:
        # Default to terminal mode
        stock_app = StockApp()
        stock_app.start_terminal_mode()


if __name__ == "__main__":
    main()