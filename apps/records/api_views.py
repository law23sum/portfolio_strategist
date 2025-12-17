import csv
from datetime import datetime
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Bill,
    BudgetPlan,
    DebtAccount,
    FinancialCalendarEvent,
    FinancialGoal,
    FinancialHealthScore,
    FinancialNotification,
    FinancialTransaction,
    InvestmentHolding,
    LinkedAccount,
    PortfolioComparison,
    RecurringTransaction,
    RetirementPlan,
    TaxOptimizationStrategy,
)

# Import services
from .notification_service import NotificationGenerator
from .portfolio_analytics import PortfolioAnalytics
from .recurring_detector import RecurringTransactionDetector
from .retirement_calculator import calculate_retirement_projections
from .serializers import ReceiptSerializer
from .services import calculate_financial_health_score
from .tax_optimization import calculate_tax_optimization_strategies


class ReceiptUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data["user"] = request.user.id  # Associate receipt with the logged-in user
        serializer = ReceiptSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# Financial Goals API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def financial_goals_api(request):
    """List or create financial goals"""
    if request.method == "GET":
        goals = FinancialGoal.objects.filter(user=request.user)
        status_filter = request.GET.get("status")
        if status_filter:
            goals = goals.filter(status=status_filter)

        goals_data = []
        for goal in goals:
            goals_data.append(
                {
                    "id": goal.id,
                    "name": goal.name,
                    "goal_type": goal.goal_type,
                    "target_amount": str(goal.target_amount),
                    "current_amount": str(goal.current_amount),
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "status": goal.status,
                    "monthly_contribution": str(goal.monthly_contribution),
                    "progress_percentage": goal.progress_percentage,
                    "remaining_amount": str(goal.remaining_amount),
                    "days_remaining": goal.days_remaining,
                    "monthly_contribution_needed": str(goal.monthly_contribution_needed)
                    if goal.monthly_contribution_needed
                    else None,
                    "priority": goal.priority,
                    "description": goal.description,
                    "created_at": goal.created_at.isoformat(),
                    "updated_at": goal.updated_at.isoformat(),
                }
            )
        return Response(goals_data)

    elif request.method == "POST":
        data = request.data
        goal = FinancialGoal.objects.create(
            user=request.user,
            name=data.get("name"),
            goal_type=data.get("goal_type", "savings"),
            target_amount=Decimal(str(data.get("target_amount", 0))),
            current_amount=Decimal(str(data.get("current_amount", 0))),
            target_date=datetime.strptime(data["target_date"], "%Y-%m-%d").date() if data.get("target_date") else None,
            monthly_contribution=Decimal(str(data.get("monthly_contribution", 0))),
            description=data.get("description", ""),
            priority=int(data.get("priority", 5)),
        )
        return Response({"id": goal.id, "message": "Goal created successfully"}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def financial_goal_detail_api(request, goal_id):
    """Get, update, or delete a specific financial goal"""
    try:
        goal = FinancialGoal.objects.get(id=goal_id, user=request.user)
    except FinancialGoal.DoesNotExist:
        return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(
            {
                "id": goal.id,
                "name": goal.name,
                "goal_type": goal.goal_type,
                "target_amount": str(goal.target_amount),
                "current_amount": str(goal.current_amount),
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "status": goal.status,
                "monthly_contribution": str(goal.monthly_contribution),
                "progress_percentage": goal.progress_percentage,
                "remaining_amount": str(goal.remaining_amount),
                "days_remaining": goal.days_remaining,
                "monthly_contribution_needed": str(goal.monthly_contribution_needed)
                if goal.monthly_contribution_needed
                else None,
                "priority": goal.priority,
                "description": goal.description,
                "notes": goal.notes,
                "created_at": goal.created_at.isoformat(),
                "updated_at": goal.updated_at.isoformat(),
            }
        )

    elif request.method == "PUT":
        data = request.data
        if "name" in data:
            goal.name = data["name"]
        if "target_amount" in data:
            goal.target_amount = Decimal(str(data["target_amount"]))
        if "current_amount" in data:
            goal.current_amount = Decimal(str(data["current_amount"]))
        if "target_date" in data:
            goal.target_date = (
                datetime.strptime(data["target_date"], "%Y-%m-%d").date() if data["target_date"] else None
            )
        if "status" in data:
            goal.status = data["status"]
        if "monthly_contribution" in data:
            goal.monthly_contribution = Decimal(str(data["monthly_contribution"]))
        if "description" in data:
            goal.description = data["description"]
        if "priority" in data:
            goal.priority = int(data["priority"])
        goal.save()
        return Response({"message": "Goal updated successfully"})

    elif request.method == "DELETE":
        goal.delete()
        return Response({"message": "Goal deleted successfully"})


# Notifications API


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications_api(request):
    """Get user's financial notifications"""
    notifications = FinancialNotification.objects.filter(user=request.user)
    unread_only = request.GET.get("unread_only", "false").lower() == "true"
    if unread_only:
        notifications = notifications.filter(read=False)

    limit = request.GET.get("limit")
    if limit:
        notifications = notifications[: int(limit)]

    notifications_data = []
    for notification in notifications:
        notifications_data.append(
            {
                "id": notification.id,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority,
                "read": notification.read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "action_url": notification.action_url,
                "action_label": notification.action_label,
                "created_at": notification.created_at.isoformat(),
            }
        )
    return Response(notifications_data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read_api(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = FinancialNotification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return Response({"message": "Notification marked as read"})
    except FinancialNotification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read_api(request):
    """Mark all notifications as read"""
    FinancialNotification.objects.filter(user=request.user, read=False).update(read=True, read_at=timezone.now())
    return Response({"message": "All notifications marked as read"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_notifications_api(request):
    """Manually trigger notification generation"""
    notifications = NotificationGenerator.generate_all_notifications(request.user)
    return Response({"generated_count": len(notifications), "message": f"Generated {len(notifications)} notifications"})


# Financial Health Score API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def financial_health_score_api(request):
    """Get or calculate financial health score"""
    if request.method == "GET":
        # Get latest score
        score = FinancialHealthScore.objects.filter(user=request.user).first()
        if not score:
            # Calculate if doesn't exist
            score = calculate_financial_health_score(request.user)

        return Response(
            {
                "overall_score": score.overall_score,
                "savings_score": score.savings_score,
                "debt_score": score.debt_score,
                "investment_score": score.investment_score,
                "budget_score": score.budget_score,
                "emergency_fund_score": score.emergency_fund_score,
                "credit_score_health": score.credit_score_health,
                "metrics": score.metrics,
                "recommendations": score.recommendations,
                "calculated_at": score.calculated_at.isoformat(),
            }
        )

    elif request.method == "POST":
        # Force recalculation
        score = calculate_financial_health_score(request.user)
        return Response(
            {
                "overall_score": score.overall_score,
                "savings_score": score.savings_score,
                "debt_score": score.debt_score,
                "investment_score": score.investment_score,
                "budget_score": score.budget_score,
                "emergency_fund_score": score.emergency_fund_score,
                "credit_score_health": score.credit_score_health,
                "metrics": score.metrics,
                "recommendations": score.recommendations,
                "calculated_at": score.calculated_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


# Export API


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_transactions_api(request):
    """Export transactions to CSV"""
    format_type = request.GET.get("format", "csv")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    account_id = request.GET.get("account_id")

    transactions = FinancialTransaction.objects.filter(account__user=request.user)

    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)
    if account_id:
        transactions = transactions.filter(account_id=account_id)

    if format_type == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="transactions_{datetime.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(["Date", "Account", "Description", "Category", "Amount", "Type", "Merchant", "Pending"])

        for transaction in transactions.select_related("account"):
            writer.writerow(
                [
                    transaction.date.isoformat(),
                    transaction.account.account_name,
                    transaction.description,
                    transaction.category,
                    str(transaction.amount),
                    transaction.transaction_type,
                    transaction.merchant_name,
                    "Yes" if transaction.pending else "No",
                ]
            )

        return response

    elif format_type == "json":
        transactions_data = []
        for transaction in transactions.select_related("account"):
            transactions_data.append(
                {
                    "date": transaction.date.isoformat(),
                    "account": transaction.account.account_name,
                    "description": transaction.description,
                    "category": transaction.category,
                    "amount": str(transaction.amount),
                    "type": transaction.transaction_type,
                    "merchant": transaction.merchant_name,
                    "pending": transaction.pending,
                }
            )
        return JsonResponse({"transactions": transactions_data}, json_dumps_params={"indent": 2})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_portfolio_api(request):
    """Export portfolio data to CSV or JSON"""
    format_type = request.GET.get("format", "csv")

    # Get all investment holdings
    holdings = InvestmentHolding.objects.filter(account__user=request.user).select_related("account")

    if format_type == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="portfolio_{datetime.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ["Account", "Security Name", "Ticker", "Quantity", "Price", "Value", "Cost Basis", "As of Date"]
        )

        for holding in holdings:
            writer.writerow(
                [
                    holding.account.account_name,
                    holding.security_name,
                    holding.security_ticker,
                    str(holding.quantity),
                    str(holding.price) if holding.price else "",
                    str(holding.value),
                    str(holding.cost_basis) if holding.cost_basis else "",
                    holding.as_of_date.isoformat(),
                ]
            )

        return response

    elif format_type == "json":
        holdings_data = []
        for holding in holdings:
            holdings_data.append(
                {
                    "account": holding.account.account_name,
                    "security_name": holding.security_name,
                    "ticker": holding.security_ticker,
                    "quantity": str(holding.quantity),
                    "price": str(holding.price) if holding.price else None,
                    "value": str(holding.value),
                    "cost_basis": str(holding.cost_basis) if holding.cost_basis else None,
                    "as_of_date": holding.as_of_date.isoformat(),
                }
            )
        return JsonResponse({"holdings": holdings_data}, json_dumps_params={"indent": 2})


# Recurring Transactions API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def recurring_transactions_api(request):
    """Get or detect recurring transactions"""
    if request.method == "GET":
        recurring = RecurringTransaction.objects.filter(user=request.user, is_active=True)

        recurring_data = []
        for rt in recurring.select_related("account"):
            recurring_data.append(
                {
                    "id": rt.id,
                    "description": rt.description,
                    "amount": str(rt.amount),
                    "category": rt.category,
                    "merchant_name": rt.merchant_name,
                    "frequency": rt.frequency,
                    "next_occurrence": rt.next_occurrence.isoformat(),
                    "last_occurrence": rt.last_occurrence.isoformat() if rt.last_occurrence else None,
                    "is_detected": rt.is_detected,
                    "confidence_score": str(rt.confidence_score) if rt.confidence_score else None,
                    "account": rt.account.account_name,
                }
            )
        return Response(recurring_data)

    elif request.method == "POST":
        # Trigger detection
        account_id = request.data.get("account_id")
        account = None
        if account_id:
            try:
                account = LinkedAccount.objects.get(id=account_id, user=request.user)
            except LinkedAccount.DoesNotExist:
                return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        min_confidence = int(request.data.get("min_confidence", 60))
        detected = RecurringTransactionDetector.detect_recurring_transactions(request.user, account, min_confidence)

        return Response(
            {
                "detected_count": len(detected),
                "recurring_transactions": [
                    {
                        "id": rt.id,
                        "description": rt.description,
                        "amount": str(rt.amount),
                        "frequency": rt.frequency,
                        "confidence_score": str(rt.confidence_score),
                    }
                    for rt in detected
                ],
            },
            status=status.HTTP_201_CREATED,
        )


# Debt Payoff Calculator API


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def debt_payoff_calculator_api(request):
    """Calculate debt payoff strategies"""
    from decimal import Decimal

    from .debt_calculator import DebtPayoffCalculator

    monthly_payment = Decimal(str(request.data.get("monthly_payment", 0)))
    debts = DebtAccount.objects.filter(account__user=request.user)

    if not debts.exists():
        return Response({"error": "No debts found"}, status=status.HTTP_400_BAD_REQUEST)

    if monthly_payment <= 0:
        return Response({"error": "Monthly payment must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

    comparison = DebtPayoffCalculator.compare_strategies(list(debts), monthly_payment)
    return Response(comparison)


# Budget vs Actual API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def budget_plans_api(request):
    """List or create budget plans"""
    if request.method == "GET":
        plans = BudgetPlan.objects.filter(user=request.user, is_active=True)
        plans_data = []
        for plan in plans:
            plans_data.append(
                {
                    "id": plan.id,
                    "name": plan.name,
                    "period": plan.period,
                    "start_date": plan.start_date.isoformat(),
                    "end_date": plan.end_date.isoformat(),
                    "total_budget": str(plan.total_budget),
                    "actual_spending": str(plan.actual_spending),
                    "variance": str(plan.variance),
                    "variance_percentage": plan.variance_percentage,
                    "category_budgets": plan.category_budgets,
                    "actual_by_category": plan.actual_by_category,
                }
            )
        return Response(plans_data)

    elif request.method == "POST":
        data = request.data
        plan = BudgetPlan.objects.create(
            user=request.user,
            name=data.get("name"),
            period=data.get("period", "monthly"),
            start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date(),
            total_budget=Decimal(str(data.get("total_budget", 0))),
            category_budgets=data.get("category_budgets", {}),
        )
        return Response({"id": plan.id, "message": "Budget plan created"}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def budget_vs_actual_api(request, plan_id):
    """Get budget vs actual comparison for a plan"""
    try:
        plan = BudgetPlan.objects.get(id=plan_id, user=request.user)
    except BudgetPlan.DoesNotExist:
        return Response({"error": "Budget plan not found"}, status=status.HTTP_404_NOT_FOUND)

    # Calculate actual spending from transactions
    transactions = FinancialTransaction.objects.filter(
        account__user=request.user, date__gte=plan.start_date, date__lte=plan.end_date, transaction_type="debit"
    )

    actual_by_category = {}
    total_actual = Decimal("0")

    for transaction in transactions:
        category = transaction.category or "Uncategorized"
        if category not in actual_by_category:
            actual_by_category[category] = Decimal("0")
        actual_by_category[category] += transaction.amount
        total_actual += transaction.amount

    # Update plan
    plan.actual_spending = total_actual
    plan.actual_by_category = {k: str(v) for k, v in actual_by_category.items()}
    plan.save()

    # Build comparison
    comparison = {
        "plan_id": plan.id,
        "plan_name": plan.name,
        "period": f"{plan.start_date} to {plan.end_date}",
        "total_budget": str(plan.total_budget),
        "total_actual": str(total_actual),
        "variance": str(plan.variance),
        "variance_percentage": plan.variance_percentage,
        "by_category": [],
    }

    # Compare by category
    all_categories = set(list(plan.category_budgets.keys()) + list(actual_by_category.keys()))
    for category in all_categories:
        budgeted = Decimal(str(plan.category_budgets.get(category, 0)))
        actual = actual_by_category.get(category, Decimal("0"))
        variance = actual - budgeted
        variance_pct = (variance / budgeted * 100) if budgeted > 0 else 0

        comparison["by_category"].append(
            {
                "category": category,
                "budgeted": str(budgeted),
                "actual": str(actual),
                "variance": str(variance),
                "variance_percentage": float(variance_pct),
            }
        )

    return Response(comparison)


# Advanced Transaction Search API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def advanced_transaction_search_api(request):
    """Advanced transaction search with multiple criteria"""
    if request.method == "POST":
        filters = request.data.get("filters", {})
    else:
        filters = request.GET

    # Build query
    transactions = FinancialTransaction.objects.filter(account__user=request.user)

    # Date range
    if filters.get("start_date"):
        transactions = transactions.filter(date__gte=filters["start_date"])
    if filters.get("end_date"):
        transactions = transactions.filter(date__lte=filters["end_date"])

    # Amount range
    if filters.get("min_amount"):
        transactions = transactions.filter(amount__gte=Decimal(str(filters["min_amount"])))
    if filters.get("max_amount"):
        transactions = transactions.filter(amount__lte=Decimal(str(filters["max_amount"])))

    # Category
    if filters.get("category"):
        transactions = transactions.filter(category__icontains=filters["category"])

    # Merchant
    if filters.get("merchant"):
        transactions = transactions.filter(merchant_name__icontains=filters["merchant"])

    # Description search
    if filters.get("description"):
        transactions = transactions.filter(description__icontains=filters["description"])

    # Transaction type
    if filters.get("transaction_type"):
        transactions = transactions.filter(transaction_type=filters["transaction_type"])

    # Account filter
    if filters.get("account_id"):
        transactions = transactions.filter(account_id=filters["account_id"])

    # Pending filter
    if filters.get("pending") is not None:
        transactions = transactions.filter(pending=filters["pending"] == "true")

    # Ordering
    order_by = filters.get("order_by", "-date")
    transactions = transactions.order_by(order_by)

    # Pagination
    page = int(filters.get("page", 1))
    page_size = int(filters.get("page_size", 50))
    start = (page - 1) * page_size
    end = start + page_size

    total_count = transactions.count()
    transactions = transactions.select_related("account")[start:end]

    results = []
    for transaction in transactions:
        results.append(
            {
                "id": transaction.id,
                "date": transaction.date.isoformat(),
                "account": transaction.account.account_name,
                "description": transaction.description,
                "amount": str(transaction.amount),
                "category": transaction.category,
                "merchant_name": transaction.merchant_name,
                "transaction_type": transaction.transaction_type,
                "pending": transaction.pending,
            }
        )

    return Response(
        {
            "results": results,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
        }
    )


# Portfolio Comparison API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def portfolio_comparison_api(request):
    """Create or list portfolio comparisons"""
    if request.method == "GET":
        comparisons = PortfolioComparison.objects.filter(user=request.user)
        comparisons_data = []
        for comp in comparisons:
            comparisons_data.append(
                {
                    "id": comp.id,
                    "name": comp.name,
                    "comparison_type": comp.comparison_type,
                    "compared_items": comp.compared_items,
                    "start_date": comp.start_date.isoformat() if comp.start_date else None,
                    "end_date": comp.end_date.isoformat() if comp.end_date else None,
                    "created_at": comp.created_at.isoformat(),
                }
            )
        return Response(comparisons_data)

    elif request.method == "POST":
        data = request.data
        comparison = PortfolioComparison.objects.create(
            user=request.user,
            name=data.get("name"),
            comparison_type=data.get("comparison_type", "stocks"),
            compared_items=data.get("compared_items", []),
            start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date() if data.get("start_date") else None,
            end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date() if data.get("end_date") else None,
        )

        # Perform comparison with actual stock data
        from apps.stock_analysis.services import StockAnalysisService

        comparison_data = {
            "items": comparison.compared_items,
            "comparison_date": timezone.now().isoformat(),
            "data": {},
        }

        service = StockAnalysisService()
        for item in comparison.compared_items:
            symbol = item.get("symbol") or item.get("ticker")
            if symbol:
                try:
                    stock_data = service.stock_app.fetch_stock_data(symbol.upper())
                    if stock_data:
                        comparison_data["data"][symbol] = {
                            "current_price": stock_data.get("currentPrice"),
                            "market_cap": stock_data.get("marketCap"),
                            "pe_ratio": stock_data.get("PE Ratio (TTM)"),
                            "dividend_yield": stock_data.get("Forward Annual Dividend Yield 4"),
                            "beta": stock_data.get("beta"),
                        }
                except Exception as e:
                    comparison_data["data"][symbol] = {"error": str(e)}

        comparison.comparison_data = comparison_data
        comparison.save()

        return Response(
            {"id": comparison.id, "comparison_data": comparison_data, "message": "Comparison created"},
            status=status.HTTP_201_CREATED,
        )


# Bill Management API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def bills_api(request):
    """List or create bills"""
    if request.method == "GET":
        bills = Bill.objects.filter(user=request.user, is_active=True)
        bills_data = []
        for bill in bills:
            bills_data.append(
                {
                    "id": bill.id,
                    "name": bill.name,
                    "amount": str(bill.amount),
                    "frequency": bill.frequency,
                    "next_due_date": bill.next_due_date.isoformat(),
                    "last_paid_date": bill.last_paid_date.isoformat() if bill.last_paid_date else None,
                    "is_autopay": bill.is_autopay,
                    "category": bill.category,
                    "merchant_name": bill.merchant_name,
                }
            )
        return Response(bills_data)

    elif request.method == "POST":
        data = request.data
        bill = Bill.objects.create(
            user=request.user,
            name=data.get("name"),
            amount=Decimal(str(data.get("amount", 0))),
            frequency=data.get("frequency", "monthly"),
            due_day=int(data.get("due_day", 1)),
            next_due_date=datetime.strptime(data["next_due_date"], "%Y-%m-%d").date()
            if data.get("next_due_date")
            else timezone.now().date(),
            category=data.get("category", ""),
            merchant_name=data.get("merchant_name", ""),
            is_autopay=data.get("is_autopay", False),
        )
        if data.get("account_id"):
            try:
                bill.account = LinkedAccount.objects.get(id=data["account_id"], user=request.user)
                bill.save()
            except LinkedAccount.DoesNotExist:
                pass

        return Response({"id": bill.id, "message": "Bill created"}, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def bill_detail_api(request, bill_id):
    """Update or delete a bill"""
    try:
        bill = Bill.objects.get(id=bill_id, user=request.user)
    except Bill.DoesNotExist:
        return Response({"error": "Bill not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        data = request.data
        if "name" in data:
            bill.name = data["name"]
        if "amount" in data:
            bill.amount = Decimal(str(data["amount"]))
        if "frequency" in data:
            bill.frequency = data["frequency"]
        if "next_due_date" in data:
            bill.next_due_date = datetime.strptime(data["next_due_date"], "%Y-%m-%d").date()
        if "is_active" in data:
            bill.is_active = data["is_active"]
        if "is_autopay" in data:
            bill.is_autopay = data["is_autopay"]
        bill.save()
        return Response({"message": "Bill updated"})

    elif request.method == "DELETE":
        bill.delete()
        return Response({"message": "Bill deleted"})


# Financial Calendar API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def financial_calendar_api(request):
    """Get or create financial calendar events"""
    if request.method == "GET":
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        events = FinancialCalendarEvent.objects.filter(user=request.user)
        if start_date:
            events = events.filter(event_date__gte=start_date)
        if end_date:
            events = events.filter(event_date__lte=end_date)

        events_data = []
        for event in events:
            events_data.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "event_type": event.event_type,
                    "description": event.description,
                    "event_date": event.event_date.isoformat(),
                    "reminder_date": event.reminder_date.isoformat() if event.reminder_date else None,
                    "is_recurring": event.is_recurring,
                    "is_completed": event.is_completed,
                    "amount": str(event.amount) if event.amount else None,
                }
            )
        return Response(events_data)

    elif request.method == "POST":
        data = request.data
        event = FinancialCalendarEvent.objects.create(
            user=request.user,
            title=data.get("title"),
            event_type=data.get("event_type", "custom"),
            description=data.get("description", ""),
            event_date=datetime.strptime(data["event_date"], "%Y-%m-%d").date(),
            reminder_date=datetime.strptime(data["reminder_date"], "%Y-%m-%d").date()
            if data.get("reminder_date")
            else None,
            is_recurring=data.get("is_recurring", False),
            amount=Decimal(str(data["amount"])) if data.get("amount") else None,
        )
        return Response({"id": event.id, "message": "Event created"}, status=status.HTTP_201_CREATED)


# Tax Optimization API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tax_optimization_api(request):
    """Get tax optimization strategies"""
    if request.method == "GET":
        tax_year = request.GET.get("tax_year", timezone.now().year)
        strategies = TaxOptimizationStrategy.objects.filter(user=request.user, tax_year=tax_year)

        strategies_data = []
        for strategy in strategies:
            strategies_data.append(
                {
                    "id": strategy.id,
                    "strategy_type": strategy.strategy_type,
                    "title": strategy.title,
                    "description": strategy.description,
                    "estimated_savings": str(strategy.estimated_savings) if strategy.estimated_savings else None,
                    "recommendations": strategy.recommendations,
                    "is_applied": strategy.is_applied,
                }
            )
        return Response(strategies_data)

    elif request.method == "POST":
        # Calculate tax optimization strategies
        tax_year = int(request.data.get("tax_year", timezone.now().year))
        strategies = calculate_tax_optimization_strategies(request.user, tax_year)

        return Response({"strategies": strategies}, status=status.HTTP_201_CREATED)


# Retirement Planning API


@api_view(["GET", "POST", "PUT"])
@permission_classes([IsAuthenticated])
def retirement_planning_api(request, plan_id=None):
    """Get, create, or update retirement plans"""
    if request.method == "GET":
        if plan_id:
            try:
                plan = RetirementPlan.objects.get(id=plan_id, user=request.user)
            except RetirementPlan.DoesNotExist:
                return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response(
                {
                    "id": plan.id,
                    "plan_name": plan.plan_name,
                    "current_age": plan.current_age,
                    "retirement_age": plan.retirement_age,
                    "current_savings": str(plan.current_savings),
                    "desired_retirement_income": str(plan.desired_retirement_income),
                    "monthly_contribution": str(plan.monthly_contribution),
                    "projections": plan.projections,
                    "scenarios": plan.scenarios,
                    "analysis": plan.analysis,
                }
            )
        else:
            plans = RetirementPlan.objects.filter(user=request.user)
            plans_data = []
            for plan in plans:
                plans_data.append(
                    {
                        "id": plan.id,
                        "plan_name": plan.plan_name,
                        "retirement_age": plan.retirement_age,
                        "current_savings": str(plan.current_savings),
                    }
                )
            return Response(plans_data)

    elif request.method == "POST":
        data = request.data
        plan = RetirementPlan.objects.create(
            user=request.user,
            plan_name=data.get("plan_name", "Retirement Plan"),
            current_age=int(data.get("current_age", 30)),
            retirement_age=int(data.get("retirement_age", 65)),
            current_savings=Decimal(str(data.get("current_savings", 0))),
            current_annual_income=Decimal(str(data.get("current_annual_income", 0))),
            desired_retirement_income=Decimal(str(data.get("desired_retirement_income", 0))),
            monthly_contribution=Decimal(str(data.get("monthly_contribution", 0))),
            expected_return_rate=Decimal(str(data.get("expected_return_rate", 7.0))),
        )

        # Calculate projections
        projections = calculate_retirement_projections(plan)
        plan.projections = projections
        plan.save()

        return Response({"id": plan.id, "projections": projections}, status=status.HTTP_201_CREATED)

    elif request.method == "PUT" and plan_id:
        try:
            plan = RetirementPlan.objects.get(id=plan_id, user=request.user)
        except RetirementPlan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if "monthly_contribution" in data:
            plan.monthly_contribution = Decimal(str(data["monthly_contribution"]))
        if "desired_retirement_income" in data:
            plan.desired_retirement_income = Decimal(str(data["desired_retirement_income"]))

        # Recalculate
        projections = calculate_retirement_projections(plan)
        plan.projections = projections
        plan.save()

        return Response({"id": plan.id, "projections": projections})


# Portfolio Analytics API


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_analytics_api(request):
    """Get comprehensive portfolio analytics"""
    analytics_type = request.GET.get("type", "summary")

    if analytics_type == "summary":
        summary = PortfolioAnalytics.get_portfolio_summary(request.user)
        return Response(summary)

    elif analytics_type == "performance":
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        metrics = PortfolioAnalytics.get_performance_metrics(request.user, start, end)
        return Response(metrics)

    elif analytics_type == "risk":
        metrics = PortfolioAnalytics.get_risk_metrics(request.user)
        return Response(metrics)

    elif analytics_type == "allocation":
        allocation = PortfolioAnalytics.get_asset_allocation(request.user)
        return Response(allocation)

    elif analytics_type == "dividends":
        dividends = PortfolioAnalytics.get_dividend_analysis(request.user)
        return Response(dividends)

    else:
        return Response({"error": "Invalid analytics type"}, status=status.HTTP_400_BAD_REQUEST)


# Report Generation API


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def generate_report_api(request):
    """Generate financial reports"""
    from .report_generator import ReportGenerator

    report_type = request.GET.get("type", "monthly")
    year = int(request.GET.get("year", timezone.now().year))
    month = int(request.GET.get("month", timezone.now().month)) if request.GET.get("month") else None

    if report_type == "monthly":
        if not month:
            month = timezone.now().month
        report = ReportGenerator.generate_monthly_summary(request.user, year, month)
    elif report_type == "annual":
        report = ReportGenerator.generate_annual_summary(request.user, year)
    elif report_type == "goals":
        report = ReportGenerator.generate_goals_progress_report(request.user)
    elif report_type == "investment":
        report = ReportGenerator.generate_investment_report(request.user)
    else:
        return Response({"error": "Invalid report type"}, status=status.HTTP_400_BAD_REQUEST)

    return Response(report)


# Dark Mode API


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def dark_mode_api(request):
    """Get or update dark mode preference"""
    from .dark_mode import get_user_preference, set_theme, toggle_dark_mode

    if request.method == "GET":
        preference = get_user_preference(request.user)
        return Response(
            {
                "dark_mode_enabled": preference.dark_mode_enabled,
                "theme": preference.theme,
            }
        )

    elif request.method == "POST":
        action = request.data.get("action", "toggle")

        if action == "toggle":
            enabled = toggle_dark_mode(request.user)
            return Response({"dark_mode_enabled": enabled, "message": "Dark mode toggled"})

        elif action == "set":
            theme = request.data.get("theme", "auto")
            preference = set_theme(request.user, theme)
            return Response(
                {
                    "dark_mode_enabled": preference.dark_mode_enabled,
                    "theme": preference.theme,
                    "message": "Theme updated",
                }
            )

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
