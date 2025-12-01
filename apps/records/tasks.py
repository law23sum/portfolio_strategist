from celery import shared_task
from .models import FinancialDocument, LinkedAccount
from .aggregation_service import PlaidAggregationService, AggregationServiceFactory
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_financial_document(document_id):
    """
    Simulate processing a financial document (e.g., parsing, saving to DB).
    """
    import time
    try:
        document = FinancialDocument.objects.get(id=document_id)

        # Simulate a long-running task
        time.sleep(10)  # e.g., 10-second delay
        document.processed = True
        document.save()
        return f"Processed document: {document.name}"
    except FinancialDocument.DoesNotExist:
        return "Document not found"


@shared_task
def sync_linked_account(linked_account_id):
    """
    Sync data for a linked account from aggregation provider.
    """
    try:
        linked_account = LinkedAccount.objects.get(id=linked_account_id)
        
        # Create appropriate service for provider
        service = AggregationServiceFactory.create_service(linked_account.provider)
        
        # Perform sync
        sync_log = service.sync_accounts(linked_account)
        
        logger.info(f"Synced account {linked_account_id}: {sync_log.status}")
        return f"Synced account {linked_account_id}: {sync_log.status}"
        
    except LinkedAccount.DoesNotExist:
        logger.error(f"Linked account {linked_account_id} not found")
        return f"Linked account {linked_account_id} not found"
    except Exception as e:
        logger.error(f"Error syncing account {linked_account_id}: {e}")
        raise


@shared_task
def sync_all_accounts():
    """
    Sync all active linked accounts.
    This should be scheduled to run periodically (e.g., every 6 hours).
    """
    active_accounts = LinkedAccount.objects.filter(status='active')
    count = 0
    
    for account in active_accounts:
        try:
            sync_linked_account.delay(account.id)
            count += 1
        except Exception as e:
            logger.error(f"Error queuing sync for account {account.id}: {e}")
    
    return f"Queued sync for {count} accounts"
