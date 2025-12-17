from io import BytesIO
from pathlib import Path

import pandas as pd

# Import adapted financia modules - handle missing lib directory gracefully
try:
    from .lib.ai_analyzer import analyze_stock_with_news
    from .lib.analysis_utils import (
        DEFAULT_BENCHMARK,
        build_decision_support,
        build_forecast_error_rows,
        build_market_overview,
        calculate_risk_statistics,
        generate_risk_insights,
    )
    from .lib.investment_utils import calculate_purchase_plan, get_current_price, summarize_forecast
    from .lib.pdf_generator import PDFGenerator
    from .lib.stock_app import StockApp
    from .lib.stock_definitions import RATIO_DEFINITIONS
    from .lib.stock_fetcher import StockFetcher
    from .lib.stock_ratio import StockRatio
    from .lib.stock_statistics import calculate_statistics, forecast_stock_prices, shift_forecast_to_actual_dates

    LIB_AVAILABLE = True
except ImportError:
    # lib directory not available - stock analysis features will be disabled
    StockApp = None
    StockFetcher = None
    StockRatio = None
    calculate_statistics = None
    forecast_stock_prices = None
    shift_forecast_to_actual_dates = None
    get_current_price = None
    calculate_purchase_plan = None
    summarize_forecast = None
    build_decision_support = None
    build_forecast_error_rows = None
    build_market_overview = None
    calculate_risk_statistics = None
    generate_risk_insights = None
    analyze_stock_with_news = None
    PDFGenerator = None
    RATIO_DEFINITIONS = {}
    DEFAULT_BENCHMARK = "^GSPC"
    LIB_AVAILABLE = False


class StockAnalysisService:
    """Service class to handle stock analysis operations"""

    def __init__(self):
        if not LIB_AVAILABLE:
            raise ImportError("Stock analysis library not available. The lib directory is missing.")
        self.stock_app = StockApp()
        # Update offline data path for Django
        self.offline_data_path = Path(__file__).parent / "resources" / "offline_data"
        self.offline_data_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _serialize_history(history_df: pd.DataFrame) -> list:
        if history_df is None or history_df.empty:
            return []
        records = []
        columns = [
            col for col in ["Date", "Open", "High", "Low", "Close", "Adj_Close", "Volume"] if col in history_df.columns
        ]
        for _, row in history_df.iterrows():
            entry = {}
            for column in columns:
                value = row.get(column)
                key = column.lower()
                if isinstance(value, pd.Timestamp):
                    entry[key] = value.isoformat()
                elif pd.isna(value):
                    entry[key] = None
                elif column == "Volume":
                    try:
                        entry[key] = int(value)
                    except (TypeError, ValueError):
                        entry[key] = None
                else:
                    try:
                        entry[key] = float(value)
                    except (TypeError, ValueError):
                        entry[key] = value
            records.append(entry)
        return records

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
        forecast_errors = []
        if not history_df.empty:
            equation_type = equation_type or "Geometric Brownian Motion External Macroeconomic Factors"
            forecast_df = self.stock_app.forecast_prices_advanced(
                history_df, symbol, ratios_table, "1d", equation_type=equation_type, forecast_days=forecast_days
            )
            if build_forecast_error_rows:
                forecast_errors = build_forecast_error_rows(history_df, forecast_df)

        benchmark_symbol = DEFAULT_BENCHMARK
        risk_metrics = {}
        risk_insights = []
        market_overview = {}
        decision_support = {}
        history_records = self._serialize_history(history_df)
        if calculate_risk_statistics and not history_df.empty:
            risk_metrics, _ = calculate_risk_statistics(history_df, benchmark_symbol)
            if generate_risk_insights:
                risk_insights = generate_risk_insights(risk_metrics, symbol)
            if build_market_overview:
                market_overview = build_market_overview(history_df, symbol, benchmark_symbol)
            if build_decision_support:
                decision_support = build_decision_support(
                    ratios_table,
                    ai_assessment,
                    history_df,
                    benchmark_symbol,
                    risk_metrics,
                )
        elif build_decision_support:
            decision_support = build_decision_support(ratios_table, ai_assessment, history_df, benchmark_symbol)

        return {
            "stock_data": stock_data,
            "ratios_table": ratios_table.to_dict("records") if not ratios_table.empty else [],
            "ai_assessment": ai_assessment,
            "forecast_data": forecast_df.to_dict("records")
            if forecast_df is not None and not forecast_df.empty
            else [],
            "news_html": news_html,
            "history_data": history_records,
            "risk_metrics": risk_metrics,
            "risk_insights": risk_insights,
            "market_overview": market_overview,
            "decision_support": decision_support,
            "forecast_errors": forecast_errors,
            "benchmark_symbol": benchmark_symbol,
        }

    def generate_pdf_report(
        self,
        symbol,
        stock_data,
        ratios_table,
        ai_assessment,
        *,
        forecast_summary=None,
        forecast_statistics=None,
        risk_metrics=None,
        risk_insights=None,
        market_overview=None,
        decision_support=None,
        output_path=None,
    ):
        """Generate PDF report. Returns bytes if no output_path is provided."""
        ratios_df = pd.DataFrame(ratios_table) if ratios_table else pd.DataFrame()

        generator = PDFGenerator(
            stock_symbol=symbol,
            stock_data=stock_data or {},
            ratios_table=ratios_df,
            ai_assessment=ai_assessment,
            ratio_definitions=RATIO_DEFINITIONS,
            forecast_summary=forecast_summary,
            forecast_statistics=forecast_statistics,
            risk_metrics=risk_metrics,
            risk_insights=risk_insights,
            market_overview=market_overview,
            decision_support=decision_support,
        )

        if output_path:
            generator.generate_pdf(output_path)
            return output_path

        buffer = BytesIO()
        generator.generate_pdf(buffer)
        buffer.seek(0)
        return buffer.getvalue()
