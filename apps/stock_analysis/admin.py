from django.contrib import admin

from .models import (
    InvestmentPlan,
    MarketDataCredential,
    PersonalLoanAnalysis,
    StockAnalysis,
    StockWatchlistEntry,
    StockWatchSnapshot,
)


@admin.register(StockAnalysis)
class StockAnalysisAdmin(admin.ModelAdmin):
    list_display = ["symbol", "user", "analysis_date", "forecast_days"]
    list_filter = ["analysis_date", "symbol"]
    search_fields = ["symbol", "user__email"]
    readonly_fields = ["analysis_date"]


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ["stock_analysis", "user", "investment_amount", "created_at"]
    list_filter = ["created_at", "alert_enabled"]
    search_fields = ["user__email", "stock_analysis__symbol"]


@admin.register(PersonalLoanAnalysis)
class PersonalLoanAnalysisAdmin(admin.ModelAdmin):
    list_display = ["user", "analysis_date"]
    list_filter = ["analysis_date"]
    search_fields = ["user__email"]


@admin.register(MarketDataCredential)
class MarketDataCredentialAdmin(admin.ModelAdmin):
    list_display = ["provider", "label", "is_active", "updated_at"]
    list_filter = ["provider", "is_active"]
    search_fields = ["label"]
    ordering = ["provider"]


@admin.register(StockWatchSnapshot)
class StockWatchSnapshotAdmin(admin.ModelAdmin):
    """
    Admin interface for StockWatchSnapshot.

    NOTE: Stock data is PUBLIC and accessible to all users.
    This admin interface shows all stock snapshots regardless of user.
    """

    list_display = ["symbol", "current_price", "change_percent", "fetched_at", "created_at"]
    list_filter = ["fetched_at", "created_at"]
    search_fields = ["symbol"]
    readonly_fields = ["symbol", "created_at", "updated_at"]

    def has_view_permission(self, request, obj=None):
        """All authenticated admins can view stock snapshots (public data)"""
        return request.user.is_authenticated

    def has_change_permission(self, request, obj=None):
        """All authenticated admins can modify stock snapshots"""
        return request.user.is_authenticated

    def has_delete_permission(self, request, obj=None):
        """All authenticated admins can delete stock snapshots"""
        return request.user.is_authenticated

    def has_add_permission(self, request):
        """All authenticated admins can add stock snapshots"""
        return request.user.is_authenticated


@admin.register(StockWatchlistEntry)
class StockWatchlistEntryAdmin(admin.ModelAdmin):
    list_display = ["symbol", "user", "nickname", "last_refreshed"]
    list_filter = ["created_at"]
    search_fields = ["symbol", "user__email", "nickname"]
