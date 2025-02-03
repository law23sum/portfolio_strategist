# pdf_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd


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
        self.left_margin = 50
        self.right_margin = 50
        self.top_margin = 50
        self.bottom_margin = 50

    def generate_pdf(self, file_path):
        """
        Generates and saves the PDF report.

        :param file_path: The path where the PDF will be saved
        """
        c = canvas.Canvas(file_path, pagesize = letter)
        self.width, self.height = letter  # Ensure width and height are set

        # **Title (Fixed Font Size)**
        c.setFont("Helvetica-Bold", 14)  # Reduced from 20 to 14
        c.drawCentredString(self.width / 2.0, self.height - 50, f"Stock Report: {self.stock_symbol}")

        # **Draw a line below the title**
        c.setStrokeColor(colors.gray)
        c.setLineWidth(1)
        c.line(50, self.height - 55, self.width - 50, self.height - 55)

        # **Stock Details**
        self._add_stock_details(c, self.height - 80)

        # **Ratios as Text**
        self._add_ratios_text(c, self.height - 150)

        # **Ratio Definitions**
        self._add_ratio_definitions(c, self.height - 400)

        # **AI Assessment**
        self._add_ai_assessment(c, self.height - 500)

        # **Save the PDF**
        c.save()

    def _add_stock_details(self, c, y_position):
        """
        Adds stock details to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        :return: Updated y_position after adding stock details
        """
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.left_margin, y_position, "Stock Details:")
        y = y_position - 20
        c.setFont("Helvetica", 10)
        for key, value in self.stock_data.items():
            text = f"{key}: {value}"
            c.drawString(self.left_margin + 10, y, text)
            y -= 15
            if y < self.bottom_margin + 50:
                c.showPage()
                y = self.height - self.top_margin
                self._add_header(c, y)
                y -= 20
        return y

    def _add_ratios_text(self, c, y_position):
        """
        Adds stock ratios as formatted text to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        :return: Updated y_position after adding ratios
        """
        if self.ratios_table is None or self.ratios_table.empty:
            return y_position

        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.left_margin, y_position, "Stock Ratios:")
        y = y_position - 20

        # Check if 'Value' column exists
        if 'Value' not in self.ratios_table.columns:
            print("Error: 'Value' column not found in ratios_table.")
            return y

        # Iterate through each ratio and display as text
        for index, row in self.ratios_table.iterrows():
            ratio_name = row.get('Ratio Name', 'N/A')
            ratio_value = row.get('Value', 'N/A')  # Safely get 'Value' column

            # Format the ratio information
            ratio_text = f"<b>{ratio_name}:</b> {ratio_value}"
            p = Paragraph(ratio_text, self.styles['Normal'])
            w, h = p.wrap(self.width - self.left_margin - self.right_margin - 20, self.height)
            if y - h < self.bottom_margin + 50:
                c.showPage()
                y = self.height - self.top_margin
                self._add_header(c, y)
                y -= 20

            p.drawOn(c, self.left_margin + 10, y - h)
            y -= h + 10

        return y

    def _add_ratio_definitions(self, c, y_position):
        """
        Adds ratio definitions to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        :return: Updated y_position after adding ratio definitions
        """
        if self.ratios_table is None or self.ratios_table.empty:
            return y_position

        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.left_margin, y_position, "Ratio Definitions:")
        y = y_position - 20

        for ratio_name in self.ratios_table['Ratio Name']:
            definition = self.ratio_definitions.get(ratio_name, {}).get('Definition', 'N/A')
            formula = self.ratio_definitions.get(ratio_name, {}).get('Formula', 'N/A')

            # Ratio Name
            c.setFont("Helvetica-Bold", 12)
            c.drawString(self.left_margin + 10, y, f"{ratio_name}:")
            y -= 15

            # Definition
            c.setFont("Helvetica", 10)
            text = f"Definition: {definition}"
            p_def = Paragraph(text, self.styles['Normal'])
            w_def, h_def = p_def.wrap(self.width - self.left_margin - self.right_margin - 20, self.height)
            if y - h_def < self.bottom_margin + 50:
                c.showPage()
                y = self.height - self.top_margin
                self._add_header(c, y)
                y -= 20
            p_def.drawOn(c, self.left_margin + 20, y - h_def)
            y -= h_def + 10

            # Formula
            text = f"Formula: {formula}"
            p_form = Paragraph(text, self.styles['Normal'])
            w_form, h_form = p_form.wrap(self.width - self.left_margin - self.right_margin - 20, self.height)
            if y - h_form < self.bottom_margin + 50:
                c.showPage()
                y = self.height - self.top_margin
                self._add_header(c, y)
                y -= 20
            p_form.drawOn(c, self.left_margin + 20, y - h_form)
            y -= h_form + 20

        return y

    def _add_ai_assessment(self, c, y_position):
        """
        Adds AI assessment to the PDF.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing
        :return: Updated y_position after adding AI assessment
        """
        if not self.ai_assessment:
            return y_position

        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.left_margin, y_position, "AI Analysis: Overall Stock Assessment")
        y = y_position - 20

        c.setFont("Helvetica", 10)
        paragraphs = self.ai_assessment.split('\n')
        for para in paragraphs:
            p = Paragraph(para, self.styles['Normal'])
            w, h = p.wrap(self.width - self.left_margin - self.right_margin - 20, self.height)
            if y - h < self.bottom_margin + 50:
                c.showPage()
                y = self.height - self.top_margin
                self._add_header(c, y)
                y -= 20
            p.drawOn(c, self.left_margin + 10, y - h)
            y -= h + 10

        return y

    def _add_header(self, c, y_position):
        """
        Adds the header (Title and line) to a new page.

        :param c: The ReportLab canvas object
        :param y_position: The vertical position to start writing the header
        """
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(self.width / 2.0, y_position, f"Stock Report: {self.stock_symbol}")

        # Draw a line below the title
        y_position -= 10
        c.setStrokeColor(colors.gray)
        c.setLineWidth(1)
        c.line(self.left_margin, y_position, self.width - self.right_margin, y_position)
        y_position -= 20  # Space after the line