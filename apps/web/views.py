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
    import logging
    
    logger = logging.getLogger(__name__)
    
    assessments = StocksAssessment.objects.filter(user=request.user).order_by('-updated_at')
    # Include active, pending, and error accounts (error accounts might still have valid data)
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status__in=['active', 'pending', 'error'],
        account_type__in=['investment', 'brokerage', 'retirement']
    ).prefetch_related('balances')
    
    # Get organized Plaid data
    plaid_data = PlaidDataDistributionService.get_organized_plaid_data(request.user)
    stocks_plaid_data = plaid_data.get('stocks_assessment', {}) or {}
    plaid_data_json = json.dumps(stocks_plaid_data)
    total_investments = float(stocks_plaid_data.get('investment_amount', 0) or 0)
    
    account_defaults = {
        'total_investments': total_investments,
        'accounts': stocks_plaid_data.get('accounts', []) or [],
    }
    
    # If no stocks accounts found but we have investment accounts, include them
    if not account_defaults['accounts'] and linked_accounts.exists():
        logger.info(f"No stocks accounts identified, but found {linked_accounts.count()} investment accounts - adding them as potential stock accounts")
        for account in linked_accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                account_defaults['accounts'].append({
                    'id': str(account.id),
                    'name': account.account_name,
                    'balance': float(latest_balance.current_balance) if latest_balance.current_balance else 0.0,
                    'institution': account.institution_name,
                    'account_type': account.account_type,
                    'subtype': account.account_subtype or '',
                })
        # Update total investments
        if account_defaults['accounts']:
            account_defaults['total_investments'] = sum(acc.get('balance', 0) for acc in account_defaults['accounts'])
    
    account_defaults_json = json.dumps(account_defaults)
    
    # Debug logging
    logger.info(f"Stocks assessment for user {request.user.id}: {len(account_defaults['accounts'])} accounts found, total: ${account_defaults['total_investments']}")
    if account_defaults['accounts']:
        for acc in account_defaults['accounts']:
            logger.info(f"  Stock account: {acc.get('name', 'Unknown')} - ${acc.get('balance', 0)}")
    
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
    ).prefetch_related('balances')
    plaid_savings_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('savings_assessment', {}) or {}
    plaid_savings_json = json.dumps(plaid_savings_data)
    
    # Prepare account defaults similar to stocks assessment
    account_defaults = {
        'initial_deposit': plaid_savings_data.get('initial_deposit', 0),
        'account_name': plaid_savings_data.get('account_name', ''),
        'accounts': plaid_savings_data.get('accounts', []) or [],
    }
    account_defaults_json = json.dumps(account_defaults)
    
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
            "account_defaults": account_defaults,
            "account_defaults_json": account_defaults_json,
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
    ).prefetch_related('balances')
    plaid_cd_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('cd_assessment', {}) or {}
    plaid_cd_json = json.dumps(plaid_cd_data)
    
    # Prepare account defaults
    account_defaults = {
        'cd_amount': plaid_cd_data.get('cd_amount', 0),
        'account_name': plaid_cd_data.get('account_name', ''),
        'accounts': plaid_cd_data.get('accounts', []) or [],
    }
    account_defaults_json = json.dumps(account_defaults)
    
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
            "account_defaults": account_defaults,
            "account_defaults_json": account_defaults_json,
        },
    )


@login_required
def bond_assessment(request):
    """Bond Assessment page"""
    from apps.records.models import BondAssessment, LinkedAccount
    
    assessments = BondAssessment.objects.filter(user=request.user).order_by('-updated_at')
    # Include active, pending, and error accounts (error accounts might still have valid data)
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status__in=['active', 'pending', 'error'],
        account_type__in=['investment', 'brokerage']
    ).prefetch_related('balances')
    
    # Get organized Plaid data
    plaid_organized = PlaidDataDistributionService.get_organized_plaid_data(request.user)
    plaid_bond_data = plaid_organized.get('bond_assessment', {}) or {}
    plaid_bond_json = json.dumps(plaid_bond_data)
    
    # Prepare account defaults - ensure accounts list is always present
    account_defaults = {
        'face_value': plaid_bond_data.get('face_value', 0),
        'purchase_price': plaid_bond_data.get('purchase_price', 0),
        'account_name': plaid_bond_data.get('account_name', ''),
        'accounts': plaid_bond_data.get('accounts', []) or [],
    }
    
    # If no bond accounts found but we have investment accounts, include them as potential bond accounts
    if not account_defaults['accounts'] and linked_accounts.exists():
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"No bond accounts identified, but found {linked_accounts.count()} investment accounts - adding them as potential bond accounts")
        for account in linked_accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                account_defaults['accounts'].append({
                    'id': str(account.id),
                    'name': account.account_name,
                    'balance': float(latest_balance.current_balance) if latest_balance.current_balance else 0.0,
                    'institution': account.institution_name,
                    'account_type': account.account_type,
                    'subtype': account.account_subtype or '',
                })
    
    account_defaults_json = json.dumps(account_defaults)
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Bond assessment for user {request.user.id}: {len(account_defaults['accounts'])} accounts found")
    if account_defaults['accounts']:
        for acc in account_defaults['accounts']:
            logger.info(f"  Bond account: {acc.get('name', 'Unknown')} - ${acc.get('balance', 0)}")
    else:
        logger.warning(f"No bond accounts found for user {request.user.id}")
    
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
            "account_defaults": account_defaults,
            "account_defaults_json": account_defaults_json,
        },
    )


@login_required
def stocks_detailed_reports(request, symbol):
    """Stock Detailed Reports page - shows comprehensive stock analysis"""
    from apps.stock_analysis.services import StockAnalysisService
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    
    period = request.GET.get('period', '1y')
    interval = request.GET.get('interval', '1d')
    
    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
    
    # Get aggregated data for detailed reports page
    try:
        page_data = aggregator.get_data_for_detailed_reports(symbol.upper())
        stock_data = page_data.get('stock_data', {})
        statistics = page_data.get('statistics', {})
        yahoo_profile = page_data.get('yahoo_profile', {})
        news_items = page_data.get('news', [])
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        stock_data = service.stock_app.fetch_stock_data(symbol.upper())
        statistics = {}
        yahoo_profile = {}
        news_items = []
    
    # Analyze ratios
    ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else None
    
    # Convert ratios_table to dict for template and normalize keys
    ratios_dict = []
    if ratios_table is not None and not ratios_table.empty:
        ratios_records = ratios_table.to_dict('records')
        for ratio in ratios_records:
            normalized_ratio = {}
            for key, value in ratio.items():
                normalized_key = key.replace(' ', '_').replace('-', '_').lower()
                normalized_ratio[normalized_key] = value
                normalized_ratio[key] = value

            def grab(keys):
                for key in keys:
                    if key in normalized_ratio and normalized_ratio[key] not in (None, ''):
                        return normalized_ratio[key]
                return None

            normalized_ratio['ratio_name'] = grab(['ratio_name', 'ratio', 'name', 'Ratio Name', 'Name'])
            normalized_ratio['ratio_value'] = grab(['ratio_value', 'value', 'Ratio Value', 'Value'])
            normalized_ratio['performance'] = grab(['performance', 'perf', 'Performance'])
            
            # Set display_name with fallback logic
            if normalized_ratio.get('ratio_name'):
                normalized_ratio['display_name'] = normalized_ratio['ratio_name']
            else:
                # Try to find any key that might be a name from the original ratio
                for orig_key in ratio.keys():
                    if orig_key not in ['Ratio Value', 'Value', 'value', 'Performance', 'performance']:
                        if ratio[orig_key] not in (None, ''):
                            normalized_ratio['display_name'] = str(ratio[orig_key])
                            break
                else:
                    normalized_ratio['display_name'] = 'Metric'
            
            ratios_dict.append(normalized_ratio)
    
    # Convert news items to HTML
    news_html_parts = []
    for item in news_items:
        title = item.get("title", "")
        url = item.get("url", "")
        publisher = item.get("publisher", item.get("source", ""))
        description = item.get("description", "")
        
        if title and url:
            article_html = f'<article><h2>{title}</h2>'
            if publisher:
                article_html += f'<p><em>{publisher}</em></p>'
            if description:
                article_html += f'<p>{description}</p>'
            article_html += f'<p><a href="{url}">Read more</a></p></article>'
            news_html_parts.append(article_html)
    
    news_html = "\n".join(news_html_parts) if news_html_parts else ""
    
    # Merge stock_data with statistics and profile
    enhanced_stock_data = {**(stock_data or {}), **statistics}
    if yahoo_profile:
        enhanced_stock_data['profile'] = yahoo_profile
    
    return render(
        request,
        "web/stocks_detailed_reports.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Stock Detailed Reports"),
            "symbol": symbol.upper(),
            "stock_data": enhanced_stock_data,
            "ratios_table": ratios_dict,
            "news_html": news_html,
            "period": period,
            "interval": interval,
        },
    )


@login_required
def stocks_analysis_predictions(request, symbol):
    """Stock Analysis/Predictions page - shows forecast charts and predictions"""
    from apps.stock_analysis.services import StockAnalysisService
    from apps.stock_analysis.lib.analysis_utils import build_forecast_error_rows
    import pandas as pd
    import json
    
    period = request.GET.get('period', '1y')
    interval = request.GET.get('interval', '1d')
    equation_type = request.GET.get('model', 'Geometric Brownian Motion External Macroeconomic Factors')
    market_ticker = request.GET.get('market', '^GSPC')
    vix_ticker = request.GET.get('vix', '^VIX')
    tnx_ticker = request.GET.get('tnx', '^TNX')
    
    service = StockAnalysisService()
    history_df = service.stock_app.fetch_stock_history(symbol.upper(), period, interval)
    stock_data = service.stock_app.fetch_stock_data(symbol.upper())
    ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else pd.DataFrame()
    
    forecast_df = None
    forecast_errors = []
    error_data = []
    if not history_df.empty:
        forecast_df = service.stock_app.forecast_prices_advanced(
            history_df, symbol.upper(), ratios_table, interval,
            equation_type=equation_type,
            market_ticker=market_ticker,
            vix_ticker=vix_ticker,
            tnx_ticker=tnx_ticker,
            forecast_days=365
        )
        
        # Calculate prediction errors
        if forecast_df is not None and not forecast_df.empty and build_forecast_error_rows:
            forecast_errors = build_forecast_error_rows(history_df, forecast_df)
            # Serialize error data for chart
            for error_row in forecast_errors:
                error_data.append({
                    'date': error_row['date'],
                    'error': error_row['error'] if error_row['error'] is not None else 0,
                })
    
    # Serialize data for template
    historical_data = []
    forecast_data = []
    future_forecast_data = []  # Only future dates (non-overlapping)
    
    if not history_df.empty:
        for idx, row in history_df.iterrows():
            date_val = row.get('Date')
            close_val = row.get('Close')
            date_str = date_val.strftime('%Y-%m-%d') if pd.notna(date_val) and hasattr(date_val, 'strftime') else str(date_val) if date_val else ''
            historical_data.append({
                'date': date_str,
                'close': float(close_val) if pd.notna(close_val) else 0
            })
    
    if forecast_df is not None and not forecast_df.empty:
        # Get overlap count (number of error rows = overlap)
        overlap_count = len(forecast_errors) if forecast_errors else 0
        
        for forecast_idx, row in forecast_df.iterrows():
            date_val = row.get('Date')
            forecast_val = row.get('Forecasted_Close')
            date_str = date_val.strftime('%Y-%m-%d') if pd.notna(date_val) and hasattr(date_val, 'strftime') else str(date_val) if date_val else ''
            forecast_item = {
                'date': date_str,
                'forecasted_close': float(forecast_val) if pd.notna(forecast_val) else 0
            }
            forecast_data.append(forecast_item)
            
            # Future forecast data (non-overlapping dates)
            if forecast_idx >= overlap_count:
                future_forecast_data.append(forecast_item)
    
    historical_data_json = json.dumps(historical_data)
    forecast_data_json = json.dumps(forecast_data)
    error_data_json = json.dumps(error_data)
    
    return render(
        request,
        "web/stocks_analysis_predictions.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Stock Analysis/Predictions"),
            "symbol": symbol.upper(),
            "historical_data": historical_data_json,
            "forecast_data": forecast_data_json,
            "future_forecast_data": future_forecast_data,
            "error_data": error_data_json,
            "forecast_errors": forecast_errors,
            "period": period,
            "interval": interval,
            "equation_type": equation_type,
            "market_ticker": market_ticker,
            "vix_ticker": vix_ticker,
            "tnx_ticker": tnx_ticker,
        },
    )


@login_required
def stocks_market_overview(request, symbol):
    """Market Overview page - shows market comparison and context"""
    from apps.stock_analysis.services import StockAnalysisService
    from apps.stock_analysis.lib.analysis_utils import build_market_overview
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    import pandas as pd
    import json
    
    market_ticker = request.GET.get('market', '^GSPC')
    
    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
    
    # Get aggregated data for market overview page
    try:
        page_data = aggregator.get_data_for_market_overview(symbol.upper(), market_ticker)
        stock_history = page_data.get('stock_history')
        benchmark_history = page_data.get('benchmark_history')
        fundamentals = page_data.get('fundamentals', {})
        statistics = page_data.get('statistics', {})
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        stock_history = service.stock_app.fetch_stock_history(symbol.upper(), period="1y", interval="1d")
        benchmark_history = service.stock_app.fetch_stock_history(market_ticker, period="1y", interval="1d")
        fundamentals = {}
        statistics = {}
    
    market_history = benchmark_history
    
    # Calculate comparison metrics using build_market_overview
    market_overview_data = {}
    market_data = []
    stock_data = []
    metrics = {}
    
    # Ensure stock_history and market_history are DataFrames
    if stock_history is not None and not isinstance(stock_history, pd.DataFrame):
        stock_history = pd.DataFrame()
    if market_history is not None and not isinstance(market_history, pd.DataFrame):
        market_history = pd.DataFrame()
    
    if stock_history is not None and not stock_history.empty:
        # Ensure Close column exists and is numeric
        if 'Close' not in stock_history.columns:
            stock_history = pd.DataFrame()
        
        if build_market_overview and not stock_history.empty:
            try:
                # Ensure stock_history has required columns and is properly formatted
                if 'Close' in stock_history.columns and 'Date' in stock_history.columns:
                    # Ensure Close is numeric
                    stock_history = stock_history.copy()
                    stock_history['Close'] = pd.to_numeric(stock_history['Close'], errors='coerce')
                    stock_history = stock_history.dropna(subset=['Close', 'Date'])
                    
                    if not stock_history.empty:
                        market_overview_data = build_market_overview(
                            stock_history, symbol.upper(), market_ticker
                        )
                        metrics = market_overview_data.get('metrics', {})
                        # Use the series data from build_market_overview if available
                        if 'price_series' in market_overview_data:
                            stock_data = [
                                {'date': str(item.get('index', '')), 'value': item.get('price', 0)}
                                for item in market_overview_data.get('price_series', [])
                            ]
                        if 'benchmark_series' in market_overview_data:
                            market_data = [
                                {'date': str(item.get('index', '')), 'value': item.get('price', 0)}
                                for item in market_overview_data.get('benchmark_series', [])
                            ]
            except Exception as e:
                import traceback
                print(f"build_market_overview failed: {e}")
                traceback.print_exc()
                market_overview_data = {}
        
        # Fallback to manual calculation if build_market_overview not available
        if not stock_data and stock_history is not None and not stock_history.empty:
            # Ensure Close column exists and is numeric
            if 'Close' in stock_history.columns:
                close_series = pd.to_numeric(stock_history['Close'], errors='coerce').dropna()
                if close_series.empty:
                    stock_start = 1
                else:
                    stock_start = float(close_series.iloc[0])
            else:
                stock_start = 1
            
            if market_history is not None and not market_history.empty and 'Close' in market_history.columns:
                market_close_series = pd.to_numeric(market_history['Close'], errors='coerce').dropna()
                if market_close_series.empty:
                    market_start = 1
                else:
                    market_start = float(market_close_series.iloc[0])
            else:
                market_start = 1
            
            for stock_idx, row in stock_history.iterrows():
                close_val = row.get('Close')
                date_val = row.get('Date')
                if pd.notna(close_val):
                    stock_data.append({
                        'date': date_val.strftime('%Y-%m-%d') if pd.notna(date_val) and hasattr(date_val, 'strftime') else str(date_val) if date_val else '',
                        'value': (float(close_val) / stock_start - 1) * 100
                    })
            
            for market_idx, row in market_history.iterrows():
                close_val = row.get('Close')
                date_val = row.get('Date')
                if pd.notna(close_val):
                    market_data.append({
                        'date': date_val.strftime('%Y-%m-%d') if pd.notna(date_val) and hasattr(date_val, 'strftime') else str(date_val) if date_val else '',
                        'value': (float(close_val) / market_start - 1) * 100
                    })
            
            # Calculate basic metrics
            if stock_history.shape[0] > 0 and not stock_history.empty:
                # Ensure Close column exists and is numeric
                if 'Close' in stock_history.columns:
                    close_series = pd.to_numeric(stock_history['Close'], errors='coerce').dropna()
                    if not close_series.empty:
                        current_price = float(close_series.iloc[-1])
                        stock_perf = (current_price / stock_start - 1) * 100
                    else:
                        current_price = None
                        stock_perf = None
                else:
                    current_price = None
                    stock_perf = None
                
                if not market_history.empty and 'Close' in market_history.columns:
                    market_close_series = pd.to_numeric(market_history['Close'], errors='coerce').dropna()
                    if not market_close_series.empty:
                        market_current = float(market_close_series.iloc[-1])
                        market_perf = (market_current / market_start - 1) * 100
                        relative = stock_perf - market_perf if stock_perf is not None else None
                    else:
                        market_perf = None
                        relative = None
                else:
                    market_perf = None
                    relative = None
                
                # Calculate daily returns safely
                if 'Close' in stock_history.columns:
                    close_series = pd.to_numeric(stock_history['Close'], errors='coerce')
                    daily_returns = close_series.pct_change().dropna()
                    latest_return = float(daily_returns.iloc[-1]) * 100 if not daily_returns.empty else None
                else:
                    latest_return = None
                
                metrics = {
                    'current_price': current_price,
                    'period_performance_pct': stock_perf,
                    'benchmark_performance_pct': market_perf,
                    'relative_performance_pct': relative,
                    'latest_daily_return_pct': latest_return,
                }
    
    stock_data_json = json.dumps(stock_data)
    market_data_json = json.dumps(market_data)
    
    return render(
        request,
        "web/stocks_market_overview.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Market Overview"),
            "symbol": symbol.upper(),
            "market_ticker": market_ticker,
            "stock_data": stock_data_json,
            "market_data": market_data_json,
            "metrics": metrics,
            "status_message": market_overview_data.get('message', ''),
        },
    )


@login_required
def stocks_risk_dashboard(request, symbol):
    """Risk Dashboard page - shows risk metrics and statistics"""
    from apps.stock_analysis.services import StockAnalysisService
    from apps.stock_analysis.lib.analysis_utils import calculate_risk_statistics, generate_risk_insights
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    
    period = request.GET.get('period', '1y')
    market_ticker = request.GET.get('market', '^GSPC')
    
    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
    
    # Get aggregated data for risk dashboard page
    try:
        page_data = aggregator.get_data_for_risk_dashboard(symbol.upper(), market_ticker)
        history_df = page_data.get('stock_history')
        statistics = page_data.get('statistics', {})
        yahoo_statistics = page_data.get('yahoo_statistics', {})
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        history_df = service.stock_app.fetch_stock_history(symbol.upper(), period, interval="1d")
        statistics = {}
        yahoo_statistics = {}
    
    risk_metrics = {}
    risk_insights = []
    benchmark_df = None
    
    if calculate_risk_statistics and history_df is not None and not history_df.empty:
        risk_metrics, benchmark_df = calculate_risk_statistics(history_df, market_ticker)
        if generate_risk_insights:
            risk_insights = generate_risk_insights(risk_metrics)
        
        # Enhance risk metrics with Yahoo Finance statistics if available
        if yahoo_statistics:
            # Merge additional statistics that might not be in risk_metrics
            for key, value in yahoo_statistics.items():
                if key not in risk_metrics and value is not None:
                    risk_metrics[f'yahoo_{key}'] = value
    
    return render(
        request,
        "web/stocks_risk_dashboard.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Risk Dashboard"),
            "symbol": symbol.upper(),
            "risk_metrics": risk_metrics,
            "risk_insights": risk_insights,
            "period": period,
            "market_ticker": market_ticker,
        },
    )


@login_required
def stocks_decision_support(request, symbol):
    """Decision Support page - shows AI-powered investment recommendations"""
    from apps.stock_analysis.services import StockAnalysisService
    from apps.stock_analysis.lib.analysis_utils import build_decision_support
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    
    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
    
    # Get aggregated data for decision support page
    try:
        page_data = aggregator.get_data_for_decision_support(symbol.upper())
        stock_data = page_data.get('fundamentals', {})
        statistics = page_data.get('statistics', {})
        yahoo_profile = page_data.get('yahoo_profile', {})
        yahoo_holders = page_data.get('yahoo_holders', {})
        news_items = page_data.get('news', [])
        stock_history = page_data.get('stock_history', None)
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        stock_data = service.stock_app.fetch_stock_data(symbol.upper())
        statistics = {}
        yahoo_profile = {}
        yahoo_holders = {}
        news_items = []
        stock_history = None
    
    ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else None
    
    # Use aggregated stock_history if available, otherwise fetch
    if stock_history is None or stock_history.empty:
        history_df = service.stock_app.fetch_stock_history(symbol.upper(), period="1y", interval="1d")
    else:
        history_df = stock_history
    
    # Merge aggregated data into stock_data for template
    enhanced_stock_data = {**(stock_data or {})}
    if statistics:
        enhanced_stock_data.update(statistics)
    if yahoo_profile:
        enhanced_stock_data['profile'] = yahoo_profile
    if yahoo_holders:
        enhanced_stock_data['holders'] = yahoo_holders
    
    decision_support = {}
    if build_decision_support and stock_data and history_df is not None and not history_df.empty:
        decision_support = build_decision_support(
            stock_data, ratios_table, history_df
        )
    
    return render(
        request,
        "web/stocks_decision_support.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Decision Support"),
            "symbol": symbol.upper(),
            "decision_support": decision_support,
            "stock_data": enhanced_stock_data,
        },
    )


@login_required
def stocks_investment_planner_alerts(request, symbol):
    """Investment Planner Alerts page - shows alerts and notifications"""
    from apps.stock_analysis.models import InvestmentPlan
    from apps.stock_analysis.services import StockAnalysisService
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    
    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)
    
    # Get aggregated data for investment planner page
    try:
        page_data = aggregator.get_data_for_investment_planner(symbol.upper())
        fundamentals = page_data.get('fundamentals', {})
        statistics = page_data.get('statistics', {})
        stock_history = page_data.get('stock_history')
        yahoo_options = page_data.get('yahoo_options', {})
        yahoo_holders = page_data.get('yahoo_holders', {})
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        fundamentals = service.stock_app.fetch_stock_data(symbol.upper()) or {}
        statistics = {}
        stock_history = None
        yahoo_options = {}
        yahoo_holders = {}
    
    # Get current price from aggregated data
    current_price = fundamentals.get('currentPrice', None)
    if (current_price is None or current_price <= 0) and stock_history is not None and not stock_history.empty:
        try:
            from apps.stock_analysis.lib.investment_utils import get_current_price
            current_price = get_current_price(stock_history)
        except (ImportError, Exception):
            if 'Close' in stock_history.columns:
                close_prices = stock_history['Close'].dropna()
                if not close_prices.empty:
                    current_price = float(close_prices.iloc[-1])
    
    # Get user's investment plans for this symbol
    plans = InvestmentPlan.objects.filter(
        user=request.user,
        stock_analysis__symbol=symbol.upper()
    ).order_by('-created_at')
    
    # Merge aggregated data
    enhanced_data = {**fundamentals, **statistics}
    if yahoo_options:
        enhanced_data['options'] = yahoo_options
    if yahoo_holders:
        enhanced_data['holders'] = yahoo_holders
    
    return render(
        request,
        "web/stocks_investment_planner_alerts.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Investment Planner Alerts"),
            "symbol": symbol.upper(),
            "plans": plans,
            "stock_data": enhanced_data,
            "current_price": current_price,
            "stock_history": stock_history,
        },
    )


@login_required
def financial_definitions(request):
    """Financial Definitions page - shows financial term definitions"""
    from apps.stock_analysis.lib.stock_definitions import RATIO_DEFINITIONS
    
    # Convert to list of dicts for template
    definitions_list = []
    for ratio_name, ratio_info in RATIO_DEFINITIONS.items():
        definitions_list.append({
            'name': ratio_name,
            'term': ratio_info.get('Term', ''),
            'definition': ratio_info.get('Definition', ''),
            'formula': ratio_info.get('Formula', ''),
        })
    
    return render(
        request,
        "web/financial_definitions.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Financial Definitions"),
            "definitions": definitions_list,
        },
    )


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
