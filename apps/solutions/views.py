# solutions/views.py

from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from apps.records.financial_aggregation import BudgetAggregationService, DebtAggregationService


@login_required
def budgeting_view(request):
    """Budget Planner page with tax, expense, and debt calculations"""
    # Get budget data from aggregated accounts
    budget_data = BudgetAggregationService.get_user_budget_data(
        user=request.user,
        days=30
    )
    
    # Get debt data
    debt_data = DebtAggregationService.get_user_debt_data(user=request.user)
    
    return render(
        request,
        'solutions/budgeting.html',
        context={
            'active_tab': 'budgeting',
            'page_title': 'Budget Planner',
            'budget_data': budget_data,
            'debt_data': debt_data,
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
    return render(
        request,
        'solutions/tax_optimization.html',
        context={
            'active_tab': 'tax_optimization',
            'page_title': 'Tax Optimization',
        },
    )


@login_required
def credit_improvement_view(request):
    """Credit Improvement page with tips and tools for boosting credit scores"""
    return render(
        request,
        'solutions/credit_improvement.html',
        context={
            'active_tab': 'credit_improvement',
            'page_title': 'Credit Improvement',
        },
    )