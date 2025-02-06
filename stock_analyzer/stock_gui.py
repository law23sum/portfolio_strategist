import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import yfinance as yf
import mplcursors

from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit, QFileDialog, QMessageBox, QStackedWidget
    )
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont

from pdf_generator import PDFGenerator
from main import StockApp, RATIO_DEFINITIONS
from stock_analyzer.stock_definitions import MACRO_ECONOMIC_INDICATORS
from stock_fetcher import StockFetcher
from ai_analyzer import analyze_stock_with_news
from stock_statistics import (
    calculate_eta_theta, calculate_factor_betas, calculate_interest_rate_beta, calculate_market_beta,
    calculate_statistics, calculate_volatility_beta, forecast_stock_prices,
    shift_forecast_to_actual_dates, calculate_prediction_errors, plot_results
    )


# --- Utility class to capture print statements ---
class EmittingStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


# --- Worker to fetch stock data and perform analysis ---
class StockWorker(QThread):
    progress = Signal(int)
    finished = Signal(dict, pd.DataFrame, str)  # Emits stock_data, ratios_table, ai_assessment

    def __init__(self, stock_symbol):
        super().__init__()
        self.stock_symbol = stock_symbol
        self.stock_app = StockApp()
        self.fetcher = StockFetcher()

    def run(self):
        try:
            print(f"Starting data fetch for {self.stock_symbol}")
            self.progress.emit(20)
            stock_data = self.stock_app.fetch_stock_data(self.stock_symbol)
            print(f"Stock data fetched: {bool(stock_data)}")
            self.progress.emit(50)

            ratios_table = None
            ai_assessment = ""
            if stock_data:
                ratios_table = self.stock_app.analyze_stock(stock_data)
                print(f"Ratios table generated: {ratios_table is not None and not ratios_table.empty}")
                self.progress.emit(80)
                combined_articles_html = self.stock_app.fetch_stock_news(self.stock_symbol)
                print(f"News articles fetched: {bool(combined_articles_html)}")
                self.progress.emit(90)
                ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
                print(f"AI assessment generated: {bool(ai_assessment)}")
            self.progress.emit(100)
            self.finished.emit(stock_data, ratios_table, ai_assessment)
        except Exception as e:
            print(f"Error in StockWorker: {e}")
            self.finished.emit({}, pd.DataFrame(), f"Error during fetching and analysis: {e}")


# --- Worker to fetch historical data and prepare it for forecasting ---
class ForecastWorker(QThread):
    finished = Signal(pd.DataFrame)

    def __init__(self, stock_symbol):
        super().__init__()
        self.stock_symbol = stock_symbol
        self.fetcher = StockFetcher()

    def run(self):
        try:
            # Fetch raw historical data
            history_data = self.fetcher.fetch_stock_history(self.stock_symbol)

            # Create a DataFrame from the raw data
            df = pd.DataFrame(history_data)

            if not df.empty:
                # Convert 'Date' column to datetime
                df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')

                # Convert 'Close' column to numeric (convert to string first to allow .str.replace)
                df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')

                # Drop rows with invalid 'Date' or 'Close'
                before_drop = len(df)
                df = df.dropna(subset = ['Date', 'Close'])
                after_drop = len(df)
                # print(f"Dropped {before_drop - after_drop} rows; DataFrame now has {after_drop} rows.")
            else:
                print("No historical data fetched.")

            self.finished.emit(df)
        except Exception as e:
            print(f"Forecast Worker Error: {e}")
            self.finished.emit(pd.DataFrame())


# --- Home Page ---
class HomePage(QWidget):
    def __init__(self, navigate_to_analysis):
        super().__init__()
        self.navigate_to_analysis = navigate_to_analysis

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        welcome_label = QLabel("Welcome to The Portfolio Strategist")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Helvetica", 26))
        layout.addWidget(welcome_label)

        description = QLabel("Analyze stock data, view AI-driven insights, and generate comprehensive PDF reports.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setFont(QFont("Helvetica", 15))
        layout.addWidget(description)

        navigate_button = QPushButton("Get Started")
        navigate_button.setFont(QFont("Helvetica", 18))
        navigate_button.setFixedSize(200, 50)
        navigate_button.clicked.connect(self.navigate_to_analysis)
        layout.addWidget(navigate_button)

        self.setLayout(layout)


# --- Definitions Page ---
class DefinitionsPage(QWidget):
    def __init__(self, navigate_back):
        super().__init__()
        self.navigate_back = navigate_back

        layout = QVBoxLayout()

        title = QLabel("Financial Definitions")
        title.setFont(QFont("Helvetica", 22))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.definitions_table = QTableWidget()
        layout.addWidget(self.definitions_table)

        back_button = QPushButton("Back")
        back_button.setFont(QFont("Helvetica", 15))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def populate_definitions(self, definitions_df):
        self.definitions_table.setRowCount(definitions_df.shape[0])
        self.definitions_table.setColumnCount(definitions_df.shape[1])
        self.definitions_table.setHorizontalHeaderLabels(definitions_df.columns.astype(str))
        for row in range(definitions_df.shape[0]):
            for col in range(definitions_df.shape[1]):
                item = QTableWidgetItem(str(definitions_df.iloc[row, col]))
                item.setFont(QFont("Helvetica", 15))
                self.definitions_table.setItem(row, col, item)


class ForecastPage(QWidget):
    def __init__(self, navigate_back):
        super().__init__()
        self.current_history_df = pd.DataFrame()
        self.navigate_back = navigate_back
        self.error_df = pd.DataFrame()  # To store prediction errors for later use

        # Main layout for the widget
        main_layout = QVBoxLayout()

        # **************************
        # Top Layout: Two Interactive Charts
        # **************************
        charts_layout = QHBoxLayout()

        # --- Original Chart (Historical & Forecast Prices) ---
        self.figure_original, self.ax_original = plt.subplots(figsize = (6, 5))
        self.canvas_original = FigureCanvas(self.figure_original)
        self.canvas_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Connect double-click for expansion
        self.canvas_original.mpl_connect("button_press_event", self.on_original_chart_click)
        charts_layout.addWidget(self.canvas_original)

        # --- Error Chart (Prediction Errors) ---
        self.figure_error, self.ax_error = plt.subplots(figsize = (6, 5))
        self.canvas_error = FigureCanvas(self.figure_error)
        self.canvas_error.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Connect double-click for expansion
        self.canvas_error.mpl_connect("button_press_event", self.on_error_chart_click)
        charts_layout.addWidget(self.canvas_error)

        main_layout.addLayout(charts_layout)

        # **************************
        # Bottom Layout: Two Tables
        # **************************
        tables_layout = QHBoxLayout()

        # --- Left Table: Error Details ---
        self.error_table = QTableWidget()
        self.error_table.setFont(QFont("Helvetica", 13))
        tables_layout.addWidget(self.error_table)

        # --- Right Table: Future Predicted Prices ---
        self.forecast_table = QTableWidget()
        self.forecast_table.setFont(QFont("Helvetica", 13))
        tables_layout.addWidget(self.forecast_table)

        main_layout.addLayout(tables_layout)

        # **************************
        # Back Button at the Bottom
        # **************************
        back_button = QPushButton("Back to Analysis")
        back_button.setFont(QFont("Helvetica", 15))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back)
        main_layout.addWidget(back_button)

        self.setLayout(main_layout)

        # Initialize mplcursors for interactivity
        self.cursor_original = None
        self.cursor_error = None

    def on_original_chart_click(self, event):
        """Double-click to expand the original forecast chart in full screen."""
        if event.dblclick:
            self.show_fullscreen_chart("original")

    def on_error_chart_click(self, event):
        """Double-click to expand the error chart in full screen."""
        if event.dblclick:
            self.show_fullscreen_chart("error")

    def show_fullscreen_chart(self, chart_type):
        """Display the selected chart in a full-screen dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Expanded {chart_type.capitalize()} Chart")
        dialog.setWindowState(dialog.windowState() | Qt.WindowFullScreen)
        layout = QVBoxLayout(dialog)

        if chart_type == "original":
            # Re-use the original figure
            canvas = FigureCanvas(self.figure_original)
        else:
            # Re-use the error figure
            canvas = FigureCanvas(self.figure_error)

        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)
        dialog.exec_()

    def populate_forecast(self, df, ratios_table, stock_symbol, equation_type):
        if df.empty:
            print("No historical data available for forecast, sweetheart.")
            QMessageBox.warning(self, "No Data", "No historical data available for forecast.")
            return

        try:
            print("Preparing forecast data...")
            # Preprocess the DataFrame: ensure proper datetime and numeric types
            df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
            df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')
            df = df.dropna(subset = ['Date', 'Close']).sort_values(by = 'Date')

            # Calculate statistics and generate the forecast
            mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
            recent_price = closing_prices[-1]
            forecast_days = 365

            # ===================================================
            # Inserted Middle Section
            # ===================================================
            main_ticker = stock_symbol  # Your main ticker
            market_ticker = "^GSPC"  # S&P 500
            vix_ticker = "^VIX"  # Volatility Index
            tnx_ticker = "^TNX"  # 10-Year Treasury Yield

            # Download all tickers in one go (over the past year for demonstration)
            data = yf.download([main_ticker, market_ticker, vix_ticker, tnx_ticker], period = "1y")

            # Align data by dropping rows that have NA in any of these tickers
            close_data = data["Close"].dropna(subset = [main_ticker, market_ticker, vix_ticker, tnx_ticker])

            # Extract each series
            stock_data = close_data[main_ticker]
            market_data = close_data[market_ticker]
            vix_data = close_data[vix_ticker]
            tnx_data = close_data[tnx_ticker]

            # Convert to numpy arrays
            price_series = stock_data.values
            market_prices = market_data.values
            vix_prices = vix_data.values
            tnx_prices = tnx_data.values

            # Compute daily returns/changes
            stock_returns = np.diff(price_series) / price_series[:-1]
            market_returns = np.diff(market_prices) / market_prices[:-1]
            vix_changes = np.diff(vix_prices) / vix_prices[:-1]
            interest_rate_changes = np.diff(tnx_prices) / tnx_prices[:-1]

            # Create Factor Returns (Placeholder)
            min_len = len(stock_returns)
            factor_returns = pd.DataFrame(
                    {
                        "SMB": np.random.normal(0, 0.01, min_len),
                        "HML": np.random.normal(0, 0.01, min_len),
                        "MOM": np.random.normal(0, 0.01, min_len)
                        }
                    )

            # Calculate eta and theta
            eta, theta = calculate_eta_theta(price_series)

            # Calculate betas
            beta_m = calculate_market_beta(stock_returns, market_returns)
            factor_betas = calculate_factor_betas(stock_returns, factor_returns)
            beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
            beta_v = calculate_volatility_beta(stock_returns, vix_changes)

            # Prepare mean reversion and external factors
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

            t_forecast, forecast_prices = forecast_stock_prices(
                    equation_type,
                    recent_price, mu_daily, sigma_daily, forecast_days,
                    valuation_metrics, financial_health_metrics,
                    mean_reversion_params, external_factors
                    )

            forecast_df = shift_forecast_to_actual_dates(df, forecast_prices, forecast_days)
            forecast_dates = forecast_df['Date'].tolist()

            # --- Update the Original Chart ---
            self.ax_original.clear()
            historical_line, = self.ax_original.plot(df['Date'], df['Close'], label = "Historical Prices", color = "blue", lw = 2, linestyle = "--")
            forecast_line, = self.ax_original.plot(
                    forecast_dates, forecast_prices, label = "Forecast Prices", color = "red", lw = 2,
                    linestyle = "--")
            self.ax_original.set_title("Stock Price Forecast")
            self.ax_original.set_xlabel("Date")
            self.ax_original.set_ylabel("Price")
            self.ax_original.legend()
            self.ax_original.grid(True)
            self.canvas_original.draw()
            print("Original forecast plot generated successfully.")

            # Add interactive cursor to the original chart
            if self.cursor_original:
                self.cursor_original.remove()
            self.cursor_original = mplcursors.cursor([historical_line, forecast_line], hover = True)
            self.cursor_original.connect("add", lambda sel: sel.annotation.set_text(f"Date: {sel.target[0]:%Y-%m-%d}\nPrice: {sel.target[1]:.2f}"))

            # --- Calculate Prediction Errors ---
            error_df = calculate_prediction_errors(df, forecast_df)
            self.error_df = error_df  # Save for table display

            # --- Update the Error Chart ---
            self.ax_error.clear()
            if not error_df.empty:
                error_line, = self.ax_error.plot(
                        error_df['Date'], error_df['Error'],
                        label = "Prediction Error", color = "purple", lw = 2, linestyle = "--"
                        )
                self.ax_error.set_title("Prediction Errors")
                self.ax_error.set_xlabel("Date")
                self.ax_error.set_ylabel("Error")
                self.ax_error.legend()
                self.ax_error.grid(True)

                # Add interactive cursor to the error chart
                if self.cursor_error:
                    self.cursor_error.remove()
                self.cursor_error = mplcursors.cursor(error_line, hover = True)
                self.cursor_error.connect("add", lambda sel: sel.annotation.set_text(f"Date: {sel.target[0]:%Y-%m-%d}\nError: {sel.target[1]:.2f}"))
            else:
                self.ax_error.text(
                        0.5, 0.5,
                        "No prediction errors to display...",
                        horizontalalignment = 'center', verticalalignment = 'center',
                        transform = self.ax_error.transAxes, fontsize = 15
                        )
            self.canvas_error.draw()

            # --- Update the Forecast Table (Right Table) ---
            overlap = len(error_df) if not error_df.empty else 0
            future_dates = forecast_dates[overlap:]
            future_prices = forecast_prices[overlap:]

            self.forecast_table.clear()
            self.forecast_table.setRowCount(len(future_dates))
            self.forecast_table.setColumnCount(2)
            self.forecast_table.setHorizontalHeaderLabels(["Date", "Predicted Price"])
            for i, date in enumerate(future_dates):
                date_str = date.strftime("%Y-%m-%d")
                price_str = f"{future_prices[i]:.2f}"
                date_item = QTableWidgetItem(date_str)
                price_item = QTableWidgetItem(price_str)
                date_item.setFont(QFont("Helvetica", 13))
                price_item.setFont(QFont("Helvetica", 13))
                self.forecast_table.setItem(i, 0, date_item)
                self.forecast_table.setItem(i, 1, price_item)
            self.forecast_table.resizeColumnsToContents()

            # --- Update the Error Table (Left Table) ---
            if not error_df.empty:
                self.error_table.show()
                self.error_table.clear()
                self.error_table.setRowCount(len(error_df))
                self.error_table.setColumnCount(4)
                self.error_table.setHorizontalHeaderLabels(["Date", "Actual Price", "Forecasted Price", "Error"])
                for idx, row in error_df.iterrows():
                    date_str = row['Date'].strftime("%Y-%m-%d")
                    actual_str = f"{row['Actual_Close']:.2f}"
                    forecasted_str = f"{row['Forecasted_Close']:.2f}"
                    error_str = f"{row['Error']:.2f}"
                    date_item = QTableWidgetItem(date_str)
                    actual_item = QTableWidgetItem(actual_str)
                    forecasted_item = QTableWidgetItem(forecasted_str)
                    error_item = QTableWidgetItem(error_str)
                    date_item.setFont(QFont("Helvetica", 13))
                    actual_item.setFont(QFont("Helvetica", 13))
                    forecasted_item.setFont(QFont("Helvetica", 13))
                    error_item.setFont(QFont("Helvetica", 13))
                    self.error_table.setItem(idx, 0, date_item)
                    self.error_table.setItem(idx, 1, actual_item)
                    self.error_table.setItem(idx, 2, forecasted_item)
                    self.error_table.setItem(idx, 3, error_item)
                self.error_table.resizeColumnsToContents()
            else:
                self.error_table.hide()
                print("No prediction errors to show...")

        except Exception as e:
            print(f"Error in forecast plotting: {e}")
            QMessageBox.critical(self, "Error", f"Forecasting failed: {e}")

    def show_error_plot(self):
        if not self.error_df.empty:
            plot_results(self.error_df)
        else:
            QMessageBox.information(self, "No Data", "No overlapping dates to plot prediction errors.")


# --- Main GUI ---
class StockGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Portfolio Strategist")
        self.setGeometry(100, 100, 1600, 900)

        self.stacked_widget = QStackedWidget()

        # Initialize pages
        self.home_page = HomePage(self.show_analysis_page)
        self.analysis_page = self.create_analysis_page()
        self.definitions_page = DefinitionsPage(self.show_previous_page)
        self.forecast_page = ForecastPage(self.show_previous_page)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.definitions_page)
        self.stacked_widget.addWidget(self.forecast_page)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        self.init_logging()

        # Internal state variables
        self.current_stock_symbol = ""
        self.current_stock_data = {}
        self.current_ratios_table = pd.DataFrame()
        self.current_ai_assessment = ""
        self.current_history_df = pd.DataFrame()

    def create_analysis_page(self):
        page = QWidget()
        page_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        self.input_label = QLabel("Enter Stock Symbol:")
        self.input_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(self.input_label)

        self.stock_input = QLineEdit()
        self.stock_input.setFont(QFont("Helvetica", 13))
        left_layout.addWidget(self.stock_input)

        self.fetch_button = QPushButton("Fetch Stock Data")
        self.fetch_button.setFont(QFont("Helvetica", 15))
        self.fetch_button.setFixedHeight(40)
        self.fetch_button.clicked.connect(self.start_fetching)
        left_layout.addWidget(self.fetch_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFont(QFont("Helvetica", 13))
        left_layout.addWidget(self.progress_bar)

        stock_details_label = QLabel("Stock Details")
        stock_details_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(stock_details_label)

        self.stock_table = QTableWidget()
        left_layout.addWidget(self.stock_table)

        ratios_table_label = QLabel("Stock Ratios")
        ratios_table_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(ratios_table_label)

        self.ratios_table = QTableWidget()
        left_layout.addWidget(self.ratios_table)

        self.logs_label = QLabel("Logs")
        self.logs_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(self.logs_label)

        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Courier", 13))
        left_layout.addWidget(self.logs_display)

        page_layout.addLayout(left_layout, 2)

        right_layout = QVBoxLayout()
        self.ai_label = QLabel("AI Analysis: Summary Stock Assessment")
        self.ai_label.setAlignment(Qt.AlignCenter)
        self.ai_label.setFont(QFont("Helvetica", 18))
        right_layout.addWidget(self.ai_label)

        self.ai_display = QTextEdit()
        self.ai_display.setReadOnly(True)
        self.ai_display.setFont(QFont("Helvetica", 15))
        right_layout.addWidget(self.ai_display)

        self.save_pdf_button = QPushButton("Save Report as PDF")
        self.save_pdf_button.setFont(QFont("Helvetica", 15))
        self.save_pdf_button.setFixedHeight(40)
        self.save_pdf_button.clicked.connect(self.save_pdf)
        self.save_pdf_button.setEnabled(False)
        right_layout.addWidget(self.save_pdf_button)

        self.view_definitions_button = QPushButton("View Ratio Definitions")
        self.view_definitions_button.setFont(QFont("Helvetica", 15))
        self.view_definitions_button.setFixedHeight(40)
        self.view_definitions_button.clicked.connect(self.show_definitions_page)
        right_layout.addWidget(self.view_definitions_button)

        equation_label = QLabel("Select Forecasting Model:")
        equation_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(equation_label)
        self.equation_dropdown = QComboBox()
        self.equation_dropdown.setFont(QFont("Helvetica", 13))
        self.equation_dropdown.addItems(
                ["GeometricBrownianMotion", "GeometricBrownianMotionwithMeanReversion", "GeometricBrownianMotionExternalMacroeconomicFactors"])
        left_layout.addWidget(self.equation_dropdown)

        market_ticker_label = QLabel("Market Ticker:")
        market_ticker_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(market_ticker_label)
        self.market_ticker_dropdown = QComboBox()
        self.market_ticker_dropdown.setFont(QFont("Helvetica", 13))
        self.market_ticker_dropdown.addItems(["^GSPC", "^DJI", "^IXIC"])
        left_layout.addWidget(self.market_ticker_dropdown)

        vix_ticker_label = QLabel("Volatility Ticker:")
        vix_ticker_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(vix_ticker_label)
        self.vix_ticker_dropdown = QComboBox()
        self.vix_ticker_dropdown.setFont(QFont("Helvetica", 13))
        self.vix_ticker_dropdown.addItems(["^VIX"])
        left_layout.addWidget(self.vix_ticker_dropdown)

        tnx_ticker_label = QLabel("Interest Rate Ticker:")
        tnx_ticker_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(tnx_ticker_label)
        self.tnx_ticker_dropdown = QComboBox()
        self.tnx_ticker_dropdown.setFont(QFont("Helvetica", 13))
        self.tnx_ticker_dropdown.addItems(["^TNX", "^TYX"])
        left_layout.addWidget(self.tnx_ticker_dropdown)

        self.view_forecast_button = QPushButton("View Stock Forecast")
        self.view_forecast_button.setFont(QFont("Helvetica", 15))
        self.view_forecast_button.setFixedHeight(40)
        self.view_forecast_button.setEnabled(False)
        self.view_forecast_button.clicked.connect(self.show_forecast_page)
        left_layout.addWidget(self.view_forecast_button)

        self.back_home_button = QPushButton("Back to Home")
        self.back_home_button.setFont(QFont("Helvetica", 15))
        self.back_home_button.setFixedHeight(40)
        self.back_home_button.clicked.connect(self.show_home_page)
        right_layout.addWidget(self.back_home_button)

        page_layout.addLayout(right_layout, 3)
        page.setLayout(page_layout)
        return page

    def show_analysis_page(self):
        self.stacked_widget.setCurrentWidget(self.analysis_page)

    def show_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_definitions_page(self):
        definitions_data = [
            {
                'Category'  : 'Financial Ratio',
                'Name'      : name,
                'Definition': RATIO_DEFINITIONS.get(name, {}).get('Definition', 'N/A'),
                'Formula'   : RATIO_DEFINITIONS.get(name, {}).get('Formula', 'N/A')
                }
            for name in RATIO_DEFINITIONS.keys()
            ]

        for category, indicators in MACRO_ECONOMIC_INDICATORS.items():
            for ticker, details in indicators.items():
                definitions_data.append(
                        {
                            'Category'  : category,  # Identifies if it's Interest Rate, Volatility, or Market Ticker
                            'Name'      : f"{ticker} - {details.get('Definition', 'N/A')}",  # Combining Ticker & Name
                            'Definition': details.get('Purpose', 'N/A'),  # Purpose now goes under Definition
                            'Formula'   : 'N/A'  # Macroeconomic indicators don’t have formulas
                            })

        definitions_df = pd.DataFrame(definitions_data)
        self.definitions_page.populate_definitions(definitions_df)
        self.stacked_widget.setCurrentWidget(self.definitions_page)

    def show_previous_page(self):
        self.stacked_widget.setCurrentWidget(self.analysis_page)

    def process_forecast_data(self, df, equation_type):
        if df.empty:
            print("No historical data available for forecast")
            QMessageBox.warning(self, "Error", "Historical data not available for forecasting.")
            return

        try:
            df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
            df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')
            df = df.dropna(subset = ['Date', 'Close'])
            df = df.sort_values(by = 'Date')
        except Exception as e:
            print(f"Error processing forecast data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process forecast data: {e}")
            return

        self.current_history_df = df
        self.forecast_page.populate_forecast(self.current_history_df, self.current_ratios_table, self.current_stock_symbol, equation_type)
        self.stacked_widget.setCurrentWidget(self.forecast_page)

    def show_forecast_page(self):
        if not self.current_stock_symbol:
            QMessageBox.warning(self, "Error", "No stock symbol available.")
            return

        equation_type = self.equation_dropdown.currentText()  # Get selected equation

        if not self.current_history_df.empty:
            self.forecast_page.populate_forecast(self.current_history_df, self.current_ratios_table, self.current_stock_symbol, equation_type)
            self.stacked_widget.setCurrentWidget(self.forecast_page)
            return

        if hasattr(self, 'history_worker') and self.history_worker.isRunning():
            QMessageBox.warning(self, "Error", "Forecast data is already being fetched.")
            return

        self.history_worker = ForecastWorker(self.current_stock_symbol)
        self.history_worker.finished.connect(lambda df: self.process_forecast_data(df, equation_type))
        self.history_worker.start()

    def populate_tables(self, stock_data, ratios_table, ai_assessment):
        self.current_stock_data = stock_data
        self.current_ratios_table = ratios_table
        self.current_ai_assessment = ai_assessment

        if stock_data:
            self.populate_table(self.stock_table, stock_data)
            self.logs_display.append("Stock details populated.")

        if ratios_table is not None and not ratios_table.empty:
            self.populate_table(self.ratios_table, ratios_table)
            self.logs_display.append("Stock ratios populated.")

        if ai_assessment:
            self.ai_display.setPlainText(ai_assessment)
            self.logs_display.append("AI assessment displayed.")
        else:
            self.ai_display.setPlainText("No AI assessment available.")
            self.logs_display.append("No AI assessment available.")

        self.progress_bar.setValue(100)
        self.fetch_button.setEnabled(True)
        self.save_pdf_button.setEnabled(True)
        self.view_forecast_button.setEnabled(True)
        self.logs_display.append("Data fetch and analysis complete.")
        self.prompt_save_pdf()

    def populate_table(self, table, data):
        if isinstance(data, pd.DataFrame):
            table.setRowCount(data.shape[0])
            table.setColumnCount(data.shape[1])
            table.setHorizontalHeaderLabels(data.columns.astype(str))
            for row in range(data.shape[0]):
                for col in range(data.shape[1]):
                    table.setItem(row, col, QTableWidgetItem(str(data.iloc[row, col])))
            table.setFont(QFont("Helvetica", 15))
        elif isinstance(data, dict):
            table.setRowCount(len(data))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Metric", "Value"])
            for row, (key, value) in enumerate(data.items()):
                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(value)))
            table.setFont(QFont("Helvetica", 15))

    def init_logging(self):
        self.emitter = EmittingStream()
        self.emitter.text_written.connect(self.append_log)
        sys.stdout = self.emitter
        sys.stderr = self.emitter

    def append_log(self, text):
        self.logs_display.append(text)

    def start_fetching(self):
        stock_symbol = self.stock_input.text().strip().upper()
        if not stock_symbol:
            self.logs_display.append("Please enter a valid stock symbol.")
            return

        self.current_stock_symbol = stock_symbol
        self.worker = StockWorker(stock_symbol)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.populate_tables)
        self.worker.start()
        self.fetch_button.setEnabled(False)
        self.save_pdf_button.setEnabled(False)
        self.ai_display.clear()
        self.stock_table.clear()
        self.ratios_table.clear()
        self.progress_bar.setValue(0)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        print(f"Progress updated to {value}%.")

    def prompt_save_pdf(self):
        reply = QMessageBox.question(
                self,
                'Save Report',
                "Do you want to save the report as a PDF?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
                )
        if reply == QMessageBox.Yes:
            self.save_pdf()
        else:
            self.logs_display.append("Report not saved as PDF.")

    def save_pdf(self):
        if not self.current_stock_symbol:
            QMessageBox.warning(self, "No Data", "No stock data available to save.")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Report as PDF",
                f"{self.current_stock_symbol}_stock_report.pdf",
                "PDF Files (*.pdf)",
                options = options
                )
        if not file_path:
            self.logs_display.append("PDF save cancelled by user.")
            return

        try:
            pdf = PDFGenerator(
                    self.current_stock_symbol,
                    self.current_stock_data,
                    self.current_ratios_table,
                    self.current_ai_assessment,
                    RATIO_DEFINITIONS
                    )
            pdf.generate_pdf(file_path)
            QMessageBox.information(self, "Success", f"Report saved successfully at:\n{file_path}")
            self.logs_display.append(f"Report saved as '{file_path}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{e}")
            self.logs_display.append(f"Failed to save PDF: {e}")

    def closeEvent(self, event):
        try:
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.quit()
                self.worker.wait()
            if hasattr(self, 'history_worker') and self.history_worker.isRunning():
                self.history_worker.quit()
                self.history_worker.wait()
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            event.accept()


def run_gui():
    app = QApplication(sys.argv)
    window = StockGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_gui()