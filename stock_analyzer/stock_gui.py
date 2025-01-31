# stock_gui.py

import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
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
        """
        Overrides the write method to emit the text to the QTextEdit.
        """
        self.text_written.emit(str(text))

    def flush(self):
        """
        Overrides the flush method. Not used but required for file-like objects.
        """
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


class StockGUI(QWidget):
    """
    The GUI for your Stock Analyzer, built on PySide6.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Stock Analyzer")
        self.setGeometry(100, 100, 1200, 700)  # Increased width and height to accommodate logs and AI assessment

        # Create the main horizontal layout
        self.main_layout = QHBoxLayout()

        # Left side layout (existing components)
        self.left_layout = QVBoxLayout()

        # Input Label
        self.input_label = QLabel("Enter Stock Symbol:")
        self.left_layout.addWidget(self.input_label)

        # Input Field
        self.stock_input = QLineEdit()
        self.left_layout.addWidget(self.stock_input)

        # Fetch Button
        self.fetch_button = QPushButton("Fetch Stock Data")
        self.fetch_button.clicked.connect(self.start_fetching)
        self.left_layout.addWidget(self.fetch_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.progress_bar)

        # Stock Details Table
        self.stock_table = QTableWidget()
        self.left_layout.addWidget(QLabel("Stock Details"))
        self.left_layout.addWidget(self.stock_table)

        # Ratios Table
        self.ratios_table = QTableWidget()
        self.left_layout.addWidget(QLabel("Stock Ratios"))
        self.left_layout.addWidget(self.ratios_table)

        # Definitions Table
        self.definitions_table = QTableWidget()
        self.left_layout.addWidget(QLabel("Ratio Definitions"))
        self.left_layout.addWidget(self.definitions_table)

        # Logs Display
        self.logs_label = QLabel("Logs")
        self.left_layout.addWidget(self.logs_label)

        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.left_layout.addWidget(self.logs_display)

        # Add the left layout to the main layout
        self.main_layout.addLayout(self.left_layout, 2)  # Assign stretch factor 2 to the left layout

        # Right side layout (AI assessment and PDF)
        self.right_layout = QVBoxLayout()

        # AI Assessment Label
        self.ai_label = QLabel("AI Analysis: Overall Stock Assessment")
        self.ai_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.ai_label)

        # AI Assessment Display
        self.ai_display = QTextEdit()
        self.ai_display.setReadOnly(True)
        self.right_layout.addWidget(self.ai_display)

        # Save PDF Button
        self.save_pdf_button = QPushButton("Save Report as PDF")
        self.save_pdf_button.clicked.connect(self.save_pdf)
        self.save_pdf_button.setEnabled(False)  # Disabled until data is fetched
        self.right_layout.addWidget(self.save_pdf_button)

        # Add the right layout to the main layout
        self.main_layout.addLayout(self.right_layout, 3)  # Assign stretch factor 3 to the right layout

        self.setLayout(self.main_layout)

        # Initialize the custom stream and redirect stdout and stderr
        self.init_logging()

        # Variables to hold fetched data
        self.current_stock_symbol = ""
        self.current_stock_data = {}
        self.current_ratios_table = pd.DataFrame()
        self.current_ai_assessment = ""

    def init_logging(self):
        """
        Initializes the logging by redirecting stdout and stderr to the logs_display QTextEdit.
        """
        # Create instances of EmittingStream for stdout and stderr
        self.emitter = EmittingStream()
        self.emitter.text_written.connect(self.append_log)

        # Redirect sys.stdout and sys.stderr
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

        # Initialize and start the worker thread
        self.worker = StockWorker(stock_symbol)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.populate_tables)
        self.worker.start()

        # Disable the fetch button to prevent multiple fetches
        self.fetch_button.setEnabled(False)
        self.save_pdf_button.setEnabled(False)
        self.ai_display.clear()
        self.stock_table.clear()
        self.ratios_table.clear()
        self.definitions_table.clear()
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
                    'Formula': RATIO_DEFINITIONS.get(name, {}).get('Formula', 'N/A')
                }
                for name in ratios_table['Ratio Name']
            ]
            definitions_df = pd.DataFrame(definitions_data)
            self.populate_table(self.definitions_table, definitions_df)
            self.logs_display.append("Ratio definitions populated.")

        if ai_assessment:
            self.ai_display.setPlainText(ai_assessment)
            self.logs_display.append("AI assessment displayed.")
        else:
            self.ai_display.setPlainText("No AI assessment available.")
            self.logs_display.append("No AI assessment available.")

        # Reset progress bar and re-enable the fetch button and PDF button
        self.progress_bar.setValue(100)
        self.fetch_button.setEnabled(True)
        self.save_pdf_button.setEnabled(True)
        self.logs_display.append("Data fetch and analysis complete.")

        # Prompt user to save as PDF
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

        elif isinstance(data, dict):
            # Dictionary of stock details
            table.setRowCount(len(data))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Metric", "Value"])

            for row, (key, value) in enumerate(data.items()):
                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(value)))

    def prompt_save_pdf(self):
        """
        Prompts the user with a dialog to decide whether to save the report as a PDF.
        If yes, opens a file dialog to choose the save location.
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

        # Open a file dialog to choose the save location
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report as PDF",
            f"{self.current_stock_symbol}_stock_report.pdf",
            "PDF Files (*.pdf)",
            options=options
        )
        if not file_path:
            self.logs_display.append("PDF save cancelled by user.")
            return  # User cancelled the save dialog

        try:
            # Generate the PDF using the PDFGenerator module
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
            # Restore original stdout and stderr
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