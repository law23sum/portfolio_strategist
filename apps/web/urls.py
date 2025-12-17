from django.urls import path
from django.views.generic import TemplateView

from . import admin_views, api_views, views

app_name = "web"
urlpatterns = [
    path("", views.home, name="home"),
    # Admin command management
    path("admin/commands/", admin_views.admin_command_list, name="admin_command_list"),
    path("admin/commands/<str:command_name>/", admin_views.admin_command_detail, name="admin_command_detail"),
    path("admin/commands/execute/", admin_views.admin_command_execute, name="admin_command_execute"),
    path("terms/", TemplateView.as_view(template_name="web/terms.html"), name="terms"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots.txt"),
    # these views are just for testing error pages
    # actual error handling is handled by Django: https://docs.djangoproject.com/en/4.1/ref/views/#error-views
    path("400/", TemplateView.as_view(template_name="400.html"), name="400"),
    path("403/", TemplateView.as_view(template_name="403.html"), name="403"),
    path("404/", TemplateView.as_view(template_name="404.html"), name="404"),
    path("500/", TemplateView.as_view(template_name="500.html"), name="500"),
    path("simulate_error/", views.simulate_error),
    path("health/", views.HealthCheck.as_view(), name="health_check"),
    path(
        "pricing/",
        TemplateView.as_view(template_name="web/pricing_page.html", extra_context={"active_tab": "pricing_page"}),
        name="pricing_page",
    ),
    path(
        "categories/",
        TemplateView.as_view(template_name="web/categories_page.html", extra_context={"active_tab": "categories_page"}),
        name="categories_page",
    ),
    path(
        "features/",
        TemplateView.as_view(template_name="web/features_page.html", extra_context={"active_tab": "features_page"}),
        name="features_page",
    ),
    path("investment-savings/", views.investment_savings, name="investment_savings"),
    path("investment-savings/stocks-assessment/", views.stocks_assessment, name="stocks_assessment"),
    path(
        "investment-savings/stocks-assessment/<int:pk>/",
        views.stocks_assessment_detail,
        name="stocks_assessment_detail",
    ),
    path(
        "investment-savings/watchlist/add/",
        views.watchlist_add,
        name="watchlist_add",
    ),
    path(
        "investment-savings/watchlist/<int:entry_id>/remove/",
        views.watchlist_remove,
        name="watchlist_remove",
    ),
    path(
        "investment-savings/watchlist/<int:entry_id>/refresh/",
        views.watchlist_refresh,
        name="watchlist_refresh",
    ),
    path(
        "investment-savings/watchlist/news/",
        views.watchlist_news,
        name="watchlist_news",
    ),
    # Financia-style stock analysis pages
    path(
        "investment-savings/stocks-assessment/<str:symbol>/detailed-reports/",
        views.stocks_detailed_reports,
        name="stocks_detailed_reports",
    ),
    path(
        "investment-savings/stocks-assessment/<str:symbol>/analysis-predictions/",
        views.stocks_analysis_predictions,
        name="stocks_analysis_predictions",
    ),
    path(
        "investment-savings/stocks-assessment/<str:symbol>/market-overview/",
        views.stocks_market_overview,
        name="stocks_market_overview",
    ),
    path(
        "investment-savings/stocks-assessment/<str:symbol>/risk-dashboard/",
        views.stocks_risk_dashboard,
        name="stocks_risk_dashboard",
    ),
    path(
        "investment-savings/stocks-assessment/<str:symbol>/decision-support/",
        views.stocks_decision_support,
        name="stocks_decision_support",
    ),
    path(
        "investment-savings/stocks-assessment/<str:symbol>/investment-planner-alerts/",
        views.stocks_investment_planner_alerts,
        name="stocks_investment_planner_alerts",
    ),
    path(
        "investment-savings/financial-definitions/",
        views.financial_definitions,
        name="financial_definitions",
    ),
    path("investment-savings/savings-assessment/", views.savings_assessment, name="savings_assessment"),
    path("investment-savings/cd-assessment/", views.cd_assessment, name="cd_assessment"),
    path("investment-savings/bond-assessment/", views.bond_assessment, name="bond_assessment"),
    # API endpoints for saving assessments
    path("api/investment-savings/save-stocks/", api_views.save_stocks_assessment, name="save_stocks_assessment"),
    path("api/investment-savings/save-savings/", api_views.save_savings_assessment, name="save_savings_assessment"),
    path("api/investment-savings/save-cd/", api_views.save_cd_assessment, name="save_cd_assessment"),
    path("api/investment-savings/save-bond/", api_views.save_bond_assessment, name="save_bond_assessment"),
    # API endpoints for watchlist
    path("api/investment-savings/watchlist/", api_views.get_watchlist, name="get_watchlist"),
    path("api/investment-savings/watchlist/add/", api_views.watchlist_add_api, name="watchlist_add_api"),
    path(
        "api/investment-savings/watchlist/<int:entry_id>/remove/",
        api_views.watchlist_remove_api,
        name="watchlist_remove_api",
    ),
    path(
        "api/investment-savings/watchlist/<int:entry_id>/refresh/",
        api_views.watchlist_refresh_api,
        name="watchlist_refresh_api",
    ),
    path("api/investment-savings/watchlist/news/", api_views.get_watchlist_news, name="get_watchlist_news"),
    # Legacy URL for backwards compatibility
    path("investment-retirement/", views.investment_savings, name="investment_retirement"),
    path("budget-planner/", views.budget_planner, name="budget_planner"),
    path("ai-financial-services/", views.ai_financial_services, name="ai_financial_services"),
]
