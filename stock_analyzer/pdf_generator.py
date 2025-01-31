# pdf_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet


class PDFGenerator:
    def __init__(self, stock_symbol, stock_data, ratios_table, ai_assessment, ratio_definitions):
        """
        Initializes the PDFGenerator with necessary data.

        :param stock_symbol: The stock symbol (e.g., 'AAPL')
        :param stock_data: Dictionary containing stock details
        :param ratios_table: pandas DataFrame containing stock ratios
        :param ai_assessment: String containing AI-generated assessment
        :param ratio_definitions: Dictionary containing definitions and formulas for ratios
        """
        self.stock_symbol = stock_symbol
        self.stock_data = stock_data
        self.ratios_table = ratios_table
        self.ai_assessment = ai_assessment
        self.ratio_definitions = ratio_definitions
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter  # Set as instance variables

    def generate_pdf(self, file_path):
        """
        Generates and saves the PDF report.

        :param file_path: The path where the PDF will be saved
        """
        c = canvas.Canvas(file_path, pagesize=letter)
        self.width, self.height = letter  # Ensure width and height are set

        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(self.width / 2.0, self.height - 50, f"Stock Report: {self.stock_symbol}")

        # Draw a line below the title
        c.setStrokeColor(colors.gray)
        c.setLineWidth(1)
        c.line(50, self.height - 55, self.width - 50, self.height - 55)

        # Stock Details
        self._add_stock_details(c, self.height - 80)

        # Ratios as Text
        self._add_ratios_text(c, self.height - 150)

        # Ratio Definitions
        self._add_ratio_definitions(c, self.height - 400)

        # AI Assessment
        self._add_ai_assessment(c, self.height - 500)

        # Save the PDF
        c.save()

    def _add_stock_details(self, c, y_position):
        """
        Adds stock details to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        """
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Stock Details:")
        c.setFont("Helvetica", 10)
        y = y_position - 20
        for key, value in self.stock_data.items():
            text = f"{key}: {value}"
            c.drawString(60, y, text)
            y -= 15
            if y < 100:
                c.showPage()
                y = self.height - 50
        self.current_y = y

    def _add_ratios_text(self, c, y_position):
        """
        Adds stock ratios as formatted text to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        """
        if self.ratios_table is None or self.ratios_table.empty:
            return

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Stock Ratios:")
        y = y_position - 20

        # Debug: Print the columns of ratios_table
        print("Ratios Table Columns:", self.ratios_table.columns.tolist())

        # Check if 'Value' column exists
        if 'Value' not in self.ratios_table.columns:
            print("Error: 'Value' column not found in ratios_table.")
            return

        # Iterate through each ratio and display as text
        for index, row in self.ratios_table.iterrows():
            ratio_name = row.get('Ratio Name', 'N/A')
            ratio_value = row.get('Value', 'N/A')  # Safely get 'Value' column

            # Format the ratio information
            ratio_text = f"<b>{ratio_name}:</b> {ratio_value}"
            p = Paragraph(ratio_text, self.styles['Normal'])
            w, h = p.wrap(500, 1000)
            if y - h < 100:
                c.showPage()
                y = self.height - 50

            p.drawOn(c, 60, y - h)
            y -= h + 10

        self.current_y = y

    def _add_ratio_definitions(self, c, y_position):
        """
        Adds ratio definitions to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        """
        if self.ratios_table is None or self.ratios_table.empty:
            return

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Ratio Definitions:")
        y = y_position - 20

        for ratio_name in self.ratios_table['Ratio Name']:
            definition = self.ratio_definitions.get(ratio_name, {}).get('Definition', 'N/A')
            formula = self.ratio_definitions.get(ratio_name, {}).get('Formula', 'N/A')

            # Ratio Name
            c.setFont("Helvetica-Bold", 12)
            c.drawString(60, y, f"{ratio_name}:")
            y -= 15

            # Definition
            c.setFont("Helvetica", 10)
            text = f"Definition: {definition}"
            c.drawString(70, y, text)
            y -= 15

            # Formula
            text = f"Formula: {formula}"
            c.drawString(70, y, text)
            y -= 25

            if y < 100:
                c.showPage()
                y = self.height - 50

        self.current_y = y

    def _add_ai_assessment(self, c, y_position):
        """
        Adds AI assessment to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        """
        if not self.ai_assessment:
            return

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "AI Analysis: Overall Stock Assessment")
        y = y_position - 20

        c.setFont("Helvetica", 10)
        paragraphs = self.ai_assessment.split('\n')
        for para in paragraphs:
            p = Paragraph(para, self.styles['Normal'])
            w, h = p.wrap(500, 1000)
            if y - h < 100:
                c.showPage()
                y = self.height - 50
            p.drawOn(c, 60, y - h)
            y -= h + 10

        self.current_y = y