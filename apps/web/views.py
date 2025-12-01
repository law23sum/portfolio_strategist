from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from health_check.views import MainView

from apps.records.financial_aggregation import (
    BudgetAggregationService,
    InvestmentAggregationService,
    DebtAggregationService,
    DashboardAggregationService,
)


def home(request):
    if request.user.is_authenticated:
        # Get financial summary for dashboard
        financial_summary = DashboardAggregationService.get_user_financial_summary(
            user=request.user
        )
        
        return render(
            request,
            "web/app_home.html",
            context={
                "active_tab": "dashboard",
                "page_title": _("Dashboard"),
                "financial_summary": financial_summary,
            },
        )
    else:
        return render(request, "web/landing_page.html")


def simulate_error(request):
    raise Exception("This is a simulated error.")


@login_required
def investment_retirement(request):
    """Investment and Retirement planning page"""
    # Get investment data from aggregated accounts
    investment_data = InvestmentAggregationService.get_user_investment_data(
        user=request.user
    )
    
    return render(
        request,
        "web/investment_retirement.html",
        context={
            "active_tab": "investment_retirement",
            "page_title": _("Investment & Retirement Planner"),
            "investment_data": investment_data,
        },
    )


@login_required
def budget_planner(request):
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
        "web/budget_planner.html",
        context={
            "active_tab": "budget_planner",
            "page_title": _("Budget Planner"),
            "budget_data": budget_data,
            "debt_data": debt_data,
        },
    )


@login_required
def ai_financial_services(request):
    """AI Financial Services page with chat functionality"""
    from apps.chat.models import Chat
    
    # Get user's chats
    chats = Chat.objects.filter(user=request.user).order_by('-created_at')
    
    return render(
        request,
        "web/ai_financial_services.html",
        context={
            "active_tab": "ai_financial_services",
            "page_title": _("AI Financial Services"),
            "chats": chats,
        },
    )


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
