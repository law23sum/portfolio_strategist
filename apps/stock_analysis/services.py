import os
from pathlib import Path
from django.conf import settings
import pandas as pd

# Import adapted financia modules
from .lib.stock_app import StockApp
from .lib.stock_fetcher import StockFetcher
from .lib.stock_ratio import StockRatio
from .lib.stock_statistics import (
    calculate_statistics, forecast_stock_prices, shift_forecast_to_actual_dates
)
from .lib.investment_utils import (
    get_current_price, calculate_purchase_plan, summarize_forecast
)
from .lib.ai_analyzer import analyze_stock_with_news
from .lib.pdf_generator import PDFGenerator
from .lib.stock_definitions import RATIO_DEFINITIONS


class StockAnalysisService:
    """Service class to handle stock analysis operations"""
    
    def __init__(self):
        self.stock_app = StockApp()
        # Update offline data path for Django
        self.offline_data_path = Path(__file__).parent / 'resources' / 'offline_data'
        self.offline_data_path.mkdir(parents=True, exist_ok=True)
    
    def analyze_stock(self, symbol, forecast_days=365, equation_type=None):
        """Perform complete stock analysis"""
        # Fetch stock data
        stock_data = self.stock_app.fetch_stock_data(symbol)
        if not stock_data:
            return None
        
        # Fetch news
        news_html = self.stock_app.fetch_stock_news(symbol)
        
        # Analyze ratios
        ratios_table = self.stock_app.analyze_stock(stock_data)
        
        # Fetch history
        history_df = self.stock_app.fetch_stock_history(symbol, period="1y", interval="1d")
        
        # AI Analysis
        ai_assessment = ""
        if not ratios_table.empty:
            ai_assessment = analyze_stock_with_news(ratios_table, news_html)
        
        # Forecast
        forecast_df = None
        if not history_df.empty:
            equation_type = equation_type or "Geometric Brownian Motion External Macroeconomic Factors"
            forecast_df = self.stock_app.forecast_prices_advanced(
                history_df, symbol, ratios_table, "1d", 
                equation_type=equation_type,
                forecast_days=forecast_days
            )
        
        return {
            'stock_data': stock_data,
            'ratios_table': ratios_table.to_dict('records') if not ratios_table.empty else [],
            'ai_assessment': ai_assessment,
            'forecast_data': forecast_df.to_dict('records') if forecast_df is not None and not forecast_df.empty else [],
            'news_html': news_html,
        }
    
    def generate_pdf_report(self, symbol, stock_data, ratios_table, ai_assessment, output_path):
        """Generate PDF report"""
        ratios_df = None
        if ratios_table:
            ratios_df = pd.DataFrame(ratios_table)
        
        generator = PDFGenerator(symbol, stock_data, ratios_df, ai_assessment, RATIO_DEFINITIONS)
        generator.generate_pdf(output_path)
        return output_path

