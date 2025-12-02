from django.urls import path
from django.views.generic import TemplateView

from . import views
from . import api_views


app_name = "web"
urlpatterns = [
    path("", views.home, name = "home"),
    path("terms/", TemplateView.as_view(template_name = "web/terms.html"), name = "terms"),
    path("robots.txt", TemplateView.as_view(template_name = "robots.txt", content_type = "text/plain"), name = "robots.txt"),
    # these views are just for testing error pages
    # actual error handling is handled by Django: https://docs.djangoproject.com/en/4.1/ref/views/#error-views
    path("400/", TemplateView.as_view(template_name = "400.html"), name = "400"),
    path("403/", TemplateView.as_view(template_name = "403.html"), name = "403"),
    path("404/", TemplateView.as_view(template_name = "404.html"), name = "404"),
    path("500/", TemplateView.as_view(template_name = "500.html"), name = "500"),
    path("simulate_error/", views.simulate_error),
    path("health/", views.HealthCheck.as_view(), name = "health_check"),
    path("pricing/",TemplateView.as_view(template_name = "web/pricing_page.html", extra_context = {"active_tab": "pricing_page"}),name = "pricing_page"),
    path("categories/", TemplateView.as_view(template_name = "web/categories_page.html", extra_context = {"active_tab": "categories_page"}), name = "categories_page"),
    path("features/", TemplateView.as_view(template_name = "web/features_page.html", extra_context = {"active_tab": "features_page"}), name = "features_page"),
    path("investment-savings/", views.investment_savings, name = "investment_savings"),
    path("investment-savings/stocks-assessment/", views.stocks_assessment, name = "stocks_assessment"),
    path(
        "investment-savings/stocks-assessment/<int:pk>/",
        views.stocks_assessment_detail,
        name = "stocks_assessment_detail",
    ),
    path("investment-savings/savings-assessment/", views.savings_assessment, name = "savings_assessment"),
    path("investment-savings/cd-assessment/", views.cd_assessment, name = "cd_assessment"),
    path("investment-savings/bond-assessment/", views.bond_assessment, name = "bond_assessment"),
    # API endpoints for saving assessments
    path("api/investment-savings/save-stocks/", api_views.save_stocks_assessment, name = "save_stocks_assessment"),
    path("api/investment-savings/save-savings/", api_views.save_savings_assessment, name = "save_savings_assessment"),
    path("api/investment-savings/save-cd/", api_views.save_cd_assessment, name = "save_cd_assessment"),
    path("api/investment-savings/save-bond/", api_views.save_bond_assessment, name = "save_bond_assessment"),
    # Legacy URL for backwards compatibility
    path("investment-retirement/", views.investment_savings, name = "investment_retirement"),
    path("budget-planner/", views.budget_planner, name = "budget_planner"),
    path("ai-financial-services/", views.ai_financial_services, name = "ai_financial_services"),
    ]
