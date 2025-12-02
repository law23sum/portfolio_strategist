# Plaid API Data Distribution Flow

## Overview

After successful Plaid login, the system **directly fetches data from Plaid APIs** and distributes it to corresponding web pages. Data is fetched in real-time from Plaid APIs, cached for performance, and sent to web pages immediately.

## Flow Diagram

```
1. User logs in via Plaid
   ↓
2. PlaidAuthExchangeView / exchange_token() called
   ↓
3. PlaidDataDistributionService.distribute_plaid_data() runs automatically
   ↓
4. Fetches directly from Plaid APIs:
   - Identity API → identity data
   - Accounts API → account balances
   - Transactions API → transaction history
   - Investments Holdings API → investment holdings
   - Investments Transactions API → investment transactions
   ↓
5. Data cached in Django cache (1 hour TTL)
   ↓
6. Data also stored in database (background sync)
   ↓
7. User visits web page
   ↓
8. View calls get_organized_plaid_data()
   ↓
9. Fetches from cache (or fresh from APIs if cache expired)
   ↓
10. Organizes data by page/category
   ↓
11. Passes to template as JSON
   ↓
12. JavaScript auto-populates form fields
```

## Plaid APIs Used

### 1. Identity API (`identity_get`)
**Fetches:** Personal information
- Names
- Email addresses
- Phone numbers
- Physical addresses

**Used by:** Profile pages, personal data forms

### 2. Accounts API (`accounts_get`)
**Fetches:** Account information
- Account balances (current, available)
- Account types (depository, investment, credit, loan)
- Account subtypes (checking, savings, 401k, IRA, etc.)
- Account limits (for credit cards)
- Currency information

**Used by:** All assessment pages

### 3. Transactions API (`transactions_get`)
**Fetches:** Transaction history (last 90 days)
- Transaction amounts
- Transaction dates
- Merchant names
- Categories
- Payment channels
- Pending status

**Used by:** Budget Planner (income/expense calculations)

### 4. Investments Holdings API (`investments_holdings_get`)
**Fetches:** Investment holdings
- Securities (stocks, bonds, mutual funds)
- Quantities
- Prices
- Values

**Used by:** Stocks Assessment, Bond Assessment

### 5. Investments Transactions API (`investments_transactions_get`)
**Fetches:** Investment transaction history
- Buys, sells, dividends
- Dates and amounts

**Used by:** Investment tracking pages

## Implementation Details

### After Login: `distribute_plaid_data()`

```python
# Fetches directly from Plaid APIs
identity_data = service.get_identity(access_token)
accounts_data = service._fetch_accounts(access_token)
transactions_data = service.client.transactions_get(...)
investment_holdings = service._sync_investment_holdings(...)
investment_transactions = service._sync_investment_transactions(...)

# Caches for immediate access
cache.set(f"plaid_data_{user.id}", {
    'identity': identity_data,
    'accounts': accounts_data,
    'transactions': transactions_data,
    'investment_holdings': investment_holdings,
    'investment_transactions': investment_transactions,
}, timeout=3600)
```

### When Page Loads: `get_organized_plaid_data()`

```python
# 1. Try cache first (fastest)
cached_data = cache.get(f"plaid_data_{user.id}")

# 2. If cache miss, fetch fresh from Plaid APIs
if not cached_data:
    identity_data = service.get_identity(access_token)
    accounts_data = service._fetch_accounts(access_token)
    transactions_data = service.client.transactions_get(...)

# 3. Fall back to database if APIs fail
if not accounts_data:
    accounts_data = get_from_database()

# 4. Organize by page
organized_data = {
    'budget_planner': {...},
    'stocks_assessment': {...},
    'savings_assessment': {...},
    ...
}
```

## Data Organization by Page

### Budget Planner
**Source APIs:** Accounts API, Transactions API

**Data Provided:**
- `checking_balance` - Sum of checking accounts
- `savings_balance` - Sum of savings accounts
- `total_cash` - Checking + Savings
- `monthly_income` - Calculated from transactions (deposits)
- `annual_salary` - Monthly income × 12
- `monthly_expenses` - Calculated from transactions (withdrawals)
- `debt_payments` - Estimated from credit/loan accounts

**Plaid API Calls:**
```python
# Get accounts
accounts = service._fetch_accounts(access_token)
# Filter depository accounts
checking_accounts = [a for a in accounts if a['type'] == 'depository' and 'checking' in a['subtype']]

# Get transactions
transactions = service.client.transactions_get(...)
# Calculate income (positive amounts)
income = sum(tx['amount'] for tx in transactions if tx['amount'] > 0)
```

### Stocks Assessment
**Source APIs:** Accounts API, Investments Holdings API

**Data Provided:**
- `investment_amount` - Sum of investment/brokerage accounts
- `accounts` - List of investment accounts with balances

**Plaid API Calls:**
```python
# Get investment accounts
accounts = service._fetch_accounts(access_token)
investment_accounts = [a for a in accounts if a['type'] in ['investment', 'brokerage']]

# Get holdings (if available)
holdings = service._sync_investment_holdings(linked_account, access_token)
```

### Savings Assessment
**Source APIs:** Accounts API

**Data Provided:**
- `initial_deposit` - Highest savings account balance
- `account_name` - Name of the account
- `accounts` - List of savings accounts

**Plaid API Calls:**
```python
# Get savings accounts
accounts = service._fetch_accounts(access_token)
savings_accounts = [a for a in accounts if a['type'] == 'depository' and 'savings' in a['subtype']]
```

### CD Assessment
**Source APIs:** Accounts API

**Data Provided:**
- `cd_amount` - CD account balance
- `account_name` - Name of the CD account

**Plaid API Calls:**
```python
# Get CD accounts
accounts = service._fetch_accounts(access_token)
cd_accounts = [a for a in accounts if a['type'] == 'depository' and 'cd' in a['subtype']]
```

### Bond Assessment
**Source APIs:** Accounts API, Investments Holdings API

**Data Provided:**
- `face_value` - Investment account balance
- `purchase_price` - Investment account balance
- `account_name` - Name of the account

**Plaid API Calls:**
```python
# Get investment accounts
accounts = service._fetch_accounts(access_token)
investment_accounts = [a for a in accounts if a['type'] in ['investment', 'brokerage']]
```

## Caching Strategy

1. **Cache on Login:** Data fetched from APIs is cached for 1 hour
2. **Cache Key:** `plaid_data_{user_id}`
3. **Cache Contents:**
   - Identity data
   - Accounts data
   - Transactions data
   - Investment holdings
   - Investment transactions
   - Timestamp

4. **Cache Invalidation:**
   - Expires after 1 hour
   - Refreshed on next page load if expired
   - Background sync updates database

## Benefits of Direct API Fetching

✅ **Real-time Data** - Always fresh from Plaid
✅ **Fast Access** - Cached for performance
✅ **Complete Data** - All Plaid APIs utilized
✅ **Reliable Fallback** - Database backup if APIs fail
✅ **No Manual Import** - Automatic after login

## Error Handling

1. **API Failure:** Falls back to database
2. **Cache Miss:** Fetches fresh from APIs
3. **Missing Data:** Uses defaults, doesn't break pages
4. **Rate Limits:** Cached data prevents excessive API calls

## Example: Complete Flow

1. **User logs in with Plaid**
   - `distribute_plaid_data()` called automatically
   - Fetches: Identity, Accounts, Transactions, Investments
   - Caches all data

2. **User visits Budget Planner**
   - `get_organized_plaid_data()` called
   - Retrieves from cache (or fresh from APIs)
   - Organizes accounts by type
   - Calculates income/expenses from transactions
   - Returns organized data

3. **Template receives data**
   - `account_defaults` JSON passed to template
   - Contains all Plaid data organized for Budget Planner

4. **JavaScript auto-populates**
   - Fields filled with Plaid data
   - User sees pre-filled form
   - Can edit if needed

## API Rate Limits

Plaid has rate limits. The caching strategy helps:
- **Cache Duration:** 1 hour reduces API calls
- **Background Sync:** Updates database without blocking
- **Fallback:** Uses database if APIs unavailable

## Adding New Plaid APIs

To add a new Plaid API:

1. **Add API call** in `distribute_plaid_data()`:
```python
# Fetch new data
new_data = service.client.new_api_method(...)

# Cache it
cache_data['new_data'] = new_data
```

2. **Add to organization** in `get_organized_plaid_data()`:
```python
# Get from cache or API
new_data = cached_data.get('new_data', [])

# Organize for pages
organized_data['new_page']['new_field'] = process_new_data(new_data)
```

3. **Update views** to pass to templates
4. **Update templates** to use the data

