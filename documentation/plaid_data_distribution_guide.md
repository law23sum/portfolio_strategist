# Plaid Data Distribution Guide

## Overview

After a user successfully logs in with Plaid from the "Online Financial Accounts" page, all Plaid data is **automatically** aggregated, separated, and organized to corresponding web pages. No manual import is needed.

## Flow Diagram

```
1. User logs in via Plaid
   ↓
2. PlaidAuthExchangeView / exchange_token() called
   ↓
3. PlaidDataDistributionService.distribute_plaid_data() runs automatically
   ↓
4. Data stored in LinkedAccount models (accounts, balances, transactions)
   ↓
5. Identity data stored in LinkedAccount.metadata['plaid_identity']
   ↓
6. User visits web page (e.g., Budget Planner)
   ↓
7. View calls PlaidDataDistributionService.get_organized_plaid_data()
   ↓
8. Data organized by page/category and passed to template
   ↓
9. JavaScript auto-populates form fields on page load
```

## Step-by-Step Process

### Step 1: Plaid Login Triggers Distribution

When a user successfully links their Plaid account, two functions automatically call the distribution service:

**Location 1:** `apps/authentication/api_views.py` - `PlaidAuthExchangeView.post()`
```python
# After accounts are saved
PlaidDataDistributionService.distribute_plaid_data(
    user=user,
    access_token=access_token,
    identity_data=identity_data
)
```

**Location 2:** `apps/records/aggregation_views.py` - `exchange_token()`
```python
# After accounts are created
PlaidDataDistributionService.distribute_plaid_data(
    user=request.user,
    access_token=access_token,
    identity_data=identity_data
)
```

### Step 2: Data Storage

The `distribute_plaid_data()` method:
1. **Stores identity data** in `LinkedAccount.metadata['plaid_identity']`:
   - Names
   - Emails
   - Phone numbers
   - Addresses

2. **Stores account data** in `LinkedAccount` models:
   - Account balances → `AccountBalance` model
   - Transactions → `FinancialTransaction` model
   - Investment holdings → `InvestmentHolding` model

3. **Triggers background sync** to fetch transactions and other data

### Step 3: Data Organization by Page

When a user visits a web page, the view calls `get_organized_plaid_data()` which organizes data by page:

**Budget Planner** (`budget_planner`):
- `checking_balance` - Sum of all checking accounts
- `savings_balance` - Sum of all savings accounts
- `total_cash` - Checking + Savings
- `monthly_income` - Calculated from transactions
- `annual_salary` - Monthly income × 12
- `monthly_expenses` - Calculated from transactions
- `debt_payments` - Estimated from credit/loan accounts

**Stocks Assessment** (`stocks_assessment`):
- `investment_amount` - Sum of investment/brokerage accounts
- `accounts` - List of investment accounts

**Savings Assessment** (`savings_assessment`):
- `initial_deposit` - Highest savings account balance
- `account_name` - Name of the account
- `accounts` - List of savings accounts

**CD Assessment** (`cd_assessment`):
- `cd_amount` - CD account balance
- `account_name` - Name of the CD account
- `accounts` - List of CD accounts

**Bond Assessment** (`bond_assessment`):
- `face_value` - Investment account balance
- `purchase_price` - Investment account balance
- `account_name` - Name of the account
- `accounts` - List of investment accounts

### Step 4: View Passes Data to Template

Example from `apps/web/views.py` - `budget_planner()`:

```python
# Get organized Plaid data (automatically distributed after login)
plaid_data = PlaidDataDistributionService.get_organized_plaid_data(request.user)
plaid_budget_data = plaid_data.get('budget_planner', {})

# Merge with existing defaults (Plaid data takes precedence)
account_defaults = AccountDataService.get_budget_defaults(request.user)
account_defaults.update(plaid_budget_data)
account_defaults_json = json.dumps(account_defaults)

return render(request, "web/budget_planner.html", {
    "account_defaults": account_defaults_json,
    # ... other context
})
```

### Step 5: Template Auto-Populates Fields

The template receives the data as JSON and JavaScript automatically populates fields:

```javascript
// Auto-populate form fields with Plaid account data
document.addEventListener('DOMContentLoaded', function() {
    const defaults = {{ account_defaults|safe }};
    
    // Populate checking balance
    if (defaults.checking_balance > 0) {
        const checkingInput = document.getElementById('checkingBalance');
        if (checkingInput) {
            checkingInput.value = defaults.checking_balance.toFixed(2);
        }
    }
    
    // Populate savings balance
    if (defaults.savings_balance > 0) {
        const savingsInput = document.getElementById('savingsBalance');
        if (savingsInput) {
            savingsInput.value = defaults.savings_balance.toFixed(2);
        }
    }
    
    // ... more fields
});
```

## Data Organization Logic

### Account Type Mapping

The service categorizes accounts based on their type and subtype:

```python
# Budget Planner (depository accounts)
if account_type == 'depository':
    if 'checking' in subtype:
        → checking_balance
    elif 'savings' in subtype:
        → savings_balance + savings_assessment

# Stocks Assessment (investment accounts)
elif account_type in ['investment', 'brokerage']:
    → stocks_assessment.investment_amount

# CD Assessment (CD accounts)
elif account_type == 'depository' and 'cd' in subtype:
    → cd_assessment.cd_amount

# Bond Assessment (investment accounts)
elif account_type in ['investment', 'brokerage']:
    → bond_assessment.face_value

# Debt (credit/loan accounts)
elif account_type in ['credit', 'loan']:
    → budget_planner.debt_payments
```

### Transaction Analysis

For Budget Planner, the service analyzes transactions:
- **Income**: Sum of positive transactions (deposits)
- **Expenses**: Sum of negative transactions (withdrawals)
- **Monthly averages**: Calculated over last 90 days

## Key Files

1. **`apps/records/plaid_data_distribution.py`**
   - `PlaidDataDistributionService.distribute_plaid_data()` - Stores data after login
   - `PlaidDataDistributionService.get_organized_plaid_data()` - Organizes data by page

2. **`apps/web/views.py`**
   - Each view function calls `get_organized_plaid_data()` and passes to template

3. **`templates/web/*.html`**
   - JavaScript auto-populates form fields on page load

4. **`apps/records/aggregation_views.py`**
   - `exchange_token()` - Triggers distribution after account linking

5. **`apps/authentication/api_views.py`**
   - `PlaidAuthExchangeView` - Triggers distribution after Plaid auth

## Example: Complete Flow

1. **User logs in with Plaid** → Accounts saved to database
2. **Distribution service runs** → Identity stored, sync triggered
3. **User visits Budget Planner** → View fetches organized data
4. **Template receives data** → `account_defaults` JSON passed
5. **JavaScript runs** → Fields auto-populate with Plaid values
6. **User sees pre-filled form** → Ready to use or modify

## Benefits

✅ **Automatic** - No manual import needed
✅ **Organized** - Data separated by page/category
✅ **Real-time** - Uses latest account balances
✅ **Smart** - Calculates income/expenses from transactions
✅ **Flexible** - Users can still manually edit fields

## Adding New Pages

To add Plaid data distribution to a new page:

1. **Add data structure** in `get_organized_plaid_data()`:
```python
'new_page': {
    'field1': Decimal('0'),
    'field2': '',
    'accounts': [],
}
```

2. **Process accounts** in the same method:
```python
if account_type == 'relevant_type':
    organized_data['new_page']['field1'] += balance
```

3. **Update view** to fetch and pass data:
```python
plaid_data = PlaidDataDistributionService.get_organized_plaid_data(request.user)
new_page_data = plaid_data.get('new_page', {})
```

4. **Update template** to auto-populate:
```javascript
const plaidData = {{ plaid_data|safe }};
if (plaidData.field1 > 0) {
    document.getElementById('field1').value = plaidData.field1;
}
```

