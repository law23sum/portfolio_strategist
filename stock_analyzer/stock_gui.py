import sys
import pandas as pd
import numpy as np
import yfinance as yf

import pyqtgraph as pg
from pyqtgraph import PlotWidget

from PySide6.QtWidgets import (
    QApplication, QComboBox, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QStackedWidget
    )
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont

# Local imports — adjust paths if needed
from pdf_generator import PDFGenerator
from main import StockApp, RATIO_DEFINITIONS
from stock_definitions import MACRO_ECONOMIC_INDICATORS
from stock_fetcher import StockFetcher
from ai_analyzer import analyze_stock_with_news
from stock_statistics import (
    calculate_eta_theta, calculate_factor_betas, calculate_interest_rate_beta,
    calculate_market_beta, calculate_statistics, calculate_volatility_beta, forecast_stock_prices,
    shift_forecast_to_actual_dates, calculate_prediction_errors, plot_results
    )


# --------------------------------------------------------------------------
#                           Utility for Logging
# --------------------------------------------------------------------------
class EmittingStream(QObject):
    """
    Utility class to reroute print statements into a Qt signal,
    so we can display them in a QTextEdit for 'Logs'.
    """
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


# --------------------------------------------------------------------------
#                           Workers (Threads)
# --------------------------------------------------------------------------
class StockWorker(QThread):
    """
    Worker thread to fetch stock data & do some initial analysis
    without freezing the main UI. (For Detailed Page)
    """
    progress = Signal(int)
    finished = Signal(dict, pd.DataFrame, str)  # (stock_data, ratios_table, ai_assessment)

    def __init__(self, stock_symbol):
        super().__init__()
        self.stock_symbol = stock_symbol
        self.stock_app = StockApp()

    def run(self):
        try:
            print(f"Starting data fetch (Detailed) for {self.stock_symbol}")
            self.progress.emit(20)
            # We no longer accept period/interval here for the detailed page;
            # We'll just rely on a default fetch or the "fetch_stock_data" signature in StockApp.
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


class ForecastWorker(QThread):
    """
    Worker thread to fetch full historical data for forecasting. (For Analysis/Predictions)
    """
    finished = Signal(pd.DataFrame)

    def __init__(self, stock_symbol, stock_period, stock_interval):
        super().__init__()
        self.stock_symbol = stock_symbol
        self.stock_period = stock_period
        self.stock_interval = stock_interval
        self.fetcher = StockFetcher()

    def run(self):
        try:
            print(f"Starting data fetch (Forecast) for {self.stock_symbol}")
            history_data = self.fetcher.fetch_stock_history(
                    self.stock_symbol,
                    self.stock_period,
                    self.stock_interval
                    )
            df = pd.DataFrame(history_data)

            if not df.empty:
                # Clean up the data
                df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
                df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')
                df = df.dropna(subset = ['Date', 'Close'])
                df = df.sort_values(by = 'Date')
            else:
                print("No historical data fetched.")

            self.finished.emit(df)

        except Exception as e:
            print(f"Forecast Worker Error: {e}")
            self.finished.emit(pd.DataFrame())


# --------------------------------------------------------------------------
#                           Helper Function
# --------------------------------------------------------------------------
def datetime_to_float(dt_series):
    """
    Convert a Pandas Series of datetime objects to numeric timestamps (float).
    This helps pyqtgraph handle x-axis as numeric values.
    """
    return dt_series.apply(lambda d: d.timestamp() if pd.notnull(d) else None)


# --------------------------------------------------------------------------
#                        Page: DefinitionsPage
# --------------------------------------------------------------------------
class DefinitionsPage(QWidget):
    """
    The page that displays 'Financial Definitions' in a table.
    """

    def __init__(self, navigate_back_to_home):
        super().__init__()
        self.navigate_back_to_home = navigate_back_to_home

        layout = QVBoxLayout()

        title = QLabel("Financial Definitions")
        title.setFont(QFont("Helvetica", 22))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.definitions_table = QTableWidget()
        layout.addWidget(self.definitions_table)

        back_button = QPushButton("Home Page")
        back_button.setFont(QFont("Helvetica", 15))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back_to_home)
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


# --------------------------------------------------------------------------
#                  Page: AnalysisPredictionsPage (Forecast Page)
# --------------------------------------------------------------------------
class AnalysisPredictionsPage(QWidget):
    """
    Contains:
      - Plot Original (Historical) + Forecast Data (Include Legends)
      - Plot Error Chart
      - Update the Error Table (Left Table)
      - Update the Forecast Table (Right Table)
      - Home Page
    """

    def __init__(self, navigate_back_to_home):
        super().__init__()
        self.navigate_back_to_home = navigate_back_to_home

        self.current_history_df = pd.DataFrame()
        self.error_df = pd.DataFrame()

        main_layout = QVBoxLayout()

        # Title
        title_label_1 = QLabel("Plot Original (Historical) + Forecast Data (Include Legends)")
        title_label_1.setFont(QFont("Helvetica", 16))
        title_label_1.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label_1)

        # Two charts side by side
        charts_layout = QHBoxLayout()

        # Left chart: Historical vs. Forecast
        self.plotWidget_original = PlotWidget()
        self.plotWidget_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.plotWidget_original)

        # Right chart: Error
        right_chart_box = QVBoxLayout()
        title_label_2 = QLabel("Plot Error Chart")
        title_label_2.setFont(QFont("Helvetica", 16))
        title_label_2.setAlignment(Qt.AlignCenter)
        right_chart_box.addWidget(title_label_2)

        self.plotWidget_error = PlotWidget()
        self.plotWidget_error.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_chart_box.addWidget(self.plotWidget_error)

        charts_layout.addLayout(right_chart_box)
        main_layout.addLayout(charts_layout)

        # Tables layout: error table (left), forecast table (right)
        bottom_tables_layout = QHBoxLayout()

        left_table_box = QVBoxLayout()
        left_table_label = QLabel("Update the Error Table")
        left_table_label.setFont(QFont("Helvetica", 14))
        left_table_box.addWidget(left_table_label)

        self.error_table = QTableWidget()
        self.error_table.setFont(QFont("Helvetica", 13))
        left_table_box.addWidget(self.error_table)

        bottom_tables_layout.addLayout(left_table_box)

        right_table_box = QVBoxLayout()
        right_table_label = QLabel("Update the Forecast Table")
        right_table_label.setFont(QFont("Helvetica", 14))
        self.forecast_table = QTableWidget()
        self.forecast_table.setFont(QFont("Helvetica", 13))
        right_table_box.addWidget(self.forecast_table)
        self.forecast_table.setFont(QFont("Helvetica", 13))

        bottom_tables_layout.addLayout(right_table_box)
        main_layout.addLayout(bottom_tables_layout)

        # Back button
        back_button = QPushButton("Home Page")
        back_button.setFont(QFont("Helvetica", 15))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back_to_home)
        main_layout.addWidget(back_button)

        self.setLayout(main_layout)

        # Mapping for forecast days
        self.period_to_days = {
            "1d" : 1,
            "5d" : 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y" : 365,
            "2y" : 730,
            "5y" : 1825,
            "10y": 3650,
            "max": 3650,  # or some large integer you prefer
            }

    def populate_forecast(
            self, df, ratios_table, stock_symbol,
            equation_type, market_ticker, vix_ticker, tnx_ticker,
            stock_period, stock_interval
            ):
        """
        Updated to accept stock_period so we can map it to forecast_days.
        """
        if df.empty:
            QMessageBox.warning(self, "No Data", "No historical data available for forecast.")
            return

        try:
            # Clean up
            df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
            df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors = 'coerce')
            df.dropna(subset = ['Date', 'Close'], inplace = True)
            df.sort_values(by = 'Date', inplace = True)

            mu_daily, sigma_daily, closing_prices, _ = calculate_statistics(df)
            if len(closing_prices) == 0:
                QMessageBox.warning(self, "Invalid Data", "No valid close prices found.")
                return

            recent_price = closing_prices[-1]

            # Use our new mapping from period -> forecast_days
            forecast_days = self.period_to_days.get(stock_period, 365)

            # Pull external data
            main_ticker = stock_symbol
            total_ticker_data = None
            for _ in range(10):
                try:
                    total_ticker_data = yf.download([main_ticker, market_ticker, vix_ticker, tnx_ticker], period = "1y")
                    if not total_ticker_data.empty:
                        break
                except:
                    print("Ticker data can't be retrieved from yfinance.")

            if total_ticker_data is not None and not total_ticker_data.empty:
                close_data = total_ticker_data["Close"].dropna(
                        subset = [main_ticker, market_ticker, vix_ticker, tnx_ticker]
                        )
                stock_data = close_data[main_ticker]
                market_data = close_data[market_ticker]
                vix_data = close_data[vix_ticker]
                tnx_data = close_data[tnx_ticker]

                price_series = stock_data.values
                market_prices = market_data.values
                vix_prices = vix_data.values
                tnx_prices = tnx_data.values

                # daily returns
                stock_returns = np.diff(price_series) / price_series[:-1]
                market_returns = np.diff(market_prices) / market_prices[:-1]
                vix_changes = np.diff(vix_prices) / vix_prices[:-1]
                interest_rate_changes = np.diff(tnx_prices) / tnx_prices[:-1]

                # dummy factor returns
                min_len = len(stock_returns)
                factor_returns = pd.DataFrame(
                        {
                            "SMB": np.random.normal(0, 0.01, min_len),
                            "HML": np.random.normal(0, 0.01, min_len),
                            "MOM": np.random.normal(0, 0.01, min_len),
                            })

                eta, theta = calculate_eta_theta(price_series)
                beta_m = calculate_market_beta(stock_returns, market_returns)
                factor_betas = calculate_factor_betas(stock_returns, factor_returns)
                beta_r = calculate_interest_rate_beta(stock_returns, interest_rate_changes)
                beta_v = calculate_volatility_beta(stock_returns, vix_changes)

                mean_reversion_params = {"eta": eta, "theta": theta}
                external_factors = {
                    "market_beta"       : beta_m,
                    "factor_betas"      : factor_betas,
                    "interest_rate_beta": beta_r,
                    "volatility_beta"   : beta_v,
                    }
            else:
                mean_reversion_params = {"eta": 0, "theta": 0}
                external_factors = {
                    "market_beta"       : 0,
                    "factor_betas"      : pd.DataFrame(),
                    "interest_rate_beta": 0,
                    "volatility_beta"   : 0,
                    }

            # Ratios
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
            valuation_metrics = {}
            financial_health_metrics = {}

            if ratios_table is not None and not ratios_table.empty:
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

            # Forecast
            t_forecast, forecast_prices = forecast_stock_prices(
                    equation_type,
                    recent_price,
                    mu_daily,
                    sigma_daily,
                    forecast_days,
                    stock_interval,
                    valuation_metrics,
                    financial_health_metrics,
                    mean_reversion_params,
                    external_factors
                    )

            forecast_df = shift_forecast_to_actual_dates(df, forecast_prices, forecast_days)
            forecast_dates = forecast_df['Date'].tolist()

            # Plot historical + forecast
            self.plotWidget_original.clear()
            x_historical = datetime_to_float(df['Date'])
            y_historical = df['Close'].values
            x_forecast = datetime_to_float(pd.Series(forecast_dates))
            y_forecast = forecast_prices

            self.plotWidget_original.plot(
                    x_historical, y_historical,
                    pen = pg.mkPen(color = 'b', width = 2),
                    name = "Historical Prices"
                    )
            self.plotWidget_original.plot(
                    x_forecast, y_forecast,
                    pen = pg.mkPen(color = 'r', width = 2),
                    name = "Forecast Prices"
                    )
            self.plotWidget_original.setLabel('bottom', 'Date (timestamp)')
            self.plotWidget_original.setLabel('left', 'Price')
            self.plotWidget_original.setTitle("Historical vs. Forecast Prices")
            self.plotWidget_original.showGrid(x = True, y = True)

            # Calculate errors
            error_df = calculate_prediction_errors(df, forecast_df)
            self.error_df = error_df
            self.plotWidget_error.clear()

            if not error_df.empty:
                x_error = datetime_to_float(error_df['Date'])
                y_error = error_df['Error'].values
                self.plotWidget_error.plot(
                        x_error, y_error,
                        pen = pg.mkPen(color = 'm', width = 2),
                        name = "Prediction Error"
                        )
                self.plotWidget_error.setLabel('bottom', 'Date (timestamp)')
                self.plotWidget_error.setLabel('left', 'Error')
                self.plotWidget_error.setTitle("Prediction Errors")
                self.plotWidget_error.showGrid(x = True, y = True)
            else:
                self.plotWidget_error.setTitle("No prediction errors to display.")

            # Forecast table
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

            # Error table
            self.error_table.clear()
            if not error_df.empty:
                self.error_table.setRowCount(len(error_df))
                self.error_table.setColumnCount(4)
                self.error_table.setHorizontalHeaderLabels(
                        ["Date", "Actual Price", "Forecasted Price", "Error"]
                        )
                for idx, row in error_df.iterrows():
                    date_str = row['Date'].strftime("%Y-%m-%d")
                    actual_str = f"{row['Actual_Close']:.2f}"
                    forecasted_str = f"{row['Forecasted_Close']:.2f}"
                    error_str = f"{row['Error']:.2f}"

                    date_item = QTableWidgetItem(date_str)
                    actual_item = QTableWidgetItem(actual_str)
                    forecasted_item = QTableWidgetItem(forecasted_str)
                    error_item = QTableWidgetItem(error_str)

                    for item in (date_item, actual_item, forecasted_item, error_item):
                        item.setFont(QFont("Helvetica", 13))

                    self.error_table.setItem(idx, 0, date_item)
                    self.error_table.setItem(idx, 1, actual_item)
                    self.error_table.setItem(idx, 2, forecasted_item)
                    self.error_table.setItem(idx, 3, error_item)

                self.error_table.resizeColumnsToContents()
            else:
                self.error_table.setRowCount(0)
                self.error_table.setColumnCount(0)

        except Exception as e:
            print(f"Error in forecast plotting: {e}")
            QMessageBox.critical(self, "Error", f"Forecasting failed: {e}")

    def show_error_plot(self):
        if not self.error_df.empty:
            plot_results(self.error_df)
        else:
            QMessageBox.information(
                    self, "No Data", "No overlapping dates to plot prediction errors."
                    )


# --------------------------------------------------------------------------
#              Page: DetailedPage
# --------------------------------------------------------------------------
class DetailedPage(QWidget):
    """
    Shows:
      - Stock Overview (table on top-left)
      - Stock Ratios (table on bottom-left)
      - AI Analysis: Stock Summary Assessment (on the right)
      - Save PDF
      - Home Page
    """

    def __init__(self, navigate_back_to_home):
        super().__init__()
        self.navigate_back_to_home = navigate_back_to_home

        self.current_stock_symbol = ""
        self.current_stock_data = {}
        self.current_ratios_table = pd.DataFrame()
        self.current_ai_assessment = ""

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left column
        left_col = QVBoxLayout()

        # Stock Overview
        overview_label = QLabel("Stock Overview")
        overview_label.setFont(QFont("Helvetica", 18))
        overview_label.setAlignment(Qt.AlignLeft)
        left_col.addWidget(overview_label)

        self.stock_table = QTableWidget()
        left_col.addWidget(self.stock_table)

        # Ratios
        ratio_label = QLabel("Stock Ratios")
        ratio_label.setFont(QFont("Helvetica", 18))
        ratio_label.setAlignment(Qt.AlignLeft)
        left_col.addWidget(ratio_label)

        self.ratios_table = QTableWidget()
        left_col.addWidget(self.ratios_table)

        # PDF button
        self.save_pdf_button = QPushButton("Save Report as PDF")
        self.save_pdf_button.setFont(QFont("Helvetica", 15))
        self.save_pdf_button.setFixedHeight(40)
        self.save_pdf_button.clicked.connect(self.save_pdf)
        self.save_pdf_button.setEnabled(False)
        left_col.addWidget(self.save_pdf_button)

        # Home Page
        back_button = QPushButton("Home Page")
        back_button.setFont(QFont("Helvetica", 15))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back_to_home)
        left_col.addWidget(back_button)

        main_layout.addLayout(left_col, 2)

        # Right column: AI analysis
        right_col = QVBoxLayout()

        ai_label = QLabel("AI Analysis: Stock Summary Assessment")
        ai_label.setFont(QFont("Helvetica", 18))
        ai_label.setAlignment(Qt.AlignLeft)
        right_col.addWidget(ai_label)

        self.ai_display = QTextEdit()
        self.ai_display.setReadOnly(True)
        self.ai_display.setFont(QFont("Helvetica", 15))
        right_col.addWidget(self.ai_display)

        main_layout.addLayout(right_col, 3)

    def populate_tables(self, stock_data, ratios_table, ai_assessment, symbol):
        self.current_stock_symbol = symbol
        self.current_stock_data = stock_data
        self.current_ratios_table = ratios_table
        self.current_ai_assessment = ai_assessment

        # Stock Table
        if stock_data:
            self._populate_table(self.stock_table, stock_data)
        else:
            self.stock_table.clear()

        # Ratios Table
        if ratios_table is not None and not ratios_table.empty:
            self._populate_table(self.ratios_table, ratios_table)
        else:
            self.ratios_table.clear()

        # AI
        if ai_assessment:
            self.ai_display.setPlainText(ai_assessment)
        else:
            self.ai_display.setPlainText("No AI assessment available.")

        # Enable PDF if data
        if stock_data:
            self.save_pdf_button.setEnabled(True)
        else:
            self.save_pdf_button.setEnabled(False)

    def _populate_table(self, table, data):
        if isinstance(data, pd.DataFrame):
            table.setRowCount(data.shape[0])
            table.setColumnCount(data.shape[1])
            table.setHorizontalHeaderLabels(data.columns.astype(str))
            for row in range(data.shape[0]):
                for col in range(data.shape[1]):
                    item = QTableWidgetItem(str(data.iloc[row, col]))
                    item.setFont(QFont("Helvetica", 15))
                    table.setItem(row, col, item)
        elif isinstance(data, dict):
            table.setRowCount(len(data))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Metric", "Value"])
            row = 0
            for key, value in data.items():
                k_item = QTableWidgetItem(str(key))
                v_item = QTableWidgetItem(str(value))
                k_item.setFont(QFont("Helvetica", 15))
                v_item.setFont(QFont("Helvetica", 15))
                table.setItem(row, 0, k_item)
                table.setItem(row, 1, v_item)
                row += 1

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
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{e}")


# --------------------------------------------------------------------------
#                  Page: HomePage
# --------------------------------------------------------------------------
class HomePage(QWidget):
    """
    The 'Home Page' with:
     - "Populate Information" button => triggers BOTH data fetch for Detailed & for Forecast
       (unless Detailed data was already fetched, in which case we skip re-fetching it)
     - "Stock Detailed Reports" button => navigates to DetailedPage (once data is fetched)
     - "Stock Analysis/Predictions" button => navigates to AnalysisPredictionsPage (once data is fetched)
     - "Financial Definitions" => navigates to DefinitionsPage
     - Also includes symbol, period, interval, forecasting model, market/vix/tnx tickers
     - Logs on the right side
    """

    def __init__(
            self,
            navigate_to_definitions,
            navigate_to_detailed_page,
            navigate_to_predictions_page
            ):
        super().__init__()
        self.navigate_to_definitions = navigate_to_definitions
        self.navigate_to_detailed_page = navigate_to_detailed_page
        self.navigate_to_predictions_page = navigate_to_predictions_page

        # State
        self.current_stock_symbol = ""
        self.current_ratios_table = pd.DataFrame()
        self.current_ai_assessment = ""
        self.current_stock_data = {}
        self.history_df = pd.DataFrame()

        # Tickers
        self.selected_market_ticker = "^GSPC"
        self.selected_vix_ticker = "^VIX"
        self.selected_tnx_ticker = "^TNX"

        # Layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left side
        left_layout = QVBoxLayout()

        welcome_label = QLabel("The Portfolio Strategist")
        welcome_label.setFont(QFont("Helvetica", 26))
        welcome_label.setAlignment(Qt.AlignLeft)
        left_layout.addWidget(welcome_label)

        # Stock Symbol
        stock_symbol_label = QLabel("Stock Symbol:")
        stock_symbol_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(stock_symbol_label)

        self.stock_input = QLineEdit()
        self.stock_input.setFont(QFont("Helvetica", 13))
        left_layout.addWidget(self.stock_input)

        # Period
        stock_period_label = QLabel("Stock Period:")
        stock_period_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(stock_period_label)

        self.stock_period_dropdown = QComboBox()
        self.stock_period_dropdown.setFont(QFont("Helvetica", 13))
        self.stock_period_dropdown.addItems(
                [
                    "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"
                    ])
        left_layout.addWidget(self.stock_period_dropdown)

        # Interval
        stock_interval_label = QLabel("Stock Interval:")
        stock_interval_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(stock_interval_label)

        self.stock_interval_dropdown = QComboBox()
        self.stock_interval_dropdown.setFont(QFont("Helvetica", 13))
        self.stock_interval_dropdown.addItems(
                [
                    "1m", "2m", "5m", "15m", "30m", "60m", "90m",
                    "1h", "1d", "5d", "1wk", "1mo", "3mo"
                    ])
        left_layout.addWidget(self.stock_interval_dropdown)

        # Forecasting Model
        forecasting_label = QLabel("Forecasting Model:")
        forecasting_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(forecasting_label)

        self.equation_dropdown = QComboBox()
        self.equation_dropdown.setFont(QFont("Helvetica", 13))
        self.equation_dropdown.addItems(
                [
                    "Geometric Brownian Motion",
                    "Geometric Brownian Motion with Mean Reversion",
                    "Geometric Brownian Motion External Macroeconomic Factors"
                    ])
        left_layout.addWidget(self.equation_dropdown)

        # Market Ticker
        market_ticker_label = QLabel("Market Ticker:")
        market_ticker_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(market_ticker_label)
        self.market_ticker_dropdown = QComboBox()
        self.market_ticker_dropdown.setFont(QFont("Helvetica", 13))
        market_ticker_map = {
            "^GSPC" : "S&P 500 (SPX)",
            "^DJI"  : "Dow Jones (DJIA)",
            "^IXIC" : "Nasdaq Composite (IXIC)",
            "^RUT"  : "Russell 2000 (RUT)",
            "^FTSE" : "FTSE 100 (UK)",
            "^GDAXI": "DAX (Germany)"
            }
        for ticker, desc in market_ticker_map.items():
            self.market_ticker_dropdown.addItem(desc, ticker)
        self.market_ticker_dropdown.setCurrentIndex(0)
        self.market_ticker_dropdown.currentIndexChanged.connect(self.on_market_ticker_changed)
        left_layout.addWidget(self.market_ticker_dropdown)

        # VIX
        vix_ticker_label = QLabel("Volatility Ticker:")
        vix_ticker_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(vix_ticker_label)
        self.vix_ticker_dropdown = QComboBox()
        self.vix_ticker_dropdown.setFont(QFont("Helvetica", 13))
        vix_ticker_map = {
            "^VIX" : "CBOE VIX",
            "^VVIX": "VVIX",
            "^VXN" : "Nasdaq 100 Volatility Index",
            "^RVX" : "Russell 2000 Volatility Index",
            "^VXD" : "Dow 30 Volatility Index",
            }
        for ticker, desc in vix_ticker_map.items():
            self.vix_ticker_dropdown.addItem(desc, ticker)
        self.vix_ticker_dropdown.currentIndexChanged.connect(self.on_vix_ticker_changed)
        left_layout.addWidget(self.vix_ticker_dropdown)

        # TNX
        tnx_ticker_label = QLabel("Interest Rate Ticker:")
        tnx_ticker_label.setFont(QFont("Helvetica", 15))
        left_layout.addWidget(tnx_ticker_label)
        self.tnx_ticker_dropdown = QComboBox()
        self.tnx_ticker_dropdown.setFont(QFont("Helvetica", 13))
        tnx_ticker_map = {
            "^TNX": "10Y Treasury Yield",
            "^TYX": "30Y Treasury Yield",
            "^FVX": "5Y Treasury Yield",
            }
        for ticker, desc in tnx_ticker_map.items():
            self.tnx_ticker_dropdown.addItem(desc, ticker)
        self.tnx_ticker_dropdown.currentIndexChanged.connect(self.on_tnx_ticker_changed)
        left_layout.addWidget(self.tnx_ticker_dropdown)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFont(QFont("Helvetica", 13))
        left_layout.addWidget(self.progress_bar)

        # 1) "Populate Information"
        self.populate_info_button = QPushButton("Populate Information")
        self.populate_info_button.setFont(QFont("Helvetica", 15))
        self.populate_info_button.setFixedHeight(40)
        self.populate_info_button.clicked.connect(self.populate_information)
        left_layout.addWidget(self.populate_info_button)

        # 2) "Stock Detailed Reports"
        self.detailed_button = QPushButton("Stock Detailed Reports")
        self.detailed_button.setFont(QFont("Helvetica", 15))
        self.detailed_button.setFixedHeight(40)
        self.detailed_button.setEnabled(False)
        self.detailed_button.clicked.connect(
                lambda: self.navigate_to_detailed_page(
                        self.current_stock_data,
                        self.current_ratios_table,
                        self.current_ai_assessment,
                        self.current_stock_symbol
                        )
                )
        left_layout.addWidget(self.detailed_button)

        # 3) "Stock Analysis/Predictions"
        self.forecast_button = QPushButton("Stock Analysis/Predictions")
        self.forecast_button.setFont(QFont("Helvetica", 15))
        self.forecast_button.setFixedHeight(40)
        self.forecast_button.setEnabled(False)
        self.forecast_button.clicked.connect(self.navigate_to_predictions_page)
        left_layout.addWidget(self.forecast_button)

        # 4) "Financial Definitions"
        self.definitions_button = QPushButton("Financial Definitions")
        self.definitions_button.setFont(QFont("Helvetica", 15))
        self.definitions_button.setFixedHeight(40)
        self.definitions_button.clicked.connect(self.navigate_to_definitions)
        left_layout.addWidget(self.definitions_button)

        main_layout.addLayout(left_layout, 2)

        # Right side => Logs
        right_layout = QVBoxLayout()
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Courier", 13))
        right_layout.addWidget(self.logs_display)

        main_layout.addLayout(right_layout, 3)

        self.init_logging()

        # Worker references
        self.detail_worker = None
        self.forecast_worker = None

    def init_logging(self):
        self.emitter = EmittingStream()
        self.emitter.text_written.connect(self.append_log)
        sys.stdout = self.emitter
        sys.stderr = self.emitter

    def append_log(self, text):
        self.logs_display.append(text)

    def on_market_ticker_changed(self):
        selected_data = self.market_ticker_dropdown.itemData(self.market_ticker_dropdown.currentIndex())
        self.selected_market_ticker = selected_data

    def on_vix_ticker_changed(self):
        selected_data = self.vix_ticker_dropdown.itemData(self.vix_ticker_dropdown.currentIndex())
        self.selected_vix_ticker = selected_data

    def on_tnx_ticker_changed(self):
        selected_data = self.tnx_ticker_dropdown.itemData(self.tnx_ticker_dropdown.currentIndex())
        self.selected_tnx_ticker = selected_data

    def populate_information(self):
        """
        If Stock Detailed data doesn't already exist, fetch it.
        Forecast is always re-fetched (because user might have changed period/interval).
        """
        stock_symbol = self.stock_input.text().strip().upper()
        stock_period = self.stock_period_dropdown.currentText()
        stock_interval = self.stock_interval_dropdown.currentText()

        if not stock_symbol:
            self.logs_display.append("Please enter a valid stock symbol.")
            return

        self.current_stock_symbol = stock_symbol
        self.detailed_button.setEnabled(False)
        self.forecast_button.setEnabled(False)
        self.progress_bar.setValue(0)

        # Only run detail worker if we don't already have data for stock_data
        # e.g. user re-clicked "Populate Information," we skip re-fetching detailed
        # if we have self.current_stock_data already.
        if not self.current_stock_data:
            self.detail_worker = StockWorker(stock_symbol)
            self.detail_worker.progress.connect(self.update_progress)
            self.detail_worker.finished.connect(self.on_detailed_fetch_finished)
            self.detail_worker.start()
        else:
            self.logs_display.append("Using cached Stock Detailed data (no re-fetch).")

        # Always run forecast worker
        self.forecast_worker = ForecastWorker(stock_symbol, stock_period, stock_interval)
        self.forecast_worker.finished.connect(self.on_forecast_fetch_finished)
        self.forecast_worker.start()

    def on_detailed_fetch_finished(self, stock_data, ratios_table, ai_assessment):
        """
        Detailed page data loaded.
        """
        if stock_data:
            self.current_stock_data = stock_data
            self.current_ratios_table = ratios_table
            self.current_ai_assessment = ai_assessment
            self.logs_display.append("Detailed data (Stock & AI) fetched successfully.")
        else:
            self.logs_display.append("No stock data found, or an error occurred in Detailed fetch.")

        self.progress_bar.setValue(100)
        self.check_if_all_fetch_done()

    def on_forecast_fetch_finished(self, df):
        """
        Forecast data loaded => store it for the Predictions page.
        """
        self.history_df = df
        if df.empty:
            self.logs_display.append("No historical data for forecasting, or an error occurred.")
        else:
            self.logs_display.append("Forecast (historical) data fetched successfully.")

        self.check_if_all_fetch_done()

    def check_if_all_fetch_done(self):
        """
        Once both detail_worker (if used) and forecast_worker are done, log completion
        and enable the two main action buttons.
        """
        detail_done = True  # default
        if self.detail_worker is not None:
            detail_done = not self.detail_worker.isRunning()

        forecast_done = True  # default
        if self.forecast_worker is not None:
            forecast_done = not self.forecast_worker.isRunning()

        if detail_done and forecast_done:
            self.logs_display.append(
                    "Completed fetching both Stock Detailed Reports and Stock Analysis/Prediction."
                    )
            self.detailed_button.setEnabled(True)
            if not self.history_df.empty:
                self.forecast_button.setEnabled(True)
            else:
                self.logs_display.append("Cannot enable Stock Analysis/Predictions - no historical data.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        print(f"Progress updated to {value}%.")


# --------------------------------------------------------------------------
#             Main Window / Application Setup with QStackedWidget
# --------------------------------------------------------------------------
class MainApp(QWidget):
    """
    This class holds all pages in a QStackedWidget:
     - HomePage
     - DefinitionsPage
     - DetailedPage
     - AnalysisPredictionsPage
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Portfolio Strategist")
        self.setGeometry(100, 100, 1600, 900)

        self.stacked_widget = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Create pages
        self.definitions_page = DefinitionsPage(self.show_home_page)
        self.detailed_page = DetailedPage(self.show_home_page)
        self.predictions_page = AnalysisPredictionsPage(self.show_home_page)

        # The HomePage needs callbacks to navigate
        self.home_page = HomePage(
                navigate_to_definitions = self.show_definitions_page,
                navigate_to_detailed_page = self.show_detailed_page,
                navigate_to_predictions_page = self.show_predictions_page
                )

        # Add them
        self.stacked_widget.addWidget(self.home_page)  # index 0
        self.stacked_widget.addWidget(self.definitions_page)  # index 1
        self.stacked_widget.addWidget(self.detailed_page)  # index 2
        self.stacked_widget.addWidget(self.predictions_page)  # index 3

        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_definitions_page(self):
        # Build definitions data
        definitions_data = []
        for name in RATIO_DEFINITIONS.keys():
            definitions_data.append(
                    {
                        'Category'  : 'Financial Ratio',
                        'Name'      : name,
                        'Definition': RATIO_DEFINITIONS.get(name, {}).get('Definition', 'N/A'),
                        'Formula'   : RATIO_DEFINITIONS.get(name, {}).get('Formula', 'N/A')
                        })
        for category, indicators in MACRO_ECONOMIC_INDICATORS.items():
            for ticker, details in indicators.items():
                definitions_data.append(
                        {
                            'Category'  : category,
                            'Name'      : f"{ticker} - {details.get('Definition', 'N/A')}",
                            'Definition': details.get('Purpose', 'N/A'),
                            'Formula'   : 'N/A'
                            })

        df = pd.DataFrame(definitions_data)
        self.definitions_page.populate_definitions(df)
        self.stacked_widget.setCurrentWidget(self.definitions_page)

    def show_detailed_page(self, stock_data, ratios_table, ai_assessment, symbol):
        self.detailed_page.populate_tables(stock_data, ratios_table, ai_assessment, symbol)
        self.stacked_widget.setCurrentWidget(self.detailed_page)

    def show_predictions_page(self):
        """
        If user presses 'Stock Analysis/Predictions' on the home page,
        we switch to AnalysisPredictionsPage with the existing data.
        """
        if not self.home_page.current_stock_symbol:
            QMessageBox.warning(self, "No Symbol", "Please populate information first!")
            return

        if self.home_page.history_df.empty:
            QMessageBox.warning(self, "No Historical Data", "No historical data for forecasting.")
            return

        # Gather forecast inputs
        equation_type = self.home_page.equation_dropdown.currentText()
        mk = self.home_page.selected_market_ticker
        vx = self.home_page.selected_vix_ticker
        tx = self.home_page.selected_tnx_ticker

        df = self.home_page.history_df
        ratios_table = self.home_page.current_ratios_table
        symbol = self.home_page.current_stock_symbol
        stock_period = self.home_page.stock_period_dropdown.currentText()
        stock_interval = self.home_page.stock_interval_dropdown.currentText()

        self.predictions_page.populate_forecast(
                df, ratios_table, symbol,
                equation_type, mk, vx, tx,
                stock_period, stock_interval  # pass period so we can pick the correct forecast_days
                )
        self.stacked_widget.setCurrentWidget(self.predictions_page)

    def closeEvent(self, event):
        try:
            # If the user is in the middle of "Populate Information"
            if self.home_page.detail_worker and self.home_page.detail_worker.isRunning():
                self.home_page.detail_worker.quit()
                self.home_page.detail_worker.wait()
            if self.home_page.forecast_worker and self.home_page.forecast_worker.isRunning():
                self.home_page.forecast_worker.quit()
                self.home_page.forecast_worker.wait()
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            # Restore stdout/stderr
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            event.accept()


def run_gui():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_gui()