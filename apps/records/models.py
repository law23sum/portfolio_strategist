from django.db import models

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
        ('earnings', "Earnings"
         ),
        ('government', "Government"
         ),
        ('retirement', "Retirement"
         ),
        ('insurance', "Insurance"
         ),
        ('debt', "Debt"
         ),
        ('investments', "Investments"
         ),
        ('budgeting', "Budgeting"
         ),
        ('assets', "Assets"
         ),
        ('credit_score', "Credit Score"
         ),
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