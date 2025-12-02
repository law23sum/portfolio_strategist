from django.contrib import admin
from .models import (
    StockAnalysis,
    InvestmentPlan,
    PersonalLoanAnalysis,
    MarketDataCredential,
)


@admin.register(StockAnalysis)
class StockAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'user', 'analysis_date', 'forecast_days']
    list_filter = ['analysis_date', 'symbol']
    search_fields = ['symbol', 'user__email']
    readonly_fields = ['analysis_date']


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ['stock_analysis', 'user', 'investment_amount', 'created_at']
    list_filter = ['created_at', 'alert_enabled']
    search_fields = ['user__email', 'stock_analysis__symbol']


@admin.register(PersonalLoanAnalysis)
class PersonalLoanAnalysisAdmin(admin.ModelAdmin):
    list_display = ['user', 'analysis_date']
    list_filter = ['analysis_date']
    search_fields = ['user__email']


@admin.register(MarketDataCredential)
class MarketDataCredentialAdmin(admin.ModelAdmin):
    list_display = ['provider', 'label', 'is_active', 'updated_at']
    list_filter = ['provider', 'is_active']
    search_fields = ['label']
    ordering = ['provider']
