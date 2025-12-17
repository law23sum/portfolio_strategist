"""Helper utilities for financial record insights and navigation."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from django.db.models import Count, Q, Sum

from .models import (
    DebtAccount,
    ExtractedField,
    FinancialDocument,
    FinancialTransaction,
    InvestmentHolding,
    LinkedAccount,
)

RecordTree = List[Dict[str, object]]


def _record_type_labels() -> Dict[str, str]:
    return dict(FinancialDocument.RECORD_TYPE_CHOICES)


def _subcategory_labels() -> Dict[str, Dict[str, str]]:
    return {key: dict(options) for key, options in FinancialDocument.SUBCATEGORY_OPTIONS.items()}


def get_document_metrics() -> Dict[str, object]:
    """Aggregate counts and helper data for dashboards."""

    # Use fresh querysets for each operation to avoid aggregate conflicts
    totals_raw = FinancialDocument.objects.aggregate(
        total=Count("id"),
        processed_count=Count("id", filter=Q(processed=True)),
        pending_count=Count("id", filter=Q(processed=False)),
    )
    totals = {
        "total": totals_raw.get("total", 0) or 0,
        "processed": totals_raw.get("processed_count", 0) or 0,
        "pending": totals_raw.get("pending_count", 0) or 0,
    }

    type_labels = _record_type_labels()
    subcategory_labels = _subcategory_labels()

    documents_by_type = [
        {
            "record_type": row["record_type"],
            "label": type_labels.get(row["record_type"], row["record_type"].replace("_", " ").title()),
            "count": row["count"],
        }
        for row in FinancialDocument.objects.values("record_type").annotate(count=Count("id")).order_by("-count")
    ]

    documents_by_year = list(FinancialDocument.objects.values("year").annotate(count=Count("id")).order_by("year"))

    coverage_by_type = []
    for record_type, label in FinancialDocument.RECORD_TYPE_CHOICES:
        subchoices = subcategory_labels.get(record_type, {})
        total_subs = len(subchoices)
        filled = FinancialDocument.objects.filter(record_type=record_type).values("sub_record_type").distinct().count()
        coverage_by_type.append(
            {
                "record_type": record_type,
                "label": label,
                "covered": filled,
                "total": total_subs,
                "percent": round(filled / total_subs * 100, 1) if total_subs else 0,
            }
        )

    coverage_by_type.sort(key=lambda item: item["percent"], reverse=True)

    subcategory_leaders = []
    subcategory_counts = (
        FinancialDocument.objects.values("record_type", "sub_record_type")
        .annotate(count=Count("id"))
        .order_by("-count")[:12]
    )
    for row in subcategory_counts:
        subcategory_leaders.append(
            {
                "record_type": row["record_type"],
                "record_label": type_labels.get(row["record_type"], row["record_type"].title()),
                "sub_record_type": row["sub_record_type"],
                "sub_label": subcategory_labels.get(row["record_type"], {}).get(
                    row["sub_record_type"], row["sub_record_type"].replace("_", " ").title()
                ),
                "count": row["count"],
            }
        )

    extracted_field_leaders = list(
        ExtractedField.objects.values("field_name").annotate(count=Count("id")).order_by("-count")[:8]
    )

    charts_payload = {
        "hasData": totals["total"] > 0,
        "byType": {
            "labels": [row["label"] for row in documents_by_type],
            "data": [row["count"] for row in documents_by_type],
        },
        "byYear": {
            "labels": [row["year"] for row in documents_by_year],
            "data": [row["count"] for row in documents_by_year],
        },
        "processing": {
            "labels": ["Processed", "Pending"],
            "data": [totals["processed"], totals["pending"]],
        },
    }

    # Include aggregated account data
    linked_accounts_count = LinkedAccount.objects.count()
    # Get latest balance for each active account and sum them
    active_accounts = LinkedAccount.objects.filter(status="active")
    total_account_balance = sum(
        account.balances.first().current_balance for account in active_accounts if account.balances.first()
    )

    return {
        "totals": totals,
        "documents_by_type": documents_by_type,
        "documents_by_year": documents_by_year,
        "coverage_by_type": coverage_by_type,
        "subcategory_leaders": subcategory_leaders,
        "recent_documents": FinancialDocument.objects.select_related("user").order_by("-uploaded_at")[:8],
        "extracted_field_leaders": extracted_field_leaders,
        "charts_payload": charts_payload,
        "linked_accounts_count": linked_accounts_count,
        "total_account_balance": total_account_balance,
    }


def build_document_library() -> RecordTree:
    """Return a record/subcategory tree with attached documents."""

    subcategory_labels = _subcategory_labels()
    grouped: Dict[str, Dict[str, List[FinancialDocument]]] = defaultdict(lambda: defaultdict(list))

    for doc in (
        FinancialDocument.objects.all()
        .select_related("user")
        .order_by("record_type", "sub_record_type", "-uploaded_at")
    ):
        grouped[doc.record_type][doc.sub_record_type].append(doc)

    record_tree: RecordTree = []
    for record_type, label in FinancialDocument.RECORD_TYPE_CHOICES:
        subentries = []
        total_docs = 0
        type_group = grouped.get(record_type, {})
        for subvalue, sublabel in subcategory_labels.get(record_type, {}).items():
            documents = type_group.get(subvalue, [])
            total_docs += len(documents)
            subentries.append(
                {
                    "value": subvalue,
                    "label": sublabel,
                    "documents": documents,
                    "count": len(documents),
                    "latest_year": documents[0].year if documents else None,
                }
            )
        covered = sum(1 for entry in subentries if entry["count"])
        record_tree.append(
            {
                "record_type": record_type,
                "label": label,
                "documents_count": total_docs,
                "covered_subcategories": covered,
                "total_subcategories": len(subentries),
                "subcategories": subentries,
            }
        )

    return record_tree


def calculate_financial_health_score(user):
    """Calculate comprehensive financial health score for a user"""
    from datetime import timedelta
    from decimal import Decimal

    from django.utils import timezone

    from .models import (
        FinancialGoal,
        FinancialHealthScore,
        InvestmentHolding,
        LinkedAccount,
    )

    # Initialize scores
    savings_score = 0
    debt_score = 0
    investment_score = 0
    budget_score = 0
    emergency_fund_score = 0
    credit_score_health = 50  # Default neutral

    metrics = {}
    recommendations = []

    # 1. Savings Score (0-100)
    # Check emergency fund adequacy (3-6 months expenses)
    active_accounts = LinkedAccount.objects.filter(user=user, status="active", account_type="depository")
    total_savings = Decimal("0")
    for account in active_accounts:
        latest_balance = account.balances.first()
        if latest_balance:
            total_savings += latest_balance.current_balance

    # Estimate monthly expenses from recent transactions
    recent_transactions = FinancialTransaction.objects.filter(
        account__user=user, transaction_type="debit", date__gte=timezone.now().date() - timedelta(days=90)
    )
    monthly_expenses = abs(recent_transactions.aggregate(Sum("amount"))["amount__sum"] or Decimal("0")) / 3

    if monthly_expenses > 0:
        months_of_expenses = total_savings / monthly_expenses
        if months_of_expenses >= 6:
            emergency_fund_score = 100
        elif months_of_expenses >= 3:
            emergency_fund_score = 75
        elif months_of_expenses >= 1:
            emergency_fund_score = 50
        else:
            emergency_fund_score = 25
    else:
        emergency_fund_score = 50  # Neutral if no expense data

    # Savings rate (savings / income)
    income_transactions = FinancialTransaction.objects.filter(
        account__user=user, transaction_type="credit", date__gte=timezone.now().date() - timedelta(days=90)
    )
    monthly_income = income_transactions.aggregate(Sum("amount"))["amount__sum"] or Decimal("0") / 3

    if monthly_income > 0:
        savings_rate = (total_savings / (monthly_income * 12)) * 100 if monthly_income > 0 else 0
        if savings_rate >= 20:
            savings_score = 100
        elif savings_rate >= 10:
            savings_score = 75
        elif savings_rate >= 5:
            savings_score = 50
        else:
            savings_score = 25
    else:
        savings_score = 50

    metrics["total_savings"] = str(total_savings)
    metrics["monthly_expenses"] = str(monthly_expenses)
    metrics["months_of_expenses"] = str(months_of_expenses) if monthly_expenses > 0 else "N/A"
    metrics["monthly_income"] = str(monthly_income)
    metrics["savings_rate"] = str(savings_rate) if monthly_income > 0 else "N/A"

    # 2. Debt Score (0-100)
    debt_accounts = DebtAccount.objects.filter(account__user=user)
    total_debt = sum(account.current_balance for account in debt_accounts)
    total_credit_limit = sum(account.credit_limit for account in debt_accounts if account.credit_limit)

    if total_credit_limit > 0:
        credit_utilization = (total_debt / total_credit_limit) * 100
        if credit_utilization <= 30:
            debt_score = 100
        elif credit_utilization <= 50:
            debt_score = 75
        elif credit_utilization <= 70:
            debt_score = 50
        else:
            debt_score = 25
    else:
        debt_score = 75 if total_debt == 0 else 50

    # Debt-to-income ratio
    if monthly_income > 0:
        debt_to_income = (total_debt / (monthly_income * 12)) * 100
        if debt_to_income <= 36:
            debt_score = max(debt_score, 80)
        elif debt_to_income <= 43:
            debt_score = max(debt_score, 60)
        else:
            debt_score = max(debt_score, 30)

    metrics["total_debt"] = str(total_debt)
    metrics["credit_utilization"] = str(credit_utilization) if total_credit_limit > 0 else "N/A"
    metrics["debt_to_income"] = str(debt_to_income) if monthly_income > 0 else "N/A"

    # 3. Investment Score (0-100)
    investment_accounts = LinkedAccount.objects.filter(
        user=user, status="active", account_type__in=["investment", "brokerage", "retirement"]
    )
    total_investments = Decimal("0")
    for account in investment_accounts:
        holdings = InvestmentHolding.objects.filter(account=account)
        total_investments += sum(holding.value for holding in holdings)

    # Check if user has investments
    unique_securities = 0
    if total_investments > 0:
        # Diversification check (simplified)
        unique_securities = (
            InvestmentHolding.objects.filter(account__user=user).values("security_ticker").distinct().count()
        )
        if unique_securities >= 10:
            investment_score = 100
        elif unique_securities >= 5:
            investment_score = 75
        elif unique_securities >= 3:
            investment_score = 50
        else:
            investment_score = 25
    else:
        investment_score = 0

    metrics["total_investments"] = str(total_investments)
    metrics["unique_securities"] = str(unique_securities)

    # 4. Budget Score (0-100) - Simplified
    # Check if spending is consistent
    monthly_spending = {}
    for transaction in recent_transactions:
        month_key = transaction.date.strftime("%Y-%m")
        if month_key not in monthly_spending:
            monthly_spending[month_key] = Decimal("0")
        monthly_spending[month_key] += abs(transaction.amount)

    if len(monthly_spending) >= 2:
        spending_values = list(monthly_spending.values())
        avg_spending = sum(spending_values) / len(spending_values)
        spending_variance = sum((s - avg_spending) ** 2 for s in spending_values) / len(spending_values)
        cv = (spending_variance**0.5) / avg_spending if avg_spending > 0 else 1

        if cv <= 0.2:
            budget_score = 100
        elif cv <= 0.4:
            budget_score = 75
        elif cv <= 0.6:
            budget_score = 50
        else:
            budget_score = 25
    else:
        budget_score = 50

    metrics["monthly_spending_variance"] = str(cv) if len(monthly_spending) >= 2 else "N/A"

    # 5. Goals Progress
    active_goals = FinancialGoal.objects.filter(user=user, status="active")
    if active_goals.exists():
        avg_progress = sum(goal.progress_percentage for goal in active_goals) / active_goals.count()
        if avg_progress >= 75:
            savings_score = max(savings_score, 90)
        elif avg_progress >= 50:
            savings_score = max(savings_score, 70)

    # Generate recommendations
    if emergency_fund_score < 50:
        recommendations.append(
            {
                "priority": "high",
                "category": "Emergency Fund",
                "message": f"Build emergency fund to cover {6 - (months_of_expenses if monthly_expenses > 0 else 0):.1f} more months of expenses",
            }
        )

    if debt_score < 50:
        recommendations.append(
            {
                "priority": "high",
                "category": "Debt Management",
                "message": "Reduce debt and improve credit utilization ratio",
            }
        )

    if investment_score < 50:
        recommendations.append(
            {
                "priority": "medium",
                "category": "Investments",
                "message": "Consider diversifying your investment portfolio",
            }
        )

    if savings_rate < 10 and monthly_income > 0:
        recommendations.append(
            {
                "priority": "medium",
                "category": "Savings",
                "message": "Aim to save at least 10-20% of your income",
            }
        )

    # Calculate overall score (weighted average)
    overall_score = int(
        (savings_score * 0.2)
        + (debt_score * 0.25)
        + (investment_score * 0.2)
        + (budget_score * 0.15)
        + (emergency_fund_score * 0.15)
        + (credit_score_health * 0.05)
    )

    # Create or update health score
    health_score, created = FinancialHealthScore.objects.update_or_create(
        user=user,
        defaults={
            "overall_score": overall_score,
            "savings_score": savings_score,
            "debt_score": debt_score,
            "investment_score": investment_score,
            "budget_score": budget_score,
            "emergency_fund_score": emergency_fund_score,
            "credit_score_health": credit_score_health,
            "metrics": metrics,
            "recommendations": recommendations,
            "calculated_at": timezone.now(),
        },
    )

    return health_score


def calculate_tax_optimization_strategies(user, tax_year):
    """Calculate tax optimization strategies for a user"""
    from datetime import timedelta
    from decimal import Decimal

    from django.utils import timezone

    from .models import InvestmentTransaction, TaxOptimizationStrategy

    strategies = []

    # Get investment holdings and transactions
    holdings = InvestmentHolding.objects.filter(account__user=user)
    transactions = InvestmentTransaction.objects.filter(account__user=user, date__year=tax_year)

    # 1. Tax Loss Harvesting
    # Find positions with losses
    loss_positions = []
    for holding in holdings:
        if holding.cost_basis and holding.price:
            cost_basis = holding.cost_basis
            current_value = holding.value
            if current_value < cost_basis:
                loss = cost_basis - current_value
                loss_positions.append(
                    {
                        "security": holding.security_name,
                        "ticker": holding.security_ticker,
                        "loss": float(loss),
                    }
                )

    if loss_positions:
        total_losses = sum(p["loss"] for p in loss_positions)
        strategies.append(
            {
                "strategy_type": "tax_loss_harvesting",
                "title": "Tax Loss Harvesting Opportunity",
                "description": f"You have {len(loss_positions)} positions with unrealized losses totaling ${total_losses:,.2f}. Consider selling these to offset capital gains.",
                "estimated_savings": total_losses * 0.15,  # Assume 15% tax rate
                "recommendations": [
                    f"Consider selling {p['security']} to realize ${p['loss']:,.2f} loss" for p in loss_positions[:5]
                ],
                "applicable_securities": loss_positions,
            }
        )

    # 2. Capital Gains Optimization
    # Check for short-term vs long-term gains
    short_term_gains = transactions.filter(
        transaction_type="sell", date__gte=timezone.now().date() - timedelta(days=365)
    ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

    if short_term_gains > 0:
        strategies.append(
            {
                "strategy_type": "capital_gains_optimization",
                "title": "Hold for Long-Term Capital Gains",
                "description": f"You have ${short_term_gains:,.2f} in short-term gains. Consider holding positions for over 1 year to qualify for lower long-term capital gains rates.",
                "estimated_savings": float(short_term_gains) * 0.10,  # 10% difference between short and long term
                "recommendations": [
                    "Hold profitable positions for at least 1 year before selling",
                    "Consider tax-loss harvesting to offset short-term gains",
                ],
            }
        )

    # Save strategies
    for strategy_data in strategies:
        TaxOptimizationStrategy.objects.update_or_create(
            user=user,
            tax_year=tax_year,
            strategy_type=strategy_data["strategy_type"],
            defaults={
                "title": strategy_data["title"],
                "description": strategy_data["description"],
                "estimated_savings": Decimal(str(strategy_data.get("estimated_savings", 0))),
                "recommendations": strategy_data.get("recommendations", []),
                "applicable_securities": strategy_data.get("applicable_securities", []),
            },
        )

    return strategies


def calculate_retirement_projections(plan):
    """Calculate retirement projections for a plan"""

    current_age = plan.current_age
    retirement_age = plan.retirement_age
    years_to_retirement = retirement_age - current_age

    current_savings = float(plan.current_savings)
    monthly_contribution = float(plan.monthly_contribution)
    annual_return = float(plan.expected_return_rate) / 100
    monthly_return = annual_return / 12

    # Calculate future value with contributions
    projections = []
    balance = current_savings

    for year in range(years_to_retirement + 1):
        age = current_age + year

        # Calculate balance at end of year
        # FV = PV * (1 + r)^n + PMT * [((1 + r)^n - 1) / r]
        months_in_year = 12
        future_value_factor = (1 + monthly_return) ** months_in_year
        balance = balance * future_value_factor + monthly_contribution * ((future_value_factor - 1) / monthly_return)

        # Calculate employer match if applicable
        employer_match = 0
        if plan.employer_match_percent > 0:
            annual_contribution = monthly_contribution * 12
            employer_match = float(annual_contribution * plan.employer_match_percent / 100)
            if plan.employer_match_limit:
                employer_match = min(employer_match, float(plan.employer_match_limit))
            balance += employer_match * future_value_factor

        # Calculate retirement income needed (adjusted for inflation)
        if year == years_to_retirement:
            inflation_factor = (1 + float(plan.inflation_rate) / 100) ** year
            needed_income = float(plan.desired_retirement_income) * inflation_factor
            # 4% rule: need 25x annual expenses
            needed_savings = needed_income * 25
        else:
            needed_income = None
            needed_savings = None

        projections.append(
            {
                "age": age,
                "year": year,
                "balance": round(balance, 2),
                "contributions": round(monthly_contribution * 12, 2),
                "employer_match": round(employer_match, 2),
                "needed_income": round(needed_income, 2) if needed_income else None,
                "needed_savings": round(needed_savings, 2) if needed_savings else None,
                "on_track": balance >= needed_savings if needed_savings else None,
            }
        )

    # Analysis
    final_balance = projections[-1]["balance"]
    needed_savings = projections[-1]["needed_savings"]

    analysis = {
        "final_balance": final_balance,
        "needed_savings": needed_savings,
        "shortfall": max(0, needed_savings - final_balance) if needed_savings else 0,
        "on_track": final_balance >= needed_savings if needed_savings else True,
        "recommendations": [],
    }

    if needed_savings and final_balance < needed_savings:
        shortfall = needed_savings - final_balance
        # Calculate additional monthly contribution needed
        # Using reverse calculation
        additional_monthly = (
            shortfall / (years_to_retirement * 12) / ((1 + monthly_return) ** (years_to_retirement * 12))
        )
        analysis["recommendations"].append(
            f"Increase monthly contribution by ${additional_monthly:,.2f} to meet retirement goal"
        )

    return {
        "projections": projections,
        "analysis": analysis,
    }
