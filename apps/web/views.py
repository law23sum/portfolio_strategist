import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from health_check.views import MainView

from apps.records.financial_aggregation import (
    BudgetAggregationService,
    InvestmentAggregationService,
    DebtAggregationService,
    DashboardAggregationService,
)
from apps.records.plaid_data_distribution import PlaidDataDistributionService


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
    # Get budget data from aggregated accounts
    budget_data = BudgetAggregationService.get_user_budget_data(
        user=request.user,
        days=30
    )
    
    # Get debt data
    debt_data = DebtAggregationService.get_user_debt_data(user=request.user)
    plaid_budget_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('budget_planner', {}) or {}
    plaid_budget_json = json.dumps(plaid_budget_data)
    
    return render(
        request,
        "web/budget_planner.html",
        context={
            "active_tab": "budget_planner",
            "page_title": _("Budget Planner"),
            "budget_data": budget_data,
            "debt_data": debt_data,
            "plaid_data": plaid_budget_json,
            "plaid_budget_defaults": plaid_budget_data,
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
    
    assessments = StocksAssessment.objects.filter(user=request.user).order_by('-updated_at')
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status='active',
        account_type__in=['investment', 'brokerage', 'retirement']
    ).prefetch_related('balances')
    plaid_data = PlaidDataDistributionService.get_organized_plaid_data(request.user)
    stocks_plaid_data = plaid_data.get('stocks_assessment', {}) or {}
    plaid_data_json = json.dumps(stocks_plaid_data)
    total_investments = float(stocks_plaid_data.get('investment_amount', 0) or 0)
    account_defaults = {
        'total_investments': total_investments,
        'accounts': stocks_plaid_data.get('accounts', []) or [],
    }
    account_defaults_json = json.dumps(account_defaults)
    
    return render(
        request,
        "web/stocks_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Stocks Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
            "plaid_data": plaid_data_json,
            "account_defaults": account_defaults,
            "account_defaults_json": account_defaults_json,
        },
    )


@login_required
def stocks_assessment_detail(request, pk):
    """Financia-style detail view for a saved stocks assessment."""
    from apps.records.models import StocksAssessment

    assessment = get_object_or_404(StocksAssessment, pk=pk, user=request.user)
    forecast_data = assessment.forecast_data or {}

    def _to_float(value):
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    period_defs = [
        ("current", _("Current Value")),
        ("biweekly", _("Biweekly")),
        ("monthly", _("Monthly")),
        ("quarterly", _("Quarterly")),
        ("biyearly", _("Biyearly")),
        ("yearly", _("Yearly")),
        ("3years", _("3 Years")),
        ("5years", _("5 Years")),
        ("decade", _("Decade")),
        ("twodecades", _("Two Decades")),
        ("threedecades", _("Three Decades")),
    ]
    period_days = {
        'biweekly': 14,
        'monthly': 30,
        'quarterly': 90,
        'biyearly': 182,
        'yearly': 365,
        '3years': 1095,
        '5years': 1825,
        'decade': 3650,
        'twodecades': 7300,
        'threedecades': 10950,
    }

    horizon_rows = []
    timeline_points = []
    for key, label in period_defs:
        data = forecast_data.get(key)
        if not isinstance(data, dict):
            continue
        price = _to_float(data.get('price') or data.get('forecast_price'))
        value = _to_float(data.get('value') or data.get('investment_value'))
        profit = _to_float(data.get('profit_loss'))
        growth = _to_float(data.get('growth_percent') or data.get('growth_pct'))
        years = _to_float(data.get('years'))
        days = data.get('days')
        if days is None and years is not None:
            days = years * 365
        elif days is None and key in period_days:
            days = period_days[key]
        target_date = data.get('target_date')

        def _normalize_level(level):
            if isinstance(level, dict):
                return level
            level_float = _to_float(level)
            if level_float is None:
                return {}
            return {'price': level_float}

        peak = _normalize_level(data.get('peak'))
        valley = _normalize_level(data.get('valley'))

        row = {
            'key': key,
            'label': label,
            'price': price,
            'value': value,
            'profit': profit,
            'growth': growth,
            'years': years,
            'target_date': target_date,
            'days': days,
            'peak': peak,
            'valley': valley,
        }
        horizon_rows.append(row)

        if price is not None:
            timeline_points.append(
                {
                    'label': str(label),
                    'price': price,
                    'value': value,
                    'target_date': target_date,
                    'days': days,
                }
            )

    timeline_points.sort(key=lambda item: item['days'] if isinstance(item.get('days'), (int, float)) else 1e9)

    investment_amount = _to_float(assessment.investment_amount) or 0.0
    current_price = _to_float(assessment.current_price) or 0.0
    shares = _to_float(assessment.share_quantity)
    if shares is None and current_price:
        shares = investment_amount / current_price if current_price else None
    current_value = _to_float((forecast_data.get('current') or {}).get('value')) or investment_amount
    biweekly_contrib = _to_float(forecast_data.get('biweekly_contribution')) or 0.0
    BIWEEKLY_PER_PHASE = 78
    three_year_data = forecast_data.get('3years') or forecast_data.get('yearly') or {}
    three_year_value = _to_float(three_year_data.get('value') or three_year_data.get('investment_value')) or 0.0
    plan_total = three_year_value + (biweekly_contrib * BIWEEKLY_PER_PHASE)

    financia_details = {
        'statistics': forecast_data.get('_statistics', {}),
        'external_factors': forecast_data.get('_external_factors', {}),
        'mean_reversion': forecast_data.get('_mean_reversion_params', {}),
        'equation_type': forecast_data.get('_equation_type'),
    }

    context = {
        'active_tab': 'investment_savings',
        'page_title': _("Stocks Assessment Detail"),
        'assessment': assessment,
        'horizon_rows': horizon_rows,
        'timeline_json': json.dumps(timeline_points),
        'investment_amount': investment_amount,
        'current_price': current_price,
        'current_value': current_value,
        'shares': shares,
        'biweekly_contrib': biweekly_contrib,
        'plan_summary': {
            'three_year_value': three_year_value,
            'plan_total': plan_total,
            'biweekly': biweekly_contrib,
            'principal': investment_amount,
        },
        'financia_details': financia_details,
    }

    return render(
        request,
        "web/stocks_assessment_detail.html",
        context=context,
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
    plaid_savings_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('savings_assessment', {}) or {}
    plaid_savings_json = json.dumps(plaid_savings_data)
    
    return render(
        request,
        "web/savings_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Savings Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
            "plaid_data": plaid_savings_json,
            "plaid_savings_defaults": plaid_savings_data,
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
    plaid_cd_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('cd_assessment', {}) or {}
    plaid_cd_json = json.dumps(plaid_cd_data)
    
    return render(
        request,
        "web/cd_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("CD Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
            "plaid_data": plaid_cd_json,
            "plaid_cd_defaults": plaid_cd_data,
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
    plaid_bond_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('bond_assessment', {}) or {}
    plaid_bond_json = json.dumps(plaid_bond_data)
    
    return render(
        request,
        "web/bond_assessment.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Bond Assessment"),
            "assessments": assessments,
            "linked_accounts": linked_accounts,
            "plaid_data": plaid_bond_json,
            "plaid_bond_defaults": plaid_bond_data,
        },
    )


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
