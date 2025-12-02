"""
Financial Data Aggregation Service
Handles integration with aggregation providers (Plaid, Yodlee, etc.)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

# Lazy import for Plaid - only import when needed
try:
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    from plaid.model.products import Products
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    from plaid.model.accounts_get_request import AccountsGetRequest
    from plaid.model.transactions_get_request import TransactionsGetRequest
    from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
    from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest
    from plaid.model.identity_get_request import IdentityGetRequest
    from plaid.model.country_code import CountryCode
    from plaid.api.plaid_api import PlaidApi
    # Note: In Plaid SDK 37.x+, Environment enum was removed, use strings directly
    PLAID_AVAILABLE = True
except ImportError as e:
    PLAID_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Plaid Python SDK not installed or import error: {e}. Financial aggregation features will be limited.")

from .models import (
    AggregationProvider,
    LinkedAccount,
    AccountBalance,
    FinancialTransaction,
    InvestmentHolding,
    InvestmentTransaction,
    DebtAccount,
    DataSyncLog,
)
from .encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


def categorize_and_connect_account(linked_account: LinkedAccount) -> Dict[str, Any]:
    """
    Categorize a linked account and connect it to the appropriate financial category:
    - Budget: depository accounts (checking, savings)
    - Debt: credit cards and loans
    - Investment: investment and brokerage accounts
    - Retirement: retirement accounts (401k, IRA, etc.)
    
    Returns a dict with categorization info.
    """
    category_info = {
        'category': None,
        'connected': False,
        'details': {}
    }
    
    account_type = linked_account.account_type
    account_subtype = linked_account.account_subtype.lower() if linked_account.account_subtype else ''
    
    # Determine category based on account type and subtype
    if account_type == 'depository':
        # Budget accounts: checking, savings, money market, etc.
        category_info['category'] = 'budget'
        category_info['connected'] = True
        category_info['details'] = {
            'type': 'budget',
            'subtype': account_subtype or 'checking',
            'description': f'Budget account: {linked_account.account_name}'
        }
        logger.info(f"Account {linked_account.id} categorized as BUDGET")
        
    elif account_type in ['credit', 'loan']:
        # Debt accounts: credit cards, loans, mortgages
        category_info['category'] = 'debt'
        
        # Determine debt type from account subtype
        debt_type_map = {
            'credit card': 'credit_card',
            'paypal': 'credit_card',
            'mortgage': 'mortgage',
            'auto': 'auto_loan',
            'student': 'student_loan',
            'personal': 'personal_loan',
        }
        
        debt_type = 'other'
        for key, value in debt_type_map.items():
            if key in account_subtype:
                debt_type = value
                break
        
        # Create or update DebtAccount
        latest_balance = linked_account.balances.first()
        if latest_balance:
            debt_account, created = DebtAccount.objects.update_or_create(
                account=linked_account,
                defaults={
                    'debt_type': debt_type,
                    'current_balance': latest_balance.current_balance,
                    'credit_limit': latest_balance.limit if account_type == 'credit' else None,
                    'as_of_date': latest_balance.balance_date,
                    'raw_data': latest_balance.raw_data,
                }
            )
            category_info['connected'] = True
            category_info['details'] = {
                'type': 'debt',
                'debt_type': debt_type,
                'debt_account_id': debt_account.id,
                'description': f'Debt account: {linked_account.account_name}'
            }
            logger.info(f"Account {linked_account.id} categorized as DEBT ({debt_type})")
        else:
            logger.warning(f"Account {linked_account.id} has no balance data for debt categorization")
        
    elif account_type in ['investment', 'brokerage']:
        # Investment accounts: brokerage, investment accounts
        category_info['category'] = 'investment'
        category_info['connected'] = True
        category_info['details'] = {
            'type': 'investment',
            'subtype': account_subtype or 'brokerage',
            'description': f'Investment account: {linked_account.account_name}'
        }
        logger.info(f"Account {linked_account.id} categorized as INVESTMENT")
        
    elif account_type == 'retirement':
        # Retirement accounts: 401k, IRA, pension, etc.
        category_info['category'] = 'retirement'
        category_info['connected'] = True
        
        # Determine retirement account subtype
        retirement_subtype = '401k'  # default
        if 'ira' in account_subtype or 'roth' in account_subtype:
            retirement_subtype = 'ira'
        elif 'pension' in account_subtype:
            retirement_subtype = 'pension'
        elif '403b' in account_subtype:
            retirement_subtype = '403b'
        elif '457' in account_subtype:
            retirement_subtype = '457'
        
        category_info['details'] = {
            'type': 'retirement',
            'subtype': retirement_subtype,
            'description': f'Retirement account: {linked_account.account_name}'
        }
        logger.info(f"Account {linked_account.id} categorized as RETIREMENT ({retirement_subtype})")
        
    else:
        category_info['category'] = 'other'
        category_info['details'] = {
            'type': 'other',
            'description': f'Other account type: {linked_account.account_name}'
        }
        logger.info(f"Account {linked_account.id} categorized as OTHER")
    
    return category_info


class PlaidAggregationService:
    """Service for integrating with Plaid API"""
    
    def __init__(self, provider: Optional[AggregationProvider] = None):
        """
        Initialize Plaid service with provider configuration.
        If no provider is provided, uses the first active Plaid provider.
        """
        if not PLAID_AVAILABLE:
            raise ImportError(
                "Plaid Python SDK is not installed. Install it with: pip install plaid-python"
            )
        
        if provider is None:
            provider = AggregationProvider.objects.filter(
                name='plaid',
                is_active=True
            ).first()
        
        if provider is None:
            raise ValueError("No active Plaid provider found. Please configure one in the database.")
        
        self.provider = provider
        
        # Initialize Plaid client
        # In Plaid SDK 37.x+, host is a string, not an Environment enum
        environment_map = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com',
        }
        plaid_environment = environment_map.get(
            self.provider.environment.lower(),
            'https://sandbox.plaid.com'
        )
        
        configuration = Configuration(
            host=plaid_environment,
            api_key={
                'clientId': self.provider.api_key,
                'secret': self.provider.api_secret,
            }
        )
        api_client = ApiClient(configuration)
        self.client = PlaidApi(api_client)
    
    def create_link_token(self, user_id: str = None, user_email: str = None, for_auth: bool = False, redirect_uri: str = None) -> Dict[str, Any]:
        """
        Create a Plaid Link token for initiating the OAuth flow.
        Returns a dictionary with 'link_token' and 'expiration'.
        
        Args:
            user_id: User ID (optional for authentication flow)
            user_email: User email (optional for authentication flow)
            for_auth: If True, include Identity product for authentication
            redirect_uri: OAuth redirect URI for banks that require OAuth flow
        """
        try:
            products = [Products('transactions'), Products('investments'), Products('liabilities')]
            if for_auth:
                products.append(Products('identity'))
            
            request_data = {
                'products': products,
                'client_name': "The Portfolio Strategist",
                'country_codes': [CountryCode('US')],
                'language': 'en',
            }
            
            if user_id:
                request_data['user'] = LinkTokenCreateRequestUser(
                    client_user_id=str(user_id)
                )
            elif for_auth:
                # For authentication, use a temporary client_user_id
                request_data['user'] = LinkTokenCreateRequestUser(
                    client_user_id='temp_auth_' + str(uuid.uuid4())
                )
            
            # Add redirect URI for OAuth flows (only if provided)
            # Note: redirect_uri must be whitelisted in Plaid developer dashboard first
            # Only include it when handling an OAuth callback, not for initial link token creation
            # For most banks that don't use OAuth, this should be None/omitted
            # We'll only include redirect_uri when we're actually handling an OAuth callback
            # For now, omit it to avoid the 400 error - OAuth will work via receivedRedirectUri in frontend
            
            if self.provider.webhook_url:
                request_data['webhook'] = self.provider.webhook_url
            
            request = LinkTokenCreateRequest(**request_data)
            response = self.client.link_token_create(request)
            
            # Handle both dict and object responses
            link_token = response.link_token if hasattr(response, 'link_token') else response.get('link_token')
            expiration = response.expiration if hasattr(response, 'expiration') else response.get('expiration')
            
            return {
                'link_token': link_token,
                'expiration': expiration.isoformat() if hasattr(expiration, 'isoformat') else str(expiration),
            }
        except Exception as e:
            logger.error(f"Error creating Plaid link token: {e}")
            raise
    
    def get_identity(self, access_token: str) -> Dict[str, Any]:
        """
        Get identity information from Plaid using an access token.
        Returns identity data including names, emails, phone numbers, and addresses.
        """
        try:
            request = IdentityGetRequest(access_token=access_token)
            response = self.client.identity_get(request)
            
            # Handle both dict and object responses
            if hasattr(response, 'accounts'):
                accounts = response.accounts
            else:
                accounts = response.get('accounts', [])
            
            identity_data = {
                'accounts': [],
                'names': [],
                'emails': [],
                'phone_numbers': [],
                'addresses': []
            }
            
            for account in accounts:
                account_data = {
                    'account_id': account.account_id if hasattr(account, 'account_id') else account.get('account_id'),
                    'owners': []
                }
                
                owners = account.owners if hasattr(account, 'owners') else account.get('owners', [])
                for owner in owners:
                    owner_data = {
                        'names': [],
                        'emails': [],
                        'phone_numbers': [],
                        'addresses': []
                    }
                    
                    # Extract names
                    names = owner.names if hasattr(owner, 'names') else owner.get('names', [])
                    for name in names:
                        if name not in identity_data['names']:
                            identity_data['names'].append(name)
                        owner_data['names'].append(name)
                    
                    # Extract emails
                    emails = owner.emails if hasattr(owner, 'emails') else owner.get('emails', [])
                    for email_obj in emails:
                        email = email_obj.data if hasattr(email_obj, 'data') else email_obj.get('data', '')
                        if email and email not in identity_data['emails']:
                            identity_data['emails'].append(email)
                        owner_data['emails'].append(email)
                    
                    # Extract phone numbers
                    phones = owner.phone_numbers if hasattr(owner, 'phone_numbers') else owner.get('phone_numbers', [])
                    for phone_obj in phones:
                        phone = phone_obj.data if hasattr(phone_obj, 'data') else phone_obj.get('data', '')
                        if phone and phone not in identity_data['phone_numbers']:
                            identity_data['phone_numbers'].append(phone)
                        owner_data['phone_numbers'].append(phone)
                    
                    # Extract addresses
                    addresses = owner.addresses if hasattr(owner, 'addresses') else owner.get('addresses', [])
                    for addr_obj in addresses:
                        addr_data = addr_obj.data if hasattr(addr_obj, 'data') else addr_obj.get('data', {})
                        if addr_data:
                            addr_str = f"{addr_data.get('street', '')}, {addr_data.get('city', '')}, {addr_data.get('region', '')} {addr_data.get('postal_code', '')}"
                            if addr_str not in identity_data['addresses']:
                                identity_data['addresses'].append(addr_str)
                            owner_data['addresses'].append(addr_data)
                    
                    account_data['owners'].append(owner_data)
                
                identity_data['accounts'].append(account_data)
            
            return identity_data
        except Exception as e:
            logger.error(f"Error getting identity from Plaid: {e}")
            raise
    
    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange a public token for an access token.
        Returns the access token.
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            # Handle both dict and object responses
            return response.access_token if hasattr(response, 'access_token') else response.get('access_token')
        except Exception as e:
            logger.error(f"Error exchanging public token: {e}")
            raise
    
    def get_item_id(self, access_token: str) -> str:
        """Get the item_id for an access token"""
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            # Handle both dict and object responses
            item = response.item if hasattr(response, 'item') else response.get('item', {})
            if isinstance(item, dict):
                return item.get('item_id', '')
            else:
                return getattr(item, 'item_id', '')
        except Exception as e:
            logger.error(f"Error getting item_id: {e}")
            raise
    
    def sync_accounts(self, linked_account: LinkedAccount) -> DataSyncLog:
        """
        Sync all account data for a linked account.
        Returns a DataSyncLog with sync results.
        """
        sync_log = DataSyncLog.objects.create(
            account=linked_account,
            status='success',
            started_at=timezone.now(),
        )
        
        try:
            # Decrypt access token
            access_token = decrypt_token(linked_account.access_token)
            
            # Sync accounts and balances
            accounts_data = self._fetch_accounts(access_token)
            accounts_synced = self._save_accounts(linked_account, accounts_data)
            sync_log.accounts_synced = accounts_synced
            
            # Sync transactions
            transactions_synced = self._sync_transactions(linked_account, access_token)
            sync_log.transactions_synced = transactions_synced
            
            # Sync investment holdings
            holdings_synced = self._sync_investment_holdings(linked_account, access_token)
            sync_log.holdings_synced = holdings_synced
            
            # Sync investment transactions
            investment_transactions_synced = self._sync_investment_transactions(linked_account, access_token)
            
            # Categorize and connect account to appropriate category (budget/debt/investment/retirement)
            category_info = categorize_and_connect_account(linked_account)
            
            # Update account status
            linked_account.status = 'active'
            linked_account.last_synced_at = timezone.now()
            linked_account.next_sync_at = timezone.now() + timedelta(hours=6)  # Sync every 6 hours
            linked_account.error_message = ''
            linked_account.save()
            
            sync_log.status = 'success'
            sync_log.completed_at = timezone.now()
            sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            sync_log.metadata = {
                'category': category_info.get('category'),
                'connected': category_info.get('connected', False),
            }
            
        except Exception as e:
            logger.error(f"Error syncing account {linked_account.id}: {e}")
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            
            linked_account.status = 'error'
            linked_account.error_message = str(e)
            linked_account.save()
        
        sync_log.save()
        return sync_log
    
    def _fetch_accounts(self, access_token: str) -> List[Dict]:
        """Fetch accounts from Plaid"""
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            # Handle both dict and object responses
            accounts_list = response.accounts if hasattr(response, 'accounts') else response.get('accounts', [])
            
            # Convert response to list of dicts
            accounts = []
            for account in accounts_list:
                # Handle both dict and object
                if hasattr(account, 'account_id'):
                    account_id = account.account_id
                    name = account.name
                    account_type = account.type
                    subtype = getattr(account, 'subtype', None)
                    mask = getattr(account, 'mask', '')
                    balances_obj = account.balances
                else:
                    account_id = account.get('account_id')
                    name = account.get('name')
                    account_type = account.get('type')
                    subtype = account.get('subtype')
                    mask = account.get('mask', '')
                    balances_obj = account.get('balances', {})
                
                # Extract balance info
                if hasattr(balances_obj, 'current'):
                    current = balances_obj.current
                    available = getattr(balances_obj, 'available', None)
                    limit = getattr(balances_obj, 'limit', None)
                    currency = getattr(balances_obj, 'iso_currency_code', 'USD')
                else:
                    current = balances_obj.get('current', 0)
                    available = balances_obj.get('available')
                    limit = balances_obj.get('limit')
                    currency = balances_obj.get('iso_currency_code', 'USD')
                
                accounts.append({
                    'account_id': account_id,
                    'name': name,
                    'type': account_type,
                    'subtype': subtype,
                    'mask': mask,
                    'balances': {
                        'current': current,
                        'available': available,
                        'limit': limit,
                        'iso_currency_code': currency,
                    }
                })
            return accounts
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            raise
    
    def _save_accounts(self, linked_account: LinkedAccount, accounts_data: List[Dict]) -> int:
        """Save account balances from Plaid data"""
        count = 0
        for account_data in accounts_data:
            # Update or create account balance
            balance_date = timezone.now()
            
            AccountBalance.objects.update_or_create(
                account=linked_account,
                balance_date=balance_date,
                defaults={
                    'current_balance': Decimal(str(account_data.get('balances', {}).get('current', 0))),
                    'available_balance': Decimal(str(account_data.get('balances', {}).get('available', 0))) if account_data.get('balances', {}).get('available') is not None else None,
                    'limit': Decimal(str(account_data.get('balances', {}).get('limit', 0))) if account_data.get('balances', {}).get('limit') is not None else None,
                    'currency_code': account_data.get('balances', {}).get('iso_currency_code', 'USD'),
                    'raw_data': account_data,
                }
            )
            count += 1
        
        return count
    
    def _sync_transactions(self, linked_account: LinkedAccount, access_token: str, days_back: int = 90) -> int:
        """Sync transactions from Plaid"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).date()
            end_date = datetime.now().date()
            
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
            )
            
            response = self.client.transactions_get(request)
            # Handle both dict and object responses
            transactions = response.transactions if hasattr(response, 'transactions') else response.get('transactions', [])
            
            count = 0
            for tx_data in transactions:
                # Handle both dict and object responses
                if hasattr(tx_data, 'transaction_id'):
                    tx_id = tx_data.transaction_id
                    tx_amount = getattr(tx_data, 'amount', 0)
                    tx_date = getattr(tx_data, 'date', None)
                    auth_date = getattr(tx_data, 'authorized_date', None)
                    categories = getattr(tx_data, 'category', [])
                    merchant = getattr(tx_data, 'merchant_name', '')
                    description = getattr(tx_data, 'name', '')
                    payment_channel = getattr(tx_data, 'payment_channel', '')
                    pending = getattr(tx_data, 'pending', False)
                    location = getattr(tx_data, 'location', {})
                    # Convert to dict for raw_data
                    raw_data = tx_data.dict() if hasattr(tx_data, 'dict') else tx_data
                else:
                    tx_id = tx_data.get('transaction_id')
                    tx_amount = tx_data.get('amount', 0)
                    tx_date = tx_data.get('date')
                    auth_date = tx_data.get('authorized_date')
                    categories = tx_data.get('category', [])
                    merchant = tx_data.get('merchant_name', '')
                    description = tx_data.get('name', '')
                    payment_channel = tx_data.get('payment_channel', '')
                    pending = tx_data.get('pending', False)
                    location = tx_data.get('location', {})
                    raw_data = tx_data
                
                # Handle date parsing - Plaid returns date strings
                if isinstance(tx_date, str):
                    tx_date = datetime.strptime(tx_date, '%Y-%m-%d').date()
                elif hasattr(tx_date, 'date'):
                    tx_date = tx_date.date()
                
                authorized_date = None
                if auth_date:
                    if isinstance(auth_date, str):
                        authorized_date = datetime.strptime(auth_date, '%Y-%m-%d').date()
                    elif hasattr(auth_date, 'date'):
                        authorized_date = auth_date.date()
                
                # Convert categories list to string
                category_str = ', '.join(categories) if isinstance(categories, list) else str(categories) if categories else ''
                
                FinancialTransaction.objects.update_or_create(
                    account=linked_account,
                    transaction_id=tx_id,
                    defaults={
                        'provider_transaction_id': tx_id,
                        'amount': abs(Decimal(str(tx_amount))),
                        'transaction_type': 'debit' if tx_amount > 0 else 'credit',
                        'date': tx_date,
                        'authorized_date': authorized_date,
                        'category': category_str,
                        'merchant_name': merchant,
                        'description': description,
                        'payment_channel': payment_channel,
                        'pending': pending,
                        'location': location if isinstance(location, dict) else {},
                        'raw_data': raw_data if isinstance(raw_data, dict) else {},
                    }
                )
                count += 1
            
            return count
        except Exception as e:
            logger.error(f"Error syncing transactions: {e}")
            raise
    
    def _sync_investment_holdings(self, linked_account: LinkedAccount, access_token: str) -> int:
        """Sync investment holdings from Plaid"""
        try:
            request = InvestmentsHoldingsGetRequest(access_token=access_token)
            response = self.client.investments_holdings_get(request)
            # Handle both dict and object responses
            holdings = response.holdings if hasattr(response, 'holdings') else response.get('holdings', [])
            
            count = 0
            as_of_date = timezone.now()
            
            for holding_data in holdings:
                # Handle both dict and object responses
                if hasattr(holding_data, 'security'):
                    security_obj = holding_data.security
                    security_id = getattr(security_obj, 'security_id', '')
                    security_name = getattr(security_obj, 'name', '')
                    security_ticker = getattr(security_obj, 'ticker_symbol', '')
                    security_type = getattr(security_obj, 'type', '')
                    quantity = getattr(holding_data, 'quantity', 0)
                    price = getattr(holding_data, 'price', None)
                    value = getattr(holding_data, 'institution_value', 0)
                    cost_basis = getattr(holding_data, 'cost_basis', None)
                    currency = getattr(holding_data, 'iso_currency_code', 'USD')
                    raw_data = holding_data.dict() if hasattr(holding_data, 'dict') else holding_data
                else:
                    security = holding_data.get('security', {})
                    security_id = security.get('security_id', '')
                    security_name = security.get('name', '')
                    security_ticker = security.get('ticker_symbol', '')
                    security_type = security.get('type', '')
                    quantity = holding_data.get('quantity', 0)
                    price = holding_data.get('price')
                    value = holding_data.get('institution_value', 0)
                    cost_basis = holding_data.get('cost_basis')
                    currency = holding_data.get('iso_currency_code', 'USD')
                    raw_data = holding_data
                
                InvestmentHolding.objects.update_or_create(
                    account=linked_account,
                    security_id=security_id,
                    as_of_date=as_of_date,
                    defaults={
                        'security_name': security_name,
                        'security_ticker': security_ticker,
                        'security_type': security_type,
                        'quantity': Decimal(str(quantity)),
                        'price': Decimal(str(price)) if price else None,
                        'value': Decimal(str(value)),
                        'cost_basis': Decimal(str(cost_basis)) if cost_basis else None,
                        'currency_code': currency,
                        'raw_data': raw_data if isinstance(raw_data, dict) else {},
                    }
                )
                count += 1
            
            return count
        except Exception as e:
            logger.error(f"Error syncing investment holdings: {e}")
            # Investments might not be available for all accounts
            return 0
    
    def _sync_investment_transactions(self, linked_account: LinkedAccount, access_token: str, days_back: int = 90) -> int:
        """Sync investment transactions from Plaid"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).date()
            end_date = datetime.now().date()
            
            request = InvestmentsTransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
            )
            
            response = self.client.investments_transactions_get(request)
            # Handle both dict and object responses
            transactions = response.investment_transactions if hasattr(response, 'investment_transactions') else response.get('investment_transactions', [])
            
            count = 0
            for tx_data in transactions:
                # Handle both dict and object responses
                if hasattr(tx_data, 'investment_transaction_id'):
                    tx_id = tx_data.investment_transaction_id
                    security = getattr(tx_data, 'security_id', '')
                    tx_type = getattr(tx_data, 'type', '').lower()
                    tx_amount = getattr(tx_data, 'amount', 0)
                    quantity = getattr(tx_data, 'quantity', None)
                    price = getattr(tx_data, 'price', None)
                    tx_date = getattr(tx_data, 'date', None)
                    fees = getattr(tx_data, 'fees', None)
                    currency = getattr(tx_data, 'iso_currency_code', 'USD')
                    raw_data = tx_data.dict() if hasattr(tx_data, 'dict') else tx_data
                else:
                    tx_id = tx_data.get('investment_transaction_id')
                    security = tx_data.get('security_id', '')
                    tx_type = tx_data.get('type', '').lower()
                    tx_amount = tx_data.get('amount', 0)
                    quantity = tx_data.get('quantity')
                    price = tx_data.get('price')
                    tx_date = tx_data.get('date')
                    fees = tx_data.get('fees')
                    currency = tx_data.get('iso_currency_code', 'USD')
                    raw_data = tx_data
                
                # Handle date parsing
                if isinstance(tx_date, str):
                    tx_date = datetime.strptime(tx_date, '%Y-%m-%d').date()
                elif hasattr(tx_date, 'date'):
                    tx_date = tx_date.date()
                
                InvestmentTransaction.objects.update_or_create(
                    account=linked_account,
                    transaction_id=tx_id,
                    defaults={
                        'provider_transaction_id': tx_id,
                        'security_id': security,
                        'transaction_type': tx_type,
                        'amount': abs(Decimal(str(tx_amount))),
                        'quantity': Decimal(str(quantity)) if quantity else None,
                        'price': Decimal(str(price)) if price else None,
                        'date': tx_date,
                        'fees': Decimal(str(fees)) if fees else None,
                        'currency_code': currency,
                        'raw_data': raw_data if isinstance(raw_data, dict) else {},
                    }
                )
                count += 1
            
            return count
        except Exception as e:
            logger.error(f"Error syncing investment transactions: {e}")
            # Investment transactions might not be available for all accounts
            return 0


class AggregationServiceFactory:
    """Factory for creating aggregation services based on provider"""
    
    @staticmethod
    def create_service(provider: AggregationProvider):
        """Create appropriate aggregation service for provider"""
        if provider.name == 'plaid':
            return PlaidAggregationService(provider)
        else:
            raise ValueError(f"Unsupported aggregation provider: {provider.name}")

