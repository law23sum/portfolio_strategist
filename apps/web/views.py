import json
import logging
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from health_check.views import MainView

logger = logging.getLogger(__name__)

# noqa: E402 - imports after logger setup
from apps.records.financial_aggregation import (  # noqa: E402
    BudgetAggregationService,
    DashboardAggregationService,
    DebtAggregationService,
    InvestmentAggregationService,
)
from apps.records.plaid_data_distribution import PlaidDataDistributionService  # noqa: E402
from apps.stock_analysis.models import StockWatchlistEntry  # noqa: E402


def home(request):
    if request.user.is_authenticated:
        # Get financial summary for dashboard
        financial_summary = DashboardAggregationService.get_user_financial_summary(user=request.user)

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
    from apps.records.models import BondAssessment, CDAssessment, LinkedAccount, SavingsAssessment, StocksAssessment

    # Get investment data from aggregated accounts
    investment_data = InvestmentAggregationService.get_user_investment_data(user=request.user)

    # Get all saved assessments
    stocks_assessments = StocksAssessment.objects.filter(user=request.user)
    savings_assessments = SavingsAssessment.objects.filter(user=request.user)
    cd_assessments = CDAssessment.objects.filter(user=request.user)
    bond_assessments = BondAssessment.objects.filter(user=request.user)

    # Get linked accounts for Plaid integration
    linked_accounts = LinkedAccount.objects.filter(user=request.user, status="active").select_related("provider")

    watchlist_entries = (
        StockWatchlistEntry.objects.filter(user=request.user)
        .select_related("snapshot")
        .order_by("symbol", "created_at")
    )

    # Calculate summary totals
    summary = {
        "stocks": {
            "count": stocks_assessments.count(),
            "total_value": sum(
                float(a.forecast_data.get("current", {}).get("value", 0) or 0) for a in stocks_assessments
            ),
            "total_monthly": sum(
                float(a.forecast_data.get("monthly", {}).get("value", 0) or 0) for a in stocks_assessments
            ),
            "total_yearly": sum(
                float(a.forecast_data.get("yearly", {}).get("value", 0) or 0) for a in stocks_assessments
            ),
            "total_decade": sum(
                float(a.forecast_data.get("decade", {}).get("value", 0) or 0) for a in stocks_assessments
            ),
            "avg_interest": 0,  # Will calculate from stock performance
        },
        "savings": {
            "count": savings_assessments.count(),
            "total_value": sum(
                float(a.forecast_data.get("current", {}).get("value", 0) or 0) for a in savings_assessments
            ),
            "total_monthly": sum(
                float(a.forecast_data.get("monthly", {}).get("value", 0) or 0) for a in savings_assessments
            ),
            "total_yearly": sum(
                float(a.forecast_data.get("yearly", {}).get("value", 0) or 0) for a in savings_assessments
            ),
            "total_decade": sum(
                float(a.forecast_data.get("decade", {}).get("value", 0) or 0) for a in savings_assessments
            ),
            "avg_interest": float(
                sum(a.annual_interest_rate for a in savings_assessments) / savings_assessments.count()
            )
            if savings_assessments.count() > 0
            else 0,
        },
        "cds": {
            "count": cd_assessments.count(),
            "total_value": sum(float(a.forecast_data.get("current", {}).get("value", 0) or 0) for a in cd_assessments),
            "total_monthly": sum(
                float(a.forecast_data.get("monthly", {}).get("value", 0) or 0) for a in cd_assessments
            ),
            "total_yearly": sum(float(a.forecast_data.get("yearly", {}).get("value", 0) or 0) for a in cd_assessments),
            "total_decade": sum(float(a.forecast_data.get("decade", {}).get("value", 0) or 0) for a in cd_assessments),
            "avg_interest": float(sum(a.annual_interest_rate for a in cd_assessments) / cd_assessments.count())
            if cd_assessments.count() > 0
            else 0,
        },
        "bonds": {
            "count": bond_assessments.count(),
            "total_value": sum(
                float(a.forecast_data.get("current", {}).get("value", 0) or 0) for a in bond_assessments
            ),
            "total_monthly": sum(
                float(a.forecast_data.get("monthly", {}).get("value", 0) or 0) for a in bond_assessments
            ),
            "total_yearly": sum(
                float(a.forecast_data.get("yearly", {}).get("value", 0) or 0) for a in bond_assessments
            ),
            "total_decade": sum(
                float(a.forecast_data.get("decade", {}).get("value", 0) or 0) for a in bond_assessments
            ),
            "avg_interest": float(sum(a.coupon_rate for a in bond_assessments) / bond_assessments.count())
            if bond_assessments.count() > 0
            else 0,
        },
    }

    allocation_breakdown = []
    total_allocation = 0.0
    for account_summary in investment_data.get("account_summaries", []):
        account = account_summary.get("account")
        value = float(account_summary.get("value", 0) or 0)
        total_allocation += value
        label_parts = []
        if account:
            if account.account_name:
                label_parts.append(account.account_name)
            if account.institution_name:
                label_parts.append(account.institution_name)
        label = " · ".join(label_parts) if label_parts else "Account"
        allocation_breakdown.append(
            {
                "label": label,
                "value": value,
                "account_type": getattr(account, "account_type", ""),
            }
        )
    allocation_breakdown.sort(key=lambda item: item["value"], reverse=True)
    for item in allocation_breakdown:
        if total_allocation > 0:
            item["percent"] = round((item["value"] / total_allocation) * 100, 2)
        else:
            item["percent"] = 0
        item["value"] = round(item["value"], 2)

    holdings_insights = []
    for holding in investment_data.get("holdings", []):
        holdings_insights.append(
            {
                "label": holding.get("security_ticker") or holding.get("security_name") or "Holding",
                "value": float(holding.get("value") or 0),
                "gain_loss": holding.get("gain_loss"),
            }
        )
    holdings_insights.sort(key=lambda item: item["value"], reverse=True)
    holdings_insights = [
        {
            **item,
            "value": round(item["value"], 2),
            "gain_loss": round(item["gain_loss"], 2) if item["gain_loss"] is not None else None,
        }
        for item in holdings_insights[:6]
    ]

    watchlist_summary = []
    for entry in watchlist_entries:
        snapshot = entry.snapshot
        watchlist_summary.append(
            {
                "symbol": entry.symbol,
                "nickname": entry.nickname,
                "current_price": float(snapshot.current_price)
                if snapshot and snapshot.current_price is not None
                else None,
                "change_percent": float(snapshot.change_percent)
                if snapshot and snapshot.change_percent is not None
                else None,
                "fetched_at": snapshot.fetched_at.isoformat() if snapshot and snapshot.fetched_at else None,
            }
        )

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
            "watchlist_entries": watchlist_entries,
            "allocation_chart": json.dumps(allocation_breakdown),
            "holdings_chart": json.dumps(holdings_insights),
            "watchlist_summary": watchlist_summary,
        },
    )


@login_required
@require_POST
def watchlist_add(request):
    symbol = request.POST.get("symbol", "").upper().strip()
    nickname = request.POST.get("nickname", "").strip()
    notes = request.POST.get("notes", "").strip()

    if not symbol:
        messages.error(request, "Please provide a stock symbol to watch.")
        return redirect("web:investment_savings")

    entry, created = StockWatchlistEntry.objects.get_or_create(
        user=request.user,
        symbol=symbol,
        defaults={"nickname": nickname, "notes": notes},
    )

    if not created:
        if nickname:
            entry.nickname = nickname
        if notes:
            entry.notes = notes
        entry.save()
        messages.info(request, f"Updated your watchlist entry for {symbol}.")
    else:
        messages.success(request, f"Added {symbol} to your watchlist.")

    try:
        from apps.stock_analysis.tasks import refresh_watchlist_symbol

        refresh_watchlist_symbol.delay(symbol)
    except Exception as exc:  # pragma: no cover - Celery not running
        messages.warning(
            request,
            f"Watchlist entry saved, but background refresh could not be queued ({exc}).",
        )

    return redirect("web:investment_savings")


@login_required
@require_POST
def watchlist_remove(request, entry_id: int):
    entry = get_object_or_404(StockWatchlistEntry, id=entry_id, user=request.user)
    entry.delete()
    messages.success(request, f"Removed {entry.symbol} from your watchlist.")
    return redirect("web:investment_savings")


@login_required
@require_POST
def watchlist_refresh(request, entry_id: int):
    entry = get_object_or_404(StockWatchlistEntry, id=entry_id, user=request.user)
    try:
        from apps.stock_analysis.tasks import refresh_watchlist_symbol

        refresh_watchlist_symbol.delay(entry.symbol)
        messages.success(request, f"Queued a refresh for {entry.symbol}.")
    except Exception as exc:  # pragma: no cover
        messages.error(request, f"Unable to queue refresh: {exc}")
    return redirect("web:investment_savings")


@login_required
def watchlist_news(request):
    """View all news for watchlist stocks"""
    from apps.stock_analysis.models import StockWatchlistEntry

    symbol_filter = request.GET.get("symbol", "").upper().strip()

    entries = StockWatchlistEntry.objects.filter(user=request.user).select_related("snapshot").order_by("symbol")

    if symbol_filter:
        entries = entries.filter(symbol=symbol_filter)

    all_news = []
    for entry in entries:
        if entry.snapshot and entry.snapshot.news_items:
            for news_item in entry.snapshot.news_items:
                # Handle nested structure where data is inside 'summary' object
                if news_item.get("summary") and isinstance(news_item.get("summary"), dict):
                    summary = news_item.get("summary", {})
                    title = summary.get("title") or news_item.get("title", "")
                    link = (
                        summary.get("canonicalUrl", {}).get("url")
                        or summary.get("clickThroughUrl", {}).get("url")
                        or summary.get("previewUrl")
                        or news_item.get("link")
                        or news_item.get("url", "")
                    )
                    publisher = (
                        summary.get("provider", {}).get("displayName")
                        or summary.get("provider", {}).get("name")
                        or news_item.get("publisher", "Yahoo Finance")
                    )
                    summary_text = summary.get("summary") or summary.get("description") or news_item.get("summary", "")
                    published = summary.get("pubDate") or summary.get("displayTime") or news_item.get("published", "")
                else:
                    # Handle flat structure (normalized format)
                    title = news_item.get("title", "")
                    link = news_item.get("link") or news_item.get("url", "")
                    publisher = news_item.get("publisher", "Yahoo Finance")
                    summary_text = news_item.get("summary", "")
                    published = news_item.get("published", "")

                if link and title:
                    all_news.append(
                        {
                            "symbol": entry.symbol,
                            "nickname": entry.nickname,
                            "title": title,
                            "link": link,
                            "publisher": publisher,
                            "summary": summary_text,
                            "published": published,
                            "fetched_at": entry.snapshot.fetched_at,
                        }
                    )

    # Sort by fetched_at (most recent first)
    all_news.sort(key=lambda x: x.get("fetched_at") or "", reverse=True)

    return render(
        request,
        "web/watchlist_news.html",
        context={
            "active_tab": "watchlist_news",
            "page_title": "Watchlist News",
            "all_news": all_news,
            "symbol_filter": symbol_filter,
            "entries": entries,
        },
    )


@login_required
def budget_planner(request):
    """Budget Planner page with tax, expense, and debt calculations"""
    # Get budget data from aggregated accounts
    budget_data = BudgetAggregationService.get_user_budget_data(user=request.user, days=30)
    debt_data = DebtAggregationService.get_user_debt_data(user=request.user)
    plaid_budget_data = (
        PlaidDataDistributionService.get_organized_plaid_data(request.user).get("budget_planner", {}) or {}
    )
    plaid_budget_json = json.dumps(plaid_budget_data)

    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    account_summaries = []
    for entry in budget_data.get("account_balances", []):
        account = entry.get("account")
        balance = entry.get("balance")
        account_summaries.append(
            {
                "account_name": getattr(account, "account_name", ""),
                "institution_name": getattr(account, "institution_name", ""),
                "account_type": getattr(account, "account_type", ""),
                "current_balance": safe_float(getattr(balance, "current_balance", None)),
                "available_balance": safe_float(getattr(balance, "available_balance", None)),
                "as_of": getattr(balance, "balance_date", None).isoformat()
                if getattr(balance, "balance_date", None)
                else None,
            }
        )

    recent_transactions = []
    for transaction in budget_data.get("recent_transactions", [])[:10]:
        recent_transactions.append(
            {
                "date": transaction.date.isoformat() if transaction.date else None,
                "amount": safe_float(transaction.amount),
                "description": transaction.description or "",
                "category": transaction.category or "Uncategorized",
                "account_name": transaction.account.account_name if transaction.account else "",
                "transaction_type": transaction.transaction_type,
            }
        )

    spending_categories = [
        {
            "category": entry.get("category") or "Uncategorized",
            "amount": safe_float(entry.get("amount")),
            "count": entry.get("count", 0),
        }
        for entry in budget_data.get("spending_by_category", [])
    ]

    budget_insights = {
        "total_balance": safe_float(budget_data.get("total_balance")),
        "total_available": safe_float(budget_data.get("total_available")),
        "total_credit_limit": safe_float(budget_data.get("total_credit_limit")),
        "income": safe_float(budget_data.get("income")),
        "expenses": safe_float(budget_data.get("expenses")),
        "net_flow": safe_float(budget_data.get("net_flow")),
        "accounts": account_summaries,
        "recent_transactions": recent_transactions,
        "spending_by_category": spending_categories,
        "period": {
            "start": budget_data.get("start_date").isoformat() if budget_data.get("start_date") else None,
            "end": budget_data.get("end_date").isoformat() if budget_data.get("end_date") else None,
            "days": budget_data.get("period_days") or 30,
        },
    }

    debt_accounts = []
    for entry in debt_data.get("account_details", []):
        account = entry.get("account")
        balance = entry.get("balance")
        debt_accounts.append(
            {
                "account_name": getattr(account, "account_name", ""),
                "institution_name": getattr(account, "institution_name", ""),
                "account_type": getattr(account, "account_type", ""),
                "current_balance": safe_float(getattr(balance, "current_balance", None)),
                "credit_limit": safe_float(getattr(balance, "limit", None)),
                "interest_rate": safe_float(getattr(balance, "interest_rate", None)),
                "as_of": getattr(balance, "balance_date", None).isoformat()
                if getattr(balance, "balance_date", None)
                else None,
                "debt_type": entry.get("debt_type"),
            }
        )

    debt_by_type = [
        {
            "type": bucket.get("type"),
            "balance": safe_float(bucket.get("balance")),
            "count": bucket.get("count", 0),
        }
        for bucket in debt_data.get("debt_by_type", [])
    ]

    upcoming_payments = []
    for payment in debt_data.get("upcoming_payments", []):
        date_value = payment.get("date")
        upcoming_payments.append(
            {
                "account": payment.get("account"),
                "amount": safe_float(payment.get("amount")),
                "date": date_value.isoformat() if hasattr(date_value, "isoformat") else date_value,
                "debt_type": payment.get("debt_type"),
            }
        )

    estimated_monthly_payment = None
    if upcoming_payments:
        estimated_monthly_payment = upcoming_payments[0]["amount"]

    debt_insights = {
        "total_debt": safe_float(debt_data.get("total_debt")),
        "total_credit_limit": safe_float(debt_data.get("total_credit_limit")),
        "credit_utilization": safe_float(debt_data.get("credit_utilization")),
        "accounts": debt_accounts,
        "debt_by_type": debt_by_type,
        "upcoming_payments": upcoming_payments,
        "estimated_monthly_payment": estimated_monthly_payment,
        "accounts_count": debt_data.get("accounts_count", 0),
    }

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
            "budget_insights": budget_insights,
            "budget_insights_json": json.dumps(budget_insights),
            "debt_insights": debt_insights,
            "debt_insights_json": json.dumps(debt_insights),
        },
    )


@login_required
def ai_financial_services(request):
    """AI Financial Services page with single chat interface"""
    from apps.chat.api_url_helpers import get_chat_api_url_templates, get_menu_urls
    from apps.chat.models import Chat
    from apps.chat.serializers import ChatSerializer

    # Get or create a single chat for the user
    chat = Chat.objects.filter(user=request.user).order_by("-updated_at").first()
    if not chat:
        chat = Chat.objects.create(user=request.user, name="Main Chat")

    serialized_chat = ChatSerializer(chat, context={"request": request}).data

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
    import logging

    from apps.records.models import LinkedAccount, StocksAssessment

    logger = logging.getLogger(__name__)

    assessments = StocksAssessment.objects.filter(user=request.user).order_by("-updated_at")
    # Include active, pending, and error accounts (error accounts might still have valid data)
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user,
        status__in=["active", "pending", "error"],
        account_type__in=["investment", "brokerage", "retirement"],
    ).prefetch_related("balances")

    # Get organized Plaid data
    plaid_data = PlaidDataDistributionService.get_organized_plaid_data(request.user)
    stocks_plaid_data = plaid_data.get("stocks_assessment", {}) or {}
    plaid_data_json = json.dumps(stocks_plaid_data)
    total_investments = float(stocks_plaid_data.get("investment_amount", 0) or 0)

    account_defaults = {
        "total_investments": total_investments,
        "accounts": stocks_plaid_data.get("accounts", []) or [],
    }

    # If no stocks accounts found but we have investment accounts, include them
    if not account_defaults["accounts"] and linked_accounts.exists():
        logger.info(
            f"No stocks accounts identified, but found {linked_accounts.count()} investment accounts - adding them as potential stock accounts"
        )
        for account in linked_accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                account_defaults["accounts"].append(
                    {
                        "id": str(account.id),
                        "name": account.account_name,
                        "balance": float(latest_balance.current_balance) if latest_balance.current_balance else 0.0,
                        "institution": account.institution_name,
                        "account_type": account.account_type,
                        "subtype": account.account_subtype or "",
                    }
                )
        # Update total investments
        if account_defaults["accounts"]:
            account_defaults["total_investments"] = sum(acc.get("balance", 0) for acc in account_defaults["accounts"])

    account_defaults_json = json.dumps(account_defaults)

    watchlist_entries = (
        StockWatchlistEntry.objects.filter(user=request.user)
        .select_related("snapshot")
        .order_by("symbol", "created_at")
    )

    # Normalize news items in snapshots to handle nested structure
    def normalize_news_item(item):
        """Normalize a news item to flat structure, handling nested 'summary' object."""
        if item.get("summary") and isinstance(item.get("summary"), dict):
            summary = item.get("summary", {})
            title = summary.get("title") or item.get("title")
            # Try multiple URL sources from nested structure
            link = None
            if summary.get("canonicalUrl") and isinstance(summary.get("canonicalUrl"), dict):
                link = summary.get("canonicalUrl", {}).get("url")
            if not link and summary.get("clickThroughUrl") and isinstance(summary.get("clickThroughUrl"), dict):
                link = summary.get("clickThroughUrl", {}).get("url")
            if not link:
                link = summary.get("previewUrl") or item.get("link") or item.get("url", "")

            publisher = "Yahoo Finance"
            if summary.get("provider") and isinstance(summary.get("provider"), dict):
                publisher = (
                    summary.get("provider", {}).get("displayName")
                    or summary.get("provider", {}).get("name")
                    or publisher
                )
            if publisher == "Yahoo Finance":
                publisher = item.get("publisher", "Yahoo Finance")

            summary_text = summary.get("summary") or summary.get("description") or item.get("summary", "")
            published = summary.get("pubDate") or summary.get("displayTime") or item.get("published", "")

            return {
                "title": title,
                "link": link,
                "url": link,  # Include both for compatibility
                "publisher": publisher,
                "summary": summary_text,
                "published": published,
            }
        else:
            # Already in flat structure
            return {
                "title": item.get("title"),
                "link": item.get("link") or item.get("url", ""),
                "url": item.get("link") or item.get("url", ""),
                "publisher": item.get("publisher", "Yahoo Finance"),
                "summary": item.get("summary", ""),
                "published": item.get("published", ""),
            }

    # Normalize news items for each watchlist entry's snapshot
    for entry in watchlist_entries:
        if entry.snapshot and entry.snapshot.news_items:
            normalized_news = []
            for news_item in entry.snapshot.news_items:
                normalized = normalize_news_item(news_item)
                if normalized.get("title") and normalized.get("link"):
                    normalized_news.append(normalized)
            # Replace news_items with normalized version (modify in memory for template)
            if normalized_news:
                entry.snapshot.news_items = normalized_news

    # Debug logging
    logger.info(
        f"Stocks assessment for user {request.user.id}: {len(account_defaults['accounts'])} accounts found, total: ${account_defaults['total_investments']}"
    )
    if account_defaults["accounts"]:
        for acc in account_defaults["accounts"]:
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
            "watchlist_entries": watchlist_entries,
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
        "biweekly": 14,
        "monthly": 30,
        "quarterly": 90,
        "biyearly": 182,
        "yearly": 365,
        "3years": 1095,
        "5years": 1825,
        "decade": 3650,
        "twodecades": 7300,
        "threedecades": 10950,
    }

    horizon_rows = []
    timeline_points = []
    for key, label in period_defs:
        data = forecast_data.get(key)
        if not isinstance(data, dict):
            continue
        price = _to_float(data.get("price") or data.get("forecast_price"))
        value = _to_float(data.get("value") or data.get("investment_value"))
        profit = _to_float(data.get("profit_loss"))
        growth = _to_float(data.get("growth_percent") or data.get("growth_pct"))
        years = _to_float(data.get("years"))
        days = data.get("days")
        if days is None and years is not None:
            days = years * 365
        elif days is None and key in period_days:
            days = period_days[key]
        target_date = data.get("target_date")

        def _normalize_level(level):
            if isinstance(level, dict):
                return level
            level_float = _to_float(level)
            if level_float is None:
                return {}
            return {"price": level_float}

        peak = _normalize_level(data.get("peak"))
        valley = _normalize_level(data.get("valley"))

        row = {
            "key": key,
            "label": label,
            "price": price,
            "value": value,
            "profit": profit,
            "growth": growth,
            "years": years,
            "target_date": target_date,
            "days": days,
            "peak": peak,
            "valley": valley,
        }
        horizon_rows.append(row)

        if price is not None:
            timeline_points.append(
                {
                    "label": str(label),
                    "price": price,
                    "value": value,
                    "target_date": target_date,
                    "days": days,
                }
            )

    timeline_points.sort(key=lambda item: item["days"] if isinstance(item.get("days"), (int, float)) else 1e9)

    investment_amount = _to_float(assessment.investment_amount) or 0.0
    current_price = _to_float(assessment.current_price) or 0.0
    shares = _to_float(assessment.share_quantity)
    if shares is None and current_price:
        shares = investment_amount / current_price if current_price else None
    current_value = _to_float((forecast_data.get("current") or {}).get("value")) or investment_amount
    biweekly_contrib = _to_float(forecast_data.get("biweekly_contribution")) or 0.0
    BIWEEKLY_PER_PHASE = 78
    three_year_data = forecast_data.get("3years") or forecast_data.get("yearly") or {}
    three_year_value = _to_float(three_year_data.get("value") or three_year_data.get("investment_value")) or 0.0
    plan_total = three_year_value + (biweekly_contrib * BIWEEKLY_PER_PHASE)

    financia_details = {
        "statistics": forecast_data.get("_statistics", {}),
        "external_factors": forecast_data.get("_external_factors", {}),
        "mean_reversion": forecast_data.get("_mean_reversion_params", {}),
        "equation_type": forecast_data.get("_equation_type"),
    }

    context = {
        "active_tab": "investment_savings",
        "page_title": _("Stocks Assessment Detail"),
        "assessment": assessment,
        "horizon_rows": horizon_rows,
        "timeline_json": json.dumps(timeline_points),
        "investment_amount": investment_amount,
        "current_price": current_price,
        "current_value": current_value,
        "shares": shares,
        "biweekly_contrib": biweekly_contrib,
        "plan_summary": {
            "three_year_value": three_year_value,
            "plan_total": plan_total,
            "biweekly": biweekly_contrib,
            "principal": investment_amount,
        },
        "financia_details": financia_details,
    }

    return render(
        request,
        "web/stocks_assessment_detail.html",
        context=context,
    )


@login_required
def savings_assessment(request):
    """Savings Assessment page"""
    from apps.records.models import LinkedAccount, SavingsAssessment

    assessments = SavingsAssessment.objects.filter(user=request.user).order_by("-updated_at")
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user, status="active", account_type="depository"
    ).prefetch_related("balances")
    plaid_savings_data = (
        PlaidDataDistributionService.get_organized_plaid_data(request.user).get("savings_assessment", {}) or {}
    )
    plaid_savings_json = json.dumps(plaid_savings_data)

    # Prepare account defaults similar to stocks assessment
    account_defaults = {
        "initial_deposit": plaid_savings_data.get("initial_deposit", 0),
        "account_name": plaid_savings_data.get("account_name", ""),
        "accounts": plaid_savings_data.get("accounts", []) or [],
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

    assessments = CDAssessment.objects.filter(user=request.user).order_by("-updated_at")
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user, status="active", account_type="depository"
    ).prefetch_related("balances")
    plaid_cd_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get("cd_assessment", {}) or {}
    plaid_cd_json = json.dumps(plaid_cd_data)

    # Prepare account defaults
    account_defaults = {
        "cd_amount": plaid_cd_data.get("cd_amount", 0),
        "account_name": plaid_cd_data.get("account_name", ""),
        "accounts": plaid_cd_data.get("accounts", []) or [],
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

    assessments = BondAssessment.objects.filter(user=request.user).order_by("-updated_at")
    # Include active, pending, and error accounts (error accounts might still have valid data)
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user, status__in=["active", "pending", "error"], account_type__in=["investment", "brokerage"]
    ).prefetch_related("balances")

    # Get organized Plaid data
    plaid_organized = PlaidDataDistributionService.get_organized_plaid_data(request.user)
    plaid_bond_data = plaid_organized.get("bond_assessment", {}) or {}
    plaid_bond_json = json.dumps(plaid_bond_data)

    # Prepare account defaults - ensure accounts list is always present
    account_defaults = {
        "face_value": plaid_bond_data.get("face_value", 0),
        "purchase_price": plaid_bond_data.get("purchase_price", 0),
        "account_name": plaid_bond_data.get("account_name", ""),
        "accounts": plaid_bond_data.get("accounts", []) or [],
    }

    # If no bond accounts found but we have investment accounts, include them as potential bond accounts
    if not account_defaults["accounts"] and linked_accounts.exists():
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"No bond accounts identified, but found {linked_accounts.count()} investment accounts - adding them as potential bond accounts"
        )
        for account in linked_accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                account_defaults["accounts"].append(
                    {
                        "id": str(account.id),
                        "name": account.account_name,
                        "balance": float(latest_balance.current_balance) if latest_balance.current_balance else 0.0,
                        "institution": account.institution_name,
                        "account_type": account.account_type,
                        "subtype": account.account_subtype or "",
                    }
                )

    account_defaults_json = json.dumps(account_defaults)

    # Debug logging
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Bond assessment for user {request.user.id}: {len(account_defaults['accounts'])} accounts found")
    if account_defaults["accounts"]:
        for acc in account_defaults["accounts"]:
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
    from datetime import timedelta

    from django.utils import timezone

    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    from apps.stock_analysis.models import StockWatchSnapshot
    from apps.stock_analysis.services import StockAnalysisService

    period = request.GET.get("period", "1y")
    interval = request.GET.get("interval", "1d")

    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)

    # PRIORITY: Use web-scraped data from StockWatchSnapshot first
    stock_data = {}
    statistics = {}
    yahoo_profile = {}
    news_items = []

    # Trigger web scraping if needed (runs in background)
    from apps.stock_analysis.tasks import scrape_yahoo_finance_comprehensive

    try:
        snapshot = StockWatchSnapshot.objects.filter(symbol=symbol.upper()).first()
        should_refresh = True
        if snapshot and snapshot.fetched_at:
            age = timezone.now() - snapshot.fetched_at
            should_refresh = age > timedelta(hours=1)  # Refresh if older than 1 hour

        if should_refresh:
            # Trigger web scraping in background
            try:
                scrape_yahoo_finance_comprehensive.delay(symbol.upper(), force_refresh=True)
                logger.info(f"Triggered web scraping for {symbol.upper()} for detailed reports")
            except Exception:
                # If Celery not available, try synchronous
                try:
                    scrape_yahoo_finance_comprehensive(symbol.upper(), force_refresh=True)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Error triggering web scraping: {e}")

    try:
        # Check for recent web-scraped snapshot
        snapshot = StockWatchSnapshot.objects.filter(symbol=symbol.upper()).first()
        if snapshot and snapshot.payload and snapshot.fetched_at:
            age = timezone.now() - snapshot.fetched_at
            if age < timedelta(hours=24):  # Use if less than 24 hours old
                payload = snapshot.payload or {}
                yahoo_comprehensive = payload.get("yahoo_comprehensive", {})

                # Extract stock_data from web-scraped snapshot
                summary = payload.get("summary", {})
                statistics_data = payload.get("statistics", {})
                yahoo_comprehensive = payload.get("yahoo_comprehensive", {})

                # Get comprehensive data if available - prioritize yahoo_comprehensive
                if yahoo_comprehensive:
                    summary = yahoo_comprehensive.get("summary", summary)
                    statistics_data = yahoo_comprehensive.get("statistics", statistics_data)
                    financials = yahoo_comprehensive.get("financials", {})
                    yahoo_profile = yahoo_comprehensive.get("profile", payload.get("profile", {}))
                else:
                    financials = payload.get("financials", {})
                    yahoo_profile = payload.get("profile", {})

                # Extract additional metrics from financials pages (income statement, balance sheet, cash flow)
                # This ensures we have all data needed for ratio calculations
                income_statement = financials.get("income_statement", {})
                balance_sheet = financials.get("balance_sheet", {})
                cash_flow_statement = financials.get("cash_flow", {})

                # Extract key metrics from financial statements and add to stock_data
                # Income Statement metrics
                for key, values in income_statement.items():
                    if values and len(values) > 0:
                        # Use most recent period (first value)
                        value = values[0] if isinstance(values, list) else values
                        if "Revenue" in key or "Total Revenue" in key:
                            stock_data["Revenue  (ttm)"] = value
                        elif "Net Income" in key or "Net Earnings" in key:
                            stock_data["Net Income Avi to Common  (ttm)"] = value
                        elif "Operating Income" in key or "Operating Profit" in key:
                            stock_data["Operating Income  (ttm)"] = value
                        elif "Gross Profit" in key:
                            stock_data["Gross Profit  (ttm)"] = value
                        elif "EBITDA" in key:
                            stock_data["EBITDA"] = value

                # Balance Sheet metrics
                for key, values in balance_sheet.items():
                    if values and len(values) > 0:
                        value = values[0] if isinstance(values, list) else values
                        if "Total Assets" in key:
                            stock_data["Total Assets  (mrq)"] = value
                        elif "Total Stockholder Equity" in key or "Shareholders' Equity" in key:
                            stock_data["Total Equity"] = value
                        elif "Total Debt" in key or "Total Liabilities" in key:
                            stock_data["Total Debt  (mrq)"] = value
                        elif "Total Cash" in key or "Cash and Cash Equivalents" in key:
                            stock_data["Total Cash  (mrq)"] = value
                        elif "Current Assets" in key:
                            stock_data["Current Assets  (mrq)"] = value
                        elif "Current Liabilities" in key:
                            stock_data["Current Liabilities  (mrq)"] = value
                        elif "Shares Outstanding" in key:
                            stock_data["Shares Outstanding 5"] = value

                # Cash Flow metrics
                for key, values in cash_flow_statement.items():
                    if values and len(values) > 0:
                        value = values[0] if isinstance(values, list) else values
                        if "Operating Cash Flow" in key or "Cash from Operations" in key:
                            stock_data["Operating Cash Flow  (ttm)"] = value
                        elif "Free Cash Flow" in key or "Levered Free Cash Flow" in key:
                            stock_data["Levered Free Cash Flow  (ttm)"] = value

                # Merge summary and statistics into stock_data (prioritize statistics for detailed metrics)
                # Statistics page has more comprehensive data
                stock_data = {**summary, **statistics_data, **stock_data}
                statistics = statistics_data
                news_items = snapshot.news_items or []

                # Add current_price from snapshot (most reliable source)
                if snapshot.current_price:
                    stock_data["currentPrice"] = float(snapshot.current_price)
                    stock_data["Current Price"] = float(snapshot.current_price)

                # Add market cap if available
                if "marketCap" in summary:
                    stock_data["Market Cap"] = summary["marketCap"]
                elif "Market Cap" in statistics_data:
                    stock_data["Market Cap"] = statistics_data["Market Cap"]

                logger.info(f"Using web-scraped snapshot data for {symbol.upper()} (age: {age})")
                logger.info(
                    f"Extracted {len(stock_data)} stock_data fields, {len(income_statement)} income items, {len(balance_sheet)} balance items, {len(cash_flow_statement)} cash flow items"
                )
    except Exception as e:
        logger.warning(f"Error using snapshot data: {e}")

    # If no snapshot data, use aggregator
    if not stock_data:
        try:
            page_data = aggregator.get_data_for_detailed_reports(symbol.upper())
            stock_data = page_data.get("stock_data", {})
            statistics = page_data.get("statistics", {})
            yahoo_profile = page_data.get("yahoo_profile", {})
            news_items = page_data.get("news", [])
        except Exception as e:
            # Fallback to original method
            print(f"Aggregator failed, using fallback: {e}")
            stock_data = service.stock_app.fetch_stock_data(symbol.upper())
            statistics = {}
            yahoo_profile = {}
            news_items = []

    # Normalize stock_data keys to match what stock_ratio.py expects
    # This maps Yahoo Finance keys to the expected metric keys
    stock_data = _normalize_stock_data_for_ratios(stock_data, statistics)

    # Log available keys for debugging
    if stock_data:
        available_keys = [k for k, v in stock_data.items() if v is not None and v != ""]
        logger.debug(f"Available stock_data keys for {symbol.upper()}: {len(available_keys)} keys")
        logger.debug(f"Sample keys: {available_keys[:10]}")

    # Analyze ratios using financia code - this calculates ratios and performance ratings
    ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else None

    if ratios_table is not None and not ratios_table.empty:
        logger.info(f"Successfully calculated {len(ratios_table)} ratios for {symbol.upper()}")
    else:
        logger.warning(f"No ratios calculated for {symbol.upper()} - stock_data may be missing required fields")

    # Convert ratios_table to dict for template and normalize keys
    ratios_dict = []
    if ratios_table is not None and not ratios_table.empty:
        ratios_records = ratios_table.to_dict("records")
        for ratio in ratios_records:
            normalized_ratio = {}
            for key, value in ratio.items():
                normalized_key = key.replace(" ", "_").replace("-", "_").lower()
                normalized_ratio[normalized_key] = value
                normalized_ratio[key] = value

            def grab(keys):
                for key in keys:
                    if key in normalized_ratio and normalized_ratio[key] not in (None, ""):
                        return normalized_ratio[key]
                return None

            normalized_ratio["ratio_name"] = grab(["ratio_name", "ratio", "name", "Ratio Name", "Name"])
            normalized_ratio["ratio_value"] = grab(["ratio_value", "value", "Ratio Value", "Value"])
            normalized_ratio["performance"] = grab(["performance", "perf", "Performance"])

            # Set display_name with fallback logic
            if normalized_ratio.get("ratio_name"):
                normalized_ratio["display_name"] = normalized_ratio["ratio_name"]
            else:
                # Try to find any key that might be a name from the original ratio
                for orig_key in ratio.keys():
                    if orig_key not in ["Ratio Value", "Value", "value", "Performance", "performance"]:
                        if ratio[orig_key] not in (None, ""):
                            normalized_ratio["display_name"] = str(ratio[orig_key])
                            break
                else:
                    normalized_ratio["display_name"] = "Metric"

            ratios_dict.append(normalized_ratio)

    # Convert news items to HTML
    news_html_parts = []
    for item in news_items:
        title = item.get("title", "")
        url = item.get("url", "")
        publisher = item.get("publisher", item.get("source", ""))
        description = item.get("description", "")

        if title and url:
            article_html = f"<article><h2>{title}</h2>"
            if publisher:
                article_html += f"<p><em>{publisher}</em></p>"
            if description:
                article_html += f"<p>{description}</p>"
            article_html += f'<p><a href="{url}">Read more</a></p></article>'
            news_html_parts.append(article_html)

    news_html = "\n".join(news_html_parts) if news_html_parts else ""

    # Merge stock_data with statistics and profile
    enhanced_stock_data = {**(stock_data or {}), **statistics}
    if yahoo_profile:
        enhanced_stock_data["profile"] = yahoo_profile

    # Generate performance thresholds table based on financia code
    performance_thresholds = _get_performance_thresholds()

    # Get valuation, financials, and analysis data from snapshot if available
    valuation_data = {}
    financials_data = {}
    analysis_data = {}
    chart_details_data = {}
    options_data = {}
    holders_data = {}
    historical_data_list = []

    try:
        snapshot = StockWatchSnapshot.objects.filter(symbol=symbol.upper()).first()
        if snapshot and snapshot.payload:
            payload = snapshot.payload or {}
            yahoo_comprehensive = payload.get("yahoo_comprehensive", {})
            if yahoo_comprehensive:
                valuation_data = yahoo_comprehensive.get("valuation", {})
                financials_data = yahoo_comprehensive.get("financials", {})
                analysis_data = yahoo_comprehensive.get("analysis", {})
                chart_details_data = yahoo_comprehensive.get("chart_details", {})
                options_data = yahoo_comprehensive.get("options", {})
                holders_data = yahoo_comprehensive.get("holders", {})
                historical_data_list = yahoo_comprehensive.get("historical_data", {}).get("price_history", [])
            else:
                valuation_data = payload.get("valuation", {})
                financials_data = payload.get("financials", {})
                analysis_data = payload.get("analysis", {})
                chart_details_data = payload.get("chart_details", {})
                options_data = payload.get("options", {})
                holders_data = payload.get("holders", {})
                historical_data_list = (
                    payload.get("historical_data", {}).get("price_history", [])
                    if isinstance(payload.get("historical_data"), dict)
                    else []
                )

            # Ensure current_price is in valuation_data for template
            if snapshot.current_price and not valuation_data.get("current_price"):
                try:
                    valuation_data["current_price"] = float(snapshot.current_price)
                except (ValueError, TypeError):
                    pass

            # If valuation_data exists but missing current_price, try to get from stock_data
            if valuation_data and not valuation_data.get("current_price"):
                current_price = enhanced_stock_data.get("currentPrice") or enhanced_stock_data.get("Current Price")
                if current_price:
                    try:
                        if isinstance(current_price, str):
                            current_price = float(current_price.replace("$", "").replace(",", ""))
                        valuation_data["current_price"] = current_price
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        logger.warning(f"Error getting additional data: {e}")

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
            "performance_thresholds": performance_thresholds,
            "valuation_data": valuation_data,
            "financials_data": financials_data,
            "analysis_data": analysis_data,
            "chart_details": chart_details_data,
            "options_data": options_data,
            "holders_data": holders_data,
            "historical_data": historical_data_list,
            "period": period,
            "interval": interval,
        },
    )


def _normalize_stock_data_for_ratios(stock_data, statistics):
    """
    Normalize stock data keys to match what stock_ratio.py expects.
    Maps Yahoo Finance web-scraped keys to expected metric keys.
    """
    if not stock_data:
        return {}

    normalized = {}

    # Key mapping: Yahoo Finance key -> Expected metric key
    # This handles variations from web scraping, API, and database sources
    key_mappings = {
        # Market Cap variations
        "marketCap": "Market Cap",
        "market_cap": "Market Cap",
        "Market Cap": "Market Cap",
        # Revenue variations
        "revenue": "Revenue  (ttm)",
        "totalRevenue": "Revenue  (ttm)",
        "Revenue (ttm)": "Revenue  (ttm)",
        "Revenue  (ttm)": "Revenue  (ttm)",
        # Net Income variations
        "netIncome": "Net Income Avi to Common  (ttm)",
        "netIncomeToCommon": "Net Income Avi to Common  (ttm)",
        "Net Income Avi to Common  (ttm)": "Net Income Avi to Common  (ttm)",
        # Debt variations
        "totalDebt": "Total Debt  (mrq)",
        "Total Debt (mrq)": "Total Debt  (mrq)",
        "Total Debt  (mrq)": "Total Debt  (mrq)",
        # Cash variations
        "totalCash": "Total Cash  (mrq)",
        "Total Cash (mrq)": "Total Cash  (mrq)",
        "Total Cash  (mrq)": "Total Cash  (mrq)",
        # Gross Profit variations
        "grossProfit": "Gross Profit  (ttm)",
        "grossProfits": "Gross Profit  (ttm)",
        "Gross Profit (ttm)": "Gross Profit  (ttm)",
        "Gross Profit  (ttm)": "Gross Profit  (ttm)",
        # Operating Cash Flow variations
        "operatingCashFlow": "Operating Cash Flow  (ttm)",
        "operatingCashflow": "Operating Cash Flow  (ttm)",
        "Operating Cash Flow (ttm)": "Operating Cash Flow  (ttm)",
        "Operating Cash Flow  (ttm)": "Operating Cash Flow  (ttm)",
        # EBITDA variations
        "ebitda": "EBITDA",
        "EBITDA": "EBITDA",
        # Assets variations
        "totalAssets": "Total Assets  (mrq)",
        "Total Assets (mrq)": "Total Assets  (mrq)",
        "Total Assets  (mrq)": "Total Assets  (mrq)",
        # Current Assets variations
        "currentAssets": "Current Assets  (mrq)",
        "Current Assets (mrq)": "Current Assets  (mrq)",
        "Current Assets  (mrq)": "Current Assets  (mrq)",
        # Current Liabilities variations
        "currentLiabilities": "Current Liabilities  (mrq)",
        "Current Liabilities (mrq)": "Current Liabilities  (mrq)",
        "Current Liabilities  (mrq)": "Current Liabilities  (mrq)",
        # Free Cash Flow variations
        "freeCashFlow": "Levered Free Cash Flow  (ttm)",
        "freeCashflow": "Levered Free Cash Flow  (ttm)",
        "Levered Free Cash Flow (ttm)": "Levered Free Cash Flow  (ttm)",
        "Levered Free Cash Flow  (ttm)": "Levered Free Cash Flow  (ttm)",
        # Shares Outstanding variations
        "sharesOutstanding": "Shares Outstanding 5",
        "Shares Outstanding": "Shares Outstanding 5",
        "Shares Outstanding 5": "Shares Outstanding 5",
        # Operating Income variations
        "operatingIncome": "Operating Income  (ttm)",
        "Operating Income (ttm)": "Operating Income  (ttm)",
        "Operating Income  (ttm)": "Operating Income  (ttm)",
        # Predefined ratios - map various formats
        "trailingEps": "Diluted EPS  (ttm)",
        "dilutedEps": "Diluted EPS  (ttm)",
        "Diluted EPS  (ttm)": "Diluted EPS  (ttm)",
        "trailingPE": "PE Ratio (TTM)",
        "peRatio": "PE Ratio (TTM)",
        "PE Ratio (TTM)": "PE Ratio (TTM)",
        "Trailing P/E": "PE Ratio (TTM)",
        "dividendYield": "Forward Annual Dividend Yield 4",
        "Forward Annual Dividend Yield 4": "Forward Annual Dividend Yield 4",
        "Dividend Yield": "Forward Annual Dividend Yield 4",
        "debtToEquity": "Total Debt/Equity  (mrq)",
        "Total Debt/Equity  (mrq)": "Total Debt/Equity  (mrq)",
        "Debt to Equity": "Total Debt/Equity  (mrq)",
        "currentRatio": "Current Ratio  (mrq)",
        "Current Ratio (mrq)": "Current Ratio  (mrq)",
        "Current Ratio  (mrq)": "Current Ratio  (mrq)",
        "operatingMargins": "Operating Margin  (ttm)",
        "operatingMargin": "Operating Margin  (ttm)",
        "Operating Margin (ttm)": "Operating Margin  (ttm)",
        "Operating Margin  (ttm)": "Operating Margin  (ttm)",
        "profitMargins": "Profit Margin",
        "netProfitMargin": "Profit Margin",
        "Profit Margin": "Profit Margin",
        "returnOnAssets": "Return on Assets  (ttm)",
        "Return on Assets (ttm)": "Return on Assets  (ttm)",
        "Return on Assets  (ttm)": "Return on Assets  (ttm)",
        "returnOnEquity": "Return on Equity  (ttm)",
        "Return on Equity (ttm)": "Return on Equity  (ttm)",
        "Return on Equity  (ttm)": "Return on Equity  (ttm)",
        "priceToSalesTrailing12Months": "Price/Sales",
        "priceToSales": "Price/Sales",
        "Price/Sales": "Price/Sales",
        "Price-to-Sales": "Price/Sales",
        "priceToBook": "Price/Book",
        "Price/Book": "Price/Book",
        "Price-to-Book": "Price/Book",
        "enterpriseToEbitda": "Enterprise Value/EBITDA",
        "Enterprise Value/EBITDA": "Enterprise Value/EBITDA",
        "EV/EBITDA": "Enterprise Value/EBITDA",
        "revenuePerShare": "Revenue Per Share  (ttm)",
        "Revenue Per Share (ttm)": "Revenue Per Share  (ttm)",
        "Revenue Per Share  (ttm)": "Revenue Per Share  (ttm)",
        "bookValue": "Book Value Per Share  (mrq)",
        "Book Value Per Share (mrq)": "Book Value Per Share  (mrq)",
        "Book Value Per Share  (mrq)": "Book Value Per Share  (mrq)",
    }

    # First, copy all original data
    normalized.update(stock_data)

    # Add statistics data with normalized keys
    if statistics:
        for key, value in statistics.items():
            # Try to map the key
            mapped_key = key_mappings.get(key, key)
            normalized[mapped_key] = value
            # Also keep original key for fallback
            if mapped_key != key:
                normalized[key] = value

    # Map all keys in stock_data to expected format
    for key, value in list(normalized.items()):
        if key in key_mappings:
            mapped_key = key_mappings[key]
            if mapped_key != key:
                normalized[mapped_key] = value
                # Keep original for reference
                if mapped_key not in normalized:
                    normalized[mapped_key] = value

    # Handle special cases - extract from nested structures
    # Market Cap might be in different formats
    if "Market Cap" not in normalized or not normalized.get("Market Cap"):
        # Try to get from various sources
        for key in ["marketCap", "market_cap", "Market Cap", "MarketCap"]:
            if key in normalized and normalized[key]:
                normalized["Market Cap"] = normalized[key]
                break

    # Ensure we have all keys that might be needed, even if None
    required_keys = [
        "Market Cap",
        "Revenue  (ttm)",
        "Net Income Avi to Common  (ttm)",
        "Total Debt  (mrq)",
        "Total Cash  (mrq)",
        "Gross Profit  (ttm)",
        "Operating Cash Flow  (ttm)",
        "EBITDA",
        "Total Assets  (mrq)",
        "Current Assets  (mrq)",
        "Current Liabilities  (mrq)",
        "Levered Free Cash Flow  (ttm)",
        "Shares Outstanding 5",
        "Operating Income  (ttm)",
    ]

    for key in required_keys:
        if key not in normalized:
            normalized[key] = None

    return normalized


def _get_performance_thresholds():
    """
    Generate performance thresholds table based on financia code.
    Returns a list of dictionaries with ratio name, thresholds, and buy/sell indicators.
    """
    thresholds = [
        {
            "ratio_name": "P/E Ratio",
            "poor": "> 25",
            "mediocre": "15 - 25",
            "excellent": "10 - 15",
            "perfect": "≤ 10",
            "direction": "Lower is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (overvalued)",
        },
        {
            "ratio_name": "Price-to-Sales",
            "poor": "> 3",
            "mediocre": "2.25 - 3",
            "excellent": "1.5 - 2.25",
            "perfect": "≤ 1.5",
            "direction": "Lower is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (overvalued)",
        },
        {
            "ratio_name": "Price-to-Book",
            "poor": "> 5",
            "mediocre": "3.6 - 5",
            "excellent": "2.2 - 3.6",
            "perfect": "≤ 2.2",
            "direction": "Lower is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (overvalued)",
        },
        {
            "ratio_name": "Debt to Equity",
            "poor": "> 2",
            "mediocre": "1 - 2",
            "excellent": "0.5 - 1",
            "perfect": "≤ 0.5",
            "direction": "Lower is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (high debt risk)",
        },
        {
            "ratio_name": "Dividend Yield",
            "poor": "< 2%",
            "mediocre": "2% - 3.33%",
            "excellent": "3.33% - 4.67%",
            "perfect": "≥ 4.67%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (low income)",
        },
        {
            "ratio_name": "Gross Margin",
            "poor": "< 30%",
            "mediocre": "30% - 50%",
            "excellent": "50% - 70%",
            "perfect": "≥ 70%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (low efficiency)",
        },
        {
            "ratio_name": "Net Profit Margin",
            "poor": "< 5%",
            "mediocre": "5% - 10%",
            "excellent": "10% - 15%",
            "perfect": "≥ 15%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (low profitability)",
        },
        {
            "ratio_name": "Operating Margin",
            "poor": "< 5%",
            "mediocre": "5% - 11.67%",
            "excellent": "11.67% - 18.33%",
            "perfect": "≥ 18.33%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (operational issues)",
        },
        {
            "ratio_name": "Return on Assets (ROA)",
            "poor": "< 2.5%",
            "mediocre": "2.5% - 10%",
            "excellent": "10% - 17.5%",
            "perfect": "≥ 17.5%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (inefficient asset use)",
        },
        {
            "ratio_name": "Return on Equity (ROE)",
            "poor": "< 2.5%",
            "mediocre": "2.5% - 10%",
            "excellent": "10% - 17.5%",
            "perfect": "≥ 17.5%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (low shareholder returns)",
        },
        {
            "ratio_name": "Current Ratio",
            "poor": "< 0.5",
            "mediocre": "0.5 - 1.33",
            "excellent": "1.33 - 2.17",
            "perfect": "≥ 2.17",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (liquidity risk)",
        },
        {
            "ratio_name": "Free Cash Flow Yield",
            "poor": "< 3%",
            "mediocre": "3% - 6%",
            "excellent": "6% - 9%",
            "perfect": "≥ 9%",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (cash generation issues)",
        },
        {
            "ratio_name": "EV/EBITDA",
            "poor": "> 25",
            "mediocre": "20 - 25",
            "excellent": "15 - 20",
            "perfect": "≤ 15",
            "direction": "Lower is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (overvalued)",
        },
        {
            "ratio_name": "Cash Flow to Debt",
            "poor": "< 0.5",
            "mediocre": "0.5 - 1",
            "excellent": "1 - 1.5",
            "perfect": "≥ 1.5",
            "direction": "Higher is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (debt servicing risk)",
        },
        {
            "ratio_name": "Debt to Assets",
            "poor": "> 80%",
            "mediocre": "60% - 80%",
            "excellent": "40% - 60%",
            "perfect": "≤ 40%",
            "direction": "Lower is better",
            "buy_indicator": "Perfect or Excellent",
            "sell_indicator": "Poor (high leverage)",
        },
    ]
    return thresholds


@login_required
def stocks_analysis_predictions(request, symbol):
    """Stock Analysis/Predictions page - shows forecast charts and predictions"""
    import json

    import pandas as pd

    from apps.stock_analysis.lib.analysis_utils import build_forecast_error_rows
    from apps.stock_analysis.services import StockAnalysisService

    period = request.GET.get("period", "1y")
    interval = request.GET.get("interval", "1d")
    equation_type = request.GET.get("model", "Geometric Brownian Motion External Macroeconomic Factors")
    market_ticker = request.GET.get("market", "^GSPC")
    vix_ticker = request.GET.get("vix", "^VIX")
    tnx_ticker = request.GET.get("tnx", "^TNX")

    service = StockAnalysisService()
    history_df = service.stock_app.fetch_stock_history(symbol.upper(), period, interval)
    stock_data = service.stock_app.fetch_stock_data(symbol.upper())
    ratios_table = service.stock_app.analyze_stock(stock_data) if stock_data else pd.DataFrame()

    forecast_df = None
    forecast_errors = []
    error_data = []
    if not history_df.empty:
        forecast_df = service.stock_app.forecast_prices_advanced(
            history_df,
            symbol.upper(),
            ratios_table,
            interval,
            equation_type=equation_type,
            market_ticker=market_ticker,
            vix_ticker=vix_ticker,
            tnx_ticker=tnx_ticker,
            forecast_days=365,
        )

        # Calculate prediction errors
        if forecast_df is not None and not forecast_df.empty and build_forecast_error_rows:
            forecast_errors = build_forecast_error_rows(history_df, forecast_df)
            # Serialize error data for chart
            for error_row in forecast_errors:
                error_data.append(
                    {
                        "date": error_row["date"],
                        "error": error_row["error"] if error_row["error"] is not None else 0,
                    }
                )

    # Serialize data for template
    historical_data = []
    forecast_data = []
    future_forecast_data = []  # Only future dates (non-overlapping)

    if not history_df.empty:
        for idx, row in history_df.iterrows():
            date_val = row.get("Date")
            close_val = row.get("Close")
            date_str = (
                date_val.strftime("%Y-%m-%d")
                if pd.notna(date_val) and hasattr(date_val, "strftime")
                else str(date_val)
                if date_val
                else ""
            )
            historical_data.append({"date": date_str, "close": float(close_val) if pd.notna(close_val) else 0})

    if forecast_df is not None and not forecast_df.empty:
        # Get overlap count (number of error rows = overlap)
        overlap_count = len(forecast_errors) if forecast_errors else 0

        for forecast_idx, row in forecast_df.iterrows():
            date_val = row.get("Date")
            forecast_val = row.get("Forecasted_Close")
            date_str = (
                date_val.strftime("%Y-%m-%d")
                if pd.notna(date_val) and hasattr(date_val, "strftime")
                else str(date_val)
                if date_val
                else ""
            )
            forecast_item = {"date": date_str, "forecasted_close": float(forecast_val) if pd.notna(forecast_val) else 0}
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
    import json

    import pandas as pd

    from apps.stock_analysis.lib.analysis_utils import build_market_overview
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    from apps.stock_analysis.services import StockAnalysisService

    market_ticker = request.GET.get("market", "^GSPC")

    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)

    # Get aggregated data for market overview page
    try:
        page_data = aggregator.get_data_for_market_overview(symbol.upper(), market_ticker)
        stock_history = page_data.get("stock_history")
        benchmark_history = page_data.get("benchmark_history")
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        stock_history = service.stock_app.fetch_stock_history(symbol.upper(), period="1y", interval="1d")
        benchmark_history = service.stock_app.fetch_stock_history(market_ticker, period="1y", interval="1d")

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
        if "Close" not in stock_history.columns:
            stock_history = pd.DataFrame()

        if build_market_overview and not stock_history.empty:
            try:
                # Ensure stock_history has required columns and is properly formatted
                if "Close" in stock_history.columns and "Date" in stock_history.columns:
                    # Ensure Close is numeric
                    stock_history = stock_history.copy()
                    stock_history["Close"] = pd.to_numeric(stock_history["Close"], errors="coerce")
                    stock_history = stock_history.dropna(subset=["Close", "Date"])

                    if not stock_history.empty:
                        market_overview_data = build_market_overview(stock_history, symbol.upper(), market_ticker)
                        metrics = market_overview_data.get("metrics", {})
                        # Use the series data from build_market_overview if available
                        if "price_series" in market_overview_data:
                            stock_data = [
                                {"date": str(item.get("index", "")), "value": item.get("price", 0)}
                                for item in market_overview_data.get("price_series", [])
                            ]
                        if "benchmark_series" in market_overview_data:
                            market_data = [
                                {"date": str(item.get("index", "")), "value": item.get("price", 0)}
                                for item in market_overview_data.get("benchmark_series", [])
                            ]
            except Exception as e:
                import traceback

                print(f"build_market_overview failed: {e}")
                traceback.print_exc()
                market_overview_data = {}

        # Fallback to manual calculation if build_market_overview not available
        if not stock_data and stock_history is not None and not stock_history.empty:
            # Ensure Close column exists and is numeric
            if "Close" in stock_history.columns:
                close_series = pd.to_numeric(stock_history["Close"], errors="coerce").dropna()
                if close_series.empty:
                    stock_start = 1
                else:
                    stock_start = float(close_series.iloc[0])
            else:
                stock_start = 1

            if market_history is not None and not market_history.empty and "Close" in market_history.columns:
                market_close_series = pd.to_numeric(market_history["Close"], errors="coerce").dropna()
                if market_close_series.empty:
                    market_start = 1
                else:
                    market_start = float(market_close_series.iloc[0])
            else:
                market_start = 1

            for stock_idx, row in stock_history.iterrows():
                close_val = row.get("Close")
                date_val = row.get("Date")
                if pd.notna(close_val):
                    stock_data.append(
                        {
                            "date": date_val.strftime("%Y-%m-%d")
                            if pd.notna(date_val) and hasattr(date_val, "strftime")
                            else str(date_val)
                            if date_val
                            else "",
                            "value": (float(close_val) / stock_start - 1) * 100,
                        }
                    )

            for market_idx, row in market_history.iterrows():
                close_val = row.get("Close")
                date_val = row.get("Date")
                if pd.notna(close_val):
                    market_data.append(
                        {
                            "date": date_val.strftime("%Y-%m-%d")
                            if pd.notna(date_val) and hasattr(date_val, "strftime")
                            else str(date_val)
                            if date_val
                            else "",
                            "value": (float(close_val) / market_start - 1) * 100,
                        }
                    )

            # Calculate basic metrics
            if stock_history.shape[0] > 0 and not stock_history.empty:
                # Ensure Close column exists and is numeric
                if "Close" in stock_history.columns:
                    close_series = pd.to_numeric(stock_history["Close"], errors="coerce").dropna()
                    if not close_series.empty:
                        current_price = float(close_series.iloc[-1])
                        stock_perf = (current_price / stock_start - 1) * 100
                    else:
                        current_price = None
                        stock_perf = None
                else:
                    current_price = None
                    stock_perf = None

                if not market_history.empty and "Close" in market_history.columns:
                    market_close_series = pd.to_numeric(market_history["Close"], errors="coerce").dropna()
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
                if "Close" in stock_history.columns:
                    close_series = pd.to_numeric(stock_history["Close"], errors="coerce")
                    daily_returns = close_series.pct_change().dropna()
                    latest_return = float(daily_returns.iloc[-1]) * 100 if not daily_returns.empty else None
                else:
                    latest_return = None

                metrics = {
                    "current_price": current_price,
                    "period_performance_pct": stock_perf,
                    "benchmark_performance_pct": market_perf,
                    "relative_performance_pct": relative,
                    "latest_daily_return_pct": latest_return,
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
            "status_message": market_overview_data.get("message", ""),
        },
    )


@login_required
def stocks_risk_dashboard(request, symbol):
    """Risk Dashboard page - shows risk metrics and statistics"""
    import pandas as pd

    from apps.stock_analysis.lib.analysis_utils import calculate_risk_statistics, generate_risk_insights
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    from apps.stock_analysis.services import StockAnalysisService

    period = request.GET.get("period", "1y")
    market_ticker = request.GET.get("market", "^GSPC")

    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)

    # Get aggregated data for risk dashboard page
    try:
        page_data = aggregator.get_data_for_risk_dashboard(symbol.upper(), market_ticker)
        history_df = page_data.get("stock_history")
        yahoo_statistics = page_data.get("yahoo_statistics", {})
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        history_df = service.stock_app.fetch_stock_history(symbol.upper(), period, interval="1d")
        yahoo_statistics = {}

    # Ensure history_df is a proper DataFrame with required columns
    if history_df is not None and not isinstance(history_df, pd.DataFrame):
        history_df = pd.DataFrame()
    elif history_df is not None and isinstance(history_df, pd.DataFrame):
        # Ensure required columns exist
        if "Close" not in history_df.columns or "Date" not in history_df.columns:
            history_df = pd.DataFrame()
        elif not history_df.empty:
            # Ensure Close column is numeric
            try:
                history_df = history_df.copy()
                if "Close" in history_df.columns:
                    history_df["Close"] = pd.to_numeric(history_df["Close"], errors="coerce")
                if "Date" in history_df.columns:
                    history_df["Date"] = pd.to_datetime(history_df["Date"], errors="coerce")
                history_df = history_df.dropna(subset=["Date", "Close"])
            except Exception as e:
                print(f"Error cleaning history_df: {e}")
                history_df = pd.DataFrame()

    risk_metrics = {}
    risk_insights = []
    benchmark_df = None

    if calculate_risk_statistics and history_df is not None and not history_df.empty:
        try:
            risk_metrics, benchmark_df = calculate_risk_statistics(history_df, market_ticker)
            if generate_risk_insights:
                risk_insights = generate_risk_insights(risk_metrics)

            # Enhance risk metrics with Yahoo Finance statistics if available
            if yahoo_statistics:
                # Merge additional statistics that might not be in risk_metrics
                for key, value in yahoo_statistics.items():
                    if key not in risk_metrics and value is not None:
                        risk_metrics[f"yahoo_{key}"] = value
        except Exception as e:
            import traceback

            print(f"Error calculating risk statistics: {e}")
            traceback.print_exc()
            # Continue with empty risk_metrics

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
    from apps.stock_analysis.lib.analysis_utils import build_decision_support
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    from apps.stock_analysis.services import StockAnalysisService

    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)

    # Get aggregated data for decision support page
    try:
        page_data = aggregator.get_data_for_decision_support(symbol.upper())
        stock_data = page_data.get("fundamentals", {})
        statistics = page_data.get("statistics", {})
        yahoo_profile = page_data.get("yahoo_profile", {})
        yahoo_holders = page_data.get("yahoo_holders", {})
        stock_history = page_data.get("stock_history", None)
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        stock_data = service.stock_app.fetch_stock_data(symbol.upper())
        statistics = {}
        yahoo_profile = {}
        yahoo_holders = {}
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
        enhanced_stock_data["profile"] = yahoo_profile
    if yahoo_holders:
        enhanced_stock_data["holders"] = yahoo_holders

    decision_support = {}
    if build_decision_support and stock_data and history_df is not None and not history_df.empty:
        decision_support = build_decision_support(stock_data, ratios_table, history_df)

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
    from apps.stock_analysis.lib.data_aggregator import StockDataAggregator
    from apps.stock_analysis.models import InvestmentPlan
    from apps.stock_analysis.services import StockAnalysisService

    service = StockAnalysisService()
    aggregator = StockDataAggregator(fetcher=service.stock_app.fetcher)

    # Get aggregated data for investment planner page
    try:
        page_data = aggregator.get_data_for_investment_planner(symbol.upper())
        fundamentals = page_data.get("fundamentals", {})
        statistics = page_data.get("statistics", {})
        stock_history = page_data.get("stock_history")
        yahoo_options = page_data.get("yahoo_options", {})
        yahoo_holders = page_data.get("yahoo_holders", {})
    except Exception as e:
        # Fallback to original method
        print(f"Aggregator failed, using fallback: {e}")
        fundamentals = service.stock_app.fetch_stock_data(symbol.upper()) or {}
        statistics = {}
        stock_history = None
        yahoo_options = {}
        yahoo_holders = {}

    # Get current price from aggregated data
    current_price = fundamentals.get("currentPrice", None)
    if (current_price is None or current_price <= 0) and stock_history is not None and not stock_history.empty:
        try:
            from apps.stock_analysis.lib.investment_utils import get_current_price

            current_price = get_current_price(stock_history)
        except (ImportError, Exception):
            if "Close" in stock_history.columns:
                close_prices = stock_history["Close"].dropna()
                if not close_prices.empty:
                    current_price = float(close_prices.iloc[-1])

    # Get user's investment plans for this symbol
    plans = InvestmentPlan.objects.filter(user=request.user, stock_analysis__symbol=symbol.upper()).order_by(
        "-created_at"
    )

    # Merge aggregated data
    enhanced_data = {**fundamentals, **statistics}
    if yahoo_options:
        enhanced_data["options"] = yahoo_options
    if yahoo_holders:
        enhanced_data["holders"] = yahoo_holders

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

    default_return_url = reverse("web:stocks_assessment")
    raw_return_url = (request.GET.get("return_url") or "").strip()
    return_url = None

    if raw_return_url:
        if url_has_allowed_host_and_scheme(
            raw_return_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            parts = urlsplit(raw_return_url)
            path = parts.path or "/"
            if not path.startswith("/"):
                path = f"/{path}"
            if ".." not in path.split("/"):
                sanitized = urlunsplit(("", "", path, parts.query, parts.fragment))
                return_url = iri_to_uri(sanitized)
        elif raw_return_url.startswith("/") and ".." not in raw_return_url.split("/"):
            return_url = iri_to_uri(raw_return_url)

    # Convert to list of dicts for template
    definitions_list = []
    for ratio_name, ratio_info in RATIO_DEFINITIONS.items():
        definitions_list.append(
            {
                "name": ratio_name,
                "term": ratio_info.get("Term", ""),
                "definition": ratio_info.get("Definition", ""),
                "formula": ratio_info.get("Formula", ""),
            }
        )

    return render(
        request,
        "web/financial_definitions.html",
        context={
            "active_tab": "investment_savings",
            "page_title": _("Financial Definitions"),
            "definitions": definitions_list,
            "return_url": return_url,
            "default_return_url": default_return_url,
        },
    )


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
