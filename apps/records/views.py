import json
from datetime import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import FinancialDocumentForm
from .models import ExtractedField, FinancialDocument
from .plaid_data_distribution import PlaidDataDistributionService
from .services import build_document_library, get_document_metrics


def upload_view(request):
    year_choices = list(range(2000, 2101))
    year_choices.reverse()

    subcategory_options = {
        record_type: dict(options) for record_type, options in FinancialDocument.SUBCATEGORY_OPTIONS.items()
    }
    subcategory_options_json = json.dumps(subcategory_options)

    documents = FinancialDocument.objects.all().order_by("record_type", "sub_record_type", "year")

    preselected_record_type = request.GET.get("record_type", "")
    preselected_sub_record_type = request.GET.get("sub_record_type", "")

    if request.method == "POST":
        form = FinancialDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            # Auto-generate original_name from record_type, sub_record_type, and year
            record_type_label = dict(FinancialDocument.RECORD_TYPE_CHOICES).get(
                document.record_type, document.record_type
            )
            subcategory_options = FinancialDocument.SUBCATEGORY_OPTIONS.get(document.record_type, [])
            subcategory_dict = dict(subcategory_options)
            sub_record_type_label = subcategory_dict.get(document.sub_record_type, document.sub_record_type)
            # Concatenate: record_type_label_sub_record_type_label_year
            document.original_name = f"{record_type_label}_{sub_record_type_label}_{document.year}"
            document.save()

            # OCR field extraction (if needed)
            from .utils import extract_fields_from_document

            extracted_fields = extract_fields_from_document(document.document.path)
            for name, value in extracted_fields:
                ExtractedField.objects.create(document=document, field_name=name.strip(), field_value=value.strip())

            document.processed = True
            document.save(update_fields=["processed"])

            return redirect("records:upload")

    else:
        form = FinancialDocumentForm()

    # Organize documents for display
    organized_docs = {}
    for doc in documents:
        if doc.record_type not in organized_docs:
            organized_docs[doc.record_type] = {
                "label": dict(FinancialDocument.RECORD_TYPE_CHOICES).get(doc.record_type, doc.record_type),
                "subcategories": {},
            }

        if doc.sub_record_type not in organized_docs[doc.record_type]["subcategories"]:
            subcategory_label = subcategory_options.get(doc.record_type, {}).get(
                doc.sub_record_type, doc.sub_record_type
            )
            organized_docs[doc.record_type]["subcategories"][doc.sub_record_type] = {
                "label": subcategory_label,
                "documents": [],
            }

        organized_docs[doc.record_type]["subcategories"][doc.sub_record_type]["documents"].append(doc)

    return render(
        request,
        "records/upload.html",
        {
            "active_tab": "records_upload",
            "form": form,
            "organized_docs": organized_docs,
            "documents": documents,
            "year_choices": year_choices,
            "subcategory_options_json": subcategory_options_json,
            "record_type_choices": FinancialDocument.RECORD_TYPE_CHOICES,
            "preselected_record_type": preselected_record_type,
            "preselected_sub_record_type": preselected_sub_record_type,
        },
    )


def insights_view(request):
    metrics = get_document_metrics()
    charts_json = json.dumps(metrics["charts_payload"], cls=DjangoJSONEncoder)
    return render(
        request,
        "records/insights.html",
        {
            **metrics,
            "charts_json": charts_json,
            "active_tab": "records_insights",
        },
    )


def explorer_view(request):
    record_tree = build_document_library()
    metrics = get_document_metrics()
    return render(
        request,
        "records/explorer.html",
        {
            "record_tree": record_tree,
            "coverage_by_type": metrics["coverage_by_type"],
            "active_tab": "records_explorer",
        },
    )


def document_list_partial(request):
    documents = FinancialDocument.objects.all()
    return render(request, "records/partials/document_list.html", {"documents": documents})


@require_POST
def delete_document(request, pk):
    try:
        document = FinancialDocument.objects.get(pk=pk)
        document.delete()
        return redirect("records:upload")
    except FinancialDocument.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Document not found"}, status=404)


def personal_details(request, pk):
    document = FinancialDocument.objects.get(pk=pk)
    fields = document.fields.all()
    return render(
        request,
        "records/personal_sensitive_details.html",
        {
            "document": document,
            "fields": fields,
        },
    )


def personal_sensitive_view(request):
    documents = FinancialDocument.objects.filter(record_type="government").prefetch_related("fields")
    plaid_personal_data = (
        PlaidDataDistributionService.get_organized_plaid_data(request.user).get("personal_sensitive", {}) or {}
    )
    plaid_personal_json = json.dumps(plaid_personal_data)

    context = {
        "active_tab": "records_personal_sensitive",
        "documents": documents,
        "plaid_data": plaid_personal_json,
        "plaid_personal_defaults": plaid_personal_data,
    }
    return render(request, "records/personal_sensitive_information.html", context)


# New feature views
from decimal import Decimal  # noqa: E402

from django.contrib.auth.decorators import login_required  # noqa: E402

from .debt_calculator import DebtPayoffCalculator  # noqa: E402
from .models import DebtAccount, FinancialGoal, FinancialHealthScore, FinancialNotification  # noqa: E402
from .services import calculate_financial_health_score  # noqa: E402


@login_required
def financial_goals_view(request):
    """Financial Goals management page"""
    goals = FinancialGoal.objects.filter(user=request.user).order_by("-priority", "-created_at")
    status_filter = request.GET.get("status")
    if status_filter:
        goals = goals.filter(status=status_filter)

    return render(
        request,
        "records/financial_goals.html",
        {
            "active_tab": "financial_goals",
            "goals": goals,
            "status_filter": status_filter,
        },
    )


@login_required
def notifications_view(request):
    """Notifications center"""
    notifications = FinancialNotification.objects.filter(user=request.user).order_by("-created_at")
    unread_count = notifications.filter(read=False).count()

    return render(
        request,
        "records/notifications.html",
        {
            "active_tab": "notifications",
            "notifications": notifications[:50],  # Limit to 50 most recent
            "unread_count": unread_count,
        },
    )


@login_required
def financial_health_view(request):
    """Financial Health Score dashboard"""
    health_score = FinancialHealthScore.objects.filter(user=request.user).first()
    if not health_score:
        health_score = calculate_financial_health_score(request.user)

    return render(
        request,
        "records/financial_health.html",
        {
            "active_tab": "financial_health",
            "health_score": health_score,
        },
    )


@login_required
def debt_payoff_calculator_view(request):
    """Debt Payoff Calculator"""
    debts = DebtAccount.objects.filter(account__user=request.user)
    monthly_payment = Decimal(request.GET.get("monthly_payment", "0"))

    comparison = None
    if monthly_payment > 0 and debts.exists():
        comparison = DebtPayoffCalculator.compare_strategies(list(debts), monthly_payment)

    return render(
        request,
        "records/debt_payoff_calculator.html",
        {
            "active_tab": "debt_calculator",
            "debts": debts,
            "monthly_payment": monthly_payment,
            "comparison": comparison,
        },
    )


@login_required
def budget_planner_view(request):
    """Budget Planner with Budget vs Actual"""
    from .models import BudgetCategory, BudgetPlan

    plans = BudgetPlan.objects.filter(user=request.user, is_active=True).order_by("-start_date")
    categories = BudgetCategory.objects.filter(user=request.user, is_active=True)

    # Get current month's plan if exists
    from django.utils import timezone

    current_date = timezone.now().date()
    current_month_plan = plans.filter(start_date__lte=current_date, end_date__gte=current_date).first()

    category_lookup = {category.name: category for category in categories}

    plan_summary = None
    category_breakdown = []
    if current_month_plan:
        total_budget = float(current_month_plan.total_budget or 0)
        actual_spending = float(current_month_plan.actual_spending or 0)
        variance = total_budget - actual_spending
        utilization_percent = 0.0
        if total_budget > 0:
            utilization_percent = min(100.0, (actual_spending / total_budget) * 100)

        plan_summary = {
            "name": current_month_plan.name,
            "period_label": current_month_plan.get_period_display(),
            "start_date": current_month_plan.start_date,
            "end_date": current_month_plan.end_date,
            "total_budget": total_budget,
            "actual_spending": actual_spending,
            "variance": variance,
            "utilization_percent": round(utilization_percent, 1),
            "plan_notes": current_month_plan.notes,
        }

        category_budgets = current_month_plan.category_budgets or {}
        actual_by_category = current_month_plan.actual_by_category or {}
        for name, budget_value in category_budgets.items():
            budget_value = float(budget_value or 0)
            actual_value = float(actual_by_category.get(name, 0) or 0)
            variance_value = budget_value - actual_value
            utilization = 0.0
            if budget_value > 0:
                utilization = max(0.0, min(100.0, (actual_value / budget_value) * 100))

            category_obj = category_lookup.get(name)
            category_breakdown.append(
                {
                    "name": category_obj.name if category_obj else name,
                    "budget": budget_value,
                    "actual": actual_value,
                    "variance": variance_value,
                    "utilization": round(utilization, 1),
                    "notes": category_obj.description if category_obj and category_obj.description else "",
                }
            )

        category_breakdown.sort(key=lambda item: item["utilization"], reverse=True)

    plan_history = []
    for plan in plans:
        total_budget = float(plan.total_budget or 0)
        actual_spending = float(plan.actual_spending or 0)
        variance = total_budget - actual_spending
        plan_history.append(
            {
                "id": plan.id,
                "name": plan.name,
                "period_label": plan.get_period_display(),
                "start_date": plan.start_date,
                "end_date": plan.end_date,
                "total_budget": total_budget,
                "actual_spending": actual_spending,
                "variance": variance,
                "is_active": plan.is_active,
            }
        )

    return render(
        request,
        "records/budget_planner.html",
        {
            "active_tab": "budget_planner_records",
            "plans": plans,
            "plan_history": plan_history,
            "categories": categories,
            "current_plan": current_month_plan,
            "plan_summary": plan_summary,
            "category_breakdown": category_breakdown,
        },
    )


@login_required
def portfolio_comparison_view(request):
    """Portfolio Comparison Tool"""
    from django.db.models import Sum

    from .models import InvestmentHolding, PortfolioComparison

    comparisons = PortfolioComparison.objects.filter(user=request.user).order_by("-created_at")

    # Get user's current portfolio summary
    holdings = InvestmentHolding.objects.filter(account__user=request.user).select_related("account")
    portfolio_summary = (
        holdings.values("security_ticker")
        .annotate(total_value=Sum("value"), total_quantity=Sum("quantity"))
        .order_by("-total_value")
    )

    return render(
        request,
        "records/portfolio_comparison.html",
        {
            "active_tab": "portfolio_comparison",
            "comparisons": comparisons,
            "portfolio_summary": portfolio_summary,
        },
    )


@login_required
def financial_calendar_view(request):
    """Financial Calendar and Reminders"""
    from datetime import timedelta

    from django.utils import timezone

    from .models import Bill, FinancialCalendarEvent

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date:
        start_date = timezone.now().date()
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if not end_date:
        end_date = start_date + timedelta(days=90)
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    events = FinancialCalendarEvent.objects.filter(
        user=request.user, event_date__gte=start_date, event_date__lte=end_date
    ).order_by("event_date")

    bills = Bill.objects.filter(user=request.user, is_active=True).order_by("next_due_date")

    return render(
        request,
        "records/financial_calendar.html",
        {
            "active_tab": "financial_calendar",
            "events": events,
            "bills": bills,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@login_required
def tax_optimization_view(request):
    """Tax Optimization Dashboard"""
    from django.utils import timezone

    from .models import TaxOptimizationStrategy

    current_year = timezone.now().year
    tax_year = int(request.GET.get("tax_year", current_year))

    strategies = TaxOptimizationStrategy.objects.filter(user=request.user, tax_year=tax_year).order_by(
        "-estimated_savings"
    )

    total_potential_savings = sum(float(s.estimated_savings) for s in strategies if s.estimated_savings)
    tax_year_options = list(range(current_year + 2, current_year - 3, -1))

    return render(
        request,
        "records/tax_optimization.html",
        {
            "active_tab": "tax_optimization_records",
            "strategies": strategies,
            "tax_year": tax_year,
            "total_potential_savings": total_potential_savings,
            "tax_year_options": tax_year_options,
        },
    )


@login_required
def retirement_planning_view(request):
    """Retirement Planning Calculator"""
    from .models import RetirementPlan

    plans = RetirementPlan.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "records/retirement_planning.html",
        {
            "active_tab": "retirement_planning",
            "plans": plans,
        },
    )


@login_required
def transaction_search_view(request):
    """Advanced Transaction Search"""
    from .models import LinkedAccount

    accounts = LinkedAccount.objects.filter(user=request.user, status="active")

    return render(
        request,
        "records/transaction_search.html",
        {
            "active_tab": "transaction_search",
            "accounts": accounts,
        },
    )
