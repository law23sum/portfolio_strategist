import csv

from celery import shared_task
from django.conf import settings

from apps.chat.models import Chat, ChatMessage, MessageTypes
from apps.chat.serializers import ChatMessageSerializer
from apps.chat.utils import get_openai_client


def get_user_context(user):
    """Get user's personal details and Plaid account data for context"""
    context_parts = []

    def truncate_list(items, limit=5):
        return items[:limit] if isinstance(items, list) else items

    def build_context_text(parts):
        # Keep total context small (17% of assumed model capacity)
        approx_chars_per_token = 4
        model_capacity_tokens = getattr(settings, "AI_CHAT_MAX_MODEL_TOKENS", 16000)
        max_tokens = max(1, int(model_capacity_tokens * 0.17))
        max_chars = max(1000, max_tokens * approx_chars_per_token)
        assembled = []
        current_length = 0
        for part in parts:
            separator = "\n\n" if assembled else ""
            addition = f"{separator}{part}"
            if current_length + len(addition) > max_chars:
                remaining = max_chars - current_length
                if remaining > 0:
                    assembled.append(addition[:remaining].rstrip())
                assembled.append("[Context truncated]")
                break
            assembled.append(addition)
            current_length += len(addition)
        return "".join(assembled)

    # User personal details
    user_details = {
        "name": user.get_full_name() or user.username,
        "email": user.email,
    }
    context_parts.append(f"User Information: {user_details}")

    # Personal details from FinancialDocument fields
    try:
        from apps.records.models import ExtractedField, FinancialDocument

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
                        "extracted_fields": {},
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
        from apps.records.models import (
            AccountBalance,
            DataSyncLog,
            DebtAccount,
            FinancialTransaction,
            InvestmentHolding,
            InvestmentTransaction,
            LinkedAccount,
        )

        linked_accounts = LinkedAccount.objects.filter(user=user, status="active")
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
                latest_balance = AccountBalance.objects.filter(account=account).order_by("-balance_date").first()
                if latest_balance:
                    account_info["balance"] = str(latest_balance.current_balance)
                    account_info["balance_date"] = str(latest_balance.balance_date)
                accounts_info.append(account_info)
            context_parts.append(f"Linked Financial Accounts (Plaid): {accounts_info}")

            # Recent transactions summary
            recent_transactions = FinancialTransaction.objects.filter(account__user=user).order_by("-date")[:20]
            if recent_transactions.exists():
                transactions_summary = [
                    {
                        "date": str(t.date),
                        "amount": str(t.amount),
                        "description": t.description[:100],
                        "category": t.category,
                        "merchant": t.merchant_name,
                        "account": t.account.account_name,
                    }
                    for t in recent_transactions
                ]
                context_parts.append(f"Recent Transactions: {transactions_summary}")

            # Investment holdings summary
            holdings = InvestmentHolding.objects.filter(account__user=user).order_by("-as_of_date")
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
                        "account": h.account.account_name,
                    }
                    for h in holdings[:20]
                ]
                context_parts.append(f"Investment Holdings: {holdings_summary}")

            # Investment transactions summary
            investment_transactions = InvestmentTransaction.objects.filter(account__user=user).order_by("-date")[:20]
            if investment_transactions.exists():
                investment_tx_summary = [
                    {
                        "date": str(tx.date),
                        "type": tx.transaction_type,
                        "amount": str(tx.amount),
                        "security": tx.security_name or tx.security_ticker,
                        "account": tx.account.account_name,
                    }
                    for tx in investment_transactions
                ]
                context_parts.append(f"Investment Transactions: {investment_tx_summary}")

            # Debt accounts snapshot
            debt_accounts = DebtAccount.objects.filter(account__user=user).order_by("-as_of_date")
            if debt_accounts.exists():
                debt_summary = [
                    {
                        "account": debt.account.account_name,
                        "debt_type": debt.debt_type,
                        "current_balance": str(debt.current_balance),
                        "interest_rate": str(debt.interest_rate) if debt.interest_rate else None,
                        "next_payment_date": str(debt.next_payment_date) if debt.next_payment_date else None,
                        "next_payment_amount": str(debt.next_payment_amount) if debt.next_payment_amount else None,
                    }
                    for debt in debt_accounts[:20]
                ]
                context_parts.append(f"Debt Accounts: {debt_summary}")

            # Recent data sync activity
            sync_logs = DataSyncLog.objects.filter(account__user=user).order_by("-started_at")[:10]
            if sync_logs.exists():
                sync_summary = [
                    {
                        "account": log.account.account_name,
                        "status": log.status,
                        "started_at": str(log.started_at),
                        "completed_at": str(log.completed_at) if log.completed_at else None,
                        "balances_synced": log.balances_synced,
                        "transactions_synced": log.transactions_synced,
                    }
                    for log in sync_logs
                ]
                context_parts.append(f"Plaid Sync Activity: {sync_summary}")
    except ImportError:
        pass

    # Aggregated financial summaries for quicker insights
    try:
        from apps.records.financial_aggregation import (
            BudgetAggregationService,
            DashboardAggregationService,
            DebtAggregationService,
            InvestmentAggregationService,
        )
    except ImportError:
        BudgetAggregationService = InvestmentAggregationService = None
        DebtAggregationService = DashboardAggregationService = None

    if BudgetAggregationService:
        try:
            budget_data = BudgetAggregationService.get_user_budget_data(user=user, days=30)
            budget_summary = {
                "period_days": budget_data.get("period_days"),
                "income": budget_data.get("income"),
                "expenses": budget_data.get("expenses"),
                "net_flow": budget_data.get("net_flow"),
                "total_balance": budget_data.get("total_balance"),
                "top_categories": truncate_list(budget_data.get("spending_by_category", []), limit=5),
            }
            context_parts.append(f"Budget Summary (last 30 days): {budget_summary}")
        except Exception:
            pass

    if InvestmentAggregationService:
        try:
            investment_data = InvestmentAggregationService.get_user_investment_data(user=user)
            investment_summary = {
                "total_portfolio_value": investment_data.get("total_portfolio_value"),
                "total_cost_basis": investment_data.get("total_cost_basis"),
                "total_gain_loss": investment_data.get("total_gain_loss"),
                "top_holdings": truncate_list(investment_data.get("holdings", []), limit=10),
            }
            context_parts.append(f"Investment Portfolio Summary: {investment_summary}")
        except Exception:
            pass

    if DebtAggregationService:
        try:
            debt_data = DebtAggregationService.get_user_debt_data(user=user)
            debt_summary = {
                "total_debt": debt_data.get("total_debt"),
                "credit_utilization": debt_data.get("credit_utilization"),
                "debt_breakdown": truncate_list(debt_data.get("debt_by_type", []), limit=5),
                "upcoming_payments": truncate_list(debt_data.get("upcoming_payments", []), limit=5),
            }
            context_parts.append(f"Debt Overview: {debt_summary}")
        except Exception:
            pass

    if DashboardAggregationService:
        try:
            dashboard_summary = DashboardAggregationService.get_user_financial_summary(user=user)
            high_level_summary = {
                "net_worth": dashboard_summary.get("net_worth"),
                "total_assets": dashboard_summary.get("total_assets"),
                "total_liabilities": dashboard_summary.get("total_liabilities"),
                "total_cash": dashboard_summary.get("total_cash"),
                "total_investments": dashboard_summary.get("total_investments"),
                "account_counts": dashboard_summary.get("account_counts"),
            }
            context_parts.append(f"Financial Dashboard Summary: {high_level_summary}")
        except Exception:
            pass

    # User created investment & savings assessments
    try:
        from apps.records.models import BondAssessment, CDAssessment, SavingsAssessment, StocksAssessment

        stocks_assessments = StocksAssessment.objects.filter(user=user).order_by("-updated_at")
        if stocks_assessments.exists():
            stocks_summary = [
                {
                    "symbol": assessment.symbol,
                    "investment_amount": str(assessment.investment_amount)
                    if assessment.investment_amount is not None
                    else None,
                    "current_price": str(assessment.current_price),
                    "forecast": {
                        key: assessment.forecast_data.get(key)
                        for key in ["current", "monthly", "yearly", "decade"]
                        if assessment.forecast_data.get(key)
                    },
                }
                for assessment in stocks_assessments[:5]
            ]
            context_parts.append(f"Stocks Assessments: {stocks_summary}")

        savings_assessments = SavingsAssessment.objects.filter(user=user).order_by("-updated_at")
        if savings_assessments.exists():
            savings_summary = [
                {
                    "account_name": assessment.account_name,
                    "initial_deposit": str(assessment.initial_deposit),
                    "annual_interest_rate": str(assessment.annual_interest_rate),
                    "monthly_contribution": str(assessment.monthly_contribution),
                    "forecast": assessment.forecast_data.get("yearly"),
                }
                for assessment in savings_assessments[:5]
            ]
            context_parts.append(f"Savings Assessments: {savings_summary}")

        cd_assessments = CDAssessment.objects.filter(user=user).order_by("-updated_at")
        if cd_assessments.exists():
            cd_summary = [
                {
                    "account_name": assessment.account_name,
                    "amount": str(assessment.amount),
                    "annual_interest_rate": str(assessment.annual_interest_rate),
                    "term_months": assessment.term_months,
                    "forecast": assessment.forecast_data.get("yearly"),
                }
                for assessment in cd_assessments[:5]
            ]
            context_parts.append(f"CD Assessments: {cd_summary}")

        bond_assessments = BondAssessment.objects.filter(user=user).order_by("-updated_at")
        if bond_assessments.exists():
            bond_summary = [
                {
                    "account_name": assessment.account_name,
                    "face_value": str(assessment.face_value),
                    "coupon_rate": str(assessment.coupon_rate),
                    "years_to_maturity": str(assessment.years_to_maturity),
                    "forecast": assessment.forecast_data.get("yearly"),
                }
                for assessment in bond_assessments[:5]
            ]
            context_parts.append(f"Bond Assessments: {bond_summary}")
    except ImportError:
        pass

    # Organized Plaid data snapshot (as used throughout the web app)
    try:
        from apps.records.plaid_data_distribution import PlaidDataDistributionService

        plaid_data = PlaidDataDistributionService.get_organized_plaid_data(user)
        if plaid_data:
            plaid_snapshot = {}

            def materialize(value, limit=5):
                if isinstance(value, list):
                    return truncate_list(value, limit)
                if isinstance(value, dict):
                    return {key: materialize(val, limit) for key, val in list(value.items())[:limit]}
                return value

            for key, value in plaid_data.items():
                plaid_snapshot[key] = materialize(value, limit=5)

            context_parts.append(f"Organized Plaid Data Snapshot: {plaid_snapshot}")
    except ImportError:
        pass
    except Exception:
        pass

    return build_context_text(context_parts)


def extract_file_content(message):
    """Extract text content from uploaded files (CSV, PDF)"""
    if not message.attachment:
        return None

    file_path = message.attachment.path
    content = None

    try:
        if message.attachment_type == "csv":
            # Read CSV content
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    # Convert to readable format
                    content = "CSV File Content:\n"
                    for i, row in enumerate(rows[:100]):  # Limit to first 100 rows
                        content += f"Row {i + 1}: {', '.join(str(cell) for cell in row)}\n"
                    if len(rows) > 100:
                        content += f"... (showing first 100 of {len(rows)} rows)\n"

        elif message.attachment_type == "pdf":
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

        elif message.attachment_type == "image":
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
        ChatMessage.objects.get(id=message_id)  # Verify message exists
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
        for msg in chat.messages.all().order_by("created_at"):
            if msg.id == message_id:
                # This is the current message - handle attachments
                content_parts = [msg.content] if msg.content else []

                if msg.attachment:
                    # Extract file content for CSV and PDF
                    file_content = extract_file_content(msg)
                    if file_content:
                        content_parts.append(file_content)
                    elif msg.attachment_type == "image":
                        # For images, we can encode as base64 or just reference the URL
                        # OpenAI vision API would need base64, but for now we'll include URL in text
                        content_parts.append(f"[User attached an image: {msg.attachment.url}]")

                messages.append(
                    {"role": "user", "content": "\n".join(content_parts) if content_parts else "[No text content]"}
                )
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
        except (AuthenticationError, APIError, ValueError):
            # If OpenAI fails, fall back to using the message itself
            chat.name = message[:100]
            chat.save()
