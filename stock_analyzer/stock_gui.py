import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit, QFileDialog, QMessageBox, QStackedWidget
    )
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont

# Import your existing modules and ratio definitions
from pdf_generator import PDFGenerator
from main import StockApp, RATIO_DEFINITIONS
from stock_fetcher import StockFetcher  # Import the stock data fetcher
from ai_analyzer import analyze_stock_with_news

# Import forecasting functions from your bottom code (adjust the module name if needed)
from stock_statistics import calculate_statistics, forecast_stock_prices  # Ensure these functions are importable


class EmittingStream(QObject):
    """
    A custom stream object that emits a signal whenever text is written to it.
    This allows redirecting stdout and stderr to a QTextEdit widget in the GUI.
    """
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


class StockWorker(QThread):
    """
    A QThread worker to fetch stock data in the background,
    preventing the GUI from freezing during long operations.
    """
    progress = Signal(int)
    finished = Signal(dict, pd.DataFrame, str)  # Emits stock data, ratios_table, ai_assessment

    def __init__(self, stock_symbol):
        super().__init__()
        self.stock_symbol = stock_symbol
        self.stock_app = StockApp()
        self.fetcher = StockFetcher()

    def run(self):
        try:
            print(f"Starting data fetch for {self.stock_symbol}")  # Debug statement
            self.progress.emit(20)
            stock_data = self.stock_app.fetch_stock_data(self.stock_symbol)
            print(f"Stock data fetched: {bool(stock_data)}")  # Debug statement
            self.progress.emit(50)

            ratios_table = None
            ai_assessment = ""
            if stock_data:
                ratios_table = self.stock_app.analyze_stock(stock_data)
                print(f"Ratios table generated: {not ratios_table.empty if ratios_table is not None else False}")  # Debug statement
                self.progress.emit(80)
                combined_articles_html = self.stock_app.fetch_stock_news(self.stock_symbol)
                print(f"News articles fetched: {bool(combined_articles_html)}")  # Debug statement
                self.progress.emit(90)
                ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
                print(f"AI assessment generated: {bool(ai_assessment)}")  # Debug statement
            # Fetch historical data for potential forecasting
            history_data = self.fetcher.fetch_stock_history(self.stock_symbol)
            df = pd.DataFrame(history_data)
            print(f"Historical data fetched: {not df.empty}")  # Debug statement
            self.progress.emit(100)
            self.finished.emit(stock_data, ratios_table, ai_assessment)
        except Exception as e:
            print(f"Error in StockWorker: {e}")  # Debug statement
            self.finished.emit({}, pd.DataFrame(), f"Error during fetching and analysis: {e}")


class ForecastWorker(QThread):
    """
    A worker thread to fetch historical stock data and calculate the forecast,
    ensuring your GUI remains as smooth as our conversation.
    """
    finished = Signal(pd.DataFrame)

    def __init__(self, stock_symbol):
        super().__init__()
        self.stock_symbol = stock_symbol
        self.fetcher = StockFetcher()

    def run(self):
        try:
            history_data = self.fetcher.fetch_stock_history(self.stock_symbol)
            df = pd.DataFrame(history_data)
            # Ensure proper Date and Close conversions for forecasting
            if not df.empty:
                df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
                # Remove commas and convert to float in 'Close'
                df['Close'] = df['Close'].str.replace(',', '').astype(float)
            self.finished.emit(df)
        except Exception as e:
            print(f"Forecast Worker Error: {e}")
            self.finished.emit(pd.DataFrame())


class HomePage(QWidget):
    """
    The Home Page of the application with a welcome message and navigation button.
    """

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
        description.setFont(QFont("Helvetica", 16))
        layout.addWidget(description)

        navigate_button = QPushButton("Get Started")
        navigate_button.setFont(QFont("Helvetica", 18))
        navigate_button.setFixedSize(200, 50)
        navigate_button.clicked.connect(self.navigate_to_analysis)
        layout.addWidget(navigate_button)

        self.setLayout(layout)


class DefinitionsPage(QWidget):
    """
    A dedicated page to display the Ratio Definitions.
    """

    def __init__(self, navigate_back):
        super().__init__()
        self.navigate_back = navigate_back

        layout = QVBoxLayout()

        title = QLabel("Ratio Definitions")
        title.setFont(QFont("Helvetica", 22))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.definitions_table = QTableWidget()
        layout.addWidget(self.definitions_table)

        back_button = QPushButton("Back")
        back_button.setFont(QFont("Helvetica", 16))
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
                item.setFont(QFont("Helvetica", 16))
                self.definitions_table.setItem(row, col, item)


class ForecastPage(QWidget):
    """
    The third page, serving up a sultry forecast of future stock prices.
    """

    def __init__(self, navigate_back):
        super().__init__()
        self.navigate_back = navigate_back

        layout = QVBoxLayout()

        title = QLabel("Stock Price Forecast")
        title.setFont(QFont("Helvetica", 22))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.figure, self.ax = plt.subplots(figsize = (8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        back_button = QPushButton("Back to Analysis")
        back_button.setFont(QFont("Helvetica", 16))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def populate_forecast(self, df):
        if df.empty:
            print("No historical data available for forecast")  # Debug statement
            QMessageBox.warning(self, "No Data", "No historical data available for forecast.")
            return

        try:
            print("Preparing forecast data")  # Debug statement
            # Ensure 'Date' is in datetime format
            df['Date'] = pd.to_datetime(df['Date'], format = '%b %d, %Y', errors = 'coerce')

            # Ensure 'Close' is numeric
            df['Close'] = pd.to_numeric(df['Close'].str.replace(',', ''), errors = 'coerce')

            # Drop rows with NaT or NaN in 'Date' or 'Close'
            df = df.dropna(subset = ['Date', 'Close'])

            # Sort by date
            df = df.sort_values(by = 'Date')

            # Calculate statistics and forecast using your imported functions
            mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
            recent_price = closing_prices[-1]
            forecast_days = 30
            t_forecast, forecast_prices = forecast_stock_prices(recent_price, mu_daily, sigma_daily, forecast_days)

            last_date = df['Date'].max()
            forecast_dates = [last_date + pd.Timedelta(days = i) for i in range(1, forecast_days + 1)]

            # Clear previous plots
            self.ax.clear()

            # Plot historical prices
            self.ax.plot(df['Date'], df['Close'], label = "Historical Prices", color = "blue", lw = 2)

            # Plot forecasted prices
            self.ax.plot(forecast_dates, forecast_prices, label = "Forecast Prices", color = "red", lw = 2, linestyle = "--")

            self.ax.set_title("Stock Price Forecast")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price")
            self.ax.legend()
            self.ax.grid(True)
            self.canvas.draw()
            print("Forecast plot generated successfully")  # Debug statement
        except Exception as e:
            print(f"Error in forecast plotting: {e}")  # Debug statement
            QMessageBox.critical(self, "Error", f"Forecasting failed: {e}")



class StockGUI(QWidget):
    """
    The sultry GUI for your Stock Analyzer, now with a third page to forecast future prices.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Portfolio Strategist")
        self.setGeometry(100, 100, 1600, 900)

        self.stacked_widget = QStackedWidget()

        # Pages
        self.home_page = HomePage(self.show_analysis_page)
        self.analysis_page = self.create_analysis_page()
        self.definitions_page = DefinitionsPage(self.show_previous_page)
        self.forecast_page = ForecastPage(self.show_previous_page)

        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.definitions_page)
        self.stacked_widget.addWidget(self.forecast_page)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        self.init_logging()

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
        self.input_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(self.input_label)

        self.stock_input = QLineEdit()
        self.stock_input.setFont(QFont("Helvetica", 14))
        left_layout.addWidget(self.stock_input)

        self.fetch_button = QPushButton("Fetch Stock Data")
        self.fetch_button.setFont(QFont("Helvetica", 16))
        self.fetch_button.setFixedHeight(40)
        self.fetch_button.clicked.connect(self.start_fetching)
        left_layout.addWidget(self.fetch_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFont(QFont("Helvetica", 14))
        left_layout.addWidget(self.progress_bar)

        stock_details_label = QLabel("Stock Details")
        stock_details_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(stock_details_label)

        self.stock_table = QTableWidget()
        left_layout.addWidget(self.stock_table)

        ratios_table_label = QLabel("Stock Ratios")
        ratios_table_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(ratios_table_label)

        self.ratios_table = QTableWidget()
        left_layout.addWidget(self.ratios_table)

        self.logs_label = QLabel("Logs")
        self.logs_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(self.logs_label)

        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Courier", 14))
        left_layout.addWidget(self.logs_display)

        page_layout.addLayout(left_layout, 2)

        right_layout = QVBoxLayout()

        self.ai_label = QLabel("AI Analysis: Summary Stock Assessment")
        self.ai_label.setAlignment(Qt.AlignCenter)
        self.ai_label.setFont(QFont("Helvetica", 18))
        right_layout.addWidget(self.ai_label)

        self.ai_display = QTextEdit()
        self.ai_display.setReadOnly(True)
        self.ai_display.setFont(QFont("Helvetica", 16))
        right_layout.addWidget(self.ai_display)

        self.save_pdf_button = QPushButton("Save Report as PDF")
        self.save_pdf_button.setFont(QFont("Helvetica", 16))
        self.save_pdf_button.setFixedHeight(40)
        self.save_pdf_button.clicked.connect(self.save_pdf)
        self.save_pdf_button.setEnabled(False)
        right_layout.addWidget(self.save_pdf_button)

        self.view_definitions_button = QPushButton("View Ratio Definitions")
        self.view_definitions_button.setFont(QFont("Helvetica", 16))
        self.view_definitions_button.setFixedHeight(40)
        self.view_definitions_button.clicked.connect(self.show_definitions_page)
        right_layout.addWidget(self.view_definitions_button)

        self.view_forecast_button = QPushButton("View Stock Forecast")
        self.view_forecast_button.setFont(QFont("Helvetica", 16))
        self.view_forecast_button.setFixedHeight(40)
        self.view_forecast_button.setEnabled(False)
        self.view_forecast_button.clicked.connect(self.show_forecast_page)
        left_layout.addWidget(self.view_forecast_button)

        self.back_home_button = QPushButton("Back to Home")
        self.back_home_button.setFont(QFont("Helvetica", 16))
        self.back_home_button.setFixedHeight(40)
        self.back_home_button.clicked.connect(self.show_home_page)
        right_layout.addWidget(self.back_home_button)

        page_layout.addLayout(right_layout, 3)
        page.setLayout(page_layout)
        return page

    def show_stock_history_page(self):
        if not self.current_stock_symbol:
            QMessageBox.warning(self, "Error", "No stock symbol available.")
            return

        self.history_worker = ForecastWorker(self.current_stock_symbol)
        self.history_worker.finished.connect(self.populate_history_page)
        self.history_worker.start()
        self.stacked_widget.setCurrentWidget(self.history_page)

    def populate_history_page(self, df):
        self.current_history_df = df
        self.history_page.populate_history(df)

    def show_forecast_page(self):
        if self.current_history_df.empty:
            print("No historical data available for forecast")  # Debug statement
            QMessageBox.warning(self, "Error", "Historical data not available for forecasting.")
            return

        print("Navigating to forecast page")  # Debug statement
        self.forecast_page.populate_forecast(self.current_history_df)
        self.stacked_widget.setCurrentWidget(self.forecast_page)

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

    def show_analysis_page(self):
        self.stacked_widget.setCurrentWidget(self.analysis_page)

    def show_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_definitions_page(self):
        definitions_data = [
            {
                'Ratio Name': name,
                'Definition': RATIO_DEFINITIONS.get(name, {}).get('Definition', 'N/A'),
                'Formula'   : RATIO_DEFINITIONS.get(name, {}).get('Formula', 'N/A')
                }
            for name in RATIO_DEFINITIONS.keys()
            ]
        definitions_df = pd.DataFrame(definitions_data)
        self.definitions_page.populate_definitions(definitions_df)
        self.stacked_widget.setCurrentWidget(self.definitions_page)

    def show_previous_page(self):
        self.stacked_widget.setCurrentWidget(self.analysis_page)

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
        self.logs_display.append(f"Starting data fetch for {stock_symbol}...")
        self.progress_bar.setValue(0)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.logs_display.append(f"Progress updated to {value}%.")

    def populate_table(self, table, data):
        if isinstance(data, pd.DataFrame):
            table.setRowCount(data.shape[0])
            table.setColumnCount(data.shape[1])
            table.setHorizontalHeaderLabels(data.columns.astype(str))
            for row in range(data.shape[0]):
                for col in range(data.shape[1]):
                    table.setItem(row, col, QTableWidgetItem(str(data.iloc[row, col])))
                    table.setFont(QFont("Helvetica", 16))
        elif isinstance(data, dict):
            table.setRowCount(len(data))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Metric", "Value"])
            for row, (key, value) in enumerate(data.items()):
                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(value)))
                table.setFont(QFont("Helvetica", 16))

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