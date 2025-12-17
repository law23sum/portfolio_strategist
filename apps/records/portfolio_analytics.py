"""
Portfolio Analytics Service
Provides comprehensive portfolio analysis and insights
"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import (
    InvestmentHolding,
    InvestmentTransaction,
    LinkedAccount,
)


class PortfolioAnalytics:
    """Portfolio analytics and insights"""

    @staticmethod
    def get_portfolio_summary(user):
        """Get overall portfolio summary"""
        investment_accounts = LinkedAccount.objects.filter(
            user=user, status="active", account_type__in=["investment", "brokerage", "retirement"]
        )

        total_value = Decimal("0")
        total_cost_basis = Decimal("0")
        holdings_count = 0
        accounts_count = investment_accounts.count()

        for account in investment_accounts:
            holdings = InvestmentHolding.objects.filter(account=account)
            for holding in holdings:
                total_value += holding.value
                if holding.cost_basis:
                    total_cost_basis += holding.cost_basis
                holdings_count += 1

        total_gain_loss = total_value - total_cost_basis
        total_return_pct = ((total_value - total_cost_basis) / total_cost_basis * 100) if total_cost_basis > 0 else 0

        # Get recent transactions
        recent_transactions = InvestmentTransaction.objects.filter(account__user=user).order_by("-date")[:10]

        return {
            "total_value": str(total_value),
            "total_cost_basis": str(total_cost_basis),
            "total_gain_loss": str(total_gain_loss),
            "total_return_percentage": float(total_return_pct),
            "holdings_count": holdings_count,
            "accounts_count": accounts_count,
            "recent_transactions": [
                {
                    "date": t.date.isoformat(),
                    "type": t.transaction_type,
                    "security": t.security_name,
                    "amount": str(t.amount),
                }
                for t in recent_transactions
            ],
        }

    @staticmethod
    def get_performance_metrics(user, start_date=None, end_date=None):
        """Get portfolio performance metrics"""
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get all investment transactions in period
        transactions = InvestmentTransaction.objects.filter(
            account__user=user, date__gte=start_date, date__lte=end_date
        )

        # Calculate returns
        buys = transactions.filter(transaction_type="buy")
        sells = transactions.filter(transaction_type="sell")
        dividends = transactions.filter(transaction_type="dividend")

        total_invested = sum(t.amount for t in buys)
        total_proceeds = sum(t.amount for t in sells)
        total_dividends = sum(t.amount for t in dividends)

        # Current holdings value
        current_holdings = InvestmentHolding.objects.filter(account__user=user)
        current_value = sum(h.value for h in current_holdings)

        # Calculate performance
        total_return = (current_value + total_proceeds + total_dividends) - total_invested
        return_percentage = (total_return / total_invested * 100) if total_invested > 0 else 0

        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = (
            ((1 + return_percentage / 100) ** (1 / years) - 1) * 100 if years > 0 and total_invested > 0 else 0
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
            "invested": str(total_invested),
            "current_value": str(current_value),
            "proceeds": str(total_proceeds),
            "dividends": str(total_dividends),
            "total_return": str(total_return),
            "return_percentage": float(return_percentage),
            "annualized_return": float(annualized_return),
        }

    @staticmethod
    def get_risk_metrics(user):
        """Get portfolio risk metrics"""
        holdings = InvestmentHolding.objects.filter(account__user=user)

        # Calculate concentration risk
        total_value = sum(h.value for h in holdings)
        if total_value == 0:
            return {"error": "No holdings found"}

        # Top holdings concentration
        sorted_holdings = sorted(holdings, key=lambda h: h.value, reverse=True)
        top_5_value = sum(h.value for h in sorted_holdings[:5])
        top_5_concentration = (top_5_value / total_value * 100) if total_value > 0 else 0

        # Sector/industry diversification (simplified - would need security details)
        unique_securities = holdings.values("security_ticker").distinct().count()
        diversification_score = min(100, (unique_securities / 20) * 100)  # Max at 20+ securities

        return {
            "total_holdings": holdings.count(),
            "unique_securities": unique_securities,
            "top_5_concentration": float(top_5_concentration),
            "diversification_score": float(diversification_score),
            "risk_level": "high" if top_5_concentration > 60 else "medium" if top_5_concentration > 40 else "low",
        }

    @staticmethod
    def get_asset_allocation(user):
        """Get asset allocation breakdown"""
        holdings = InvestmentHolding.objects.filter(account__user=user)

        total_value = sum(h.value for h in holdings)
        if total_value == 0:
            return {"error": "No holdings found"}

        # Group by account type
        allocation_by_account = {}
        for holding in holdings:
            account_type = holding.account.account_type
            if account_type not in allocation_by_account:
                allocation_by_account[account_type] = Decimal("0")
            allocation_by_account[account_type] += holding.value

        # Convert to percentages
        allocation = []
        for account_type, value in allocation_by_account.items():
            allocation.append(
                {"type": account_type, "value": str(value), "percentage": float((value / total_value) * 100)}
            )

        return {
            "total_value": str(total_value),
            "allocation": allocation,
        }

    @staticmethod
    def get_dividend_analysis(user):
        """Get dividend income analysis"""
        dividends = InvestmentTransaction.objects.filter(account__user=user, transaction_type="dividend")

        # Group by year
        dividends_by_year = {}
        for dividend in dividends:
            year = dividend.date.year
            if year not in dividends_by_year:
                dividends_by_year[year] = Decimal("0")
            dividends_by_year[year] += dividend.amount

        # Current year
        current_year = timezone.now().year
        current_year_dividends = dividends_by_year.get(current_year, Decimal("0"))

        # Projected annual (based on current year)
        months_elapsed = timezone.now().month
        projected_annual = (current_year_dividends / months_elapsed * 12) if months_elapsed > 0 else Decimal("0")

        return {
            "current_year": current_year,
            "current_year_dividends": str(current_year_dividends),
            "projected_annual": str(projected_annual),
            "by_year": {str(year): str(amount) for year, amount in dividends_by_year.items()},
        }
