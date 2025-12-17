"""
Tax Optimization Service
Calculates tax optimization strategies for users
"""

from datetime import date
from decimal import Decimal

from .models import (
    InvestmentHolding,
    InvestmentTransaction,
    TaxOptimizationStrategy,
)


def calculate_tax_optimization_strategies(user, tax_year):
    """Calculate tax optimization strategies for a user"""
    strategies = []

    # 1. Tax-Loss Harvesting
    tax_loss_strategy = calculate_tax_loss_harvesting(user, tax_year)
    if tax_loss_strategy:
        strategies.append(tax_loss_strategy)

    # 2. Capital Gains Optimization
    capital_gains_strategy = calculate_capital_gains_optimization(user, tax_year)
    if capital_gains_strategy:
        strategies.append(capital_gains_strategy)

    # 3. Dividend Tax Optimization
    dividend_strategy = calculate_dividend_optimization(user, tax_year)
    if dividend_strategy:
        strategies.append(dividend_strategy)

    # Save strategies
    for strategy_data in strategies:
        TaxOptimizationStrategy.objects.update_or_create(
            user=user,
            tax_year=tax_year,
            strategy_type=strategy_data["strategy_type"],
            defaults={
                "title": strategy_data["title"],
                "description": strategy_data["description"],
                "estimated_savings": strategy_data.get("estimated_savings"),
                "recommendations": strategy_data.get("recommendations", []),
                "applicable_securities": strategy_data.get("applicable_securities", []),
            },
        )

    return strategies


def calculate_tax_loss_harvesting(user, tax_year):
    """Calculate tax-loss harvesting opportunities"""
    # Get investment transactions for the year
    start_date = date(tax_year, 1, 1)
    end_date = date(tax_year, 12, 31)

    transactions = InvestmentTransaction.objects.filter(
        account__user=user, date__gte=start_date, date__lte=end_date, transaction_type__in=["buy", "sell"]
    )

    # Calculate realized gains/losses
    sells = transactions.filter(transaction_type="sell")
    total_losses = Decimal("0")
    loss_securities = []

    for sell in sells:
        # Find corresponding buy (simplified - would need proper cost basis tracking)
        buys = transactions.filter(security_ticker=sell.security_ticker, transaction_type="buy", date__lt=sell.date)

        if buys.exists():
            # Simplified: assume average cost basis
            avg_cost = sum(b.amount for b in buys) / buys.count()
            gain_loss = sell.amount - avg_cost

            if gain_loss < 0:  # Loss
                total_losses += abs(gain_loss)
                loss_securities.append(
                    {
                        "ticker": sell.security_ticker,
                        "loss": str(abs(gain_loss)),
                    }
                )

    # Check for unrealized losses (current holdings below cost basis)
    holdings = InvestmentHolding.objects.filter(account__user=user)
    unrealized_losses = Decimal("0")
    unrealized_loss_securities = []

    for holding in holdings:
        if holding.cost_basis and holding.value < holding.cost_basis:
            loss = holding.cost_basis - holding.value
            unrealized_losses += loss
            unrealized_loss_securities.append(
                {
                    "ticker": holding.security_ticker,
                    "unrealized_loss": str(loss),
                }
            )

    if total_losses > 0 or unrealized_losses > 0:
        # Estimate tax savings (assuming 20% capital gains tax rate)
        tax_rate = Decimal("0.20")
        estimated_savings = (total_losses + unrealized_losses) * tax_rate

        recommendations = []
        if unrealized_losses > 0:
            recommendations.append(
                f"Consider harvesting ${unrealized_losses:.2f} in unrealized losses by selling underperforming positions"
            )
        if total_losses > 0:
            recommendations.append(f"You have ${total_losses:.2f} in realized losses that can offset capital gains")

        return {
            "strategy_type": "tax_loss_harvesting",
            "title": "Tax-Loss Harvesting Opportunity",
            "description": "Potential tax savings through loss harvesting",
            "estimated_savings": estimated_savings,
            "recommendations": recommendations,
            "applicable_securities": loss_securities + unrealized_loss_securities,
        }

    return None


def calculate_capital_gains_optimization(user, tax_year):
    """Calculate capital gains optimization strategies"""
    # Get realized gains
    transactions = InvestmentTransaction.objects.filter(
        account__user=user, date__year=tax_year, transaction_type="sell"
    )

    total_gains = Decimal("0")
    long_term_gains = Decimal("0")
    short_term_gains = Decimal("0")

    for transaction in transactions:
        # Simplified: would need to check holding period
        # Assume gains are positive (would need cost basis calculation)
        if transaction.amount > 0:
            total_gains += transaction.amount
            # Simplified: assume 50/50 split
            long_term_gains += transaction.amount * Decimal("0.5")
            short_term_gains += transaction.amount * Decimal("0.5")

    if total_gains > 0:
        # Long-term gains are taxed at lower rates
        long_term_rate = Decimal("0.15")  # 15% for most taxpayers
        short_term_rate = Decimal("0.37")  # Ordinary income rate (top bracket)

        current_tax = (long_term_gains * long_term_rate) + (short_term_gains * short_term_rate)
        optimized_tax = total_gains * long_term_rate  # If all were long-term

        potential_savings = current_tax - optimized_tax

        recommendations = []
        if short_term_gains > 0:
            recommendations.append(
                "Consider holding positions for over 1 year to qualify for long-term capital gains rates"
            )
            recommendations.append(
                f"Potential savings: ${potential_savings:.2f} by converting short-term to long-term gains"
            )

        return {
            "strategy_type": "capital_gains_optimization",
            "title": "Capital Gains Tax Optimization",
            "description": "Optimize capital gains tax through holding period management",
            "estimated_savings": potential_savings if potential_savings > 0 else None,
            "recommendations": recommendations,
        }

    return None


def calculate_dividend_optimization(user, tax_year):
    """Calculate dividend tax optimization strategies"""
    dividends = InvestmentTransaction.objects.filter(
        account__user=user, date__year=tax_year, transaction_type="dividend"
    )

    total_dividends = sum(d.amount for d in dividends)

    if total_dividends > 0:
        # Qualified dividends are taxed at lower rates
        qualified_rate = Decimal("0.15")
        ordinary_rate = Decimal("0.37")

        # Simplified: assume 70% qualified
        qualified_dividends = total_dividends * Decimal("0.7")
        ordinary_dividends = total_dividends * Decimal("0.3")

        current_tax = (qualified_dividends * qualified_rate) + (ordinary_dividends * ordinary_rate)
        max_optimized_tax = total_dividends * qualified_rate  # If all were qualified

        potential_savings = current_tax - max_optimized_tax

        recommendations = []
        if ordinary_dividends > 0:
            recommendations.append("Focus on qualified dividend-paying stocks to reduce tax burden")
            recommendations.append(f"Potential savings: ${potential_savings:.2f} by maximizing qualified dividends")

        return {
            "strategy_type": "dividend_optimization",
            "title": "Dividend Tax Optimization",
            "description": "Optimize dividend income tax through qualified dividend strategies",
            "estimated_savings": potential_savings if potential_savings > 0 else None,
            "recommendations": recommendations,
        }

    return None
