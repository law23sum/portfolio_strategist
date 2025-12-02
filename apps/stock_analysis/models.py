from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MarketDataCredential(models.Model):
    """API keys for external market data providers."""

    PROVIDER_POLYGON = 'polygon'
    PROVIDER_ALPHA = 'alpha_vantage'
    PROVIDER_CHOICES = (
        (PROVIDER_POLYGON, 'Polygon.io'),
        (PROVIDER_ALPHA, 'Alpha Vantage'),
    )

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    label = models.CharField(max_length=128, blank=True,
                             help_text='Optional note to help identify this key')
    api_key = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Market Data Credential'
        verbose_name_plural = 'Market Data Credentials'
        ordering = ['provider']

    def __str__(self):
        label = self.label or dict(self.PROVIDER_CHOICES).get(self.provider, self.provider)
        return f"{label} ({'active' if self.is_active else 'inactive'})"


class StockAnalysis(models.Model):
    """Store stock analysis results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_analyses')
    symbol = models.CharField(max_length=10, db_index=True)
    analysis_date = models.DateTimeField(auto_now_add=True)
    
    stock_data = models.JSONField(default=dict)
    ratios_table = models.JSONField(default=dict)
    ai_assessment = models.TextField(blank=True)
    forecast_data = models.JSONField(default=dict, null=True, blank=True)
    news_html = models.TextField(blank=True)
    history_data = models.JSONField(default=list, blank=True)
    forecast_errors = models.JSONField(default=list, blank=True)
    risk_metrics = models.JSONField(default=dict, blank=True)
    risk_insights = models.JSONField(default=list, blank=True)
    market_overview = models.JSONField(default=dict, blank=True)
    decision_support = models.JSONField(default=dict, blank=True)
    benchmark_symbol = models.CharField(max_length=20, default='^GSPC')
    
    forecast_days = models.IntegerField(default=365)
    equation_type = models.CharField(max_length=100, default='Geometric Brownian Motion External Macroeconomic Factors')
    
    class Meta:
        ordering = ['-analysis_date']
        verbose_name_plural = 'Stock Analyses'
        indexes = [
            models.Index(fields=['user', '-analysis_date']),
            models.Index(fields=['symbol']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.user.email} - {self.analysis_date.date()}"


class InvestmentPlan(models.Model):
    """Store investment plans and alerts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_plans')
    stock_analysis = models.ForeignKey(StockAnalysis, on_delete=models.CASCADE, related_name='plans')
    
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    share_quantity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    forecast_summary = models.JSONField(default=dict)
    
    alert_enabled = models.BooleanField(default=False)
    alert_email = models.EmailField(blank=True)
    alert_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Plan for {self.stock_analysis.symbol} - {self.user.email}"


class PersonalLoanAnalysis(models.Model):
    """Store personal loan analysis results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_analyses')
    csv_file = models.FileField(upload_to='loan_analyses/')
    analysis_date = models.DateTimeField(auto_now_add=True)
    
    individual_amounts = models.JSONField(default=dict)
    total_amounts = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-analysis_date']
        verbose_name_plural = 'Personal Loan Analyses'
    
    def __str__(self):
        return f"Loan Analysis - {self.user.email} - {self.analysis_date.date()}"
