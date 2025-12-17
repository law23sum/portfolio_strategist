"""
Debt Payoff Calculator
Implements debt payoff strategies: Snowball and Avalanche methods
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List


class DebtPayoffCalculator:
    """Calculate and compare debt payoff strategies"""

    @classmethod
    def compare_strategies(cls, debts: List, monthly_payment: Decimal) -> Dict[str, Any]:
        """
        Compare different debt payoff strategies

        Args:
            debts: List of DebtAccount instances
            monthly_payment: Total monthly payment available for debt payoff

        Returns:
            Dictionary containing comparison of strategies
        """
        if not debts or monthly_payment <= 0:
            return {"error": "Invalid input: debts list cannot be empty and monthly payment must be greater than 0"}

        # Convert to list with required fields, defaulting missing values
        debt_list = []
        for debt in debts:
            debt_list.append(
                {
                    "id": debt.id,
                    "name": getattr(debt.account, "name", "Unknown Account"),
                    "balance": debt.current_balance or Decimal("0"),
                    "interest_rate": (debt.interest_rate or Decimal("0")) / 100,  # Convert to decimal
                    "minimum_payment": debt.minimum_payment or Decimal("0"),
                    "debt_type": getattr(debt, "debt_type", "other"),
                }
            )

        # Calculate strategies
        snowball_result = cls._calculate_snowball(debt_list.copy(), monthly_payment)
        avalanche_result = cls._calculate_avalanche(debt_list.copy(), monthly_payment)

        return {
            "snowball": snowball_result,
            "avalanche": avalanche_result,
            "summary": cls._generate_summary(snowball_result, avalanche_result),
        }

    @classmethod
    def _calculate_snowball(cls, debts: List[Dict], monthly_payment: Decimal) -> Dict[str, Any]:
        """
        Calculate debt payoff using Snowball method (smallest balance first)

        Args:
            debts: List of debt dictionaries
            monthly_payment: Monthly payment amount

        Returns:
            Dictionary with payoff details
        """
        # Sort by balance (smallest first)
        sorted_debts = sorted(debts, key=lambda x: x["balance"])

        return cls._calculate_payoff_plan(sorted_debts, monthly_payment, "Snowball")

    @classmethod
    def _calculate_avalanche(cls, debts: List[Dict], monthly_payment: Decimal) -> Dict[str, Any]:
        """
        Calculate debt payoff using Avalanche method (highest interest first)

        Args:
            debts: List of debt dictionaries
            monthly_payment: Monthly payment amount

        Returns:
            Dictionary with payoff details
        """
        # Sort by interest rate (highest first), then by balance
        sorted_debts = sorted(debts, key=lambda x: (-x["interest_rate"], x["balance"]))

        return cls._calculate_payoff_plan(sorted_debts, monthly_payment, "Avalanche")

    @classmethod
    def _calculate_payoff_plan(
        cls, ordered_debts: List[Dict], monthly_payment: Decimal, strategy_name: str
    ) -> Dict[str, Any]:
        """
        Calculate payoff plan for ordered list of debts

        Args:
            ordered_debts: List of debts in payoff order
            monthly_payment: Monthly payment amount
            strategy_name: Name of the strategy

        Returns:
            Dictionary with payoff plan details
        """
        # Store original balances for total calculation
        original_total = sum(debt["balance"] for debt in ordered_debts)

        total_interest = Decimal("0")
        total_months = 0
        remaining_debts = [debt.copy() for debt in ordered_debts]
        current_date = datetime.now()
        timeline = []

        while remaining_debts:
            # Calculate minimum payments for all remaining debts
            total_minimums = sum(debt["minimum_payment"] for debt in remaining_debts)
            extra_payment = monthly_payment - total_minimums

            if extra_payment < 0:
                # Not enough to cover minimums - use available payment only
                extra_payment = Decimal("0")
                actual_payment = monthly_payment
            else:
                actual_payment = monthly_payment

            # Calculate interest for this month for all debts
            month_interest = Decimal("0")
            for debt in remaining_debts:
                if debt["balance"] > 0:
                    monthly_rate = debt["interest_rate"] / 12
                    interest = debt["balance"] * monthly_rate
                    month_interest += interest
                    debt["balance"] += interest  # Add interest to balance

            total_interest += month_interest

            # Apply payment to debts
            payment_remaining = actual_payment
            for i, debt in enumerate(remaining_debts):
                if payment_remaining <= 0:
                    break

                min_payment = debt["minimum_payment"]
                if extra_payment > 0:
                    # Can pay more than minimums - focus debt gets extra
                    if i == 0:
                        # Focus debt gets minimum + extra
                        payment_to_debt = min(debt["balance"], min_payment + extra_payment)
                    else:
                        # Other debts get minimum only
                        payment_to_debt = min(debt["balance"], min_payment)
                else:
                    # Cannot cover all minimums - pay proportionally
                    if total_minimums > 0:
                        proportional_share = (min_payment / total_minimums) * actual_payment
                        payment_to_debt = min(debt["balance"], proportional_share)
                    else:
                        payment_to_debt = Decimal("0")

                payment_to_debt = min(payment_to_debt, payment_remaining)
                debt["balance"] -= payment_to_debt
                payment_remaining -= payment_to_debt

            # Remove paid off debts
            remaining_debts = [d for d in remaining_debts if d["balance"] > Decimal("0.01")]

            total_months += 1
            current_date += timedelta(days=30)  # Approximate month

            # Record timeline entry
            if total_months <= 12 or total_months % 6 == 0 or not remaining_debts:
                timeline.append(
                    {
                        "month": total_months,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "total_remaining": sum(d["balance"] for d in remaining_debts),
                        "debts_remaining": len(remaining_debts),
                    }
                )

            # Safety check - prevent infinite loop
            if total_months > 600:  # 50 years max
                break

        # Use original total as principal
        total_principal = original_total
        total_paid = total_principal + total_interest

        return {
            "strategy": strategy_name,
            "total_principal": float(total_principal),
            "total_interest": float(total_interest),
            "total_paid": float(total_paid),
            "total_months": total_months,
            "total_years": round(total_months / 12, 1),
            "payoff_date": current_date.strftime("%Y-%m-%d"),
            "timeline": timeline,
            "debt_order": [
                {
                    "name": debt["name"],
                    "balance": float(debt["balance"]),
                    "interest_rate": float(debt["interest_rate"] * 100),
                }
                for debt in ordered_debts
            ],
        }

    @classmethod
    def _generate_summary(cls, snowball: Dict, avalanche: Dict) -> Dict[str, Any]:
        """Generate comparison summary between strategies"""
        best_strategy = "avalanche" if avalanche["total_interest"] < snowball["total_interest"] else "snowball"
        interest_savings = abs(snowball["total_interest"] - avalanche["total_interest"])
        time_difference = abs(snowball["total_months"] - avalanche["total_months"])

        return {
            "best_strategy": best_strategy,
            "interest_savings": float(interest_savings),
            "time_difference_months": int(time_difference),
            "recommendation": (
                f"The {best_strategy.capitalize()} method saves ${float(interest_savings):,.2f} in interest"
                + (f" and {int(time_difference)} months" if time_difference > 0 else "")
            ),
        }
