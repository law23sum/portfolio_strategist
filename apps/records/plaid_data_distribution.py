"""
Automatic Plaid Data Distribution Service
Automatically organizes and distributes Plaid data to corresponding web pages after login
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from .aggregation_service import PlaidAggregationService
from .models import FinancialTransaction, LinkedAccount

logger = logging.getLogger(__name__)
User = get_user_model()


def _is_network_error(error: Exception) -> bool:
    """
    Check if an exception is a network/DNS connectivity error.

    Args:
        error: The exception to check

    Returns:
        True if it's a network/DNS error, False otherwise
    """
    error_str = str(error)
    error_type = type(error).__name__

    # Check for DNS/network errors
    network_indicators = [
        "NameResolutionError",
        "Failed to resolve",
        "Max retries exceeded",
        "Connection",
        "DNS",
        "timeout",
        "network",
        "HTTPSConnectionPool",
        "Temporary failure",
        "urllib3",
    ]

    return any(indicator in error_str or indicator in error_type for indicator in network_indicators)


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

            provider = AggregationProvider.objects.filter(name="plaid", is_active=True).first()
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
                    if _is_network_error(e):
                        logger.warning(
                            f"Network error fetching identity from Plaid API for user {user.id}. "
                            f"Error: {type(e).__name__}: {str(e)[:200]}"
                        )
                    else:
                        logger.warning(f"Could not fetch identity: {e}")
                    identity_data = {}

            # 2. Get Accounts data
            accounts_data = []
            try:
                accounts_data = service._fetch_accounts(access_token)
            except Exception as e:
                if _is_network_error(e):
                    logger.warning(
                        f"Network error fetching accounts from Plaid API for user {user.id}. "
                        f"Error: {type(e).__name__}: {str(e)[:200]}"
                    )
                else:
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
                transactions = (
                    response.transactions if hasattr(response, "transactions") else response.get("transactions", [])
                )

                # Convert transactions to dict format
                for tx in transactions:
                    if hasattr(tx, "transaction_id"):
                        transactions_data.append(
                            {
                                "transaction_id": tx.transaction_id,
                                "amount": getattr(tx, "amount", 0),
                                "date": getattr(tx, "date", None),
                                "name": getattr(tx, "name", ""),
                                "merchant_name": getattr(tx, "merchant_name", ""),
                                "category": getattr(tx, "category", []),
                                "account_id": getattr(tx, "account_id", ""),
                                "pending": getattr(tx, "pending", False),
                            }
                        )
                    else:
                        transactions_data.append(tx)
            except Exception as e:
                if _is_network_error(e):
                    logger.warning(
                        f"Network error fetching transactions from Plaid API for user {user.id}. "
                        f"Error: {type(e).__name__}: {str(e)[:200]}"
                    )
                else:
                    logger.warning(f"Could not fetch transactions: {e}")

            # Get linked accounts first - needed for investment data sync
            # Include 'active', 'pending', and 'error' accounts
            linked_accounts = LinkedAccount.objects.filter(
                user=user, provider=provider, status__in=["active", "pending", "error"]
            )

            # 4. Get Investment Holdings data (only if we have a linked account)
            investment_holdings = []
            if linked_accounts.exists():
                try:
                    # Use the first linked account for investment holdings
                    first_account = linked_accounts.first()
                    service._sync_investment_holdings(first_account, access_token)
                    # Note: _sync_investment_holdings returns count, not data
                    # If we need the actual holdings data, we'd need a separate fetch method
                except Exception as e:
                    if _is_network_error(e):
                        logger.warning(
                            f"Network error fetching investment holdings from Plaid API for user {user.id}. "
                            f"Error: {type(e).__name__}: {str(e)[:200]}"
                        )
                    else:
                        logger.warning(f"Could not fetch investment holdings: {e}")

            # 5. Get Investment Transactions data (only if we have a linked account)
            investment_transactions = []
            if linked_accounts.exists():
                try:
                    # Use the first linked account for investment transactions
                    first_account = linked_accounts.first()
                    service._sync_investment_transactions(first_account, access_token, days_back=90)
                    # Note: _sync_investment_transactions returns count, not data
                    # If we need the actual transaction data, we'd need a separate fetch method
                except Exception as e:
                    if _is_network_error(e):
                        logger.warning(
                            f"Network error fetching investment transactions from Plaid API for user {user.id}. "
                            f"Error: {type(e).__name__}: {str(e)[:200]}"
                        )
                    else:
                        logger.warning(f"Could not fetch investment transactions: {e}")

            if linked_accounts.exists() and identity_data:
                first_account = linked_accounts.first()
                # Store identity in metadata if not already present
                if "plaid_identity" not in first_account.metadata:
                    first_account.metadata["plaid_identity"] = identity_data
                    first_account.save(update_fields=["metadata"])
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
                elif hasattr(obj, "value") and not isinstance(obj, (str, int, float, bool, type(None))):
                    return str(obj.value)
                elif type(obj).__name__ in ["AccountType", "AccountSubtype", "CountryCode", "Products"]:
                    return str(obj.value) if hasattr(obj, "value") else str(obj)
                return obj

            cache_key = f"plaid_data_{user.id}"
            cache_data = {
                "identity": convert_enums_for_cache(identity_data),
                "accounts": convert_enums_for_cache(accounts_data),
                "transactions": convert_enums_for_cache(transactions_data),
                "investment_holdings": convert_enums_for_cache(investment_holdings),
                "investment_transactions": convert_enums_for_cache(investment_transactions),
                "fetched_at": timezone.now().isoformat(),
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
        from decimal import Decimal, InvalidOperation

        from django.core.cache import cache

        from .models import AggregationProvider

        provider = AggregationProvider.objects.filter(name="plaid", is_active=True).first()
        if not provider:
            # Try to get provider even if not active
            provider = AggregationProvider.objects.filter(name="plaid").first()
            if not provider:
                logger.warning(f"No Plaid provider found for user {user.id}")
                # Don't return empty - try to find accounts without provider filter
                logger.info("Attempting to find accounts without provider filter...")
            else:
                logger.info(f"Found Plaid provider but it's not active for user {user.id}")

        # Try to get cached API data first
        accounts_data = []
        transactions_data = []
        identity_data = {}

        if use_api_data:
            cache_key = f"plaid_data_{user.id}"
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Using cached Plaid API data for user {user.id}")
                accounts_data = cached_data.get("accounts", [])
                transactions_data = cached_data.get("transactions", [])
                identity_data = cached_data.get("identity", {})
            else:
                # Try to fetch directly from Plaid APIs
                # Include 'active', 'pending', and 'error' accounts
                linked_accounts = LinkedAccount.objects.filter(
                    user=user, provider=provider, status__in=["active", "pending", "error"]
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
                        transactions = (
                            response.transactions
                            if hasattr(response, "transactions")
                            else response.get("transactions", [])
                        )
                        transactions_data = []
                        for tx in transactions:
                            if hasattr(tx, "transaction_id"):
                                # Convert category list - handle enum types
                                category = getattr(tx, "category", [])
                                category_list = []
                                if category:
                                    for cat in category:
                                        if hasattr(cat, "value"):
                                            category_list.append(str(cat.value))
                                        else:
                                            category_list.append(str(cat))

                                # Handle date
                                tx_date = getattr(tx, "date", None)
                                if tx_date and hasattr(tx_date, "isoformat"):
                                    tx_date = tx_date.isoformat()
                                elif tx_date:
                                    tx_date = str(tx_date)

                                transactions_data.append(
                                    {
                                        "transaction_id": str(getattr(tx, "transaction_id", "")),
                                        "amount": float(getattr(tx, "amount", 0)),
                                        "date": tx_date,
                                        "name": str(getattr(tx, "name", "")),
                                        "merchant_name": str(getattr(tx, "merchant_name", "")),
                                        "category": category_list,
                                        "account_id": str(getattr(tx, "account_id", "")),
                                        "pending": bool(getattr(tx, "pending", False)),
                                    }
                                )
                            else:
                                # Already a dict, ensure all values are JSON-serializable
                                tx_dict = dict(tx) if hasattr(tx, "__dict__") else tx
                                transactions_data.append(tx_dict)

                        logger.info(f"Fetched fresh data from Plaid APIs for user {user.id}")
                    except Exception as e:
                        if _is_network_error(e):
                            logger.warning(
                                f"Network/DNS error connecting to Plaid API for user {user.id}. "
                                f"Falling back to database. Error: {type(e).__name__}: {str(e)[:200]}"
                            )
                        else:
                            logger.warning(
                                f"Could not fetch from Plaid APIs for user {user.id}, using DB. "
                                f"Error: {type(e).__name__}: {str(e)[:200]}"
                            )
                        use_api_data = False

        # Fall back to database if API data not available
        if not accounts_data or not use_api_data:
            # Include 'active', 'pending', and 'error' accounts - error accounts might still have valid data
            # First try with provider filter if provider exists
            linked_accounts = None
            if provider:
                linked_accounts = (
                    LinkedAccount.objects.filter(
                        user=user, provider=provider, status__in=["active", "pending", "error"]
                    )
                    .select_related("provider")
                    .prefetch_related("balances")
                )
            else:
                # No provider, try to find accounts without provider filter
                linked_accounts = (
                    LinkedAccount.objects.filter(user=user, status__in=["active", "pending", "error"])
                    .select_related("provider")
                    .prefetch_related("balances")
                )

            if not linked_accounts or not linked_accounts.exists():
                if provider:
                    logger.warning(
                        f"No linked accounts found for user {user.id} with provider {provider.name} (id: {provider.id})"
                    )
                else:
                    logger.warning(f"No linked accounts found for user {user.id} - no provider available")

                # Try without provider filter to see if accounts exist with any provider
                all_accounts = (
                    LinkedAccount.objects.filter(user=user, status__in=["active", "pending", "error"])
                    .select_related("provider")
                    .prefetch_related("balances")
                )

                if all_accounts.exists():
                    logger.info(
                        f"Found {all_accounts.count()} accounts for user {user.id} without provider filter, using those"
                    )
                    linked_accounts = all_accounts
                    # Use the provider from the first account if available
                    first_account = linked_accounts.first()
                    if first_account and first_account.provider:
                        provider = first_account.provider
                        logger.info(f"Using provider from account: {provider.name} (id: {provider.id})")
                else:
                    # Check if accounts exist with different statuses
                    any_accounts = LinkedAccount.objects.filter(user=user)
                    if any_accounts.exists():
                        status_counts = {}
                        provider_counts = {}
                        for acc in any_accounts:
                            status = acc.status
                            status_counts[status] = status_counts.get(status, 0) + 1
                            prov_name = acc.provider.name if acc.provider else "None"
                            provider_counts[prov_name] = provider_counts.get(prov_name, 0) + 1
                        logger.warning(
                            f"Found {any_accounts.count()} accounts but none with 'active' or 'pending' status."
                        )
                        logger.warning(f"  Status breakdown: {status_counts}")
                        logger.warning(f"  Provider breakdown: {provider_counts}")
                        # Log first few account details
                        for acc in any_accounts[:3]:
                            logger.warning(
                                f"  Account: {acc.account_name} (status: {acc.status}, provider: {acc.provider.name if acc.provider else 'None'})"
                            )
                        # Try using accounts with any status
                        linked_accounts = any_accounts.select_related("provider").prefetch_related("balances")
                        logger.info(f"Using {linked_accounts.count()} accounts with any status")
                    else:
                        logger.warning(f"No accounts at all found for user {user.id}")
                        return {}

            if not linked_accounts or not linked_accounts.exists():
                logger.warning(f"Still no linked accounts found for user {user.id}")
                return {}

            # Get identity data from first account metadata
            first_account = linked_accounts.first()
            if first_account.metadata.get("plaid_identity"):
                identity_data = first_account.metadata["plaid_identity"]

            # Convert linked accounts to accounts_data format
            accounts_data = []
            logger.info(f"Converting {linked_accounts.count()} linked accounts to accounts_data format")
            for account in linked_accounts:
                latest_balance = account.balances.first()
                # Convert subtype to string if it's an enum
                subtype = account.account_subtype
                if subtype and hasattr(subtype, "value"):
                    subtype = str(subtype.value)
                elif subtype:
                    subtype = str(subtype)
                else:
                    subtype = ""

                # Use account name, or fallback to account_name field
                account_name = str(account.account_name) if account.account_name else ""
                account_type = str(account.account_type) if account.account_type else ""
                balance = (
                    float(latest_balance.current_balance) if latest_balance and latest_balance.current_balance else 0.0
                )

                logger.info(f"  Account: {account_name} (type: {account_type}, subtype: {subtype}, balance: {balance})")

                accounts_data.append(
                    {
                        "account_id": str(account.provider_account_id) if account.provider_account_id else "",
                        "name": account_name,
                        "type": account_type,
                        "subtype": subtype,
                        "mask": str(account.account_number_masked) if account.account_number_masked else "",
                        "institution_name": str(account.institution_name) if account.institution_name else "",
                        "balances": {
                            "current": balance,
                            "available": float(latest_balance.available_balance)
                            if latest_balance and latest_balance.available_balance
                            else None,
                            "limit": float(latest_balance.limit) if latest_balance and latest_balance.limit else None,
                            "iso_currency_code": str(latest_balance.currency_code) if latest_balance else "USD",
                        },
                    }
                )

            logger.info(f"Fetched {len(accounts_data)} accounts from database for user {user.id}")

            # Get transactions from database
            from datetime import timedelta

            cutoff_date = timezone.now() - timedelta(days=90)
            transactions = FinancialTransaction.objects.filter(
                account__in=linked_accounts, date__gte=cutoff_date.date()
            )[:100]

            transactions_data = [
                {
                    "transaction_id": tx.transaction_id,
                    "amount": float(tx.amount),
                    "date": tx.date.isoformat() if tx.date else None,
                    "name": tx.description,
                    "merchant_name": tx.merchant_name,
                    "category": tx.category.split(", ") if tx.category else [],
                    "account_id": tx.account.provider_account_id,
                    "pending": tx.pending,
                }
                for tx in transactions
            ]

        # Organize accounts by type
        organized_data = {
            "identity": identity_data,
            "budget_planner": {
                "checking_balance": Decimal("0"),
                "savings_balance": Decimal("0"),
                "total_cash": Decimal("0"),
                "monthly_income": Decimal("0"),
                "annual_salary": Decimal("0"),
                "monthly_expenses": Decimal("0"),
                "debt_payments": Decimal("0"),
            },
            "stocks_assessment": {
                "investment_amount": Decimal("0"),
                "accounts": [],
            },
            "savings_assessment": {
                "initial_deposit": Decimal("0"),
                "account_name": "",
                "accounts": [],
            },
            "cd_assessment": {
                "cd_amount": Decimal("0"),
                "account_name": "",
                "accounts": [],
            },
            "bond_assessment": {
                "face_value": Decimal("0"),
                "purchase_price": Decimal("0"),
                "account_name": "",
                "accounts": [],
            },
            "debt": {
                "total_debt": Decimal("0"),
                "total_credit_limit": Decimal("0"),
                "monthly_payments": Decimal("0"),
                "accounts": [],
            },
            "tax_optimization": {
                "annual_income": Decimal("0"),
                "retirement_contributions": Decimal("0"),
                "hsa_contributions": Decimal("0"),
                "investment_accounts": [],
                "retirement_accounts": [],
            },
            "credit_score": {
                "total_credit_limit": Decimal("0"),
                "total_credit_used": Decimal("0"),
                "credit_utilization_percent": Decimal("0"),
                "credit_accounts": [],
                "loan_accounts": [],
            },
            "personal_sensitive": {
                "identity": identity_data,
                "accounts_summary": [],
            },
            "documentation": {
                "total_accounts": 0,
                "account_types": {},
                "institutions": [],
                "accounts": [],
            },
        }

        # Helper function to parse account name and identify account type
        def parse_account_name(account_name):
            """
            Parse account name to identify account type.
            Returns a dict with identified types based on name patterns.
            """
            if not account_name:
                return {}

            name_lower = str(account_name).lower()
            identified_types = {}

            # Identify account types from name
            if "hsa" in name_lower or "health savings" in name_lower:
                identified_types["is_hsa"] = True
                identified_types["parsed_type"] = "hsa"

            if "savings" in name_lower and "cd" not in name_lower:
                identified_types["is_savings"] = True
                if "parsed_type" not in identified_types:
                    identified_types["parsed_type"] = "savings"

            if "cd" in name_lower or "certificate" in name_lower or "certificate of deposit" in name_lower:
                identified_types["is_cd"] = True
                identified_types["parsed_type"] = "cd"

            if "checking" in name_lower:
                identified_types["is_checking"] = True
                if "parsed_type" not in identified_types:
                    identified_types["parsed_type"] = "checking"

            if "401k" in name_lower or "401(k)" in name_lower:
                identified_types["is_retirement"] = True
                identified_types["retirement_type"] = "401k"

            if "ira" in name_lower or "roth" in name_lower:
                identified_types["is_retirement"] = True
                identified_types["retirement_type"] = "ira"

            if "pension" in name_lower:
                identified_types["is_retirement"] = True
                identified_types["retirement_type"] = "pension"

            if "investment" in name_lower or "brokerage" in name_lower or "trading" in name_lower:
                identified_types["is_investment"] = True
                if "parsed_type" not in identified_types:
                    identified_types["parsed_type"] = "investment"

            if (
                "bond" in name_lower
                or "treasury" in name_lower
                or "municipal" in name_lower
                or "corporate bond" in name_lower
                or "government bond" in name_lower
                or "fixed income" in name_lower
            ):
                identified_types["is_bond"] = True
                if "parsed_type" not in identified_types:
                    identified_types["parsed_type"] = "bond"

            if "credit" in name_lower or "card" in name_lower:
                identified_types["is_credit"] = True
                if "parsed_type" not in identified_types:
                    identified_types["parsed_type"] = "credit"

            if "loan" in name_lower or "mortgage" in name_lower:
                identified_types["is_loan"] = True
                if "parsed_type" not in identified_types:
                    identified_types["parsed_type"] = "loan"

            return identified_types

        # Helper function to safely convert Plaid enums to strings
        # Defined here so it's available throughout the loop
        def safe_convert_to_string(value):
            """Safely convert Plaid enum or any value to string without triggering __contains__"""
            if not value:
                return ""
            try:
                # Check type name first to avoid triggering __contains__ on Plaid objects
                type_name = type(value).__name__
                if type_name in ["AccountType", "AccountSubtype", "CountryCode"]:
                    # Try to get value attribute without triggering __contains__
                    if hasattr(value, "value"):
                        try:
                            return str(value.value).lower()
                        except (KeyError, AttributeError, TypeError):
                            pass
                    # Fallback: convert to string directly
                    try:
                        return str(value).lower()
                    except (KeyError, AttributeError, TypeError):
                        return ""
                elif hasattr(value, "value"):
                    try:
                        return str(value.value).lower()
                    except (KeyError, AttributeError, TypeError):
                        return str(value).lower() if value else ""
                else:
                    return str(value).lower() if value else ""
            except (KeyError, AttributeError, TypeError):
                try:
                    return str(value).lower() if value else ""
                except (KeyError, AttributeError, TypeError):
                    return ""

        # Process accounts from API data or database
        logger.info(f"Processing {len(accounts_data)} accounts for user {user.id}")
        if not accounts_data:
            logger.warning(f"No accounts_data found for user {user.id} - returning empty data")
            return {}

        for account_data in accounts_data:
            # Handle both API format and database format
            if isinstance(account_data, dict):
                account_id = account_data.get("account_id", "")
                account_name = account_data.get("name", "Unknown Account")
                account_type = account_data.get("type", "")

                # Handle type - could be string, enum, or AccountType object
                # Convert enum types to strings safely
                if account_type:
                    try:
                        # Check type name first to avoid triggering __contains__ on Plaid objects
                        type_name = type(account_type).__name__
                        if type_name in ["AccountType", "AccountSubtype"]:
                            try:
                                account_type = str(account_type.value).lower()
                            except (KeyError, AttributeError):
                                account_type = str(account_type).lower()
                        elif hasattr(account_type, "value"):
                            try:
                                account_type = str(account_type.value).lower()
                            except (KeyError, AttributeError):
                                account_type = str(account_type).lower()
                        else:
                            account_type = str(account_type).lower()
                    except (KeyError, AttributeError):
                        account_type = str(account_type).lower() if account_type else ""
                else:
                    account_type = ""

                subtype_raw = account_data.get("subtype", "")
                subtype = safe_convert_to_string(subtype_raw)

                balances = account_data.get("balances", {})
                # Safely convert balance, handling None and invalid values
                balance_value = balances.get("current", 0)
                if balance_value is None:
                    balance = Decimal("0")
                else:
                    try:
                        balance_str = str(balance_value).strip()
                        if balance_str.lower() in ("none", "null", ""):
                            balance = Decimal("0")
                        else:
                            balance = Decimal(balance_str)
                    except (ValueError, TypeError, InvalidOperation):
                        logger.warning(f"Invalid balance value for account {account_name}: {balance_value}, using 0")
                        balance = Decimal("0")
                account_id_for_list = str(account_id) if account_id else ""
                institution_name = (
                    account_data.get("institution_name")
                    or account_data.get("official_name")
                    or account_data.get("name")
                    or "Linked Account"
                )
            else:
                # Database format (LinkedAccount object)
                latest_balance = account_data.balances.first()
                if not latest_balance:
                    continue

                balance = latest_balance.current_balance or Decimal("0")
                account_type = account_data.account_type
                account_name = account_data.account_name
                account_id_for_list = account_data.id
                # Database stores account_subtype as CharField, so it's already a string
                subtype = (account_data.account_subtype or "").lower()
                balances = {}
                institution_name = account_data.institution_name

            # Final safeguard: ensure subtype is always a string before any 'in' checks
            # This prevents KeyError when Plaid enum objects trigger __contains__
            if not isinstance(subtype, str):
                try:
                    subtype = safe_convert_to_string(subtype)
                except Exception:
                    subtype = str(subtype).lower() if subtype else ""

            # Convert subtype to string for safe membership checks
            # This ensures we never trigger __contains__ on Plaid enum objects
            subtype_str = str(subtype).lower() if subtype else ""

            # Parse account name to identify account type - ALWAYS check name first
            name_parsed = parse_account_name(account_name)

            # Log account details for debugging
            logger.info(
                f"Processing account: name='{account_name}', type='{account_type}', subtype='{subtype_str}', balance={balance}, parsed={name_parsed}"
            )

            # Determine account characteristics from name parsing (priority) and type/subtype (fallback)
            # Name parsing takes priority - if name says "savings", it's savings regardless of type
            is_checking = name_parsed.get("is_checking") or (
                account_type == "depository"
                and (
                    "checking" in subtype_str
                    or ("depository" in subtype_str and "savings" not in subtype_str and "cd" not in subtype_str)
                )
            )
            is_savings = name_parsed.get("is_savings") or (
                account_type == "depository" and "savings" in subtype_str and "cd" not in subtype_str
            )
            is_cd = name_parsed.get("is_cd") or (
                account_type == "depository" and ("cd" in subtype_str or "certificate" in subtype_str)
            )
            is_hsa = name_parsed.get("is_hsa") or "hsa" in subtype_str

            # Bond identification: check name first, then subtype, also check if account name suggests bonds
            account_name_lower = str(account_name).lower()
            is_bond = (
                name_parsed.get("is_bond")
                or "bond" in subtype_str
                or "bond" in account_name_lower
                or "treasury" in account_name_lower
                or "municipal" in account_name_lower
                or "corporate bond" in account_name_lower
                or "government bond" in account_name_lower
                or "fixed income" in account_name_lower
            )

            # Investment identification - check type first, then name
            is_investment = (
                account_type in ["investment", "brokerage"]
                or name_parsed.get("is_investment")
                or "investment" in account_name_lower
                or "brokerage" in account_name_lower
                or "trading" in account_name_lower
            )

            is_retirement = (
                name_parsed.get("is_retirement")
                or account_type == "retirement"
                or (
                    account_type == "investment"
                    and (
                        "401k" in subtype_str
                        or "ira" in subtype_str
                        or "retirement" in subtype_str
                        or "roth" in subtype_str
                    )
                )
                or "401k" in account_name_lower
                or "ira" in account_name_lower
                or "roth" in account_name_lower
                or "pension" in account_name_lower
            )

            logger.info(
                f"  Categorization: is_bond={is_bond}, is_investment={is_investment}, is_retirement={is_retirement}, is_savings={is_savings}, is_cd={is_cd}"
            )

            # Budget Planner data - checking accounts
            if is_checking:
                organized_data["budget_planner"]["checking_balance"] += balance

            # Savings Assessment - check name FIRST, then type
            if is_savings and not is_cd:
                organized_data["budget_planner"]["savings_balance"] += balance
                # Always add to savings assessment accounts list
                organized_data["savings_assessment"]["accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "balance": float(balance),
                        "institution": str(institution_name) if institution_name else "",
                    }
                )
                # Update initial deposit if this is the largest
                if balance > organized_data["savings_assessment"]["initial_deposit"]:
                    organized_data["savings_assessment"]["initial_deposit"] = balance
                    organized_data["savings_assessment"]["account_name"] = str(account_name) if account_name else ""

            # CD Assessment - check name FIRST, then type
            if is_cd:
                # Always add to CD assessment accounts list
                organized_data["cd_assessment"]["accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "balance": float(balance),
                        "institution": str(institution_name) if institution_name else "",
                    }
                )
                # Update CD amount if this is the largest
                if balance > organized_data["cd_assessment"]["cd_amount"]:
                    organized_data["cd_assessment"]["cd_amount"] = balance
                    organized_data["cd_assessment"]["account_name"] = str(account_name) if account_name else ""

            # HSA accounts go to tax optimization
            if is_hsa:
                organized_data["tax_optimization"]["hsa_contributions"] += balance

            # Bond Assessment - check name FIRST (before stocks, since bonds are more specific)
            if is_bond:
                logger.info(f"Identified bond account: {account_name} (balance: {balance})")
                # Always add to bond assessment accounts list
                organized_data["bond_assessment"]["accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "balance": float(balance),
                        "institution": str(institution_name) if institution_name else "",
                        "account_type": account_type,
                        "subtype": subtype,
                    }
                )
                # Update face value if this is the largest
                if balance > organized_data["bond_assessment"]["face_value"]:
                    organized_data["bond_assessment"]["face_value"] = balance
                    organized_data["bond_assessment"]["purchase_price"] = balance
                    organized_data["bond_assessment"]["account_name"] = str(account_name) if account_name else ""

            # Stocks Assessment data - investment accounts that are NOT bonds and NOT retirement
            elif is_investment and not is_bond and not is_retirement:
                logger.info(f"Identified stock/investment account: {account_name} (balance: {balance})")
                # Always add to stocks assessment accounts list
                organized_data["stocks_assessment"]["investment_amount"] += balance
                organized_data["stocks_assessment"]["accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "balance": float(balance),
                        "institution": str(institution_name) if institution_name else "",
                        "account_type": account_type,
                        "subtype": subtype,
                    }
                )
            # Fallback: If it's an investment account but wasn't categorized, add it to stocks
            elif (
                account_type in ["investment", "brokerage"] and not is_bond and not is_retirement and not is_investment
            ):
                logger.warning(
                    f"Investment account {account_name} not properly categorized - adding to stocks as fallback"
                )
                organized_data["stocks_assessment"]["investment_amount"] += balance
                organized_data["stocks_assessment"]["accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "balance": float(balance),
                        "institution": str(institution_name) if institution_name else "",
                        "account_type": account_type,
                        "subtype": subtype,
                    }
                )

            # Debt data for budget planner and debt page - check name first
            is_credit = account_type == "credit" or name_parsed.get("is_credit")
            is_loan = account_type == "loan" or name_parsed.get("is_loan")

            if is_credit or is_loan:
                if isinstance(account_data, dict):
                    limit_value = balances.get("limit")
                    # Handle None, empty string, or invalid values
                    if limit_value is None or limit_value == "":
                        limit = Decimal("0")
                    else:
                        try:
                            # Convert to string first, then to Decimal
                            limit_str = str(limit_value).strip()
                            if limit_str.lower() in ("none", "null", ""):
                                limit = Decimal("0")
                            else:
                                limit = Decimal(limit_str)
                        except (ValueError, TypeError, InvalidOperation):
                            logger.warning(f"Invalid limit value for account {account_name}: {limit_value}, using 0")
                            limit = Decimal("0")
                else:
                    limit = latest_balance.limit or Decimal("0")
                min_payment = max(balance * Decimal("0.02"), Decimal("25"))
                organized_data["budget_planner"]["debt_payments"] += min_payment

                # Add to debt page data
                organized_data["debt"]["total_debt"] += balance
                if limit > 0:
                    organized_data["debt"]["total_credit_limit"] += limit
                organized_data["debt"]["monthly_payments"] += min_payment
                organized_data["debt"]["accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "type": account_type,
                        "subtype": subtype,
                        "balance": float(balance),
                        "limit": float(limit) if limit > 0 else None,
                        "min_payment": float(min_payment),
                        "institution": str(institution_name) if institution_name else "",
                    }
                )

                # Add to credit score data
                if account_type == "credit":
                    organized_data["credit_score"]["total_credit_limit"] += limit if limit > 0 else Decimal("0")
                    organized_data["credit_score"]["total_credit_used"] += balance
                    organized_data["credit_score"]["credit_accounts"].append(
                        {
                            "id": str(account_id_for_list) if account_id_for_list else "",
                            "name": str(account_name) if account_name else "",
                            "balance": float(balance),
                            "limit": float(limit) if limit > 0 else None,
                            "utilization": float((balance / limit * 100) if limit > 0 else 0),
                            "institution": str(institution_name) if institution_name else "",
                        }
                    )
                elif account_type == "loan":
                    organized_data["credit_score"]["loan_accounts"].append(
                        {
                            "id": str(account_id_for_list) if account_id_for_list else "",
                            "name": str(account_name) if account_name else "",
                            "balance": float(balance),
                            "institution": str(institution_name) if institution_name else "",
                        }
                    )

            # Retirement accounts for tax optimization - check name first
            is_retirement = (
                account_type == "retirement"
                or name_parsed.get("is_retirement")
                or (
                    account_type == "investment"
                    and (
                        "401k" in subtype_str
                        or "ira" in subtype_str
                        or "retirement" in subtype_str
                        or "roth" in subtype_str
                    )
                )
            )

            if is_retirement:
                retirement_type = name_parsed.get("retirement_type") or subtype_str
                organized_data["tax_optimization"]["retirement_accounts"].append(
                    {
                        "id": str(account_id_for_list) if account_id_for_list else "",
                        "name": str(account_name) if account_name else "",
                        "balance": float(balance),
                        "type": account_type,
                        "subtype": retirement_type,
                        "institution": str(institution_name) if institution_name else "",
                    }
                )

            # Investment accounts for tax optimization (non-retirement)
            elif account_type in ["investment", "brokerage"] or name_parsed.get("is_investment"):
                # Don't add bonds or retirement accounts
                if not name_parsed.get("is_bond") and not is_retirement:
                    organized_data["tax_optimization"]["investment_accounts"].append(
                        {
                            "id": str(account_id_for_list) if account_id_for_list else "",
                            "name": str(account_name) if account_name else "",
                            "balance": float(balance),
                            "type": account_type,
                            "subtype": subtype,
                            "institution": str(institution_name) if institution_name else "",
                        }
                    )

            # Documentation page - all accounts
            account_summary = {
                "id": str(account_id_for_list) if account_id_for_list else "",
                "name": str(account_name) if account_name else "",
                "type": account_type,
                "subtype": subtype,
                "balance": float(balance),
                "institution": str(institution_name) if institution_name else "",
                "mask": str(account_data.get("mask", "")) if isinstance(account_data, dict) else "",
            }
            organized_data["documentation"]["accounts"].append(account_summary)

            # Track account types for documentation
            if account_type not in organized_data["documentation"]["account_types"]:
                organized_data["documentation"]["account_types"][account_type] = 0
            organized_data["documentation"]["account_types"][account_type] += 1

            # Track institutions
            if institution_name and institution_name not in organized_data["documentation"]["institutions"]:
                organized_data["documentation"]["institutions"].append(str(institution_name))

        # Calculate totals
        organized_data["budget_planner"]["total_cash"] = (
            organized_data["budget_planner"]["checking_balance"] + organized_data["budget_planner"]["savings_balance"]
        )

        # Calculate credit utilization percentage
        if organized_data["credit_score"]["total_credit_limit"] > 0:
            organized_data["credit_score"]["credit_utilization_percent"] = (
                organized_data["credit_score"]["total_credit_used"]
                / organized_data["credit_score"]["total_credit_limit"]
                * 100
            )

        # Calculate retirement contributions from transactions (HSA, 401k contributions)
        if transactions_data:
            retirement_contrib_total = Decimal("0")
            hsa_contrib_total = Decimal("0")
            for tx in transactions_data:
                if isinstance(tx, dict):
                    tx_name = str(tx.get("name", "")).lower()
                    tx_amount = Decimal(str(tx.get("amount", 0)))
                    if tx_amount > 0:  # Positive amounts are credits/income
                        if "401k" in tx_name or "retirement" in tx_name or "ira" in tx_name:
                            retirement_contrib_total += tx_amount
                        elif "hsa" in tx_name or "health savings" in tx_name:
                            hsa_contrib_total += tx_amount
            organized_data["tax_optimization"]["retirement_contributions"] = retirement_contrib_total
            organized_data["tax_optimization"]["hsa_contributions"] = hsa_contrib_total

        # Set documentation totals
        organized_data["documentation"]["total_accounts"] = len(organized_data["documentation"]["accounts"])

        # Set personal sensitive account summary
        organized_data["personal_sensitive"]["accounts_summary"] = [
            {
                "institution": acc.get("institution", ""),
                "type": acc.get("type", ""),
                "name": acc.get("name", ""),
            }
            for acc in organized_data["documentation"]["accounts"]
        ]

        # Calculate income and expenses from transactions (from API or database)
        if transactions_data:
            income_total = Decimal("0")
            expense_total = Decimal("0")
            transaction_count = 0

            for tx in transactions_data:
                if isinstance(tx, dict):
                    tx_amount = Decimal(str(tx.get("amount", 0)))
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

                organized_data["budget_planner"]["monthly_income"] = avg_daily_income * 30
                organized_data["budget_planner"]["annual_salary"] = (
                    organized_data["budget_planner"]["monthly_income"] * 12
                )
                organized_data["budget_planner"]["monthly_expenses"] = avg_daily_expenses * 30

                # Also set annual income for tax optimization
                organized_data["tax_optimization"]["annual_income"] = organized_data["budget_planner"]["annual_salary"]

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
            if obj_type_name in ["AccountType", "AccountSubtype", "CountryCode", "Products"]:
                try:
                    # Try to get value attribute safely
                    if hasattr(obj, "value"):
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
                if obj_module and "plaid" in str(obj_module).lower():
                    # Try to convert Plaid model to dict safely
                    try:
                        if hasattr(obj, "dict") and callable(getattr(obj, "dict", None)):
                            return convert_for_json(obj.dict())
                    except (KeyError, AttributeError, TypeError):
                        pass
                    # Fallback: try to get attributes without triggering __contains__
                    try:
                        if hasattr(obj, "__dict__"):
                            return {k: convert_for_json(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
                    except (KeyError, AttributeError, TypeError):
                        pass
                    return str(obj)
            except (KeyError, AttributeError, TypeError):
                pass

            # Handle other objects with __dict__
            try:
                if hasattr(obj, "__dict__"):
                    return {k: convert_for_json(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
            except (KeyError, AttributeError, TypeError):
                pass

            # Final fallback: convert to string
            return str(obj)

        # Log summary of what was found
        logger.info(f"Plaid data organization summary for user {user.id}:")
        logger.info(f"  Stocks accounts: {len(organized_data['stocks_assessment']['accounts'])}")
        logger.info(f"  Savings accounts: {len(organized_data['savings_assessment']['accounts'])}")
        logger.info(f"  CD accounts: {len(organized_data['cd_assessment']['accounts'])}")
        logger.info(f"  Bond accounts: {len(organized_data['bond_assessment']['accounts'])}")
        logger.info(f"  Debt accounts: {len(organized_data['debt']['accounts'])}")

        return convert_for_json(organized_data)
