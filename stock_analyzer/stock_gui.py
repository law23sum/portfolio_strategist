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

# External module imports (make sure these work on your end)
from pdf_generator import PDFGenerator
from main import StockApp, RATIO_DEFINITIONS
from stock_fetcher import StockFetcher
from ai_analyzer import analyze_stock_with_news
from stock_statistics import calculate_statistics, forecast_stock_prices


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
            # print("Raw historical data fetched:", history_data)

            # Create a DataFrame from the raw data
            df = pd.DataFrame(history_data)
            # print("DataFrame created from raw data:", df)

            if not df.empty:
                # Convert 'Date' column to datetime
                df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
                # print("DataFrame after converting 'Date':", df)

                # Convert 'Close' column to numeric (convert to string first to allow .str.replace)
                df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')
                # print("DataFrame after converting 'Close' to numeric:", df)

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
        description.setFont(QFont("Helvetica", 16))
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
    def __init__(self, navigate_back):
        super().__init__()
        self.current_history_df = pd.DataFrame()
        self.navigate_back = navigate_back

        # Main layout
        layout = QVBoxLayout()

        # Title at the top
        title = QLabel("Stock Price Forecast")
        title.setFont(QFont("Helvetica", 22))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Chart (canvas) on the top
        self.figure, self.ax = plt.subplots(figsize = (8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Table to display forecasted stock prices (placed below the chart)
        self.forecast_table = QTableWidget()
        self.forecast_table.setFont(QFont("Helvetica", 14))
        layout.addWidget(self.forecast_table)

        # Back button at the bottom
        back_button = QPushButton("Back to Analysis")
        back_button.setFont(QFont("Helvetica", 16))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def populate_forecast(self, df):
        if df.empty:
            print("No historical data available for forecast")
            QMessageBox.warning(self, "No Data", "No historical data available for forecast.")
            return

        try:
            print("Preparing forecast data")
            # Convert 'Date' column to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')

            # Convert 'Close' column to numeric (using astype(str) to safely call .str.replace)
            df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')

            # Drop rows with missing values and sort the DataFrame
            df = df.dropna(subset = ['Date', 'Close'])
            df = df.sort_values(by = 'Date')

            # Calculate statistics and generate forecast
            mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
            recent_price = closing_prices[-1]
            forecast_days = 30
            t_forecast, forecast_prices = forecast_stock_prices(recent_price, mu_daily, sigma_daily, forecast_days)

            last_date = df['Date'].max()
            forecast_dates = [last_date + pd.Timedelta(days = i) for i in range(1, forecast_days + 1)]

            # Plot the historical and forecasted prices
            self.ax.clear()
            self.ax.plot(df['Date'], df['Close'], label = "Historical Prices", color = "blue", lw = 2)
            self.ax.plot(forecast_dates, forecast_prices, label = "Forecast Prices", color = "red", lw = 2, linestyle = "--")
            self.ax.set_title("Stock Price Forecast")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price")
            self.ax.legend()
            self.ax.grid(True)
            self.canvas.draw()
            print("Forecast plot generated successfully")

            # Populate the forecast table with predicted data
            self.forecast_table.clear()
            self.forecast_table.setRowCount(forecast_days)
            self.forecast_table.setColumnCount(2)
            self.forecast_table.setHorizontalHeaderLabels(["Date", "Predicted Price"])

            for i in range(forecast_days):
                date_str = forecast_dates[i].strftime("%Y-%m-%d")
                price_str = f"{forecast_prices[i]:.2f}"
                date_item = QTableWidgetItem(date_str)
                price_item = QTableWidgetItem(price_str)
                date_item.setFont(QFont("Helvetica", 14))
                price_item.setFont(QFont("Helvetica", 14))
                self.forecast_table.setItem(i, 0, date_item)
                self.forecast_table.setItem(i, 1, price_item)
            try:
                print("Preparing forecast data")
                # Convert 'Date' column to datetime
                df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')

                # Convert 'Close' column to numeric (using astype(str) to safely call .str.replace)
                df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')

                # Drop rows with missing values and sort the DataFrame
                df = df.dropna(subset = ['Date', 'Close'])
                df = df.sort_values(by = 'Date')

                # Calculate statistics and generate forecast
                mu_daily, sigma_daily, closing_prices, log_returns = calculate_statistics(df)
                recent_price = closing_prices[-1]
                forecast_days = 30
                t_forecast, forecast_prices = forecast_stock_prices(recent_price, mu_daily, sigma_daily, forecast_days)

                last_date = df['Date'].max()
                forecast_dates = [last_date + pd.Timedelta(days = i) for i in range(1, forecast_days + 1)]

                # Plot the historical and forecasted prices
                self.ax.clear()
                self.ax.plot(df['Date'], df['Close'], label = "Historical Prices", color = "blue", lw = 2)
                self.ax.plot(forecast_dates, forecast_prices, label = "Forecast Prices", color = "red", lw = 2, linestyle = "--")
                self.ax.set_title("Stock Price Forecast")
                self.ax.set_xlabel("Date")
                self.ax.set_ylabel("Price")
                self.ax.legend()
                self.ax.grid(True)
                self.canvas.draw()
                print("Forecast plot generated successfully")

                # Populate the forecast table with predicted data
                self.forecast_table.clear()
                self.forecast_table.setRowCount(forecast_days)
                self.forecast_table.setColumnCount(2)
                self.forecast_table.setHorizontalHeaderLabels(["Date", "Predicted Price"])

                for i in range(forecast_days):
                    date_str = forecast_dates[i].strftime("%Y-%m-%d")
                    price_str = f"{forecast_prices[i]:.2f}"
                    date_item = QTableWidgetItem(date_str)
                    price_item = QTableWidgetItem(price_str)
                    date_item.setFont(QFont("Helvetica", 14))
                    price_item.setFont(QFont("Helvetica", 14))
                    self.forecast_table.setItem(i, 0, date_item)
                    self.forecast_table.setItem(i, 1, price_item)

                # Adjust columns to fit contents nicely
                self.forecast_table.resizeColumnsToContents()

            except Exception as e:
                print(f"Error in forecast plotting: {e}")
                QMessageBox.critical(self, "Error", f"Forecasting failed: {e}")

            # Adjust columns to fit contents nicely
            self.forecast_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error in forecast plotting: {e}")
            QMessageBox.critical(self, "Error", f"Forecasting failed: {e}")


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

    def process_forecast_data(self, df):
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
        self.forecast_page.populate_forecast(self.current_history_df)
        self.stacked_widget.setCurrentWidget(self.forecast_page)

    def show_forecast_page(self):
        if not self.current_stock_symbol:
            QMessageBox.warning(self, "Error", "No stock symbol available.")
            return

        # If forecast data is already cached, use it!
        if not self.current_history_df.empty:
            self.forecast_page.populate_forecast(self.current_history_df)
            self.stacked_widget.setCurrentWidget(self.forecast_page)
            return

        # Prevent duplicate worker runs
        if hasattr(self, 'history_worker') and self.history_worker.isRunning():
            QMessageBox.warning(self, "Error", "Forecast data is already being fetched.")
            return

        # Otherwise, fetch the forecast data
        self.history_worker = ForecastWorker(self.current_stock_symbol)
        self.history_worker.finished.connect(self.process_forecast_data)
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
            table.setFont(QFont("Helvetica", 16))
        elif isinstance(data, dict):
            table.setRowCount(len(data))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Metric", "Value"])
            for row, (key, value) in enumerate(data.items()):
                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(value)))
            table.setFont(QFont("Helvetica", 16))

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
        self.logs_display.append(f"Progress updated to {value}%.")

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