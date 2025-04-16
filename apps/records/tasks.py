from celery import shared_task
from .models import FinancialDocument
import time

@shared_task
def process_financial_document(document_id):
    """
    Simulate processing a financial document (e.g., parsing, saving to DB).
    """
    try:
        document = FinancialDocument.objects.get(id=document_id)
        # Simulate a long-running task
        time.sleep(10)  # e.g., 10-second delay
        document.processed = True
        document.save()
        return f"Processed document: {document.name}"
    except FinancialDocument.DoesNotExist:
        return "Document not found"