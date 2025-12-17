"""
Report Generation Service
Generates various financial reports
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from .models import (
    FinancialGoal,
    FinancialTransaction,
    InvestmentHolding,
    LinkedAccount,
)


class ReportGenerator:
    """Generate financial reports"""

    @staticmethod
    def generate_monthly_summary(user, year, month):
        """Generate monthly financial summary report"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Income
        income_transactions = FinancialTransaction.objects.filter(
            account__user=user, transaction_type="credit", date__gte=start_date, date__lte=end_date
        )
        total_income = income_transactions.aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

        # Expenses
        expense_transactions = FinancialTransaction.objects.filter(
            account__user=user, transaction_type="debit", date__gte=start_date, date__lte=end_date
        )
        total_expenses = abs(expense_transactions.aggregate(Sum("amount"))["amount__sum"] or Decimal("0"))

        # Expenses by category
        expenses_by_category = {}
        for transaction in expense_transactions:
            category = transaction.category or "Uncategorized"
            if category not in expenses_by_category:
                expenses_by_category[category] = Decimal("0")
            expenses_by_category[category] += abs(transaction.amount)

        # Net cash flow
        net_cash_flow = total_income - total_expenses

        # Account balances
        accounts = LinkedAccount.objects.filter(user=user, status="active")
        account_balances = {}
        for account in accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                account_balances[account.account_name] = {
                    "balance": str(latest_balance.current_balance),
                    "type": account.account_type,
                }

        # Top transactions
        top_expenses = expense_transactions.order_by("-amount")[:10]

        return {
            "period": {
                "year": year,
                "month": month,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "income": {
                "total": str(total_income),
                "transaction_count": income_transactions.count(),
            },
            "expenses": {
                "total": str(total_expenses),
                "transaction_count": expense_transactions.count(),
                "by_category": {k: str(v) for k, v in expenses_by_category.items()},
            },
            "cash_flow": {
                "net": str(net_cash_flow),
                "savings_rate": float((net_cash_flow / total_income * 100)) if total_income > 0 else 0,
            },
            "account_balances": account_balances,
            "top_expenses": [
                {
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "amount": str(t.amount),
                    "category": t.category,
                }
                for t in top_expenses
            ],
        }

    @staticmethod
    def generate_annual_summary(user, year):
        """Generate annual financial summary report"""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Monthly breakdown
        monthly_data = []
        for month in range(1, 13):
            monthly_summary = ReportGenerator.generate_monthly_summary(user, year, month)
            monthly_data.append(monthly_summary)

        # Annual totals
        all_transactions = FinancialTransaction.objects.filter(
            account__user=user, date__gte=start_date, date__lte=end_date
        )

        total_income = all_transactions.filter(transaction_type="credit").aggregate(Sum("amount"))[
            "amount__sum"
        ] or Decimal("0")
        total_expenses = abs(
            all_transactions.filter(transaction_type="debit").aggregate(Sum("amount"))["amount__sum"] or Decimal("0")
        )

        # Investment performance
        holdings = InvestmentHolding.objects.filter(account__user=user)
        total_investment_value = sum(h.value for h in holdings)

        return {
            "year": year,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "annual_totals": {
                "income": str(total_income),
                "expenses": str(total_expenses),
                "net": str(total_income - total_expenses),
            },
            "monthly_breakdown": monthly_data,
            "investments": {
                "total_value": str(total_investment_value),
                "holdings_count": holdings.count(),
            },
        }

    @staticmethod
    def generate_goals_progress_report(user):
        """Generate goals progress report"""
        goals = FinancialGoal.objects.filter(user=user, status="active")

        goals_data = []
        for goal in goals:
            goals_data.append(
                {
                    "name": goal.name,
                    "goal_type": goal.goal_type,
                    "target_amount": str(goal.target_amount),
                    "current_amount": str(goal.current_amount),
                    "progress_percentage": goal.progress_percentage,
                    "remaining_amount": str(goal.remaining_amount),
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "days_remaining": goal.days_remaining,
                    "monthly_contribution": str(goal.monthly_contribution),
                    "monthly_contribution_needed": str(goal.monthly_contribution_needed)
                    if goal.monthly_contribution_needed
                    else None,
                }
            )

        # Summary
        total_goals = goals.count()
        completed_goals = sum(1 for g in goals if g.progress_percentage >= 100)
        total_target = sum(g.target_amount for g in goals)
        total_current = sum(g.current_amount for g in goals)
        overall_progress = (total_current / total_target * 100) if total_target > 0 else 0

        return {
            "summary": {
                "total_goals": total_goals,
                "completed_goals": completed_goals,
                "active_goals": total_goals - completed_goals,
                "total_target": str(total_target),
                "total_current": str(total_current),
                "overall_progress": float(overall_progress),
            },
            "goals": goals_data,
        }

    @staticmethod
    def generate_investment_report(user):
        """Generate investment portfolio report"""
        investment_accounts = LinkedAccount.objects.filter(
            user=user, status="active", account_type__in=["investment", "brokerage", "retirement"]
        )

        holdings = InvestmentHolding.objects.filter(account__in=investment_accounts)

        # Portfolio summary
        total_value = sum(h.value for h in holdings)
        total_cost_basis = sum(h.cost_basis for h in holdings if h.cost_basis)
        total_gain_loss = total_value - total_cost_basis
        total_return_pct = ((total_gain_loss / total_cost_basis) * 100) if total_cost_basis > 0 else 0

        # Holdings by account
        holdings_by_account = {}
        for account in investment_accounts:
            account_holdings = holdings.filter(account=account)
            holdings_by_account[account.account_name] = {
                "holdings_count": account_holdings.count(),
                "total_value": str(sum(h.value for h in account_holdings)),
            }

        # Top holdings
        top_holdings = sorted(holdings, key=lambda h: h.value, reverse=True)[:10]

        return {
            "portfolio_summary": {
                "total_value": str(total_value),
                "total_cost_basis": str(total_cost_basis),
                "total_gain_loss": str(total_gain_loss),
                "total_return_percentage": float(total_return_pct),
                "holdings_count": holdings.count(),
                "accounts_count": investment_accounts.count(),
            },
            "holdings_by_account": holdings_by_account,
            "top_holdings": [
                {
                    "security_name": h.security_name,
                    "ticker": h.security_ticker,
                    "quantity": str(h.quantity),
                    "value": str(h.value),
                    "cost_basis": str(h.cost_basis) if h.cost_basis else None,
                }
                for h in top_holdings
            ],
        }
