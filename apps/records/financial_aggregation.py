"""
Financial Data Aggregation Services
Provides aggregated financial data for budget, investment, debt, and dashboard views
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from collections import defaultdict

from django.db.models import Sum, Count, Avg, Q, Max
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    LinkedAccount,
    AccountBalance,
    FinancialTransaction,
    InvestmentHolding,
    InvestmentTransaction,
    DebtAccount,
)

User = get_user_model()


class BudgetAggregationService:
    """Service for aggregating budget-related financial data"""
    
    @staticmethod
    def get_user_budget_data(user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated budget data for a user including:
        - Account balances
        - Recent transactions
        - Spending by category
        - Income vs expenses
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get active linked accounts
        accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type__in=['depository', 'credit']
        )
        
        # Get latest balances
        total_balance = Decimal('0.00')
        total_available = Decimal('0.00')
        total_credit_limit = Decimal('0.00')
        account_balances = []
        
        for account in accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                if account.account_type == 'depository':
                    total_balance += latest_balance.current_balance
                    if latest_balance.available_balance:
                        total_available += latest_balance.available_balance
                elif account.account_type == 'credit':
                    # For credit cards, balance is debt
                    total_balance -= latest_balance.current_balance
                    if latest_balance.limit:
                        total_credit_limit += latest_balance.limit
                
                account_balances.append({
                    'account': account,
                    'balance': latest_balance,
                    'type': account.account_type,
                })
        
        # Get transactions for the period
        transactions = FinancialTransaction.objects.filter(
            account__user=user,
            account__status='active',
            date__gte=start_date,
            date__lte=end_date,
        ).select_related('account').order_by('-date')
        
        # Calculate income and expenses
        income = Decimal('0.00')
        expenses = Decimal('0.00')
        
        # Group by category
        spending_by_category = defaultdict(lambda: {'amount': Decimal('0.00'), 'count': 0})
        
        for transaction in transactions:
            amount = transaction.amount
            if transaction.transaction_type == 'credit':
                income += amount
            else:
                expenses += amount
                # Group by category
                category = transaction.category or 'Uncategorized'
                spending_by_category[category]['amount'] += amount
                spending_by_category[category]['count'] += 1
        
        # Convert to list and sort
        category_spending = [
            {
                'category': cat,
                'amount': float(data['amount']),
                'count': data['count'],
            }
            for cat, data in sorted(
                spending_by_category.items(),
                key=lambda x: x[1]['amount'],
                reverse=True
            )[:10]
        ]
        
        # Get recent transactions
        recent_transactions = transactions[:20]
        
        return {
            'total_balance': float(total_balance),
            'total_available': float(total_available),
            'total_credit_limit': float(total_credit_limit),
            'account_balances': account_balances,
            'income': float(income),
            'expenses': float(expenses),
            'net_flow': float(income - expenses),
            'spending_by_category': category_spending,
            'recent_transactions': recent_transactions,
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
        }


class InvestmentAggregationService:
    """Service for aggregating investment and retirement data"""
    
    @staticmethod
    def get_user_investment_data(user: User) -> Dict[str, Any]:
        """
        Get aggregated investment data including:
        - Total portfolio value
        - Holdings by security
        - Investment accounts
        - Recent investment transactions
        """
        # Get investment accounts
        investment_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type__in=['investment', 'brokerage', 'retirement']
        )
        
        # Get all holdings
        holdings = InvestmentHolding.objects.filter(
            account__user=user,
            account__status='active',
        ).select_related('account').order_by('-as_of_date', 'security_name')
        
        # Calculate total portfolio value
        total_value = Decimal('0.00')
        total_cost_basis = Decimal('0.00')
        
        # Group holdings by security
        holdings_by_security = defaultdict(lambda: {
            'quantity': Decimal('0.00'),
            'value': Decimal('0.00'),
            'cost_basis': Decimal('0.00'),
            'accounts': set(),
        })
        
        # Get latest holdings per security
        latest_holdings = {}
        for holding in holdings:
            security_key = holding.security_id or holding.security_name
            if security_key not in latest_holdings:
                latest_holdings[security_key] = holding
            elif holding.as_of_date > latest_holdings[security_key].as_of_date:
                latest_holdings[security_key] = holding
        
        # Aggregate by security
        for security_key, holding in latest_holdings.items():
            total_value += holding.value
            if holding.cost_basis:
                total_cost_basis += holding.cost_basis
            
            holdings_by_security[security_key]['quantity'] += holding.quantity
            holdings_by_security[security_key]['value'] += holding.value
            if holding.cost_basis:
                holdings_by_security[security_key]['cost_basis'] += holding.cost_basis
            holdings_by_security[security_key]['accounts'].add(holding.account.account_name)
        
        # Convert to list
        security_list = []
        for security_key, data in sorted(
            holdings_by_security.items(),
            key=lambda x: x[1]['value'],
            reverse=True
        ):
            holding = latest_holdings[security_key]
            security_list.append({
                'security_id': holding.security_id,
                'security_name': holding.security_name,
                'security_ticker': holding.security_ticker,
                'security_type': holding.security_type,
                'quantity': float(data['quantity']),
                'value': float(data['value']),
                'cost_basis': float(data['cost_basis']),
                'gain_loss': float(data['value'] - data['cost_basis']) if data['cost_basis'] else None,
                'accounts': list(data['accounts']),
            })
        
        # Get recent investment transactions
        recent_transactions = InvestmentTransaction.objects.filter(
            account__user=user,
            account__status='active',
        ).select_related('account').order_by('-date')[:20]
        
        # Get account summaries
        account_summaries = []
        for account in investment_accounts:
            account_holdings = holdings.filter(account=account)
            account_value = sum(h.value for h in account_holdings)
            account_summaries.append({
                'account': account,
                'value': float(account_value),
                'holdings_count': account_holdings.count(),
            })
        
        return {
            'total_portfolio_value': float(total_value),
            'total_cost_basis': float(total_cost_basis),
            'total_gain_loss': float(total_value - total_cost_basis) if total_cost_basis else None,
            'holdings': security_list,
            'account_summaries': account_summaries,
            'recent_transactions': recent_transactions,
            'accounts_count': investment_accounts.count(),
        }


class DebtAggregationService:
    """Service for aggregating debt data"""
    
    @staticmethod
    def get_user_debt_data(user: User) -> Dict[str, Any]:
        """
        Get aggregated debt data including:
        - Total debt
        - Debt by type
        - Credit card utilization
        - Payment schedules
        """
        # Get debt accounts (credit cards, loans, etc.)
        debt_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type__in=['credit', 'loan']
        )
        
        # Get debt account records
        debt_records = DebtAccount.objects.filter(
            account__user=user,
            account__status='active',
        ).select_related('account')
        
        # Calculate total debt
        total_debt = Decimal('0.00')
        total_credit_limit = Decimal('0.00')
        
        # Group by debt type
        debt_by_type = defaultdict(lambda: {
            'balance': Decimal('0.00'),
            'count': 0,
            'accounts': [],
        })
        
        # Process accounts
        account_details = []
        for account in debt_accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                balance = latest_balance.current_balance
                total_debt += balance
                
                if account.account_type == 'credit':
                    total_credit_limit += (latest_balance.limit or Decimal('0.00'))
                    debt_type = 'credit_card'
                else:
                    debt_type = account.account_subtype or 'loan'
                
                debt_by_type[debt_type]['balance'] += balance
                debt_by_type[debt_type]['count'] += 1
                debt_by_type[debt_type]['accounts'].append({
                    'name': account.account_name,
                    'balance': float(balance),
                })
                
                account_details.append({
                    'account': account,
                    'balance': latest_balance,
                    'debt_type': debt_type,
                })
        
        # Convert debt by type to list
        debt_type_list = [
            {
                'type': debt_type,
                'balance': float(data['balance']),
                'count': data['count'],
                'accounts': data['accounts'],
            }
            for debt_type, data in sorted(
                debt_by_type.items(),
                key=lambda x: x[1]['balance'],
                reverse=True
            )
        ]
        
        # Calculate credit utilization
        credit_utilization = None
        if total_credit_limit > 0:
            credit_card_debt = debt_by_type.get('credit_card', {}).get('balance', Decimal('0.00'))
            credit_utilization = float((credit_card_debt / total_credit_limit) * 100)
        
        # Get upcoming payments
        upcoming_payments = []
        for debt_record in debt_records:
            if debt_record.next_payment_date and debt_record.next_payment_date >= timezone.now().date():
                upcoming_payments.append({
                    'account': debt_record.account.account_name,
                    'date': debt_record.next_payment_date,
                    'amount': float(debt_record.next_payment_amount or Decimal('0.00')),
                    'debt_type': debt_record.debt_type,
                })
        
        upcoming_payments.sort(key=lambda x: x['date'])
        
        return {
            'total_debt': float(total_debt),
            'total_credit_limit': float(total_credit_limit),
            'credit_utilization': credit_utilization,
            'debt_by_type': debt_type_list,
            'account_details': account_details,
            'upcoming_payments': upcoming_payments[:10],
            'accounts_count': debt_accounts.count(),
        }


class DashboardAggregationService:
    """Service for aggregating dashboard summary data"""
    
    @staticmethod
    def get_user_financial_summary(user: User) -> Dict[str, Any]:
        """
        Get comprehensive financial summary for dashboard including:
        - Net worth
        - Account summary
        - Recent activity
        - Quick stats
        """
        # Get all active accounts
        all_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active'
        )
        
        # Calculate assets (depository + investments)
        total_assets = Decimal('0.00')
        total_investments = Decimal('0.00')
        total_cash = Decimal('0.00')
        
        # Calculate liabilities (credit + loans)
        total_liabilities = Decimal('0.00')
        
        for account in all_accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                balance = latest_balance.current_balance
                if account.account_type in ['depository']:
                    total_cash += balance
                    total_assets += balance
                elif account.account_type in ['investment', 'brokerage', 'retirement']:
                    # For investments, use holdings value if available
                    holdings_value = InvestmentHolding.objects.filter(
                        account=account
                    ).aggregate(total=Sum('value'))['total'] or Decimal('0.00')
                    total_investments += holdings_value
                    total_assets += holdings_value
                elif account.account_type in ['credit', 'loan']:
                    total_liabilities += balance
        
        # Net worth
        net_worth = total_assets - total_liabilities
        
        # Get recent transactions
        recent_transactions = FinancialTransaction.objects.filter(
            account__user=user,
            account__status='active',
        ).select_related('account').order_by('-date')[:10]
        
        # Get account counts by type
        account_counts = all_accounts.values('account_type').annotate(
            count=Count('id')
        )
        
        # Get linked accounts status
        linked_accounts_count = all_accounts.count()
        accounts_with_errors = all_accounts.filter(status='error').count()
        
        return {
            'net_worth': float(net_worth),
            'total_assets': float(total_assets),
            'total_liabilities': float(total_liabilities),
            'total_cash': float(total_cash),
            'total_investments': float(total_investments),
            'account_counts': {item['account_type']: item['count'] for item in account_counts},
            'linked_accounts_count': linked_accounts_count,
            'accounts_with_errors': accounts_with_errors,
            'recent_transactions': recent_transactions,
        }

