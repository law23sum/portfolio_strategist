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
def investment_savings(request):
    """Investment & Savings main summary page"""
    from apps.records.models import StocksAssessment, SavingsAssessment, CDAssessment, BondAssessment, LinkedAccount
    
    # Get investment data from aggregated accounts
    investment_data = InvestmentAggregationService.get_user_investment_data(
        user=request.user
    )
    
    # Get all saved assessments
    stocks_assessments = StocksAssessment.objects.filter(user=request.user)
    savings_assessments = SavingsAssessment.objects.filter(user=request.user)
    cd_assessments = CDAssessment.objects.filter(user=request.user)
    bond_assessments = BondAssessment.objects.filter(user=request.user)
    
    # Get linked accounts for Plaid integration
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status='active'
    ).select_related('provider')
    
    # Calculate summary totals
    summary = {
        'stocks': {
            'count': stocks_assessments.count(),
            'total_value': sum(float(a.forecast_data.get('current', {}).get('value', 0) or 0) for a in stocks_assessments),
            'total_monthly': sum(float(a.forecast_data.get('monthly', {}).get('value', 0) or 0) for a in stocks_assessments),
            'total_yearly': sum(float(a.forecast_data.get('yearly', {}).get('value', 0) or 0) for a in stocks_assessments),
            'total_decade': sum(float(a.forecast_data.get('decade', {}).get('value', 0) or 0) for a in stocks_assessments),
            'avg_interest': 0,  # Will calculate from stock performance
        },
        'savings': {
            'count': savings_assessments.count(),
            'total_value': sum(float(a.forecast_data.get('current', {}).get('value', 0) or 0) for a in savings_assessments),
            'total_monthly': sum(float(a.forecast_data.get('monthly', {}).get('value', 0) or 0) for a in savings_assessments),
            'total_yearly': sum(float(a.forecast_data.get('yearly', {}).get('value', 0) or 0) for a in savings_assessments),
            'total_decade': sum(float(a.forecast_data.get('decade', {}).get('value', 0) or 0) for a in savings_assessments),
            'avg_interest': float(sum(a.annual_interest_rate for a in savings_assessments) / savings_assessments.count()) if savings_assessments.count() > 0 else 0,
        },
        'cds': {
            'count': cd_assessments.count(),
            'total_value': sum(float(a.forecast_data.get('current', {}).get('value', 0) or 0) for a in cd_assessments),
            'total_monthly': sum(float(a.forecast_data.get('monthly', {}).get('value', 0) or 0) for a in cd_assessments),
            'total_yearly': sum(float(a.forecast_data.get('yearly', {}).get('value', 0) or 0) for a in cd_assessments),
            'total_decade': sum(float(a.forecast_data.get('decade', {}).get('value', 0) or 0) for a in cd_assessments),
            'avg_interest': float(sum(a.annual_interest_rate for a in cd_assessments) / cd_assessments.count()) if cd_assessments.count() > 0 else 0,
        },
        'bonds': {
            'count': bond_assessments.count(),
            'total_value': sum(float(a.forecast_data.get('current', {}).get('value', 0) or 0) for a in bond_assessments),
            'total_monthly': sum(float(a.forecast_data.get('monthly', {}).get('value', 0) or 0) for a in bond_assessments),
            'total_yearly': sum(float(a.forecast_data.get('yearly', {}).get('value', 0) or 0) for a in bond_assessments),
            'total_decade': sum(float(a.forecast_data.get('decade', {}).get('value', 0) or 0) for a in bond_assessments),
            'avg_interest': float(sum(a.coupon_rate for a in bond_assessments) / bond_assessments.count()) if bond_assessments.count() > 0 else 0,
        },
    }
    
    return render(
        request,
        "web/investment_savings.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Investment & Savings"),
            "investment_data": investment_data,
            "stocks_assessments": stocks_assessments,
            "savings_assessments": savings_assessments,
            "cd_assessments": cd_assessments,
            "bond_assessments": bond_assessments,
            "linked_accounts": linked_accounts,
            "summary": summary,
        },
    )


@login_required
def budget_planner(request):
    """Budget Planner page with tax, expense, and debt calculations"""
    from apps.records.account_data_service import AccountDataService
    
    # Get budget data from aggregated accounts
    budget_data = BudgetAggregationService.get_user_budget_data(
        user=request.user,
        days=30
    )
    
    # Get debt data
    debt_data = DebtAggregationService.get_user_debt_data(user=request.user)
    
    # Get default values from Plaid accounts
    account_defaults = AccountDataService.get_budget_defaults(request.user)
    
    return render(
        request,
        "web/budget_planner.html",
        context={
            "active_tab": "budget_planner",
            "page_title": _("Budget Planner"),
            "budget_data": budget_data,
            "debt_data": debt_data,
            "account_defaults": account_defaults,
        },
    )


@login_required
def ai_financial_services(request):
    """AI Financial Services page with single chat interface"""
    from apps.chat.models import Chat
    from apps.chat.serializers import ChatSerializer
    from apps.chat.api_url_helpers import get_chat_api_url_templates, get_menu_urls
    
    # Get or create a single chat for the user
    chat = Chat.objects.filter(user=request.user).order_by('-updated_at').first()
    if not chat:
        chat = Chat.objects.create(user=request.user, name="Main Chat")
    
    serialized_chat = ChatSerializer(chat, context={'request': request}).data
    
    return render(
        request,
        "chat/single_chat_react.html",
        context={
            "active_tab": "ai_financial_services",
            "page_title": _("AI Financial Services"),
            "chat": chat,
            "serialized_chat": serialized_chat,
            "api_urls": get_chat_api_url_templates(),
            "menu_urls": get_menu_urls(),
        },
    )


@login_required
def stocks_assessment(request):
    """Stocks Assessment page"""
    from apps.records.models import StocksAssessment, LinkedAccount
    from apps.records.account_data_service import AccountDataService
    
    assessments = StocksAssessment.objects.filter(user=request.user).order_by('-updated_at')
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status='active',
        account_type__in=['investment', 'brokerage', 'retirement']
    )
    
    # Get default values from Plaid accounts
    account_defaults = AccountDataService.get_investment_defaults(request.user)
    
    return render(
        request,
        "web/stocks_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Stocks Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
            "account_defaults": account_defaults,
        },
    )


@login_required
def savings_assessment(request):
    """Savings Assessment page"""
    from apps.records.models import SavingsAssessment, LinkedAccount
    
    assessments = SavingsAssessment.objects.filter(user=request.user).order_by('-updated_at')
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status='active',
        account_type='depository'
    )
    
    return render(
        request,
        "web/savings_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Savings Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
        },
    )


@login_required
def cd_assessment(request):
    """CD Assessment page"""
    from apps.records.models import CDAssessment, LinkedAccount
    
    assessments = CDAssessment.objects.filter(user=request.user).order_by('-updated_at')
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status='active',
        account_type='depository'
    )
    
    return render(
        request,
        "web/cd_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("CD Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
        },
    )


@login_required
def bond_assessment(request):
    """Bond Assessment page"""
    from apps.records.models import BondAssessment, LinkedAccount
    
    assessments = BondAssessment.objects.filter(user=request.user).order_by('-updated_at')
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status='active',
        account_type__in=['investment', 'brokerage']
    )
    
    return render(
        request,
        "web/bond_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Bond Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
        },
    )


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
