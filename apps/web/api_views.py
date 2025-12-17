"""
API views for Investment & Savings assessments
"""

import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.records.models import BondAssessment, CDAssessment, LinkedAccount, SavingsAssessment, StocksAssessment
from apps.stock_analysis.models import StockWatchlistEntry


@login_required
@require_http_methods(["POST"])
def save_stocks_assessment(request):
    """Save stocks assessment"""
    try:
        data = json.loads(request.body)

        symbol = data.get("symbol", "").upper().strip()
        if not symbol:
            return JsonResponse({"error": "Stock symbol is required"}, status=400)

        linked_account_id = data.get("linked_account_id")
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(id=linked_account_id, user=request.user).first()

        assessment, created = StocksAssessment.objects.update_or_create(
            user=request.user,
            symbol=symbol,
            defaults={
                "linked_account": linked_account,
                "investment_amount": Decimal(str(data.get("investment_amount", 0)))
                if data.get("investment_amount")
                else None,
                "share_quantity": Decimal(str(data.get("share_quantity", 0))) if data.get("share_quantity") else None,
                "current_price": Decimal(str(data.get("current_price", 0))),
                "forecast_data": data.get("forecast_data", {}),
                "notes": data.get("notes", ""),
            },
        )

        return JsonResponse(
            {
                "success": True,
                "created": created,
                "id": assessment.id,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_savings_assessment(request):
    """Save savings assessment"""
    try:
        data = json.loads(request.body)

        linked_account_id = data.get("linked_account_id")
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(id=linked_account_id, user=request.user).first()

        account_name = data.get("account_name", "Savings Account")
        assessment_id = data.get("id")

        if assessment_id:
            try:
                assessment = SavingsAssessment.objects.get(id=assessment_id, user=request.user)
                created = False
            except SavingsAssessment.DoesNotExist:
                assessment = SavingsAssessment(user=request.user)
                created = True
        else:
            assessment = SavingsAssessment(user=request.user)
            created = True

        assessment.linked_account = linked_account
        assessment.account_name = account_name
        assessment.initial_deposit = Decimal(str(data.get("initial_deposit", 0)))
        assessment.annual_interest_rate = Decimal(str(data.get("annual_interest_rate", 0)))
        # Handle both biweekly and monthly contributions
        biweekly_contrib = data.get("biweekly_contribution")
        if biweekly_contrib is not None:
            assessment.monthly_contribution = (
                Decimal(str(biweekly_contrib)) * Decimal("26") / Decimal("12")
            )  # Convert biweekly to monthly
        else:
            assessment.monthly_contribution = Decimal(str(data.get("monthly_contribution", 0)))
        assessment.compounding_frequency = int(data.get("compounding_frequency", 12))
        forecast_data = data.get("forecast_data", {})
        # Store biweekly contribution in forecast_data for reference
        if biweekly_contrib is not None:
            forecast_data["biweekly_contribution"] = float(biweekly_contrib)
        assessment.forecast_data = forecast_data
        assessment.notes = data.get("notes", "")
        assessment.save()

        return JsonResponse(
            {
                "success": True,
                "created": created,
                "id": assessment.id,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_cd_assessment(request):
    """Save CD assessment"""
    try:
        data = json.loads(request.body)

        linked_account_id = data.get("linked_account_id")
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(id=linked_account_id, user=request.user).first()

        assessment_id = data.get("id")
        if assessment_id:
            try:
                assessment = CDAssessment.objects.get(id=assessment_id, user=request.user)
                created = False
            except CDAssessment.DoesNotExist:
                assessment = CDAssessment(user=request.user)
                created = True
        else:
            assessment = CDAssessment(user=request.user)
            created = True

        assessment.linked_account = linked_account
        assessment.account_name = data.get("account_name", "CD Account")
        assessment.amount = Decimal(str(data.get("amount", 0)))
        assessment.annual_interest_rate = Decimal(str(data.get("annual_interest_rate", 0)))
        assessment.term_months = int(data.get("term_months", 36))  # Default to 36 months (3 years)
        assessment.compounding_frequency = int(data.get("compounding_frequency", 12))
        forecast_data = data.get("forecast_data", {})
        # Store biweekly contribution in forecast_data for reference
        biweekly_contrib = data.get("biweekly_contribution")
        if biweekly_contrib is not None:
            forecast_data["biweekly_contribution"] = float(biweekly_contrib)
        assessment.forecast_data = forecast_data
        assessment.notes = data.get("notes", "")
        assessment.save()

        return JsonResponse(
            {
                "success": True,
                "created": created,
                "id": assessment.id,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_bond_assessment(request):
    """Save bond assessment"""
    try:
        data = json.loads(request.body)

        linked_account_id = data.get("linked_account_id")
        linked_account = None
        if linked_account_id:
            linked_account = LinkedAccount.objects.filter(id=linked_account_id, user=request.user).first()

        assessment_id = data.get("id")
        if assessment_id:
            try:
                assessment = BondAssessment.objects.get(id=assessment_id, user=request.user)
                created = False
            except BondAssessment.DoesNotExist:
                assessment = BondAssessment(user=request.user)
                created = True
        else:
            assessment = BondAssessment(user=request.user)
            created = True

        assessment.linked_account = linked_account
        assessment.account_name = data.get("account_name", "Bond Investment")
        assessment.face_value = Decimal(str(data.get("face_value", 0)))
        assessment.coupon_rate = Decimal(str(data.get("coupon_rate", 0)))
        assessment.purchase_price = Decimal(str(data.get("purchase_price", 0)))
        assessment.years_to_maturity = Decimal(str(data.get("years_to_maturity", 0)))
        assessment.payment_frequency = int(data.get("payment_frequency", 2))
        forecast_data = data.get("forecast_data", {})
        # Store biweekly contribution in forecast_data for reference
        biweekly_contrib = data.get("biweekly_contribution")
        if biweekly_contrib is not None:
            forecast_data["biweekly_contribution"] = float(biweekly_contrib)
        assessment.forecast_data = forecast_data
        assessment.notes = data.get("notes", "")
        assessment.save()

        return JsonResponse(
            {
                "success": True,
                "created": created,
                "id": assessment.id,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_watchlist(request):
    """Get user's watchlist entries with latest news and links"""
    try:
        entries = StockWatchlistEntry.objects.filter(user=request.user).select_related("snapshot").order_by("symbol")
        entries_data = []
        for entry in entries:
            entry_data = {
                "id": entry.id,
                "symbol": entry.symbol,
                "nickname": entry.nickname,
                "notes": entry.notes,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "last_refreshed": entry.last_refreshed.isoformat() if entry.last_refreshed else None,
                "latest_news": [],
            }
            if entry.snapshot:
                entry_data["snapshot"] = {
                    "current_price": float(entry.snapshot.current_price) if entry.snapshot.current_price else None,
                    "change_percent": float(entry.snapshot.change_percent) if entry.snapshot.change_percent else None,
                    "payload": entry.snapshot.payload,
                }
                # Include latest news items with links
                if entry.snapshot.news_items:
                    # Get latest 5 news items
                    latest_news = entry.snapshot.news_items[:5]
                    entry_data["latest_news"] = [
                        {
                            "title": item.get("title", ""),
                            "link": item.get("link") or item.get("url", ""),
                            "publisher": item.get("publisher", "Yahoo Finance"),
                            "summary": item.get("summary", ""),
                            "published": item.get("published", ""),
                        }
                        for item in latest_news
                        if item.get("title") and (item.get("link") or item.get("url"))
                    ]
            entries_data.append(entry_data)

        return JsonResponse(
            {
                "success": True,
                "entries": entries_data,
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def watchlist_add_api(request):
    """Add symbol to watchlist"""
    try:
        data = json.loads(request.body)
        symbol = data.get("symbol", "").upper().strip()
        nickname = data.get("nickname", "").strip()
        notes = data.get("notes", "").strip()

        if not symbol:
            return JsonResponse({"error": "Stock symbol is required"}, status=400)

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

        # Try to queue refresh
        try:
            from apps.stock_analysis.tasks import refresh_watchlist_symbol

            refresh_watchlist_symbol.delay(symbol)
        except Exception:
            pass  # Celery might not be running

        return JsonResponse(
            {
                "success": True,
                "created": created,
                "id": entry.id,
                "symbol": entry.symbol,
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def watchlist_remove_api(request, entry_id: int):
    """Remove symbol from watchlist"""
    try:
        entry = StockWatchlistEntry.objects.get(id=entry_id, user=request.user)
        symbol = entry.symbol
        entry.delete()

        return JsonResponse(
            {
                "success": True,
                "message": f"Removed {symbol} from watchlist",
            }
        )
    except StockWatchlistEntry.DoesNotExist:
        return JsonResponse({"error": "Watchlist entry not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_watchlist_news(request):
    """Get latest news for all watchlist stocks with links"""
    try:
        entries = StockWatchlistEntry.objects.filter(user=request.user).select_related("snapshot").order_by("symbol")
        all_news = []

        for entry in entries:
            if entry.snapshot and entry.snapshot.news_items:
                for news_item in entry.snapshot.news_items:
                    link = news_item.get("link") or news_item.get("url", "")
                    if link and news_item.get("title"):
                        all_news.append(
                            {
                                "symbol": entry.symbol,
                                "nickname": entry.nickname,
                                "title": news_item.get("title", ""),
                                "link": link,
                                "publisher": news_item.get("publisher", "Yahoo Finance"),
                                "summary": news_item.get("summary", ""),
                                "published": news_item.get("published", ""),
                                "fetched_at": entry.snapshot.fetched_at.isoformat()
                                if entry.snapshot.fetched_at
                                else None,
                            }
                        )

        # Sort by fetched_at (most recent first)
        all_news.sort(key=lambda x: x.get("fetched_at") or "", reverse=True)

        return JsonResponse(
            {
                "success": True,
                "news": all_news[:50],  # Limit to 50 most recent items
                "total": len(all_news),
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def watchlist_refresh_api(request, entry_id: int):
    """Refresh watchlist symbol"""
    try:
        entry = StockWatchlistEntry.objects.get(id=entry_id, user=request.user)
        try:
            from apps.stock_analysis.tasks import refresh_watchlist_symbol

            refresh_watchlist_symbol.delay(entry.symbol)
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Queued refresh for {entry.symbol}",
                }
            )
        except Exception as exc:
            return JsonResponse({"error": f"Unable to queue refresh: {exc}"}, status=500)
    except StockWatchlistEntry.DoesNotExist:
        return JsonResponse({"error": "Watchlist entry not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
