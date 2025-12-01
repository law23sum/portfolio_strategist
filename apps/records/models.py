from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator

from apps.users.models import CustomUser


class Receipt(models.Model):
    # ImageField to store the uploaded photo of the receipt
    image = models.ImageField(upload_to = 'receipts/')

    # Fields for receipt details
    title = models.CharField(max_length = 255)  # Title of the receipt
    amount = models.DecimalField(max_digits = 10, decimal_places = 2)  # Total amount
    date = models.DateField()  # Date of the receipt

    def __str__(self):
        return f"Receipt {self.title} - {self.amount}"


class FinancialDocument(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='financial_documents',
        null=True,  # Temporary to allow existing records
        blank=True
    )
    # Main record type choices (unchanged)
    RECORD_TYPE_CHOICES = [
        ('earnings', "Earnings"),
        ('government', "Governemnt"),
        ('retirement', "Retirement"),
        ('insurance', "Insurance"),
        ('debt', "Debt"),
        ('investments', "Investments"),
        ('budgeting', "Budgeting"),
        ('assets', "Assets"),
        ('credit_score', "Credit Score"),
    ]

    # Here is the brand-new, fully loaded SUBCATEGORY_OPTIONS!
    SUBCATEGORY_OPTIONS = {
        'earnings'    : [
            ('pay_stubs', 'Pay stubs'),
            ('w2_forms', 'W-2 forms'),
            ('1099_forms', '1099 forms (for freelance or contract work)'),
            ('bank_statements', 'Bank statements showing direct deposits'),
            ('tax_returns', 'Tax returns (income sections)'),
            ('bonus_commission', 'Bonus or commission statements'),
            ('profit_sharing', 'Profit-sharing statements'),
            ('dividend_income', 'Dividend income records'),
            ('royalty_income', 'Royalty income statements'),
            ('alimony_child_support', 'Alimony or child support records'),
            ],
        'government'  : [
            ('social_security', 'Social Security statements'),
            ('tax_assessment', 'Tax assessment notices'),
            ('gov_benefits', 'Government benefit statements'),
            ('stimulus_payments', 'Stimulus payment records'),
            ('irs_notices', 'IRS notices or correspondence'),
            ('property_tax_bills', 'Property tax bills'),
            ('fafsa_records', 'FAFSA records (for student aid)'),
            ('veterans_benefits', 'Veterans benefits statements'),
            ('medicare_medicaid', 'Medicare/Medicaid statements'),
            ('court_ordered', 'Court-ordered financial documents'),
            ],
        'retirement'  : [
            ('401k_statements', '401(k) statements'),
            ('ira_statements', 'IRA (Traditional or Roth) statements'),
            ('pension_plan_summaries', 'Pension plan summaries'),
            ('annuity_contracts', 'Annuity contracts'),
            ('ss_benefit_estimates', 'Social Security benefit estimates'),
            ('retirement_contributions', 'Retirement account contribution records'),
            ('rmd_notices', 'Required Minimum Distribution (RMD) notices'),
            ('rollover_docs', 'Rollover documentation'),
            ('beneficiary_designations', 'Beneficiary designation forms'),
            ('retirement_withdrawals', 'Retirement plan withdrawal records'),
            ],
        'insurance'   : [
            ('policy_docs', 'Policy documents (life, health, auto, home, etc.)'),
            ('premium_receipts', 'Premium payment receipts'),
            ('claims_history', 'Claims history records'),
            ('deductible_coverage', 'Deductible and coverage summaries'),
            ('insurance_id_cards', 'Insurance ID cards'),
            ('declarations_pages', 'Declarations pages'),
            ('renewal_notices', 'Renewal notices'),
            ('settlement_offers', 'Settlement offers'),
            ('umbrella_policy', 'Umbrella insurance policies'),
            ('long_term_care', 'Long-term care insurance documents'),
            ],
        'debt'        : [
            ('loan_agreements', 'Loan agreements (personal, auto, student, etc.)'),
            ('credit_card_statements', 'Credit card statements'),
            ('mortgage_statements', 'Mortgage statements'),
            ('debt_collection_notices', 'Debt collection notices'),
            ('payment_history', 'Payment history records'),
            ('promissory_notes', 'Promissory notes'),
            ('debt_settlement', 'Debt settlement agreements'),
            ('bankruptcy_filings', 'Bankruptcy filings'),
            ('credit_counseling', 'Credit counseling reports'),
            ('cosigned_loans', 'Co-signed loan documents'),
            ],
        'investments' : [
            ('brokerage_statements', 'Brokerage account statements'),
            ('stock_bond_certificates', 'Stock or bond certificates'),
            ('mutual_fund_statements', 'Mutual fund statements'),
            ('real_estate_investments', 'Real estate investment records'),
            ('crypto_transactions', 'Cryptocurrency transaction history'),
            ('investment_performance', 'Investment performance reports'),
            ('capital_gains_losses', 'Capital gains/loss statements'),
            ('drip_records', 'Dividend reinvestment plans (DRIPs)'),
            ('prospectuses', 'Prospectuses for investments'),
            ('partnership_investments', 'Partnership or LLC investment records'),
            ],
        'budgeting'   : [
            ('monthly_budgets', 'Monthly budget spreadsheets'),
            ('expense_tracking', 'Expense tracking logs'),
            ('savings_goals', 'Savings goal trackers'),
            ('spending_breakdowns', 'Spending category breakdowns'),
            ('cash_flow_statements', 'Cash flow statements'),
            ('financial_planning_worksheets', 'Financial planning worksheets'),
            ('subscriptions', 'Subscription or membership records'),
            ('utility_bills', 'Utility bills'),
            ('grocery_dining_logs', 'Grocery and dining expense logs'),
            ('entertainment_spending', 'Entertainment and leisure spending records'),
            ],
        'assets'      : [
            ('property_deeds', 'Property deeds (real estate)'),
            ('vehicle_titles', 'Vehicle titles'),
            ('appraisals', 'Appraisals (jewelry, art, etc.)'),
            ('inventory', 'Inventory of personal belongings'),
            ('business_docs', 'Business ownership documents'),
            ('trust_fund_statements', 'Trust fund statements'),
            ('inheritance_records', 'Inheritance records'),
            ('collectibles', 'Collectibles valuation reports'),
            ('intellectual_property', 'Intellectual property documents'),
            ('lease_agreements', 'Lease agreements (if renting out property)'),
            ],
        'credit_score': [
            ('credit_reports', 'Credit reports (Equifax, Experian, TransUnion)'),
            ('credit_monitoring', 'Credit monitoring service updates'),
            ('credit_card_utilization', 'Credit card utilization summaries'),
            ('loan_approvals_denials', 'Loan approval/denial letters'),
            ('inquiry_records', 'Hard and soft inquiry records'),
            ('dispute_letters', 'Dispute resolution letters'),
            ('credit_score_improvement', 'Credit score improvement plans'),
            ('identity_theft_reports', 'Identity theft reports'),
            ('credit_counseling_notes', 'Credit counseling session notes'),
            ('payment_history_reports', 'Payment history reports (on-time/late payments)'),
            ],
        }

    YEARS = [(y, str(y)) for y in range(1970, 2100)]

    original_name = models.CharField(max_length = 255)
    record_type = models.CharField(max_length = 50, choices = RECORD_TYPE_CHOICES)
    sub_record_type = models.CharField(max_length = 50, choices = SUBCATEGORY_OPTIONS)
    year = models.IntegerField(choices = YEARS)
    document = models.FileField(upload_to='financial_documents/')
    processed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        """
        Update the `name` field before saving,
        concatenating original_name, record type label, and year.
        """
        record_type_label = dict(self.RECORD_TYPE_CHOICES).get(self.record_type, 'Unknown Type')
        subcategory_options = self.SUBCATEGORY_OPTIONS.get(self.record_type, [])
        subcategory_dict = dict(subcategory_options)
        sub_record_type_label = subcategory_dict.get(self.sub_record_type, 'Unknown Type')
        self.original_name = self.original_name.replace(" ", "_")
        self.name = f"{self.original_name}_{record_type_label}_{sub_record_type_label}_{self.year}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ExtractedField(models.Model):
    document = models.ForeignKey(FinancialDocument, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=255)
    field_value = models.TextField()

    def __str__(self):
        return f"{self.field_name}: {self.field_value}"


# Financial Data Aggregation Models

class AggregationProvider(models.Model):
    """Supported financial data aggregation providers (Plaid, Yodlee, Finicity, etc.)"""
    PROVIDER_CHOICES = [
        ('plaid', 'Plaid'),
        ('yodlee', 'Yodlee'),
        ('finicity', 'Finicity (Mastercard)'),
        ('mx', 'MX'),
        ('stripe_financial', 'Stripe Financial Connections'),
        ('flinks', 'Flinks'),
        ('akoya', 'Akoya'),
    ]
    
    name = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True, help_text="Encrypted API key")
    api_secret = models.CharField(max_length=255, blank=True, help_text="Encrypted API secret")
    environment = models.CharField(max_length=20, choices=[('sandbox', 'Sandbox'), ('development', 'Development'), ('production', 'Production')], default='sandbox')
    webhook_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class LinkedAccount(models.Model):
    """Represents a user's linked financial account (bank, brokerage, credit card, etc.)"""
    ACCOUNT_TYPE_CHOICES = [
        ('depository', 'Bank Account'),
        ('credit', 'Credit Card'),
        ('loan', 'Loan'),
        ('investment', 'Investment Account'),
        ('brokerage', 'Brokerage Account'),
        ('retirement', 'Retirement Account'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('error', 'Error'),
        ('disconnected', 'Disconnected'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='linked_accounts')
    provider = models.ForeignKey(AggregationProvider, on_delete=models.PROTECT, related_name='linked_accounts')
    
    # Provider-specific identifiers
    provider_account_id = models.CharField(max_length=255, db_index=True, help_text="Account ID from aggregation provider")
    provider_item_id = models.CharField(max_length=255, db_index=True, help_text="Item ID from aggregation provider (e.g., Plaid item_id)")
    access_token = models.TextField(help_text="Encrypted access token for fetching data")
    
    # Account details
    institution_name = models.CharField(max_length=255)
    institution_id = models.CharField(max_length=255, blank=True)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES)
    account_subtype = models.CharField(max_length=100, blank=True)
    account_number_masked = models.CharField(max_length=50, blank=True, help_text="Last 4 digits or masked account number")
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    next_sync_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata from provider
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['user', 'provider', 'provider_account_id']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['provider', 'provider_account_id']),
        ]
    
    def __str__(self):
        return f"{self.institution_name} - {self.account_name} ({self.user.email})"


class AccountBalance(models.Model):
    """Current and historical balances for linked accounts"""
    account = models.ForeignKey(LinkedAccount, on_delete=models.CASCADE, related_name='balances')
    
    # Balance information
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2)
    limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Credit limit for credit cards")
    
    # Currency
    currency_code = models.CharField(max_length=3, default='USD')
    
    # Timestamp
    balance_date = models.DateTimeField()
    
    # Additional data from provider
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-balance_date']
        indexes = [
            models.Index(fields=['account', '-balance_date']),
        ]
        get_latest_by = 'balance_date'
    
    def __str__(self):
        return f"{self.account.account_name}: ${self.current_balance} ({self.balance_date.date()})"


class FinancialTransaction(models.Model):
    """Transactions from linked accounts"""
    TRANSACTION_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
        ('transfer', 'Transfer'),
    ]
    
    account = models.ForeignKey(LinkedAccount, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction identifiers
    transaction_id = models.CharField(max_length=255, db_index=True, help_text="Provider transaction ID")
    provider_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Transaction details
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    date = models.DateField(db_index=True)
    authorized_date = models.DateField(null=True, blank=True)
    
    # Categorization
    category = models.CharField(max_length=100, blank=True)
    category_detail = models.CharField(max_length=255, blank=True)
    merchant_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Payment details
    payment_channel = models.CharField(max_length=50, blank=True)
    pending = models.BooleanField(default=False)
    
    # Location (if available)
    location = models.JSONField(default=dict, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = [['account', 'transaction_id']]
        indexes = [
            models.Index(fields=['account', '-date']),
            models.Index(fields=['date', 'category']),
            models.Index(fields=['account', 'pending']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name}: ${self.amount} - {self.description[:50]} ({self.date})"


class InvestmentHolding(models.Model):
    """Investment holdings (stocks, bonds, mutual funds, etc.) from brokerage/retirement accounts"""
    account = models.ForeignKey(LinkedAccount, on_delete=models.CASCADE, related_name='holdings')
    
    # Security information
    security_id = models.CharField(max_length=255, db_index=True)
    security_name = models.CharField(max_length=255)
    security_ticker = models.CharField(max_length=20, blank=True)
    security_type = models.CharField(max_length=100, blank=True)
    
    # Holding details
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    cost_basis = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Currency
    currency_code = models.CharField(max_length=3, default='USD')
    
    # Timestamp
    as_of_date = models.DateTimeField()
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-as_of_date', 'security_name']
        unique_together = [['account', 'security_id', 'as_of_date']]
        indexes = [
            models.Index(fields=['account', '-as_of_date']),
            models.Index(fields=['security_ticker']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name}: {self.security_name} - {self.quantity} @ ${self.price or 0}"


class InvestmentTransaction(models.Model):
    """Investment transactions (buys, sells, dividends, etc.)"""
    TRANSACTION_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
        ('interest', 'Interest'),
        ('transfer', 'Transfer'),
        ('fee', 'Fee'),
        ('other', 'Other'),
    ]
    
    account = models.ForeignKey(LinkedAccount, on_delete=models.CASCADE, related_name='investment_transactions')
    
    # Transaction identifiers
    transaction_id = models.CharField(max_length=255, db_index=True)
    provider_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Security information
    security_id = models.CharField(max_length=255, blank=True)
    security_name = models.CharField(max_length=255, blank=True)
    security_ticker = models.CharField(max_length=20, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date = models.DateField(db_index=True)
    
    # Fees and costs
    fees = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Currency
    currency_code = models.CharField(max_length=3, default='USD')
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = [['account', 'transaction_id']]
        indexes = [
            models.Index(fields=['account', '-date']),
            models.Index(fields=['date', 'transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name}: {self.transaction_type} {self.security_name or 'N/A'} - ${self.amount} ({self.date})"


class DebtAccount(models.Model):
    """Debt accounts (loans, credit cards, mortgages) extracted from linked accounts"""
    account = models.ForeignKey(LinkedAccount, on_delete=models.CASCADE, related_name='debt_accounts')
    
    # Debt details
    debt_type = models.CharField(max_length=50, choices=[
        ('credit_card', 'Credit Card'),
        ('mortgage', 'Mortgage'),
        ('auto_loan', 'Auto Loan'),
        ('student_loan', 'Student Loan'),
        ('personal_loan', 'Personal Loan'),
        ('other', 'Other'),
    ])
    
    # Balance information
    current_balance = models.DecimalField(max_digits=15, decimal_places=2)
    original_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Interest and terms
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Annual percentage rate")
    minimum_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    next_payment_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Timestamp
    as_of_date = models.DateTimeField()
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-as_of_date']
        indexes = [
            models.Index(fields=['account', '-as_of_date']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name}: {self.debt_type} - ${self.current_balance}"


class DataSyncLog(models.Model):
    """Log of data synchronization attempts for linked accounts"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('partial', 'Partial'),
    ]
    
    account = models.ForeignKey(LinkedAccount, on_delete=models.CASCADE, related_name='sync_logs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # Sync results
    accounts_synced = models.IntegerField(default=0)
    transactions_synced = models.IntegerField(default=0)
    balances_synced = models.IntegerField(default=0)
    holdings_synced = models.IntegerField(default=0)
    
    # Error information
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['account', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.account.account_name}: {self.status} at {self.started_at}"


# Investment & Savings Assessment Models

class StocksAssessment(models.Model):
    """User's stock investment assessment"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='stocks_assessments')
    linked_account = models.ForeignKey(LinkedAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Link to Plaid account")
    
    symbol = models.CharField(max_length=10, db_index=True)
    investment_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    share_quantity = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Forecast data for different time periods
    forecast_data = models.JSONField(default=dict, blank=True)  # Stores forecasts for current, monthly, biyearly, yearly, decade
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = [['user', 'symbol']]
    
    def __str__(self):
        return f"{self.user.email} - {self.symbol}"


class SavingsAssessment(models.Model):
    """User's savings account assessment"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='savings_assessments')
    linked_account = models.ForeignKey(LinkedAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Link to Plaid account")
    
    account_name = models.CharField(max_length=255, default="Savings Account")
    initial_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    compounding_frequency = models.IntegerField(default=12, choices=[(1, 'Annually'), (2, 'Semi-Annually'), (4, 'Quarterly'), (12, 'Monthly'), (365, 'Daily')])
    
    # Forecast data for different time periods
    forecast_data = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.account_name}"


class CDAssessment(models.Model):
    """User's Certificate of Deposit assessment"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cd_assessments')
    linked_account = models.ForeignKey(LinkedAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Link to Plaid account")
    
    account_name = models.CharField(max_length=255, default="CD Account")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    compounding_frequency = models.IntegerField(default=12, choices=[(1, 'Annually'), (2, 'Semi-Annually'), (4, 'Quarterly'), (12, 'Monthly'), (365, 'Daily')])
    
    # Forecast data
    forecast_data = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.account_name}"


class BondAssessment(models.Model):
    """User's bond investment assessment"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bond_assessments')
    linked_account = models.ForeignKey(LinkedAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Link to Plaid account")
    
    account_name = models.CharField(max_length=255, default="Bond Investment")
    face_value = models.DecimalField(max_digits=15, decimal_places=2)
    coupon_rate = models.DecimalField(max_digits=5, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    years_to_maturity = models.DecimalField(max_digits=5, decimal_places=2)
    payment_frequency = models.IntegerField(default=2, choices=[(1, 'Annually'), (2, 'Semi-Annually'), (4, 'Quarterly'), (12, 'Monthly')])
    
    # Forecast data
    forecast_data = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.account_name}"
