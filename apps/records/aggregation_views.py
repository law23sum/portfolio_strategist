"""
Views for financial data aggregation (account linking, syncing, etc.)
"""

import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

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
from .aggregation_service import PlaidAggregationService, AggregationServiceFactory, categorize_and_connect_account
from .encryption import encrypt_token
from .tasks import sync_linked_account
from .plaid_data_distribution import PlaidDataDistributionService

logger = logging.getLogger(__name__)


def convert_to_json_serializable(obj):
    """Convert Plaid enum objects and other non-serializable types to JSON-serializable formats"""
    # Handle Plaid enum types (AccountType, AccountSubtype, etc.)
    if hasattr(obj, 'value') and not isinstance(obj, (str, int, float, bool, type(None))):
        # Plaid enum objects have a 'value' attribute
        try:
            return str(obj.value)
        except:
            return str(obj)
    # Handle enum types directly (check class name)
    elif type(obj).__name__ in ['AccountType', 'AccountSubtype', 'CountryCode', 'Products']:
        try:
            return str(obj.value) if hasattr(obj, 'value') else str(obj)
        except:
            return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (type(None), str, int, float, bool)):
        return obj
    elif hasattr(obj, '__dict__'):
        # Handle other objects that might have attributes
        try:
            return {k: convert_to_json_serializable(v) for k, v in obj.__dict__.items()}
        except:
            return str(obj)
    return obj


@login_required
def link_account_view(request):
    """View for initiating account linking flow - Online Financial Accounts"""
    # Ensure Plaid always exists in the database (even if not configured)
    plaid_provider, _ = AggregationProvider.objects.get_or_create(
        name='plaid',
        defaults={
            'display_name': 'Plaid',
            'is_active': True,
            'environment': 'sandbox'
        }
    )
    # Ensure it's active even if it was created before
    if not plaid_provider.is_active:
        plaid_provider.is_active = True
        plaid_provider.save()
    
    providers = list(AggregationProvider.objects.filter(is_active=True))
    linked_accounts = LinkedAccount.objects.filter(user=request.user).select_related('provider')
    
    # Check if Plaid provider has credentials
    if not plaid_provider.api_key or not plaid_provider.api_secret:
        # Provider exists but missing credentials
        from django.contrib import messages
        messages.warning(
            request,
            'Plaid provider is configured but missing credentials. '
            'Please run: python manage.py bootstrap_plaid'
        )
    
    # Get aggregate financial data
    from .financial_aggregation import (
        DashboardAggregationService,
        BudgetAggregationService,
        InvestmentAggregationService,
        DebtAggregationService,
    )
    
    financial_summary = DashboardAggregationService.get_user_financial_summary(request.user)
    budget_data = BudgetAggregationService.get_user_budget_data(request.user, days=30)
    investment_data = InvestmentAggregationService.get_user_investment_data(request.user)
    debt_data = DebtAggregationService.get_user_debt_data(request.user)
    
    return render(request, 'records/link_account.html', {
        'providers': providers,
        'linked_accounts': linked_accounts,
        'financial_summary': financial_summary,
        'budget_data': budget_data,
        'investment_data': investment_data,
        'debt_data': debt_data,
        'active_tab': 'records_link_account',
        'page_title': 'Online Financial Accounts',
    })


@login_required
@require_http_methods(["POST"])
def create_link_token(request):
    """Create a Plaid Link token for OAuth flow"""
    try:
        provider_id = request.POST.get('provider_id')
        if not provider_id:
            return JsonResponse({
                'error': 'No provider specified. Please run: python manage.py bootstrap_plaid'
            }, status=400)
        
        try:
            provider = AggregationProvider.objects.get(id=provider_id, is_active=True)
        except AggregationProvider.DoesNotExist:
            return JsonResponse({
                'error': 'Plaid provider not configured. Please run: python manage.py bootstrap_plaid'
            }, status=404)
        
        if provider.name != 'plaid':
            return JsonResponse({'error': 'Only Plaid is currently supported'}, status=400)
        
        # Check if provider has credentials
        if not provider.api_key or not provider.api_secret:
            return JsonResponse({
                'error': 'Plaid credentials not configured. Please run: python manage.py bootstrap_plaid'
            }, status=400)
        
        service = PlaidAggregationService(provider)
        link_token_data = service.create_link_token(
            user_id=str(request.user.id),
            user_email=request.user.email
        )
        
        return JsonResponse(link_token_data)
    except ValueError as e:
        # Handle "No active Plaid provider found" error
        logger.error(f"Error creating link token: {e}")
        return JsonResponse({
            'error': f'Plaid not configured: {str(e)}. Please run: python manage.py bootstrap_plaid'
        }, status=500)
    except ImportError as e:
        logger.error(f"Error creating link token: {e}")
        return JsonResponse({
            'error': 'Plaid Python SDK not installed. Install with: pip install plaid-python'
        }, status=500)
    except Exception as e:
        logger.error(f"Error creating link token: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def exchange_token(request):
    """Exchange public token for access token and create linked account"""
    try:
        data = json.loads(request.body)
        public_token = data.get('public_token')
        provider_id = data.get('provider_id')
        institution_id = data.get('institution_id')
        institution_name = data.get('institution_name')
        
        if not all([public_token, provider_id, institution_id, institution_name]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        provider = get_object_or_404(AggregationProvider, id=provider_id, is_active=True)
        
        if provider.name != 'plaid':
            return JsonResponse({'error': 'Only Plaid is currently supported'}, status=400)
        
        service = PlaidAggregationService(provider)
        
        # Exchange public token for access token
        access_token = service.exchange_public_token(public_token)
        item_id = service.get_item_id(access_token)
        
        # Fetch identity and accounts to get account details
        identity_data = {}
        try:
            identity_data = service.get_identity(access_token)
        except Exception as identity_error:
            logger.warning("Unable to fetch Plaid identity data during exchange: %s", identity_error)

        accounts_data = service._fetch_accounts(access_token)
        
        # Create linked accounts for each account returned
        created_accounts = []
        categorized_accounts = {
            'budget': [],
            'debt': [],
            'investment': [],
            'retirement': [],
            'other': []
        }
        
        for account_data in accounts_data:
            account_type_map = {
                'depository': 'depository',
                'credit': 'credit',
                'loan': 'loan',
                'investment': 'investment',
                'brokerage': 'brokerage',
                'other': 'other',
            }
            
            # Check if this is a retirement account based on subtype
            # Handle subtype - convert enum to string safely
            subtype_raw = account_data.get('subtype', '')
            if subtype_raw:
                if hasattr(subtype_raw, 'value'):
                    account_subtype_lower = str(subtype_raw.value).lower()
                    account_subtype_stored = str(subtype_raw.value)
                elif type(subtype_raw).__name__ in ['AccountType', 'AccountSubtype']:
                    account_subtype_lower = str(subtype_raw.value).lower() if hasattr(subtype_raw, 'value') else str(subtype_raw).lower()
                    account_subtype_stored = str(subtype_raw.value) if hasattr(subtype_raw, 'value') else str(subtype_raw)
                else:
                    account_subtype_lower = str(subtype_raw).lower()
                    account_subtype_stored = str(subtype_raw)
            else:
                account_subtype_lower = ''
                account_subtype_stored = ''
            
            # Handle type - convert enum to string safely
            type_raw = account_data.get('type', '')
            if type_raw:
                if hasattr(type_raw, 'value'):
                    account_type = str(type_raw.value).lower()
                elif type(type_raw).__name__ in ['AccountType', 'AccountSubtype']:
                    account_type = str(type_raw.value).lower() if hasattr(type_raw, 'value') else str(type_raw).lower()
                else:
                    account_type = str(type_raw).lower()
            else:
                account_type = ''
            
            # Identify retirement accounts by subtype (401k, ira, pension, etc.)
            retirement_keywords = ['401k', '403b', '457', 'ira', 'roth', 'pension', 'retirement', 'sep', 'simple']
            is_retirement = any(keyword in account_subtype_lower for keyword in retirement_keywords)
            
            # Override account type if it's a retirement account
            if is_retirement and account_type in ['investment', 'brokerage']:
                account_type = 'retirement'
            
            # Encrypt access token before storing
            encrypted_token = encrypt_token(access_token)
            
            # Convert account_data to JSON-serializable format for metadata storage
            serializable_metadata = convert_to_json_serializable(account_data)
            
            linked_account, created = LinkedAccount.objects.get_or_create(
                user=request.user,
                provider=provider,
                provider_account_id=account_data['account_id'],
                defaults={
                    'provider_item_id': item_id,
                    'access_token': encrypted_token,
                    'institution_name': institution_name,
                    'institution_id': institution_id,
                    'account_name': account_data.get('name', 'Unknown Account'),
                    'account_type': 'retirement' if is_retirement else account_type_map.get(account_type, 'other'),
                    'account_subtype': account_subtype_stored,
                    'account_number_masked': account_data.get('mask', ''),
                    'status': 'pending',
                    'metadata': serializable_metadata,
                }
            )
            
            if created:
                created_accounts.append(linked_account)
                
                # Categorize and connect the account
                category_info = categorize_and_connect_account(linked_account)
                category = category_info.get('category', 'other')
                if category in categorized_accounts:
                    categorized_accounts[category].append({
                        'account_id': linked_account.id,
                        'account_name': linked_account.account_name,
                        'category_info': category_info
                    })
                
                # Trigger initial sync (this will also create debt accounts if needed)
                sync_linked_account.delay(linked_account.id)
        
        # Trigger Plaid data distribution so downstream pages have fresh data
        try:
            PlaidDataDistributionService.distribute_plaid_data(
                user=request.user,
                access_token=access_token,
                identity_data=identity_data,
            )
        except Exception as distribution_error:
            logger.warning(
                "Plaid data distribution failed after account link for user %s: %s",
                request.user.id,
                distribution_error,
            )

        return JsonResponse({
            'success': True,
            'accounts_created': len(created_accounts),
            'account_ids': [acc.id for acc in created_accounts],
            'categorized': {
                'budget': len(categorized_accounts['budget']),
                'debt': len(categorized_accounts['debt']),
                'investment': len(categorized_accounts['investment']),
                'retirement': len(categorized_accounts['retirement']),
                'other': len(categorized_accounts['other']),
            },
            'categories': categorized_accounts,
        })
        
    except Exception as e:
        logger.error(f"Error exchanging token: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def linked_accounts_view(request):
    """View showing all linked accounts"""
    linked_accounts = LinkedAccount.objects.filter(
        user=request.user
    ).select_related('provider').prefetch_related('balances').order_by('-created_at')
    
    # Get latest balances for each account
    accounts_with_balances = []
    for account in linked_accounts:
        latest_balance = account.balances.first()
        accounts_with_balances.append({
            'account': account,
            'latest_balance': latest_balance,
        })
    
    return render(request, 'records/linked_accounts.html', {
        'accounts_with_balances': accounts_with_balances,
        'active_tab': 'records_link_account',
    })


@login_required
@require_http_methods(["POST"])
def sync_account(request, account_id):
    """Manually trigger sync for a linked account"""
    linked_account = get_object_or_404(LinkedAccount, id=account_id, user=request.user)
    
    try:
        # Trigger async sync
        sync_linked_account.delay(linked_account.id)
        return JsonResponse({'success': True, 'message': 'Sync started'})
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def disconnect_account(request, account_id):
    """Disconnect a linked account"""
    linked_account = get_object_or_404(LinkedAccount, id=account_id, user=request.user)
    
    linked_account.status = 'disconnected'
    linked_account.save()
    
    return JsonResponse({'success': True, 'message': 'Account disconnected'})


@login_required
def account_detail_view(request, account_id):
    """View showing detailed information for a linked account"""
    linked_account = get_object_or_404(LinkedAccount, id=account_id, user=request.user)
    
    # Get latest balance
    latest_balance = linked_account.balances.first()
    
    # Get recent transactions
    recent_transactions = linked_account.transactions.all()[:50]
    
    # Get investment holdings if applicable
    holdings = linked_account.holdings.all() if linked_account.account_type in ['investment', 'brokerage', 'retirement'] else []
    
    # Get sync history
    sync_logs = linked_account.sync_logs.all()[:10]
    
    # Check if this is an API request (JSON response)
    accept_header = request.headers.get('Accept', '')
    if 'application/json' in accept_header or request.GET.get('format') == 'json':
        # Serialize data for API response
        transactions_data = []
        for transaction in recent_transactions:
            transactions_data.append({
                'id': transaction.id,
                'date': str(transaction.date),
                'amount': str(transaction.amount),
                'description': transaction.description or '',
                'category': transaction.category or 'Uncategorized',
                'transaction_type': transaction.transaction_type,
            })
        
        holdings_data = []
        for holding in holdings:
            holdings_data.append({
                'id': holding.id,
                'security_name': holding.security_name or '',
                'security_ticker': holding.security_ticker or '',
                'quantity': str(holding.quantity),
                'value': str(holding.value),
                'cost_basis': str(holding.cost_basis) if holding.cost_basis else None,
                'as_of_date': str(holding.as_of_date),
            })
        
        return JsonResponse({
            'account': {
                'id': linked_account.id,
                'account_name': linked_account.account_name,
                'account_type': linked_account.account_type,
                'institution_name': linked_account.institution_name,
                'account_number_masked': linked_account.account_number_masked,
                'status': linked_account.status,
            },
            'latest_balance': {
                'current_balance': str(latest_balance.current_balance) if latest_balance else None,
                'available_balance': str(latest_balance.available_balance) if latest_balance and latest_balance.available_balance else None,
                'limit': str(latest_balance.limit) if latest_balance and latest_balance.limit else None,
                'balance_date': str(latest_balance.balance_date) if latest_balance else None,
            } if latest_balance else None,
            'recent_transactions': transactions_data,
            'holdings': holdings_data,
        })
    
    return render(request, 'records/account_detail.html', {
        'linked_account': linked_account,
        'latest_balance': latest_balance,
        'recent_transactions': recent_transactions,
        'holdings': holdings,
        'sync_logs': sync_logs,
        'active_tab': 'records_link_account',
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def plaid_oauth_callback(request):
    """Handle OAuth callback from Plaid"""
    try:
        # OAuth callback typically includes oauth_state_id and error (if any)
        oauth_state_id = request.GET.get('oauth_state_id') or request.POST.get('oauth_state_id')
        error = request.GET.get('error') or request.POST.get('error')
        
        if error:
            logger.error(f"Plaid OAuth error: {error}")
            return JsonResponse({'error': error}, status=400)
        
        if not oauth_state_id:
            return JsonResponse({'error': 'Missing oauth_state_id'}, status=400)
        
        # The OAuth flow is typically handled client-side
        # This endpoint just acknowledges the callback
        logger.info(f"Plaid OAuth callback received with state: {oauth_state_id}")
        return JsonResponse({'status': 'ok', 'oauth_state_id': oauth_state_id}, status=200)
        
    except Exception as e:
        logger.error(f"Error processing Plaid OAuth callback: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def plaid_webhook(request):
    """Handle webhooks from Plaid"""
    try:
        data = json.loads(request.body)
        webhook_type = data.get('webhook_type')
        webhook_code = data.get('webhook_code')
        item_id = data.get('item_id')
        
        logger.info(f"Received Plaid webhook: {webhook_type} - {webhook_code} for item {item_id}")
        
        # Find linked account by item_id
        linked_account = LinkedAccount.objects.filter(provider_item_id=item_id).first()
        
        if not linked_account:
            logger.warning(f"No linked account found for item_id: {item_id}")
            return JsonResponse({'status': 'ignored'}, status=200)
        
        # Handle different webhook types
        if webhook_type == 'TRANSACTIONS':
            if webhook_code in ['INITIAL_UPDATE', 'HISTORICAL_UPDATE', 'DEFAULT_UPDATE']:
                # Trigger sync for new transactions
                sync_linked_account.delay(linked_account.id)
        elif webhook_type == 'ITEM':
            if webhook_code == 'ERROR':
                linked_account.status = 'error'
                linked_account.error_message = data.get('error', {}).get('error_message', 'Unknown error')
                linked_account.save()
            elif webhook_code == 'PENDING_EXPIRATION':
                # Token is expiring, notify user
                logger.warning(f"Access token expiring for account {linked_account.id}")
        
        return JsonResponse({'status': 'processed'}, status=200)
        
    except Exception as e:
        logger.error(f"Error processing Plaid webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# API endpoints for financial aggregation data
@login_required
@require_http_methods(["GET"])
def dashboard_summary_api(request):
    """API endpoint for dashboard financial summary"""
    from .financial_aggregation import DashboardAggregationService
    
    try:
        summary = DashboardAggregationService.get_user_financial_summary(request.user)
        
        # Serialize recent transactions
        recent_transactions = []
        for transaction in summary.get('recent_transactions', [])[:10]:
            recent_transactions.append({
                'id': transaction.id,
                'date': str(transaction.date),
                'amount': str(transaction.amount),
                'description': transaction.description or '',
                'category': transaction.category or 'Uncategorized',
                'account_name': transaction.account.account_name if transaction.account else '',
                'transaction_type': transaction.transaction_type,
            })
        
        return JsonResponse({
            'net_worth': summary.get('net_worth', 0),
            'total_assets': summary.get('total_assets', 0),
            'total_liabilities': summary.get('total_liabilities', 0),
            'total_cash': summary.get('total_cash', 0),
            'total_investments': summary.get('total_investments', 0),
            'account_counts': summary.get('account_counts', {}),
            'linked_accounts_count': summary.get('linked_accounts_count', 0),
            'accounts_with_errors': summary.get('accounts_with_errors', 0),
            'recent_transactions': recent_transactions,
        })
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def budget_data_api(request):
    """API endpoint for budget aggregation data"""
    from .financial_aggregation import BudgetAggregationService
    
    try:
        days = int(request.GET.get('days', 30))
        budget_data = BudgetAggregationService.get_user_budget_data(request.user, days=days)
        
        # Serialize account balances
        account_balances = []
        for item in budget_data.get('account_balances', []):
            account = item['account']
            balance = item['balance']
            account_balances.append({
                'account_id': account.id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'balance': str(balance.current_balance) if balance else '0.00',
                'available_balance': str(balance.available_balance) if balance and balance.available_balance else None,
            })
        
        # Serialize recent transactions
        recent_transactions = []
        for transaction in budget_data.get('recent_transactions', [])[:20]:
            recent_transactions.append({
                'id': transaction.id,
                'date': str(transaction.date),
                'amount': str(transaction.amount),
                'description': transaction.description or '',
                'category': transaction.category or 'Uncategorized',
                'account_name': transaction.account.account_name if transaction.account else '',
                'transaction_type': transaction.transaction_type,
            })
        
        return JsonResponse({
            'total_balance': str(budget_data.get('total_balance', 0)),
            'total_available': str(budget_data.get('total_available', 0)),
            'total_credit_limit': str(budget_data.get('total_credit_limit', 0)),
            'income': str(budget_data.get('income', 0)),
            'expenses': str(budget_data.get('expenses', 0)),
            'spending_by_category': [
                {
                    'category': cat,
                    'amount': str(data['amount']),
                    'count': data['count'],
                }
                for cat, data in budget_data.get('spending_by_category', {}).items()
            ],
            'account_balances': account_balances,
            'recent_transactions': recent_transactions,
        })
    except Exception as e:
        logger.error(f"Error getting budget data: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def investment_data_api(request):
    """API endpoint for investment aggregation data"""
    from .financial_aggregation import InvestmentAggregationService
    
    try:
        investment_data = InvestmentAggregationService.get_user_investment_data(request.user)
        
        # Serialize holdings
        holdings = []
        for holding in investment_data.get('holdings', [])[:50]:
            holdings.append({
                'id': holding.id,
                'security_name': holding.security_name or '',
                'security_ticker': holding.security_ticker or '',
                'quantity': str(holding.quantity),
                'value': str(holding.value),
                'cost_basis': str(holding.cost_basis) if holding.cost_basis else '0.00',
                'account_name': holding.account.account_name if holding.account else '',
                'as_of_date': str(holding.as_of_date),
            })
        
        # Serialize investment accounts
        investment_accounts = []
        for account in investment_data.get('investment_accounts', []):
            investment_accounts.append({
                'id': account.id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'institution_name': account.institution_name,
            })
        
        return JsonResponse({
            'total_portfolio_value': str(investment_data.get('total_portfolio_value', 0)),
            'total_cost_basis': str(investment_data.get('total_cost_basis', 0)),
            'holdings_by_security': [
                {
                    'security_name': sec,
                    'quantity': str(data['quantity']),
                    'value': str(data['value']),
                    'cost_basis': str(data['cost_basis']),
                }
                for sec, data in investment_data.get('holdings_by_security', {}).items()
            ],
            'holdings': holdings,
            'investment_accounts': investment_accounts,
        })
    except Exception as e:
        logger.error(f"Error getting investment data: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def debt_data_api(request):
    """API endpoint for debt aggregation data"""
    from .financial_aggregation import DebtAggregationService
    
    try:
        debt_data = DebtAggregationService.get_user_debt_data(request.user)
        
        # Serialize debt accounts
        debt_accounts = []
        for account in debt_data.get('debt_accounts', []):
            debt_accounts.append({
                'id': account.id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'current_balance': str(account.current_balance),
                'minimum_payment': str(account.minimum_payment) if account.minimum_payment else None,
                'interest_rate': str(account.interest_rate) if account.interest_rate else None,
                'due_date': str(account.due_date) if account.due_date else None,
            })
        
        return JsonResponse({
            'total_debt': str(debt_data.get('total_debt', 0)),
            'total_minimum_payments': str(debt_data.get('total_minimum_payments', 0)),
            'total_interest_rate': str(debt_data.get('total_interest_rate', 0)),
            'debt_by_type': [
                {
                    'type': debt_type,
                    'total': str(data['total']),
                    'count': data['count'],
                }
                for debt_type, data in debt_data.get('debt_by_type', {}).items()
            ],
            'debt_accounts': debt_accounts,
            'accounts_count': debt_data.get('accounts_count', 0),
        })
    except Exception as e:
        logger.error(f"Error getting debt data: {e}")
        return JsonResponse({'error': str(e)}, status=500)
