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
from .aggregation_service import PlaidAggregationService, AggregationServiceFactory
from .encryption import encrypt_token
from .tasks import sync_linked_account

logger = logging.getLogger(__name__)


@login_required
def link_account_view(request):
    """View for initiating account linking flow - Online Financial Accounts"""
    providers = AggregationProvider.objects.filter(is_active=True)
    linked_accounts = LinkedAccount.objects.filter(user=request.user).select_related('provider')
    
    return render(request, 'records/link_account.html', {
        'providers': providers,
        'linked_accounts': linked_accounts,
        'active_tab': 'records_link_account',
        'page_title': 'Online Financial Accounts',
    })


@login_required
@require_http_methods(["POST"])
def create_link_token(request):
    """Create a Plaid Link token for OAuth flow"""
    try:
        provider_id = request.POST.get('provider_id')
        provider = get_object_or_404(AggregationProvider, id=provider_id, is_active=True)
        
        if provider.name != 'plaid':
            return JsonResponse({'error': 'Only Plaid is currently supported'}, status=400)
        
        service = PlaidAggregationService(provider)
        link_token_data = service.create_link_token(
            user_id=str(request.user.id),
            user_email=request.user.email
        )
        
        return JsonResponse(link_token_data)
    except Exception as e:
        logger.error(f"Error creating link token: {e}")
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
        
        # Fetch accounts to get account details
        accounts_data = service._fetch_accounts(access_token)
        
        # Create linked accounts for each account returned
        created_accounts = []
        for account_data in accounts_data:
            account_type_map = {
                'depository': 'depository',
                'credit': 'credit',
                'loan': 'loan',
                'investment': 'investment',
                'brokerage': 'brokerage',
                'other': 'other',
            }
            
            # Encrypt access token before storing
            encrypted_token = encrypt_token(access_token)
            
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
                    'account_type': account_type_map.get(account_data.get('type', '').lower(), 'other'),
                    'account_subtype': account_data.get('subtype', ''),
                    'account_number_masked': account_data.get('mask', ''),
                    'status': 'pending',
                    'metadata': account_data,
                }
            )
            
            if created:
                created_accounts.append(linked_account)
                # Trigger initial sync
                sync_linked_account.delay(linked_account.id)
        
        return JsonResponse({
            'success': True,
            'accounts_created': len(created_accounts),
            'account_ids': [acc.id for acc in created_accounts],
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
    
    return render(request, 'records/account_detail.html', {
        'linked_account': linked_account,
        'latest_balance': latest_balance,
        'recent_transactions': recent_transactions,
        'holdings': holdings,
        'sync_logs': sync_logs,
        'active_tab': 'records_link_account',
    })


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

