# solutions/views.py

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from apps.records.financial_aggregation import BudgetAggregationService, DebtAggregationService
from apps.records.plaid_data_distribution import PlaidDataDistributionService


@login_required
def budgeting_view(request):
    """Budget Planner page with tax, expense, and debt calculations"""
    # Get budget data from aggregated accounts
    budget_data = BudgetAggregationService.get_user_budget_data(user=request.user, days=30)

    # Get debt data
    debt_data = DebtAggregationService.get_user_debt_data(user=request.user)

    # Get Plaid data for budget and debt
    plaid_organized = PlaidDataDistributionService.get_organized_plaid_data(request.user)
    plaid_budget_data = plaid_organized.get("budget_planner", {}) or {}
    plaid_debt_data = plaid_organized.get("debt", {}) or {}
    plaid_budget_json = json.dumps(plaid_budget_data)
    plaid_debt_json = json.dumps(plaid_debt_data)

    return render(
        request,
        "solutions/budgeting.html",
        context={
            "active_tab": "budgeting",
            "page_title": "Budget Planner",
            "budget_data": budget_data,
            "debt_data": debt_data,
            "plaid_budget_data": plaid_budget_json,
            "plaid_budget_defaults": plaid_budget_data,
            "plaid_debt_data": plaid_debt_json,
            "plaid_debt_defaults": plaid_debt_data,
        },
    )


@method_decorator(login_required, name="dispatch")
class ChartsView(TemplateView):
    template_name = "reports/charts.html"

    def get_context_data(self, **kwargs):
        return {
            "active_tab": "charts",
        }


@login_required
def tax_optimization_view(request):
    """Tax Optimization page with resources for minimizing tax liabilities"""
    plaid_tax_data = (
        PlaidDataDistributionService.get_organized_plaid_data(request.user).get("tax_optimization", {}) or {}
    )
    plaid_tax_json = json.dumps(plaid_tax_data)

    return render(
        request,
        "solutions/tax_optimization.html",
        context={
            "active_tab": "tax_optimization",
            "page_title": "Tax Optimization",
            "plaid_data": plaid_tax_json,
            "plaid_tax_defaults": plaid_tax_data,
        },
    )


@login_required
def credit_improvement_view(request):
    """Credit Improvement page with tips and tools for boosting credit scores"""
    plaid_credit_data = (
        PlaidDataDistributionService.get_organized_plaid_data(request.user).get("credit_score", {}) or {}
    )
    plaid_credit_json = json.dumps(plaid_credit_data)

    return render(
        request,
        "solutions/credit_improvement.html",
        context={
            "active_tab": "credit_improvement",
            "page_title": "Credit Improvement",
            "plaid_data": plaid_credit_json,
            "plaid_credit_defaults": plaid_credit_data,
        },
    )
