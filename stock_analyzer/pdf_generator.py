# pdf_generator.py

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
        """
        self.stock_symbol = stock_symbol
        self.stock_data = stock_data
        self.ratios_table = ratios_table
        self.ai_assessment = ai_assessment
        self.ratio_definitions = ratio_definitions
        self.styles = getSampleStyleSheet()

    def generate_pdf(self, file_path):
        """
        Generates and saves the PDF report using ReportLab's Platypus.

        :param file_path: The path where the PDF will be saved
        """
        doc = SimpleDocTemplate(
                file_path,
                pagesize = letter,
                leftMargin = 50,
                rightMargin = 50,
                topMargin = 50,
                bottomMargin = 50
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

        # Stock Ratios (if available)
        if self.ratios_table is not None and not self.ratios_table.empty:
            story.append(Paragraph("Stock Ratios:", self.styles["Heading2"]))
            story.append(Spacer(1, 12))
            # Check if "Value" column exists; if not, use the second column.
            data = [["Ratio Name", "Value"]]
            if "Value" in self.ratios_table.columns:
                value_column = "Value"
            else:
                cols = self.ratios_table.columns.tolist()
                # If there is a second column, use it.
                value_column = cols[1] if len(cols) >= 2 else None

            for index, row in self.ratios_table.iterrows():
                ratio_name = row["Ratio Name"]
                ratio_value = row[value_column] if value_column else ""
                data.append([ratio_name, ratio_value])
            table = Table(data, colWidths = [200, 200])
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
                                ]))
            story.append(table)
            story.append(PageBreak())

        # AI Assessment (if available)
        if self.ai_assessment:
            story.append(Paragraph("AI Analysis: Overall Stock Assessment", self.styles["Heading2"]))
            story.append(Spacer(1, 12))
            for para in self.ai_assessment.split("\n"):
                story.append(Paragraph(para, self.styles["Normal"]))
                story.append(Spacer(1, 6))

        # Ratio Definitions (if available)
        # if self.ratios_table is not None and not self.ratios_table.empty:
        #     story.append(Paragraph("Ratio Definitions:", self.styles["Heading2"]))
        #     story.append(Spacer(1, 12))
        #     for ratio_name in self.ratios_table["Ratio Name"]:
        #         definition = self.ratio_definitions.get(ratio_name, {}).get("Definition")
        #         formula = self.ratio_definitions.get(ratio_name, {}).get("Formula")
        #         story.append(Paragraph(f"<b>{ratio_name}</b>", self.styles["Heading3"]))
        #         story.append(Paragraph(f"Definition: {definition}", self.styles["Normal"]))
        #         story.append(Paragraph(f"Formula: {formula}", self.styles["Normal"]))
        #         story.append(Spacer(1, 12))
        #     story.append(PageBreak())

        # Build PDF
        doc.build(story)