# Financial Data Aggregation Implementation

## Overview

This implementation replaces the manual document upload system with automated financial data aggregation using services like Plaid, Yodlee, Finicity, etc. Users can now link their bank accounts, credit cards, investment accounts, and other financial institutions to automatically import transactions, balances, and investment data.

## What Was Implemented

### 1. Database Models (`apps/records/models.py`)

- **AggregationProvider**: Stores configuration for aggregation providers (Plaid, Yodlee, etc.)
- **LinkedAccount**: Represents a user's linked financial account
- **AccountBalance**: Current and historical balances for accounts
- **FinancialTransaction**: Transactions from linked accounts
- **InvestmentHolding**: Investment holdings (stocks, bonds, mutual funds)
- **InvestmentTransaction**: Investment transactions (buys, sells, dividends)
- **DebtAccount**: Debt accounts (loans, credit cards, mortgages)
- **DataSyncLog**: Logs of data synchronization attempts

### 2. Aggregation Service (`apps/records/aggregation_service.py`)

- **PlaidAggregationService**: Service class for Plaid API integration
  - `create_link_token()`: Creates Plaid Link token for OAuth flow
  - `exchange_public_token()`: Exchanges public token for access token
  - `sync_accounts()`: Syncs all account data (balances, transactions, investments)
  - `_fetch_accounts()`: Fetches accounts from Plaid
  - `_save_accounts()`: Saves account balances
  - `_sync_transactions()`: Syncs transactions (last 90 days)
  - `_sync_investment_holdings()`: Syncs investment holdings
  - `_sync_investment_transactions()`: Syncs investment transactions

- **AggregationServiceFactory**: Factory for creating appropriate service based on provider

### 3. Views (`apps/records/aggregation_views.py`)

- `link_account_view()`: Main view for account linking
- `create_link_token()`: API endpoint to create Plaid Link token
- `exchange_token()`: API endpoint to exchange public token and create linked accounts
- `linked_accounts_view()`: View showing all linked accounts
- `account_detail_view()`: Detailed view for a specific account
- `sync_account()`: Manually trigger sync for an account
- `disconnect_account()`: Disconnect a linked account
- `plaid_webhook()`: Handle webhooks from Plaid

### 4. Celery Tasks (`apps/records/tasks.py`)

- `sync_linked_account()`: Sync data for a single linked account
- `sync_all_accounts()`: Sync all active accounts (for scheduled tasks)

### 5. Templates

- `templates/records/link_account.html`: UI for linking accounts with Plaid Link integration

### 6. URLs (`apps/records/urls.py`)

Added routes for:
- `/records/link-account/` - Account linking page
- `/records/linked-accounts/` - List of linked accounts
- `/records/account/<id>/` - Account detail page
- `/records/api/create-link-token/` - Create Link token API
- `/records/api/exchange-token/` - Exchange token API
- `/records/api/sync-account/<id>/` - Sync account API
- `/records/api/disconnect-account/<id>/` - Disconnect account API
- `/records/webhooks/plaid/` - Plaid webhook endpoint

### 7. Settings (`portfolio_strategist/settings.py`)

Added configuration for:
- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `PLAID_ENVIRONMENT` (sandbox/development/production)
- `PLAID_WEBHOOK_URL`

### 8. Dependencies (`pyproject.toml`)

Added:
- `plaid-python>=11.0.0`
- `cryptography` (for encrypting tokens)

## Next Steps

### 1. Fix Plaid API Integration

The current implementation uses placeholder API patterns. You need to update `apps/records/aggregation_service.py` to use the correct Plaid Python SDK v11+ API:

```python
# Correct pattern for Plaid Python SDK v11+
from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.model import (
    CountryCode,
    Products,
    LinkTokenCreateRequest,
    LinkTokenCreateRequestUser,
    ItemPublicTokenExchangeRequest,
    AccountsGetRequest,
    TransactionsGetRequest,
    # ... etc
)

# Configuration
configuration = Configuration(
    host=Environment.sandbox,  # or Environment.development, Environment.production
    api_key={
        'clientId': client_id,
        'secret': secret,
    }
)
api_client = plaid_api.PlaidApi(configuration)

# Create link token
request = LinkTokenCreateRequest(
    products=[Products('transactions')],
    client_name="The Portfolio Strategist",
    country_codes=[CountryCode('US')],
    language='en',
    user=LinkTokenCreateRequestUser(
        client_user_id=str(user_id)
    ),
)
response = api_client.link_token_create(request)
link_token = response['link_token']
```

### 2. Create Database Migrations

Run:
```bash
python manage.py makemigrations records
python manage.py migrate
```

### 3. Set Up Aggregation Provider in Database

Create an `AggregationProvider` record via Django admin or management command:

```python
from apps.records.models import AggregationProvider

AggregationProvider.objects.create(
    name='plaid',
    display_name='Plaid',
    is_active=True,
    api_key='your_plaid_client_id',
    api_secret='your_plaid_secret',
    environment='sandbox',  # or 'development', 'production'
    webhook_url='https://yourdomain.com/records/webhooks/plaid/'
)
```

### 4. Encrypt Access Tokens

Currently, access tokens are stored in plain text. Implement encryption:

```python
from cryptography.fernet import Fernet

# In settings
FERNET_KEY = env('FERNET_KEY')  # Generate with: Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

# When saving
linked_account.access_token = cipher.encrypt(access_token.encode()).decode()

# When using
access_token = cipher.decrypt(linked_account.access_token.encode()).decode()
```

### 5. Schedule Periodic Syncs

Add to `django_celery_beat` schedule:

```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule

schedule, created = IntervalSchedule.objects.get_or_create(
    every=6,
    period=IntervalSchedule.HOURS,
)

PeriodicTask.objects.get_or_create(
    name='Sync All Linked Accounts',
    defaults={
        'task': 'apps.records.tasks.sync_all_accounts',
        'interval': schedule,
    }
)
```

### 6. Update Existing Views

Update `apps/records/views.py` and `apps/records/services.py` to:
- Show aggregated data alongside documents
- Use transactions from linked accounts for insights
- Combine document-based and API-based data

### 7. Add Error Handling

- Handle expired tokens
- Handle disconnected accounts
- Handle API rate limits
- Retry failed syncs

### 8. Add Tests

Create tests for:
- Account linking flow
- Data synchronization
- Webhook handling
- Error scenarios

## Usage Flow

1. **User clicks "Link Account"** → `link_account_view()`
2. **Frontend calls `/api/create-link-token/`** → Gets Plaid Link token
3. **Plaid Link opens** → User selects institution and logs in
4. **Plaid returns public_token** → Frontend calls `/api/exchange-token/`
5. **Backend exchanges token** → Creates `LinkedAccount` records
6. **Celery task syncs data** → Fetches accounts, transactions, investments
7. **Data appears in dashboard** → User can view transactions, balances, etc.
8. **Periodic syncs** → Celery task runs every 6 hours to update data
9. **Webhooks** → Plaid sends updates when new transactions occur

## Security Considerations

1. **Encrypt access tokens** in database
2. **Use HTTPS** for all API endpoints
3. **Validate webhook signatures** from Plaid
4. **Store API keys** in environment variables, not code
5. **Implement rate limiting** for API endpoints
6. **Log all access** to financial data
7. **Comply with PCI-DSS** if handling payment data

## Supported Providers

Currently implemented:
- **Plaid** (fully implemented, needs API fixes)

Can be extended to:
- **Yodlee**
- **Finicity (Mastercard)**
- **MX**
- **Stripe Financial Connections**
- **Flinks**
- **Akoya**

## Data Mapping

The aggregated data maps to existing document categories:

- **Bank Accounts** → `earnings`, `budgeting`
- **Credit Cards** → `debt`
- **Investment Accounts** → `investments`, `retirement`
- **Loans** → `debt`
- **Mortgages** → `debt`, `assets`

This allows the existing insights and explorer views to work with both document-based and API-based data.

