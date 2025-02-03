# stock_gui.py

import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit, QFileDialog, QMessageBox, QStackedWidget
    )
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont
from pdf_generator import PDFGenerator  # Corrected import

# Adjust your imports to point to the module where StockApp & RATIO_DEFINITIONS reside
from main import StockApp, RATIO_DEFINITIONS
from ai_analyzer import analyze_stock_with_news  # Ensure this import is correct


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
        # Create a new instance of StockApp for each worker thread
        self.stock_app = StockApp()

    def run(self):
        try:
            self.progress.emit(20)
            stock_data = self.stock_app.fetch_stock_data(self.stock_symbol)
            self.progress.emit(50)

            ratios_table = None
            ai_assessment = ""
            if stock_data:
                ratios_table = self.stock_app.analyze_stock(stock_data)
                self.progress.emit(80)
                combined_articles_html = self.stock_app.fetch_stock_news(self.stock_symbol)
                self.progress.emit(90)
                ai_assessment = analyze_stock_with_news(ratios_table, combined_articles_html)
            self.progress.emit(100)
            self.finished.emit(stock_data, ratios_table, ai_assessment)
        except Exception as e:
            print(f"Error in StockWorker: {e}")
            self.finished.emit({}, pd.DataFrame(), f"Error during fetching and analysis: {e}")


class HomePage(QWidget):
    """
    The Home Page of the application with a welcome message and navigation button.
    """

    def __init__(self, navigate_to_analysis):
        super().__init__()

        self.navigate_to_analysis = navigate_to_analysis

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Welcome Label
        welcome_label = QLabel("Welcome to The Portfolio Strategist")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Helvetica", 26))
        layout.addWidget(welcome_label)

        # Description
        description = QLabel("Analyze stock data, view AI-driven insights, and generate comprehensive PDF reports.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setFont(QFont("Helvetica", 16))
        layout.addWidget(description)

        # Navigate Button
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

        # Table to display definitions
        self.definitions_table = QTableWidget()
        layout.addWidget(self.definitions_table)

        # Button to go back (to Analysis page)
        back_button = QPushButton("Back")
        back_button.setFont(QFont("Helvetica", 16))
        back_button.setFixedHeight(40)
        back_button.clicked.connect(self.navigate_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def populate_definitions(self, definitions_df):
        """
        Populates the definitions table with the given DataFrame.
        """
        self.definitions_table.setRowCount(definitions_df.shape[0])
        self.definitions_table.setColumnCount(definitions_df.shape[1])
        self.definitions_table.setHorizontalHeaderLabels(definitions_df.columns.astype(str))
        for row in range(definitions_df.shape[0]):
            for col in range(definitions_df.shape[1]):
                item = QTableWidgetItem(str(definitions_df.iloc[row, col]))
                # Increase cell font size if desired
                item.setFont(QFont("Helvetica", 16))
                self.definitions_table.setItem(row, col, item)


class StockGUI(QWidget):
    """
    The GUI for your Stock Analyzer, built on PySide6.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("The Portfolio Strategist")
        self.setGeometry(100, 100, 1600, 900)

        # Initialize the stacked widget to manage multiple pages
        self.stacked_widget = QStackedWidget()

        # Create pages: Home, Analysis, and Definitions
        self.home_page = HomePage(self.show_analysis_page)
        self.analysis_page = self.create_analysis_page()
        self.definitions_page = DefinitionsPage(self.show_previous_page)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.definitions_page)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        self.init_logging()

        # Variables to hold fetched data
        self.current_stock_symbol = ""
        self.current_stock_data = {}
        self.current_ratios_table = pd.DataFrame()
        self.current_ai_assessment = ""

    def create_analysis_page(self):
        """
        Creates the main Stock Analysis page.
        """
        page = QWidget()
        page_layout = QHBoxLayout()

        # Left side layout
        left_layout = QVBoxLayout()

        # Input Label
        self.input_label = QLabel("Enter Stock Symbol:")
        self.input_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(self.input_label)

        # Input Field
        self.stock_input = QLineEdit()
        self.stock_input.setFont(QFont("Helvetica", 14))
        left_layout.addWidget(self.stock_input)

        # Fetch Button
        self.fetch_button = QPushButton("Fetch Stock Data")
        self.fetch_button.setFont(QFont("Helvetica", 16))
        self.fetch_button.setFixedHeight(40)
        self.fetch_button.clicked.connect(self.start_fetching)
        left_layout.addWidget(self.fetch_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFont(QFont("Helvetica", 14))
        left_layout.addWidget(self.progress_bar)

        # Stock Details Table
        stock_details_label = QLabel("Stock Details")
        stock_details_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(stock_details_label)

        self.stock_table = QTableWidget()
        left_layout.addWidget(self.stock_table)

        # Ratios Table
        ratios_table_label = QLabel("Stock Ratios")
        ratios_table_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(ratios_table_label)

        self.ratios_table = QTableWidget()
        left_layout.addWidget(self.ratios_table)

        # Logs Display
        self.logs_label = QLabel("Logs")
        self.logs_label.setFont(QFont("Helvetica", 16))
        left_layout.addWidget(self.logs_label)

        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Courier", 14))
        left_layout.addWidget(self.logs_display)

        page_layout.addLayout(left_layout, 2)

        # Right side layout (AI assessment and PDF)
        right_layout = QVBoxLayout()

        # AI Assessment Label
        self.ai_label = QLabel("AI Analysis: Overall Stock Assessment")
        self.ai_label.setAlignment(Qt.AlignCenter)
        self.ai_label.setFont(QFont("Helvetica", 18))
        right_layout.addWidget(self.ai_label)

        # AI Assessment Display
        self.ai_display = QTextEdit()
        self.ai_display.setReadOnly(True)
        self.ai_display.setFont(QFont("Helvetica", 16))
        right_layout.addWidget(self.ai_display)

        # Save PDF Button
        self.save_pdf_button = QPushButton("Save Report as PDF")
        self.save_pdf_button.setFont(QFont("Helvetica", 16))
        self.save_pdf_button.setFixedHeight(40)
        self.save_pdf_button.clicked.connect(self.save_pdf)
        self.save_pdf_button.setEnabled(False)
        right_layout.addWidget(self.save_pdf_button)

        # New: View Ratio Definitions Button (placed below Save Report as PDF)
        self.view_definitions_button = QPushButton("View Ratio Definitions")
        self.view_definitions_button.setFont(QFont("Helvetica", 16))
        self.view_definitions_button.setFixedHeight(40)
        self.view_definitions_button.clicked.connect(self.show_definitions_page)
        right_layout.addWidget(self.view_definitions_button)

        # Back to Home Button
        self.back_home_button = QPushButton("Back to Home")
        self.back_home_button.setFont(QFont("Helvetica", 16))
        self.back_home_button.setFixedHeight(40)
        self.back_home_button.clicked.connect(self.show_home_page)
        right_layout.addWidget(self.back_home_button)

        page_layout.addLayout(right_layout, 3)

        page.setLayout(page_layout)
        return page

    def show_analysis_page(self):
        """
        Switches the view to the Stock Analysis page.
        """
        self.stacked_widget.setCurrentWidget(self.analysis_page)

    def show_home_page(self):
        """
        Switches the view back to the Home Page.
        """
        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_definitions_page(self):
        """
        Switches to the Definitions page and populates the definitions table.
        """
        # Populate the definitions table using RATIO_DEFINITIONS directly.
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
        """
        Returns to the Analysis page from the Definitions page.
        """
        self.stacked_widget.setCurrentWidget(self.analysis_page)

    def init_logging(self):
        """
        Initializes the logging by redirecting stdout and stderr to the logs_display QTextEdit.
        """
        self.emitter = EmittingStream()
        self.emitter.text_written.connect(self.append_log)
        sys.stdout = self.emitter
        sys.stderr = self.emitter

    def append_log(self, text):
        """
        Appends text to the logs_display QTextEdit.
        """
        self.logs_display.append(text)

    def start_fetching(self):
        """
        Spins up a worker thread to fetch data without blocking the UI.
        """
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
        """Reflect the progress in the QProgressBar."""
        self.progress_bar.setValue(value)
        self.logs_display.append(f"Progress updated to {value}%.")

    def populate_tables(self, stock_data, ratios_table, ai_assessment):
        """
        Populate the Stock Details, Ratios, Definitions tables, and AI assessment once data is fetched.
        """
        self.current_stock_data = stock_data
        self.current_ratios_table = ratios_table
        self.current_ai_assessment = ai_assessment

        if stock_data:
            self.populate_table(self.stock_table, stock_data)
            self.logs_display.append("Stock details populated.")

        if ratios_table is not None and not ratios_table.empty:
            self.populate_table(self.ratios_table, ratios_table)
            self.logs_display.append("Stock ratios populated.")

            # Build definitions data for each ratio
            definitions_data = [
                {
                    'Ratio Name': name,
                    'Definition': RATIO_DEFINITIONS.get(name, {}).get('Definition', 'N/A'),
                    'Formula'   : RATIO_DEFINITIONS.get(name, {}).get('Formula', 'N/A')
                    }
                for name in ratios_table['Ratio Name']
                ]
            definitions_df = pd.DataFrame(definitions_data)
            self.populate_table(self.analysis_page.definitions_table, definitions_df)
            self.logs_display.append("Ratio definitions populated.")

        if ai_assessment:
            self.ai_display.setPlainText(ai_assessment)
            self.logs_display.append("AI assessment displayed.")
        else:
            self.ai_display.setPlainText("No AI assessment available.")
            self.logs_display.append("No AI assessment available.")

        self.progress_bar.setValue(100)
        self.fetch_button.setEnabled(True)
        self.save_pdf_button.setEnabled(True)
        self.logs_display.append("Data fetch and analysis complete.")

        self.prompt_save_pdf()

    def populate_table(self, table, data):
        """
        Helper function to populate QTableWidget with dict or DataFrame data.
        """
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
        """
        Prompts the user with a dialog to decide whether to save the report as a PDF.
        """
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
        """
        Save the current stock analysis as a PDF file.
        """
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
        """
        Handle the window close event to ensure that all threads are properly terminated.
        """
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
    """
    Convenience function to launch the GUI if called directly.
    """
    app = QApplication(sys.argv)
    window = StockGUI()
    window.show()
    sys.exit(app.exec())