"""
Retirement Planning Calculator
Calculates retirement projections and scenarios
"""

from datetime import date
from decimal import Decimal


def calculate_retirement_projections(plan):
    """
    Calculate comprehensive retirement projections

    Args:
        plan: RetirementPlan instance

    Returns:
        Dictionary with projections data
    """
    years_to_retirement = plan.retirement_age - plan.current_age

    if years_to_retirement <= 0:
        return {"error": "Retirement age must be greater than current age"}

    # Monthly return rate
    monthly_return = (plan.expected_return_rate / 100) / 12

    # Projections year by year
    projections = []
    current_savings = plan.current_savings
    monthly_contribution = plan.monthly_contribution

    # Calculate employer match
    employer_match = Decimal("0")
    if plan.employer_match_percent > 0:
        employer_match = monthly_contribution * (plan.employer_match_percent / 100)
        if plan.employer_match_limit:
            employer_match = min(employer_match, plan.employer_match_limit / 12)

    total_monthly_contribution = monthly_contribution + employer_match

    for year in range(years_to_retirement + 1):
        age = plan.current_age + year

        if year == 0:
            # Starting point
            projections.append(
                {
                    "age": age,
                    "year": date.today().year + year,
                    "savings": float(current_savings),
                    "contributions": float(total_monthly_contribution * 12),
                    "growth": 0,
                }
            )
        else:
            # Calculate growth for the year
            # Simplified: compound monthly
            year_start = current_savings

            for month in range(12):
                # Add contribution
                current_savings += total_monthly_contribution
                # Apply growth
                current_savings *= 1 + monthly_return

            year_end = current_savings
            growth = year_end - year_start - (total_monthly_contribution * 12)

            projections.append(
                {
                    "age": age,
                    "year": date.today().year + year,
                    "savings": float(current_savings),
                    "contributions": float(total_monthly_contribution * 12),
                    "growth": float(growth),
                }
            )

    # Calculate retirement needs
    # Adjust desired income for inflation
    inflation_factor = (1 + plan.inflation_rate / 100) ** years_to_retirement
    inflated_retirement_income = plan.desired_retirement_income * Decimal(str(inflation_factor))

    # 4% rule: need 25x annual expenses
    retirement_need = inflated_retirement_income * Decimal("25")

    # Social Security adjustment
    if plan.social_security_benefit:
        annual_ss = plan.social_security_benefit * Decimal("12")
        retirement_need -= annual_ss

    # Projected savings at retirement
    projected_savings = current_savings

    # Calculate shortfall/surplus
    shortfall = retirement_need - projected_savings

    # Generate scenarios
    scenarios = []

    # Scenario 1: Current plan
    scenarios.append(
        {
            "name": "Current Plan",
            "monthly_contribution": float(monthly_contribution),
            "projected_savings": float(projected_savings),
            "retirement_need": float(retirement_need),
            "shortfall": float(shortfall),
            "meets_goal": shortfall <= 0,
        }
    )

    # Scenario 2: Increase contribution by 20%
    increased_contribution = monthly_contribution * Decimal("1.2")
    increased_savings = calculate_future_value(
        plan.current_savings, increased_contribution + employer_match, plan.expected_return_rate, years_to_retirement
    )
    scenarios.append(
        {
            "name": "Increase Contribution 20%",
            "monthly_contribution": float(increased_contribution),
            "projected_savings": float(increased_savings),
            "retirement_need": float(retirement_need),
            "shortfall": float(retirement_need - increased_savings),
            "meets_goal": (retirement_need - increased_savings) <= 0,
        }
    )

    # Scenario 3: Work 2 more years
    extended_years = years_to_retirement + 2
    extended_savings = calculate_future_value(
        plan.current_savings, total_monthly_contribution, plan.expected_return_rate, extended_years
    )
    scenarios.append(
        {
            "name": "Work 2 More Years",
            "monthly_contribution": float(monthly_contribution),
            "projected_savings": float(extended_savings),
            "retirement_need": float(retirement_need),
            "shortfall": float(retirement_need - extended_savings),
            "meets_goal": (retirement_need - extended_savings) <= 0,
        }
    )

    # Analysis and recommendations
    analysis = {
        "years_to_retirement": years_to_retirement,
        "projected_savings_at_retirement": float(projected_savings),
        "retirement_need": float(retirement_need),
        "shortfall": float(shortfall),
        "meets_goal": shortfall <= 0,
        "recommendations": [],
    }

    if shortfall > 0:
        # Calculate required monthly contribution to meet goal
        required_contribution = calculate_required_contribution(
            plan.current_savings, retirement_need, plan.expected_return_rate, years_to_retirement
        )

        analysis["recommendations"].append(
            f"To meet your retirement goal, you need to save ${required_contribution:.2f} per month"
        )
        analysis["recommendations"].append(f"Current shortfall: ${shortfall:,.2f}")
    else:
        analysis["recommendations"].append("You're on track to meet your retirement goal!")

    return {
        "projections": projections,
        "scenarios": scenarios,
        "analysis": analysis,
    }


def calculate_future_value(present_value, monthly_contribution, annual_return_rate, years):
    """Calculate future value with monthly contributions"""
    monthly_rate = (annual_return_rate / 100) / 12
    months = years * 12

    # Future value of present value
    fv_pv = present_value * ((1 + monthly_rate) ** months)

    # Future value of annuity (monthly contributions)
    if monthly_rate > 0:
        fv_annuity = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_annuity = monthly_contribution * months

    return fv_pv + fv_annuity


def calculate_required_contribution(present_value, future_goal, annual_return_rate, years):
    """Calculate required monthly contribution to reach goal"""
    monthly_rate = (annual_return_rate / 100) / 12
    months = years * 12

    # Future value of present value
    fv_pv = present_value * ((1 + monthly_rate) ** months)

    # Remaining needed from contributions
    needed = future_goal - fv_pv

    # Calculate required monthly contribution
    if monthly_rate > 0:
        required = needed / (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        required = needed / months

    return max(Decimal("0"), required)
