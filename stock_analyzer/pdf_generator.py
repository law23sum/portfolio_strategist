from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
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
        :param performance: (Optional) List of performance details corresponding to each ratio.
        """
        self.stock_symbol = stock_symbol
        self.stock_data = stock_data
        self.ratios_table = ratios_table
        self.ai_assessment = ai_assessment
        self.ratio_definitions = ratio_definitions
        self.styles = getSampleStyleSheet()

    def generate_pdf(self, file_path):
        """
        Generates and saves the PDF report.

        :param file_path: The path where the PDF will be saved
        """
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        story = []

        # Title (on its own page)
        title = Paragraph(f"Stock Report: {self.stock_symbol}", self.styles["Title"])
        story.append(title)
        story.append(Spacer(1, 12))
        story.append(PageBreak())

        # Stock Details (new header starts on a new page)
        story.append(Paragraph("Stock Details:", self.styles["Heading2"]))
        story.append(Spacer(1, 12))
        for key, value in self.stock_data.items():
            text = f"<b>{key}:</b> {value}"
            story.append(Paragraph(text, self.styles["Normal"]))
            story.append(Spacer(1, 6))
        story.append(PageBreak())

        # Stock Ratios (if available) with Performance details
        if self.ratios_table is not None and not self.ratios_table.empty:
            story.append(Paragraph("Stock Ratios:", self.styles["Heading2"]))
            story.append(Spacer(1, 12))
            # Prepare a table with 3 columns: Ratio Name, Value, and Performance
            data = [["Ratio Name", "Value", "Performance"]]
            # Determine which column holds the value
            if "Value" in self.ratios_table.columns:
                value_column = "Value"
            else:
                cols = self.ratios_table.columns.tolist()
                value_column = cols[1] if len(cols) >= 2 else None

            for i, (_, row) in enumerate(self.ratios_table.iterrows()):
                ratio_name = row["Ratio Name"]
                ratio_value = row[value_column] if value_column else ""
                # If the "Performance" column exists, use its value; otherwise, default to "N/A"
                if "Performance" in self.ratios_table.columns:
                    perf_detail = row["Performance"]
                else:
                    perf_detail = "N/A"
                data.append([ratio_name, ratio_value, perf_detail])
            table = Table(data, colWidths = [150, 150, 150])
            table.setStyle(
                    TableStyle(
                            [
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ])
                    )
            story.append(table)
            story.append(PageBreak())

        # AI Assessment (if available)
        if self.ai_assessment:
            story.append(Paragraph("AI Analysis: Overall Stock Assessment", self.styles["Heading2"]))
            story.append(Spacer(1, 12))
            for para in self.ai_assessment.split("\n"):
                story.append(Paragraph(para, self.styles["Normal"]))
                story.append(Spacer(1, 6))

        # Build PDF
        doc.build(story)