import csv
from celery import shared_task
from django.conf import settings

from apps.chat.models import Chat, ChatMessage, MessageTypes
from apps.chat.serializers import ChatMessageSerializer
from apps.chat.utils import get_openai_client


def get_user_context(user):
    """Get user's personal details and Plaid account data for context"""
    context_parts = []
    
    # User personal details
    user_details = {
        "name": user.get_full_name() or user.username,
        "email": user.email,
    }
    context_parts.append(f"User Information: {user_details}")
    
    # Personal details from FinancialDocument fields
    try:
        from apps.records.models import FinancialDocument, ExtractedField
        
        # Get all financial documents with extracted fields
        documents = FinancialDocument.objects.filter(user=user, processed=True)
        if documents.exists():
            personal_details = []
            for doc in documents:
                fields = ExtractedField.objects.filter(document=doc)
                if fields.exists():
                    doc_details = {
                        "document_type": doc.record_type,
                        "subcategory": doc.sub_record_type,
                        "year": doc.year,
                        "extracted_fields": {}
                    }
                    for field in fields:
                        doc_details["extracted_fields"][field.field_name] = field.field_value
                    personal_details.append(doc_details)
            
            if personal_details:
                context_parts.append(f"Personal Details from Documents: {personal_details}")
    except ImportError:
        pass
    
    # Plaid/Linked accounts data
    try:
        from apps.records.models import LinkedAccount, AccountBalance, FinancialTransaction, InvestmentHolding
        
        linked_accounts = LinkedAccount.objects.filter(user=user, status='active')
        if linked_accounts.exists():
            accounts_info = []
            for account in linked_accounts:
                account_info = {
                    "institution": account.institution_name,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "account_subtype": account.account_subtype,
                    "account_number_masked": account.account_number_masked,
                }
                # Get latest balance
                latest_balance = AccountBalance.objects.filter(account=account).order_by('-balance_date').first()
                if latest_balance:
                    account_info["balance"] = str(latest_balance.current_balance)
                    account_info["balance_date"] = str(latest_balance.balance_date)
                accounts_info.append(account_info)
            context_parts.append(f"Linked Financial Accounts (Plaid): {accounts_info}")
            
            # Recent transactions summary
            recent_transactions = FinancialTransaction.objects.filter(
                account__user=user
            ).order_by('-date')[:20]
            if recent_transactions.exists():
                transactions_summary = [
                    {
                        "date": str(t.date),
                        "amount": str(t.amount),
                        "description": t.description[:100],
                        "category": t.category,
                        "merchant": t.merchant_name,
                        "account": t.account.account_name
                    }
                    for t in recent_transactions
                ]
                context_parts.append(f"Recent Transactions: {transactions_summary}")
            
            # Investment holdings summary
            holdings = InvestmentHolding.objects.filter(account__user=user).order_by('-as_of_date')
            if holdings.exists():
                holdings_summary = [
                    {
                        "security_name": h.security_name,
                        "security_ticker": h.security_ticker,
                        "security_type": h.security_type,
                        "quantity": str(h.quantity),
                        "price": str(h.price) if h.price else "N/A",
                        "value": str(h.value),
                        "cost_basis": str(h.cost_basis) if h.cost_basis else "N/A",
                        "account": h.account.account_name
                    }
                    for h in holdings[:20]
                ]
                context_parts.append(f"Investment Holdings: {holdings_summary}")
    except ImportError:
        pass
    
    return "\n\n".join(context_parts)


def extract_file_content(message):
    """Extract text content from uploaded files (CSV, PDF)"""
    if not message.attachment:
        return None
    
    file_path = message.attachment.path
    file_name = message.attachment.name.lower()
    content = None
    
    try:
        if message.attachment_type == 'csv':
            # Read CSV content
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    # Convert to readable format
                    content = "CSV File Content:\n"
                    for i, row in enumerate(rows[:100]):  # Limit to first 100 rows
                        content += f"Row {i+1}: {', '.join(str(cell) for cell in row)}\n"
                    if len(rows) > 100:
                        content += f"... (showing first 100 of {len(rows)} rows)\n"
        
        elif message.attachment_type == 'pdf':
            # Extract PDF text
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text_parts = []
                for page_num, page in enumerate(reader.pages[:10]):  # Limit to first 10 pages
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"Page {page_num + 1}:\n{page_text}")
                if text_parts:
                    content = "PDF File Content:\n" + "\n\n".join(text_parts)
                    if len(reader.pages) > 10:
                        content += f"\n... (showing first 10 of {len(reader.pages)} pages)"
            except ImportError:
                content = f"[PDF file: {message.attachment.name} - PDF processing not available]"
        
        elif message.attachment_type == 'image':
            # For images, we'll just note the attachment
            content = f"[Image file: {message.attachment.name}]"
    
    except Exception as e:
        content = f"[File: {message.attachment.name} - Error reading file: {str(e)}]"
    
    return content


@shared_task(bind=True)
def get_chat_response(self, chat_id: int, message_id: int) -> str:
    from openai import APIError, AuthenticationError
    
    try:
        chat = Chat.objects.get(id=chat_id)
        user_message = ChatMessage.objects.get(id=message_id)
        client = get_openai_client()
        
        # Build messages with user context
        messages = []
        
        # Add system message with user context
        user_context = get_user_context(chat.user)
        if user_context:
            system_message = f"""You are a helpful financial assistant. You have access to the user's financial information:
{user_context}

Use this information to provide personalized financial advice and insights when relevant."""
            messages.append({"role": "system", "content": system_message})
        
        # Add chat history (all messages up to and including the current one)
        for msg in chat.messages.all().order_by('created_at'):
            if msg.id == message_id:
                # This is the current message - handle attachments
                content_parts = [msg.content] if msg.content else []
                
                if msg.attachment:
                    # Extract file content for CSV and PDF
                    file_content = extract_file_content(msg)
                    if file_content:
                        content_parts.append(file_content)
                    elif msg.attachment_type == 'image':
                        # For images, we can encode as base64 or just reference the URL
                        # OpenAI vision API would need base64, but for now we'll include URL in text
                        content_parts.append(f"[User attached an image: {msg.attachment.url}]")
                
                messages.append({
                    "role": "user",
                    "content": "\n".join(content_parts) if content_parts else "[No text content]"
                })
            elif msg.id < message_id:
                # Previous messages - include attachment info if present
                msg_dict = msg.to_openai_dict()
                if msg.attachment:
                    file_content = extract_file_content(msg)
                    if file_content:
                        if msg_dict.get("content"):
                            msg_dict["content"] += "\n\n" + file_content
                        else:
                            msg_dict["content"] = file_content
                messages.append(msg_dict)
        
        response = client.chat.completions.create(model=settings.AI_CHAT_OPENAI_MODEL, messages=messages)

        message = ChatMessage.objects.create(
            chat_id=chat_id,
            message_type=MessageTypes.AI,
            content=response.choices[0].message.content.strip(),
        )
        # Serialize without request context (URLs will be relative)
        return ChatMessageSerializer(message).data
    
    except AuthenticationError as e:
        error_message = ChatMessage.objects.create(
            chat_id=chat_id,
            message_type=MessageTypes.AI,
            content=f"Error: Authentication failed with OpenAI API. Please check that your AI_CHAT_OPENAI_API_KEY is set correctly. Error details: {str(e)}",
        )
        return ChatMessageSerializer(error_message).data
    
    except APIError as e:
        error_message = ChatMessage.objects.create(
            chat_id=chat_id,
            message_type=MessageTypes.AI,
            content=f"Error: OpenAI API error occurred. Please try again later. Error details: {str(e)}",
        )
        return ChatMessageSerializer(error_message).data
    
    except ValueError as e:
        error_message = ChatMessage.objects.create(
            chat_id=chat_id,
            message_type=MessageTypes.AI,
            content=f"Error: {str(e)}",
        )
        return ChatMessageSerializer(error_message).data
    
    except Exception as e:
        error_message = ChatMessage.objects.create(
            chat_id=chat_id,
            message_type=MessageTypes.AI,
            content=f"Error: An unexpected error occurred while processing your message. Please try again. Error details: {str(e)}",
        )
        return ChatMessageSerializer(error_message).data


@shared_task
def set_chat_name(chat_id: int, message: str):
    from openai import APIError, AuthenticationError
    
    chat = Chat.objects.get(id=chat_id)
    if not message:
        return
    elif len(message) < 20:
        # for short messages, just use them as the chat name. the summary won't help
        chat.name = message
        chat.save()
    else:
        try:
            # set the name with openAI
            system_naming_prompt = """
        You are SummaryBot. When I give you an input, your job is to summarize the intent of that input.
        Provide only the summary of the input and nothing else.
        Summaries should be less than 100 characters long.
        """
            messages = [
                {"role": "system", "content": system_naming_prompt},
                {"role": "user", "content": f"Summarize the following text: '{message}'"},
            ]
            client = get_openai_client()
            response = client.chat.completions.create(model=settings.AI_CHAT_OPENAI_MODEL, messages=messages)
            chat.name = response.choices[0].message.content[:100].strip()
            chat.save()
        except (AuthenticationError, APIError, ValueError) as e:
            # If OpenAI fails, fall back to using the message itself
            chat.name = message[:100]
            chat.save()
