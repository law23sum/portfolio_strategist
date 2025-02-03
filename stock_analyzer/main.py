# main.py

import sys
import pandas as pd
from ratio_definitions import RATIO_DEFINITIONS
from pdf_generator import PDFGenerator
from stock_fetcher import StockFetcher
from stock_analyzer import StockAnalyzer
from database_handler import DatabaseHandler
from stock_news_fetcher import StockNewsFetcher
from ai_analyzer import analyze_stock_with_news


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
        self.analyzer = StockAnalyzer()
        self.db_handler = DatabaseHandler()
        self.news_fetcher = StockNewsFetcher()  # Initialize the News Fetcher
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
            combined_html = self.news_fetcher.fetch_stock_news(stock_symbol)
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

    def display_stock_data_terminal(self, stock_symbol):
        """Fetch and display stock data in the terminal, including fresh news."""
        print(f"Displaying stock data for symbol: {stock_symbol} in terminal mode.")
        stock_data = self.fetch_stock_data(stock_symbol)
        if not stock_data:
            print("Unable to retrieve stock data.")
            print("Ensure VPN is ON.")
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
                print(f"\nRatio: {ratio_name}")
                print(f"   Definition: {definition}")
                print(f"   Formula: {formula}")

        # Use AI to analyze the ratios and news
        print("\n--- AI Analysis: Overall Stock Assessment ---")
        combined_articles_html = self.fetch_stock_news(stock_symbol)
        ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
        print(ai_assessment)

        # Prompt user to save as PDF
        self.prompt_save_pdf(stock_symbol, stock_data, ratios_table, ai_assessment, RATIO_DEFINITIONS)

        # Close Selenium driver for news (optional best practice)
        print("Closing news fetcher driver.")
        self.news_fetcher.close()

    def prompt_save_pdf(self, stock_symbol, stock_data, ratios_table, ai_assessment, ratio_definitions):
        """
        Prompts the user to decide whether to save the report as a PDF.
        If yes, asks for the directory to save the PDF.
        """
        while True:
            choice = input("\nDo you want to save the report as a PDF? (y/n): ").strip().lower()
            if choice == 'y':
                print("User opted to save the report as a PDF.")
                # Prompt for save location
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

    def start_terminal_mode(self):
        """Prompt user for a symbol and display data in the terminal."""
        stock_symbol = input("Enter the stock symbol: ").upper()
        print(f"User entered symbol: {stock_symbol}.")
        self.display_stock_data_terminal(stock_symbol)


def main():
    """
    Entry point for the application.
    If --gui is in sys.argv and GUI_AVAILABLE, launch the GUI. Otherwise, terminal mode.
    """
    print("Starting the Stock Application.")
    stock_app = StockApp()
    if GUI_AVAILABLE and "--gui" in sys.argv:
        print("GUI mode selected. Launching GUI.")
        # Import and launch GUI
        from stock_gui import run_gui
        run_gui()
    else:
        print("Terminal mode selected. Running in terminal mode.")
        stock_app.start_terminal_mode()


if __name__ == "__main__":
    main()