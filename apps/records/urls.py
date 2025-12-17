from django.urls import path

from . import aggregation_views, api_views, views

app_name = "records"

urlpatterns = [
    path("", views.insights_view, name="insights"),
    path("insights/", views.insights_view, name="insights"),
    path("explorer/", views.explorer_view, name="explorer"),
    path("upload/", views.upload_view, name="upload"),
    path("documents/partial/", views.document_list_partial, name="document_list_partial"),
    path("delete/<int:pk>/", views.delete_document, name="delete_document"),
    path("details/<int:pk>/", views.personal_details, name="personal_details"),
    path("personal-sensitive/", views.personal_sensitive_view, name="personal_sensitive"),
    # Financial data aggregation routes
    path("link-account/", aggregation_views.link_account_view, name="link_account"),
    path("linked-accounts/", aggregation_views.linked_accounts_view, name="linked_accounts"),
    path("account/<int:account_id>/", aggregation_views.account_detail_view, name="account_detail"),
    path("api/create-link-token/", aggregation_views.create_link_token, name="create_link_token"),
    path("api/exchange-token/", aggregation_views.exchange_token, name="exchange_token"),
    path("api/sync-account/<int:account_id>/", aggregation_views.sync_account, name="sync_account"),
    path("api/disconnect-account/<int:account_id>/", aggregation_views.disconnect_account, name="disconnect_account"),
    path("api/plaid-oauth-callback/", aggregation_views.plaid_oauth_callback, name="plaid_oauth_callback"),
    path("webhooks/plaid/", aggregation_views.plaid_webhook, name="plaid_webhook"),
    # Financial aggregation API endpoints
    path("api/dashboard-summary/", aggregation_views.dashboard_summary_api, name="dashboard_summary_api"),
    path("api/budget-data/", aggregation_views.budget_data_api, name="budget_data_api"),
    path("api/investment-data/", aggregation_views.investment_data_api, name="investment_data_api"),
    path("api/debt-data/", aggregation_views.debt_data_api, name="debt_data_api"),
    # Financial Goals API
    path("api/goals/", api_views.financial_goals_api, name="financial_goals_api"),
    path("api/goals/<int:goal_id>/", api_views.financial_goal_detail_api, name="financial_goal_detail_api"),
    # Notifications API
    path("api/notifications/", api_views.notifications_api, name="notifications_api"),
    path(
        "api/notifications/<int:notification_id>/read/",
        api_views.mark_notification_read_api,
        name="mark_notification_read_api",
    ),
    path(
        "api/notifications/read-all/", api_views.mark_all_notifications_read_api, name="mark_all_notifications_read_api"
    ),
    path("api/notifications/generate/", api_views.generate_notifications_api, name="generate_notifications_api"),
    # Financial Health Score API
    path("api/health-score/", api_views.financial_health_score_api, name="financial_health_score_api"),
    # Export API
    path("api/export/transactions/", api_views.export_transactions_api, name="export_transactions_api"),
    path("api/export/portfolio/", api_views.export_portfolio_api, name="export_portfolio_api"),
    # Recurring Transactions API
    path("api/recurring-transactions/", api_views.recurring_transactions_api, name="recurring_transactions_api"),
    # Debt Payoff Calculator API
    path("api/debt-payoff-calculator/", api_views.debt_payoff_calculator_api, name="debt_payoff_calculator_api"),
    # Budget vs Actual API
    path("api/budget-plans/", api_views.budget_plans_api, name="budget_plans_api"),
    path("api/budget-plans/<int:plan_id>/vs-actual/", api_views.budget_vs_actual_api, name="budget_vs_actual_api"),
    # Advanced Transaction Search API
    path("api/transactions/search/", api_views.advanced_transaction_search_api, name="advanced_transaction_search_api"),
    # Portfolio Comparison API
    path("api/portfolio-comparison/", api_views.portfolio_comparison_api, name="portfolio_comparison_api"),
    # Bill Management API
    path("api/bills/", api_views.bills_api, name="bills_api"),
    path("api/bills/<int:bill_id>/", api_views.bill_detail_api, name="bill_detail_api"),
    # Financial Calendar API
    path("api/calendar/", api_views.financial_calendar_api, name="financial_calendar_api"),
    # Tax Optimization API
    path("api/tax-optimization/", api_views.tax_optimization_api, name="tax_optimization_api"),
    # Retirement Planning API
    path("api/retirement-planning/", api_views.retirement_planning_api, name="retirement_planning_api"),
    path(
        "api/retirement-planning/<int:plan_id>/",
        api_views.retirement_planning_api,
        name="retirement_planning_detail_api",
    ),
    # Portfolio Analytics API
    path("api/portfolio-analytics/", api_views.portfolio_analytics_api, name="portfolio_analytics_api"),
    # New feature views
    path("goals/", views.financial_goals_view, name="financial_goals"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("health-score/", views.financial_health_view, name="financial_health"),
    path("debt-calculator/", views.debt_payoff_calculator_view, name="debt_calculator"),
    path("budget-planner/", views.budget_planner_view, name="budget_planner"),
    path("portfolio-comparison/", views.portfolio_comparison_view, name="portfolio_comparison"),
    path("calendar/", views.financial_calendar_view, name="financial_calendar"),
    path("tax-optimization/", views.tax_optimization_view, name="tax_optimization"),
    path("retirement-planning/", views.retirement_planning_view, name="retirement_planning"),
    path("transaction-search/", views.transaction_search_view, name="transaction_search"),
    # Report Generation API
    path("api/reports/", api_views.generate_report_api, name="generate_report_api"),
    # Dark Mode API
    path("api/dark-mode/", api_views.dark_mode_api, name="dark_mode_api"),
]
