"""
Automatic Plaid Data Distribution Service
Automatically organizes and distributes Plaid data to corresponding web pages after login
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import LinkedAccount, AccountBalance, FinancialTransaction
from .aggregation_service import PlaidAggregationService
from .encryption import decrypt_token

logger = logging.getLogger(__name__)
User = get_user_model()


class PlaidDataDistributionService:
    """Service to automatically organize and distribute Plaid data after login"""
    
    @staticmethod
    def distribute_plaid_data(user, access_token: str, identity_data: Optional[Dict] = None):
        """
        Automatically fetch data from Plaid APIs and distribute to web pages after successful login.
        This fetches directly from Plaid APIs and organizes data for each web page.
        
        Args:
            user: The user object
            access_token: Plaid access token
            identity_data: Optional identity data from Plaid
        """
        try:
            # Get or create Plaid provider
            from .models import AggregationProvider
            provider = AggregationProvider.objects.filter(name='plaid', is_active=True).first()
            if not provider:
                logger.warning("Plaid provider not found")
                return
            
            service = PlaidAggregationService(provider)
            
            # Fetch all data directly from Plaid APIs
            logger.info(f"Fetching Plaid data directly from APIs for user {user.id}")
            
            # 1. Get Identity data (if not already provided)
            if not identity_data:
                try:
                    identity_data = service.get_identity(access_token)
                except Exception as e:
                    logger.warning(f"Could not fetch identity: {e}")
                    identity_data = {}
            
            # 2. Get Accounts data
            accounts_data = []
            try:
                accounts_data = service._fetch_accounts(access_token)
            except Exception as e:
                logger.error(f"Error fetching accounts: {e}")
            
            # 3. Get Transactions data
            transactions_data = []
            try:
                from datetime import timedelta
                start_date = (timezone.now() - timedelta(days=90)).date()
                end_date = timezone.now().date()
                
                from plaid.model.transactions_get_request import TransactionsGetRequest
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                )
                response = service.client.transactions_get(request)
                transactions = response.transactions if hasattr(response, 'transactions') else response.get('transactions', [])
                
                # Convert transactions to dict format
                for tx in transactions:
                    if hasattr(tx, 'transaction_id'):
                        transactions_data.append({
                            'transaction_id': tx.transaction_id,
                            'amount': getattr(tx, 'amount', 0),
                            'date': getattr(tx, 'date', None),
                            'name': getattr(tx, 'name', ''),
                            'merchant_name': getattr(tx, 'merchant_name', ''),
                            'category': getattr(tx, 'category', []),
                            'account_id': getattr(tx, 'account_id', ''),
                            'pending': getattr(tx, 'pending', False),
                        })
                    else:
                        transactions_data.append(tx)
            except Exception as e:
                logger.warning(f"Could not fetch transactions: {e}")
            
            # Get linked accounts first - needed for investment data sync
            linked_accounts = LinkedAccount.objects.filter(
                user=user,
                provider=provider,
                status='active'
            )
            
            # 4. Get Investment Holdings data (only if we have a linked account)
            investment_holdings = []
            if linked_accounts.exists():
                try:
                    # Use the first linked account for investment holdings
                    first_account = linked_accounts.first()
                    holdings_count = service._sync_investment_holdings(first_account, access_token)
                    # Note: _sync_investment_holdings returns count, not data
                    # If we need the actual holdings data, we'd need a separate fetch method
                except Exception as e:
                    logger.warning(f"Could not fetch investment holdings: {e}")
            
            # 5. Get Investment Transactions data (only if we have a linked account)
            investment_transactions = []
            if linked_accounts.exists():
                try:
                    # Use the first linked account for investment transactions
                    first_account = linked_accounts.first()
                    tx_count = service._sync_investment_transactions(first_account, access_token, days_back=90)
                    # Note: _sync_investment_transactions returns count, not data
                    # If we need the actual transaction data, we'd need a separate fetch method
                except Exception as e:
                    logger.warning(f"Could not fetch investment transactions: {e}")
            
            if linked_accounts.exists() and identity_data:
                first_account = linked_accounts.first()
                # Store identity in metadata if not already present
                if 'plaid_identity' not in first_account.metadata:
                    first_account.metadata['plaid_identity'] = identity_data
                    first_account.save(update_fields=['metadata'])
                    logger.info(f"Stored Plaid identity data for user {user.id}")
            
            # Store all fetched data in a cache/session for immediate access
            # This allows web pages to access data immediately without waiting for DB sync
            from django.core.cache import cache
            
            # Convert all enum types to strings before caching
            def convert_enums_for_cache(obj):
                if isinstance(obj, dict):
                    return {k: convert_enums_for_cache(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums_for_cache(item) for item in obj]
                elif hasattr(obj, 'value') and not isinstance(obj, (str, int, float, bool, type(None))):
                    return str(obj.value)
                elif type(obj).__name__ in ['AccountType', 'AccountSubtype', 'CountryCode', 'Products']:
                    return str(obj.value) if hasattr(obj, 'value') else str(obj)
                return obj
            
            cache_key = f"plaid_data_{user.id}"
            cache_data = {
                'identity': convert_enums_for_cache(identity_data),
                'accounts': convert_enums_for_cache(accounts_data),
                'transactions': convert_enums_for_cache(transactions_data),
                'investment_holdings': convert_enums_for_cache(investment_holdings),
                'investment_transactions': convert_enums_for_cache(investment_transactions),
                'fetched_at': timezone.now().isoformat(),
            }
            cache.set(cache_key, cache_data, timeout=3600)  # Cache for 1 hour
            
            logger.info(f"Successfully fetched and cached Plaid data from APIs for user {user.id}")
            
            # Trigger background sync for persistence
            from .tasks import sync_linked_account
            for account in linked_accounts:
                try:
                    sync_linked_account.delay(account.id)
                except Exception as e:
                    logger.error(f"Error triggering sync for account {account.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error distributing Plaid data: {e}", exc_info=True)
    
    @staticmethod
    def get_organized_plaid_data(user, use_api_data: bool = True) -> Dict[str, Any]:
        """
        Get organized Plaid data for a user, organized by page/category.
        Fetches directly from Plaid APIs if available, otherwise uses database.
        
        Args:
            user: The user object
            use_api_data: If True, try to fetch from Plaid APIs first, then fall back to DB
        
        Returns:
            Data structure that web pages can use to auto-populate fields.
        """
        from .models import AggregationProvider
        from decimal import Decimal
        from django.core.cache import cache
        
        provider = AggregationProvider.objects.filter(name='plaid', is_active=True).first()
        if not provider:
            return {}
        
        # Try to get cached API data first
        accounts_data = []
        transactions_data = []
        identity_data = {}
        investment_holdings = []
        investment_transactions = []
        
        if use_api_data:
            cache_key = f"plaid_data_{user.id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.info(f"Using cached Plaid API data for user {user.id}")
                accounts_data = cached_data.get('accounts', [])
                transactions_data = cached_data.get('transactions', [])
                identity_data = cached_data.get('identity', {})
                investment_holdings = cached_data.get('investment_holdings', [])
                investment_transactions = cached_data.get('investment_transactions', [])
            else:
                # Try to fetch directly from Plaid APIs
                linked_accounts = LinkedAccount.objects.filter(
                    user=user,
                    provider=provider,
                    status='active'
                ).first()
                
                if linked_accounts:
                    try:
                        from .encryption import decrypt_token
                        access_token = decrypt_token(linked_accounts.access_token)
                        service = PlaidAggregationService(provider)
                        
                        # Fetch from APIs
                        identity_data = service.get_identity(access_token)
                        accounts_data = service._fetch_accounts(access_token)
                        
                        # Fetch transactions
                        from datetime import timedelta
                        from plaid.model.transactions_get_request import TransactionsGetRequest
                        start_date = (timezone.now() - timedelta(days=90)).date()
                        end_date = timezone.now().date()
                        request = TransactionsGetRequest(
                            access_token=access_token,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        response = service.client.transactions_get(request)
                        transactions = response.transactions if hasattr(response, 'transactions') else response.get('transactions', [])
                        transactions_data = []
                        for tx in transactions:
                            if hasattr(tx, 'transaction_id'):
                                # Convert category list - handle enum types
                                category = getattr(tx, 'category', [])
                                category_list = []
                                if category:
                                    for cat in category:
                                        if hasattr(cat, 'value'):
                                            category_list.append(str(cat.value))
                                        else:
                                            category_list.append(str(cat))
                                
                                # Handle date
                                tx_date = getattr(tx, 'date', None)
                                if tx_date and hasattr(tx_date, 'isoformat'):
                                    tx_date = tx_date.isoformat()
                                elif tx_date:
                                    tx_date = str(tx_date)
                                
                                transactions_data.append({
                                    'transaction_id': str(getattr(tx, 'transaction_id', '')),
                                    'amount': float(getattr(tx, 'amount', 0)),
                                    'date': tx_date,
                                    'name': str(getattr(tx, 'name', '')),
                                    'merchant_name': str(getattr(tx, 'merchant_name', '')),
                                    'category': category_list,
                                    'account_id': str(getattr(tx, 'account_id', '')),
                                    'pending': bool(getattr(tx, 'pending', False)),
                                })
                            else:
                                # Already a dict, ensure all values are JSON-serializable
                                tx_dict = dict(tx) if hasattr(tx, '__dict__') else tx
                                transactions_data.append(tx_dict)
                        
                        logger.info(f"Fetched fresh data from Plaid APIs for user {user.id}")
                    except Exception as e:
                        logger.warning(f"Could not fetch from APIs, using DB: {e}")
                        use_api_data = False
        
        # Fall back to database if API data not available
        if not accounts_data or not use_api_data:
            linked_accounts = LinkedAccount.objects.filter(
                user=user,
                provider=provider,
                status='active'
            ).select_related('provider').prefetch_related('balances')
            
            if not linked_accounts.exists():
                return {}
            
            # Get identity data from first account metadata
            first_account = linked_accounts.first()
            if first_account.metadata.get('plaid_identity'):
                identity_data = first_account.metadata['plaid_identity']
            
            # Convert linked accounts to accounts_data format
            accounts_data = []
            for account in linked_accounts:
                latest_balance = account.balances.first()
                # Convert subtype to string if it's an enum
                subtype = account.account_subtype
                if subtype and hasattr(subtype, 'value'):
                    subtype = str(subtype.value)
                elif subtype:
                    subtype = str(subtype)
                else:
                    subtype = ''
                
                accounts_data.append({
                    'account_id': str(account.provider_account_id) if account.provider_account_id else '',
                    'name': str(account.account_name) if account.account_name else '',
                    'type': str(account.account_type) if account.account_type else '',
                    'subtype': subtype,
                    'mask': str(account.account_number_masked) if account.account_number_masked else '',
                    'balances': {
                        'current': float(latest_balance.current_balance) if latest_balance else 0.0,
                        'available': float(latest_balance.available_balance) if latest_balance and latest_balance.available_balance else None,
                        'limit': float(latest_balance.limit) if latest_balance and latest_balance.limit else None,
                        'iso_currency_code': str(latest_balance.currency_code) if latest_balance else 'USD',
                    }
                })
            
            # Get transactions from database
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=90)
            transactions = FinancialTransaction.objects.filter(
                account__in=linked_accounts,
                date__gte=cutoff_date.date()
            )[:100]
            
            transactions_data = [
                {
                    'transaction_id': tx.transaction_id,
                    'amount': float(tx.amount),
                    'date': tx.date.isoformat() if tx.date else None,
                    'name': tx.description,
                    'merchant_name': tx.merchant_name,
                    'category': tx.category.split(', ') if tx.category else [],
                    'account_id': tx.account.provider_account_id,
                    'pending': tx.pending,
                }
                for tx in transactions
            ]
        
        # Organize accounts by type
        organized_data = {
            'identity': identity_data,
            'budget_planner': {
                'checking_balance': Decimal('0'),
                'savings_balance': Decimal('0'),
                'total_cash': Decimal('0'),
                'monthly_income': Decimal('0'),
                'annual_salary': Decimal('0'),
                'monthly_expenses': Decimal('0'),
                'debt_payments': Decimal('0'),
            },
            'stocks_assessment': {
                'investment_amount': Decimal('0'),
                'accounts': [],
            },
            'savings_assessment': {
                'initial_deposit': Decimal('0'),
                'account_name': '',
                'accounts': [],
            },
            'cd_assessment': {
                'cd_amount': Decimal('0'),
                'account_name': '',
                'accounts': [],
            },
            'bond_assessment': {
                'face_value': Decimal('0'),
                'purchase_price': Decimal('0'),
                'account_name': '',
                'accounts': [],
            },
        }
        
        # Process accounts from API data or database
        for account_data in accounts_data:
            # Handle both API format and database format
            if isinstance(account_data, dict):
                account_id = account_data.get('account_id', '')
                account_name = account_data.get('name', 'Unknown Account')
                account_type = account_data.get('type', '')
                
                # Handle type - could be string, enum, or AccountType object
                # Convert enum types to strings safely
                if account_type:
                    try:
                        # Check type name first to avoid triggering __contains__ on Plaid objects
                        type_name = type(account_type).__name__
                        if type_name in ['AccountType', 'AccountSubtype']:
                            try:
                                account_type = str(account_type.value).lower()
                            except (KeyError, AttributeError):
                                account_type = str(account_type).lower()
                        elif hasattr(account_type, 'value'):
                            try:
                                account_type = str(account_type.value).lower()
                            except (KeyError, AttributeError):
                                account_type = str(account_type).lower()
                        else:
                            account_type = str(account_type).lower()
                    except (KeyError, AttributeError):
                        account_type = str(account_type).lower() if account_type else ''
                else:
                    account_type = ''
                
                subtype_raw = account_data.get('subtype', '')
                # Handle subtype - convert enum to string safely
                if subtype_raw:
                    try:
                        # Check type name first to avoid triggering __contains__ on Plaid objects
                        subtype_type_name = type(subtype_raw).__name__
                        if subtype_type_name in ['AccountType', 'AccountSubtype']:
                            try:
                                subtype = str(subtype_raw.value).lower()
                            except (KeyError, AttributeError):
                                subtype = str(subtype_raw).lower()
                        elif hasattr(subtype_raw, 'value'):
                            try:
                                subtype = str(subtype_raw.value).lower()
                            except (KeyError, AttributeError):
                                subtype = str(subtype_raw).lower()
                        else:
                            subtype = str(subtype_raw).lower()
                    except (KeyError, AttributeError):
                        subtype = str(subtype_raw).lower() if subtype_raw else ''
                else:
                    subtype = ''
                
                balances = account_data.get('balances', {})
                balance = Decimal(str(balances.get('current', 0)))
                account_id_for_list = str(account_id) if account_id else ''
                institution_name = account_data.get('institution_name') or account_data.get('official_name') or account_data.get('name') or 'Linked Account'
            else:
                # Database format (LinkedAccount object)
                latest_balance = account_data.balances.first()
                if not latest_balance:
                    continue
                
                balance = latest_balance.current_balance or Decimal('0')
                account_type = account_data.account_type
                account_name = account_data.account_name
                account_id_for_list = account_data.id
                # Database stores account_subtype as CharField, so it's already a string
                subtype = (account_data.account_subtype or '').lower()
                balances = {}
                institution_name = account_data.institution_name
            
            # Budget Planner data
            if account_type == 'depository':
                if 'checking' in subtype or 'depository' in subtype:
                    organized_data['budget_planner']['checking_balance'] += balance
                elif 'savings' in subtype:
                    organized_data['budget_planner']['savings_balance'] += balance
                    # Also add to savings assessment
                    if balance > organized_data['savings_assessment']['initial_deposit']:
                        organized_data['savings_assessment']['initial_deposit'] = balance
                        organized_data['savings_assessment']['account_name'] = str(account_name) if account_name else ''
                        organized_data['savings_assessment']['accounts'].append({
                            'id': str(account_id_for_list) if account_id_for_list else '',
                            'name': str(account_name) if account_name else '',
                            'balance': float(balance),
                        })
            
            # Stocks Assessment data
            elif account_type in ['investment', 'brokerage']:
                organized_data['stocks_assessment']['investment_amount'] += balance
                organized_data['stocks_assessment']['accounts'].append({
                    'id': str(account_id_for_list) if account_id_for_list else '',
                    'name': str(account_name) if account_name else '',
                    'balance': float(balance),
                    'institution': str(institution_name) if institution_name else '',
                    'account_type': account_type,
                    'subtype': subtype,
                })
            
            # CD Assessment data
            elif account_type == 'depository' and 'cd' in subtype:
                if balance > organized_data['cd_assessment']['cd_amount']:
                    organized_data['cd_assessment']['cd_amount'] = balance
                    organized_data['cd_assessment']['account_name'] = str(account_name) if account_name else ''
                    organized_data['cd_assessment']['accounts'].append({
                        'id': str(account_id_for_list) if account_id_for_list else '',
                        'name': str(account_name) if account_name else '',
                        'balance': float(balance),
                    })
            
            # Bond Assessment data
            elif account_type in ['investment', 'brokerage']:
                if balance > organized_data['bond_assessment']['face_value']:
                    organized_data['bond_assessment']['face_value'] = balance
                    organized_data['bond_assessment']['purchase_price'] = balance
                    organized_data['bond_assessment']['account_name'] = str(account_name) if account_name else ''
                    organized_data['bond_assessment']['accounts'].append({
                        'id': str(account_id_for_list) if account_id_for_list else '',
                        'name': str(account_name) if account_name else '',
                        'balance': float(balance),
                    })
            
            # Debt data for budget planner
            elif account_type in ['credit', 'loan']:
                if isinstance(account_data, dict):
                    limit = Decimal(str(balances.get('limit', 0)))
                else:
                    limit = latest_balance.limit or Decimal('0')
                min_payment = max(balance * Decimal('0.02'), Decimal('25'))
                organized_data['budget_planner']['debt_payments'] += min_payment
        
        # Calculate totals
        organized_data['budget_planner']['total_cash'] = (
            organized_data['budget_planner']['checking_balance'] +
            organized_data['budget_planner']['savings_balance']
        )
        
        # Calculate income and expenses from transactions (from API or database)
        if transactions_data:
            income_total = Decimal('0')
            expense_total = Decimal('0')
            transaction_count = 0
            
            for tx in transactions_data:
                if isinstance(tx, dict):
                    tx_amount = Decimal(str(tx.get('amount', 0)))
                else:
                    tx_amount = tx.amount
                
                if tx_amount > 0:
                    income_total += tx_amount
                else:
                    expense_total += abs(tx_amount)
                transaction_count += 1
            
            if transaction_count > 0:
                avg_daily_income = income_total / 90
                avg_daily_expenses = expense_total / 90
                
                organized_data['budget_planner']['monthly_income'] = avg_daily_income * 30
                organized_data['budget_planner']['annual_salary'] = organized_data['budget_planner']['monthly_income'] * 12
                organized_data['budget_planner']['monthly_expenses'] = avg_daily_expenses * 30
        
        # Convert Decimal and enum types to JSON-serializable formats
        def convert_for_json(obj):
            # Handle basic types first
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            
            # Handle Decimal
            if isinstance(obj, Decimal):
                return float(obj)
            
            # Handle datetime
            if isinstance(obj, (datetime, timezone.datetime)):
                return obj.isoformat()
            
            # Handle dict
            if isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            
            # Handle list
            if isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            
            # Handle Plaid enum types - check class name first to avoid triggering __contains__
            obj_type_name = type(obj).__name__
            if obj_type_name in ['AccountType', 'AccountSubtype', 'CountryCode', 'Products']:
                try:
                    # Try to get value attribute safely
                    if hasattr(obj, 'value'):
                        try:
                            return str(obj.value)
                        except (KeyError, AttributeError):
                            pass
                    return str(obj)
                except (KeyError, AttributeError):
                    return str(obj)
            
            # Handle other Plaid model objects
            try:
                obj_module = type(obj).__module__
                if obj_module and 'plaid' in str(obj_module).lower():
                    # Try to convert Plaid model to dict safely
                    try:
                        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict', None)):
                            return convert_for_json(obj.dict())
                    except (KeyError, AttributeError, TypeError):
                        pass
                    # Fallback: try to get attributes without triggering __contains__
                    try:
                        if hasattr(obj, '__dict__'):
                            return {k: convert_for_json(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
                    except (KeyError, AttributeError, TypeError):
                        pass
                    return str(obj)
            except (KeyError, AttributeError, TypeError):
                pass
            
            # Handle other objects with __dict__
            try:
                if hasattr(obj, '__dict__'):
                    return {k: convert_for_json(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            except (KeyError, AttributeError, TypeError):
                pass
            
            # Final fallback: convert to string
            return str(obj)
        
        return convert_for_json(organized_data)
