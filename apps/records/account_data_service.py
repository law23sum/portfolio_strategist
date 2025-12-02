"""
Service to extract and format account data from Plaid/LinkedAccounts
for use in assessment pages (budget, debt, investment, retirement, etc.)
"""

from decimal import Decimal
from typing import Dict, List, Optional
from django.db.models import Sum, Q

from .models import LinkedAccount, AccountBalance, FinancialTransaction


class AccountDataService:
    """Service to format account data for different assessment pages"""
    
    @staticmethod
    def get_budget_defaults(user) -> Dict:
        """Get default values for budget planner page"""
        defaults = {
            'annual_salary': 0,
            'monthly_income': 0,
            'checking_balance': 0,
            'savings_balance': 0,
            'total_cash': 0,
            'monthly_expenses': 0,
            'debt_payments': 0,
        }
        
        # Get depository accounts (checking, savings)
        depository_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type='depository'
        )
        
        checking_total = Decimal('0')
        savings_total = Decimal('0')
        
        for account in depository_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                subtype = account.account_subtype.lower() if account.account_subtype else ''
                
                if 'checking' in subtype or 'depository' in subtype:
                    checking_total += balance
                elif 'savings' in subtype:
                    savings_total += balance
        
        defaults['checking_balance'] = float(checking_total)
        defaults['savings_balance'] = float(savings_total)
        defaults['total_cash'] = float(checking_total + savings_total)
        
        # Estimate monthly income from recent transactions (deposits)
        recent_transactions = FinancialTransaction.objects.filter(
            account__user=user,
            account__account_type='depository',
            amount__gt=0  # Positive amounts are deposits/income
        ).order_by('-date')[:30]  # Last 30 transactions
        
        if recent_transactions.exists():
            total_income = sum(tx.amount for tx in recent_transactions if tx.amount > 0)
            # Estimate monthly income (average over transactions)
            avg_daily = total_income / 30 if recent_transactions.count() > 0 else 0
            defaults['monthly_income'] = float(avg_daily * 30)
            defaults['annual_salary'] = float(defaults['monthly_income'] * 12)
        
        # Calculate monthly expenses from transactions
        expense_transactions = FinancialTransaction.objects.filter(
            account__user=user,
            amount__lt=0  # Negative amounts are expenses
        ).order_by('-date')[:30]
        
        if expense_transactions.exists():
            total_expenses = abs(sum(tx.amount for tx in expense_transactions))
            avg_daily_expenses = total_expenses / 30 if expense_transactions.count() > 0 else 0
            defaults['monthly_expenses'] = float(avg_daily_expenses * 30)
        
        # Calculate debt payments
        debt_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type__in=['credit', 'loan']
        )
        
        debt_payments = Decimal('0')
        for account in debt_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance and latest_balance.limit:
                # Estimate minimum payment (typically 2-3% of balance or $25 minimum)
                balance = latest_balance.current_balance or Decimal('0')
                min_payment = max(balance * Decimal('0.02'), Decimal('25'))
                debt_payments += min_payment
        
        defaults['debt_payments'] = float(debt_payments)
        
        return defaults
    
    @staticmethod
    def get_debt_defaults(user) -> Dict:
        """Get default values for debt consolidation page"""
        defaults = {
            'total_debt': 0,
            'monthly_payments': 0,
            'credit_cards': [],
            'loans': [],
        }
        
        # Get credit card accounts
        credit_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type='credit'
        )
        
        total_debt = Decimal('0')
        monthly_payments = Decimal('0')
        
        for account in credit_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                limit = latest_balance.limit or Decimal('0')
                total_debt += balance
                
                # Estimate minimum payment
                min_payment = max(balance * Decimal('0.02'), Decimal('25'))
                monthly_payments += min_payment
                
                defaults['credit_cards'].append({
                    'name': account.account_name,
                    'institution': account.institution_name,
                    'balance': float(balance),
                    'limit': float(limit),
                    'min_payment': float(min_payment),
                    'interest_rate': 18.0,  # Default estimate
                })
        
        # Get loan accounts
        loan_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type='loan'
        )
        
        for account in loan_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                total_debt += balance
                
                # Estimate monthly payment (would need loan terms, but estimate based on balance)
                estimated_payment = balance * Decimal('0.01')  # Rough estimate
                monthly_payments += estimated_payment
                
                defaults['loans'].append({
                    'name': account.account_name,
                    'institution': account.institution_name,
                    'balance': float(balance),
                    'monthly_payment': float(estimated_payment),
                    'interest_rate': 5.0,  # Default estimate
                })
        
        defaults['total_debt'] = float(total_debt)
        defaults['monthly_payments'] = float(monthly_payments)
        
        return defaults
    
    @staticmethod
    def get_investment_defaults(user) -> Dict:
        """Get default values for investment/retirement pages"""
        defaults = {
            'total_investments': 0,
            'total_retirement': 0,
            'brokerage_accounts': [],
            'retirement_accounts': [],
            'savings_accounts': [],
        }
        
        # Get investment/brokerage accounts
        investment_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type__in=['investment', 'brokerage']
        )
        
        total_investments = Decimal('0')
        
        for account in investment_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                total_investments += balance
                
                defaults['brokerage_accounts'].append({
                    'name': account.account_name,
                    'institution': account.institution_name,
                    'balance': float(balance),
                    'account_type': account.account_subtype or 'investment',
                })
        
        defaults['total_investments'] = float(total_investments)
        
        # Get retirement accounts
        retirement_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type='retirement'
        )
        
        total_retirement = Decimal('0')
        
        for account in retirement_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                total_retirement += balance
                
                defaults['retirement_accounts'].append({
                    'name': account.account_name,
                    'institution': account.institution_name,
                    'balance': float(balance),
                    'account_type': account.account_subtype or 'retirement',
                })
        
        defaults['total_retirement'] = float(total_retirement)
        
        # Get savings accounts for investment pages
        savings_accounts = LinkedAccount.objects.filter(
            user=user,
            status='active',
            account_type='depository',
            account_subtype__icontains='savings'
        )
        
        for account in savings_accounts:
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                
                defaults['savings_accounts'].append({
                    'name': account.account_name,
                    'institution': account.institution_name,
                    'balance': float(balance),
                })
        
        return defaults
    
    @staticmethod
    def get_all_accounts_summary(user) -> Dict:
        """Get summary of all accounts"""
        accounts = LinkedAccount.objects.filter(
            user=user,
            status='active'
        )
        
        summary = {
            'total_accounts': accounts.count(),
            'by_type': {},
            'total_assets': Decimal('0'),
            'total_debt': Decimal('0'),
        }
        
        for account in accounts:
            account_type = account.account_type
            summary['by_type'][account_type] = summary['by_type'].get(account_type, 0) + 1
            
            latest_balance = AccountBalance.objects.filter(
                account=account
            ).order_by('-balance_date').first()
            
            if latest_balance:
                balance = latest_balance.current_balance or Decimal('0')
                
                if account_type in ['depository', 'investment', 'brokerage', 'retirement']:
                    summary['total_assets'] += balance
                elif account_type in ['credit', 'loan']:
                    summary['total_debt'] += balance
        
        summary['total_assets'] = float(summary['total_assets'])
        summary['total_debt'] = float(summary['total_debt'])
        summary['net_worth'] = summary['total_assets'] - summary['total_debt']
        
        return summary

