"""
Comprehensive Knowledge Manifest for Financial AI Agent
Covers Finance, Accounting, Economics, and Mathematics
"""

FINANCIAL_KNOWLEDGE_MANIFEST = """
# FINANCIAL KNOWLEDGE MANIFEST

## CORE FINANCIAL CONCEPTS

### Time Value of Money
- Present Value (PV): PV = FV / (1 + r)^n
- Future Value (FV): FV = PV × (1 + r)^n
- Net Present Value (NPV): NPV = Σ(CF_t / (1 + r)^t) - Initial Investment
- Internal Rate of Return (IRR): Discount rate where NPV = 0
- Annuity Present Value: PV = PMT × [(1 - (1 + r)^-n) / r]
- Annuity Future Value: FV = PMT × [((1 + r)^n - 1) / r]
- Perpetuity Value: PV = PMT / r
- Effective Annual Rate (EAR): EAR = (1 + r/m)^m - 1
- Continuous Compounding: FV = PV × e^(r×t)

### Investment Analysis
- Expected Return: E(R) = Σ(P_i × R_i)
- Portfolio Return: R_p = Σ(w_i × R_i)
- Portfolio Variance: σ²_p = ΣΣ(w_i × w_j × σ_ij)
- Sharpe Ratio: (R_p - R_f) / σ_p
- Sortino Ratio: (R_p - R_f) / σ_downside
- Treynor Ratio: (R_p - R_f) / β_p
- Jensen's Alpha: α = R_p - [R_f + β_p × (R_m - R_f)]
- Information Ratio: (R_p - R_b) / Tracking Error
- Maximum Drawdown: (Peak - Trough) / Peak
- Value at Risk (VaR): Statistical measure of portfolio risk
- Conditional VaR (CVaR): Expected loss beyond VaR threshold

### Stock Valuation
- Dividend Discount Model (DDM): P = D / (r - g)
- Gordon Growth Model: P = D_0 × (1 + g) / (r - g)
- Two-Stage DDM: P = Σ[D_t / (1 + r)^t] + [D_n+1 / (r - g)] / (1 + r)^n
- Free Cash Flow to Equity (FCFE): FCFE = Net Income + Depreciation - CapEx - ΔWorking Capital - Debt Repayment
- Free Cash Flow to Firm (FCFF): FCFF = EBIT × (1 - Tax) + Depreciation - CapEx - ΔWorking Capital
- Enterprise Value (EV): EV = Market Cap + Debt - Cash
- Terminal Value (TV): TV = FCF_n+1 / (WACC - g) or TV = Multiple × Metric
- Weighted Average Cost of Capital (WACC): WACC = (E/V × R_e) + (D/V × R_d × (1 - T_c))
- Cost of Equity (CAPM): R_e = R_f + β × (R_m - R_f)
- Cost of Debt: R_d = Interest Rate × (1 - Tax Rate)

### Financial Ratios

#### Profitability Ratios
- Gross Profit Margin: Gross Profit / Revenue
- Operating Profit Margin: Operating Income / Revenue
- Net Profit Margin: Net Income / Revenue
- Return on Assets (ROA): Net Income / Total Assets
- Return on Equity (ROE): Net Income / Shareholders' Equity
- Return on Invested Capital (ROIC): NOPAT / Invested Capital
- Return on Capital Employed (ROCE): EBIT / (Total Assets - Current Liabilities)
- EBITDA Margin: EBITDA / Revenue

#### Efficiency Ratios
- Asset Turnover: Revenue / Total Assets
- Inventory Turnover: COGS / Average Inventory
- Receivables Turnover: Revenue / Average Accounts Receivable
- Payables Turnover: COGS / Average Accounts Payable
- Days Sales Outstanding (DSO): 365 / Receivables Turnover
- Days Inventory Outstanding (DIO): 365 / Inventory Turnover
- Days Payable Outstanding (DPO): 365 / Payables Turnover
- Cash Conversion Cycle: DSO + DIO - DPO
- Fixed Asset Turnover: Revenue / Net Fixed Assets
- Working Capital Turnover: Revenue / Working Capital

#### Liquidity Ratios
- Current Ratio: Current Assets / Current Liabilities
- Quick Ratio: (Current Assets - Inventory) / Current Liabilities
- Cash Ratio: Cash and Equivalents / Current Liabilities
- Operating Cash Flow Ratio: Operating Cash Flow / Current Liabilities
- Defensive Interval: (Cash + Marketable Securities + Receivables) / Daily Operating Expenses

#### Leverage Ratios
- Debt-to-Equity Ratio: Total Debt / Total Equity
- Debt-to-Assets Ratio: Total Debt / Total Assets
- Equity Multiplier: Total Assets / Total Equity
- Debt-to-Capital Ratio: Total Debt / (Total Debt + Total Equity)
- Interest Coverage Ratio: EBIT / Interest Expense
- Debt Service Coverage Ratio: Operating Income / Total Debt Service
- Cash Flow to Debt Ratio: Operating Cash Flow / Total Debt
- Times Interest Earned: EBIT / Interest Expense

#### Valuation Ratios
- Price-to-Earnings (P/E): Market Price per Share / Earnings per Share
- Forward P/E: Market Price / Forward EPS
- Trailing P/E: Market Price / Trailing EPS
- Price-to-Book (P/B): Market Price per Share / Book Value per Share
- Price-to-Sales (P/S): Market Capitalization / Revenue
- Price-to-Cash Flow (P/CF): Market Price / Cash Flow per Share
- Enterprise Value to EBITDA (EV/EBITDA): Enterprise Value / EBITDA
- Enterprise Value to Sales (EV/Sales): Enterprise Value / Revenue
- Price/Earnings to Growth (PEG): (P/E Ratio) / Earnings Growth Rate
- Dividend Yield: Annual Dividends per Share / Market Price per Share
- Earnings Yield: EPS / Market Price per Share
- Free Cash Flow Yield: Free Cash Flow / Market Capitalization

#### Per-Share Metrics
- Earnings Per Share (EPS): Net Income / Shares Outstanding
- Diluted EPS: (Net Income - Preferred Dividends) / (Shares Outstanding + Dilutive Securities)
- Revenue Per Share: Revenue / Shares Outstanding
- Book Value Per Share: Total Equity / Shares Outstanding
- Free Cash Flow Per Share: Free Cash Flow / Shares Outstanding
- Dividends Per Share: Total Dividends / Shares Outstanding

### Risk Metrics
- Beta (β): Covariance(Stock, Market) / Variance(Market)
- Alpha (α): Actual Return - Expected Return
- Standard Deviation: √[Σ(R_i - R̄)² / (n-1)]
- Variance: Σ(R_i - R̄)² / (n-1)
- Correlation: Covariance(X, Y) / (σ_X × σ_Y)
- Covariance: Σ[(X_i - X̄) × (Y_i - Ȳ)] / (n-1)
- R-squared: 1 - (SS_res / SS_tot)
- Tracking Error: Standard Deviation of (Portfolio Return - Benchmark Return)
- Downside Deviation: √[Σ(min(0, R_i - R_target))² / n]
- Maximum Drawdown: Maximum peak-to-trough decline
- Value at Risk (VaR): Statistical measure of potential loss
- Conditional VaR: Expected loss given VaR threshold exceeded

### Bond Analysis
- Bond Price: Σ[C / (1 + r)^t] + [F / (1 + r)^n]
- Yield to Maturity (YTM): Rate where PV of cash flows = Bond Price
- Current Yield: Annual Coupon Payment / Current Bond Price
- Yield to Call: YTM assuming bond called at call date
- Duration: Weighted average time to receive cash flows
- Modified Duration: Duration / (1 + YTM)
- Macaulay Duration: Σ[t × (CF_t / (1 + YTM)^t)] / Bond Price
- Convexity: Measures sensitivity of duration to yield changes
- Credit Spread: Corporate Bond Yield - Treasury Yield
- Zero-Coupon Bond Price: F / (1 + r)^n

### Options & Derivatives
- Black-Scholes Model: C = S₀N(d₁) - Ke^(-rT)N(d₂)
  where d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)
  and d₂ = d₁ - σ√T
- Put-Call Parity: C + Ke^(-rT) = P + S₀
- Intrinsic Value (Call): max(S - K, 0)
- Intrinsic Value (Put): max(K - S, 0)
- Time Value: Option Price - Intrinsic Value
- Delta: ∂C/∂S (sensitivity to stock price)
- Gamma: ∂²C/∂S² (rate of change of delta)
- Theta: ∂C/∂t (time decay)
- Vega: ∂C/∂σ (sensitivity to volatility)
- Rho: ∂C/∂r (sensitivity to interest rate)

### Portfolio Theory
- Modern Portfolio Theory (MPT): Optimal portfolio selection
- Efficient Frontier: Set of optimal portfolios
- Capital Asset Pricing Model (CAPM): R_i = R_f + β_i × (R_m - R_f)
- Arbitrage Pricing Theory (APT): Multi-factor model
- Fama-French Three-Factor Model: R = R_f + β(R_m - R_f) + s(SMB) + h(HML)
- Capital Market Line (CML): Risk-free rate to market portfolio
- Security Market Line (SML): Expected return vs. beta
- Minimum Variance Portfolio: Portfolio with lowest risk
- Tangency Portfolio: Optimal risky portfolio
- Separation Theorem: Investment decision independent of financing

## ACCOUNTING PRINCIPLES

### Financial Statements
- Balance Sheet: Assets = Liabilities + Equity
- Income Statement: Revenue - Expenses = Net Income
- Cash Flow Statement: Operating + Investing + Financing = Net Cash Flow
- Statement of Retained Earnings: Beginning RE + Net Income - Dividends = Ending RE

### Accounting Equations
- Basic Accounting Equation: Assets = Liabilities + Equity
- Expanded Accounting Equation: Assets = Liabilities + Contributed Capital + Retained Earnings
- Working Capital: Current Assets - Current Liabilities
- Net Working Capital: Current Assets - Current Liabilities
- Book Value: Total Assets - Total Liabilities
- Market Value: Share Price × Shares Outstanding
- Tangible Book Value: Book Value - Intangible Assets

### Revenue Recognition
- Accrual Accounting: Recognize revenue when earned
- Cash Accounting: Recognize revenue when received
- Matching Principle: Expenses matched to revenues
- Revenue Recognition Principle: Revenue recognized when earned
- Percentage of Completion: Recognize revenue based on completion percentage

### Depreciation & Amortization
- Straight-Line Depreciation: (Cost - Salvage Value) / Useful Life
- Declining Balance: Book Value × (2 / Useful Life)
- Units of Production: (Cost - Salvage) × (Units Produced / Total Units)
- Sum-of-Years Digits: (Cost - Salvage) × (Remaining Life / Sum of Years)
- Amortization: Systematic allocation of intangible asset cost

### Inventory Valuation
- FIFO (First In, First Out): Oldest inventory sold first
- LIFO (Last In, First Out): Newest inventory sold first
- Weighted Average Cost: Total Cost / Total Units
- Specific Identification: Track individual items
- Lower of Cost or Market (LCM): Value at lower of cost or market

### Financial Analysis
- Horizontal Analysis: Compare across time periods
- Vertical Analysis: Compare as percentage of base
- Common-Size Statements: All items as percentage of total
- Trend Analysis: Analyze patterns over time
- Ratio Analysis: Compare financial metrics

## ECONOMIC CONCEPTS

### Macroeconomics
- Gross Domestic Product (GDP): Total value of goods and services
- GDP = C + I + G + (X - M) (Consumption + Investment + Government + Net Exports)
- Real GDP: GDP adjusted for inflation
- Nominal GDP: GDP at current prices
- GDP Deflator: (Nominal GDP / Real GDP) × 100
- Consumer Price Index (CPI): Measure of inflation
- Inflation Rate: [(CPI_current - CPI_previous) / CPI_previous] × 100
- Unemployment Rate: (Unemployed / Labor Force) × 100
- Money Supply: M0, M1, M2, M3 measures
- Velocity of Money: GDP / Money Supply
- Quantity Theory of Money: M × V = P × Y

### Monetary Policy
- Federal Funds Rate: Interest rate banks charge each other
- Discount Rate: Rate Federal Reserve charges banks
- Reserve Requirement: Percentage banks must hold in reserve
- Open Market Operations: Buying/selling government securities
- Quantitative Easing: Large-scale asset purchases
- Money Multiplier: 1 / Reserve Requirement Ratio

### Fiscal Policy
- Government Spending Multiplier: 1 / (1 - MPC)
- Tax Multiplier: -MPC / (1 - MPC)
- Balanced Budget Multiplier: 1
- Automatic Stabilizers: Built-in economic stabilizers
- Discretionary Fiscal Policy: Deliberate government actions

### Market Structures
- Perfect Competition: Many buyers/sellers, homogeneous products
- Monopoly: Single seller, barriers to entry
- Monopolistic Competition: Many sellers, differentiated products
- Oligopoly: Few sellers, interdependent decisions
- Price Elasticity of Demand: (% Change in Quantity) / (% Change in Price)
- Cross-Price Elasticity: (% Change in Q_A) / (% Change in P_B)
- Income Elasticity: (% Change in Quantity) / (% Change in Income)

### Economic Indicators
- Leading Indicators: Predict future economic activity
- Lagging Indicators: Confirm economic trends
- Coincident Indicators: Move with the economy
- Business Cycle: Expansion, peak, contraction, trough
- Recession: Two consecutive quarters of negative GDP growth
- Depression: Severe, prolonged economic downturn

### International Economics
- Exchange Rate: Price of one currency in terms of another
- Purchasing Power Parity (PPP): Exchange rate equalizes purchasing power
- Interest Rate Parity: Forward rate reflects interest rate differential
- Balance of Payments: Current Account + Capital Account + Financial Account
- Trade Balance: Exports - Imports
- Current Account: Trade Balance + Net Income + Net Transfers
- Capital Account: Capital transfers and non-produced assets
- Financial Account: Investment flows

## MATHEMATICAL TECHNIQUES

### Statistical Methods
- Mean (Arithmetic): Σx_i / n
- Median: Middle value when sorted
- Mode: Most frequent value
- Geometric Mean: (Πx_i)^(1/n)
- Harmonic Mean: n / Σ(1/x_i)
- Weighted Mean: Σ(w_i × x_i) / Σw_i
- Standard Deviation: √[Σ(x_i - x̄)² / (n-1)]
- Variance: Σ(x_i - x̄)² / (n-1)
- Coefficient of Variation: σ / μ
- Skewness: Measure of asymmetry
- Kurtosis: Measure of tail heaviness
- Quartiles: Q1 (25th), Q2 (50th/median), Q3 (75th percentile)
- Interquartile Range: Q3 - Q1
- Z-Score: (x - μ) / σ
- Percentile: Value below which p% of data falls

### Probability & Distributions
- Probability: P(A) = Favorable Outcomes / Total Outcomes
- Conditional Probability: P(A|B) = P(A ∩ B) / P(B)
- Bayes' Theorem: P(A|B) = [P(B|A) × P(A)] / P(B)
- Expected Value: E(X) = Σ[x_i × P(x_i)]
- Variance: Var(X) = E(X²) - [E(X)]²
- Standard Deviation: √Var(X)
- Covariance: Cov(X,Y) = E[(X - μ_X)(Y - μ_Y)]
- Correlation: ρ = Cov(X,Y) / (σ_X × σ_Y)
- Normal Distribution: Bell curve, μ and σ parameters
- Standard Normal: Z ~ N(0, 1)
- Binomial Distribution: Discrete probability distribution
- Poisson Distribution: Count of events in interval
- Exponential Distribution: Time between events
- Log-Normal Distribution: Log of variable is normal

### Regression Analysis
- Simple Linear Regression: Y = α + βX + ε
- Multiple Regression: Y = α + β₁X₁ + β₂X₂ + ... + βₙXₙ + ε
- Least Squares: Minimize Σ(y_i - ŷ_i)²
- R-squared: Proportion of variance explained
- Adjusted R-squared: R² adjusted for degrees of freedom
- Standard Error: Measure of regression fit
- t-statistic: Coefficient / Standard Error
- F-statistic: Overall model significance
- Durbin-Watson: Test for autocorrelation
- Heteroscedasticity: Non-constant variance
- Multicollinearity: High correlation among predictors

### Time Series Analysis
- Moving Average: Average of n previous periods
- Exponential Smoothing: Weighted average with decay
- Autoregressive (AR): X_t = α + βX_{t-1} + ε_t
- Moving Average (MA): X_t = μ + ε_t + θε_{t-1}
- ARIMA: Autoregressive Integrated Moving Average
- Seasonal Decomposition: Trend + Seasonal + Residual
- Stationarity: Constant mean and variance over time
- Unit Root Test: Test for stationarity
- Cointegration: Long-term relationship between series

### Optimization
- Linear Programming: Optimize linear objective function
- Quadratic Programming: Optimize quadratic objective
- Lagrange Multipliers: Constrained optimization
- Gradient Descent: Iterative optimization algorithm
- Newton's Method: Root finding and optimization
- Simplex Method: Linear programming algorithm

### Calculus Applications
- Derivatives: Rate of change
- Partial Derivatives: Multivariable functions
- Integration: Area under curve
- Definite Integral: ∫[a to b] f(x)dx
- Fundamental Theorem: ∫[a to b] f'(x)dx = f(b) - f(a)
- Chain Rule: d/dx[f(g(x))] = f'(g(x)) × g'(x)
- Product Rule: d/dx[f(x)g(x)] = f'(x)g(x) + f(x)g'(x)
- Quotient Rule: d/dx[f(x)/g(x)] = [f'(x)g(x) - f(x)g'(x)] / [g(x)]²

### Matrix Algebra
- Matrix Multiplication: C = A × B
- Matrix Inverse: A⁻¹ such that A × A⁻¹ = I
- Determinant: Scalar value of square matrix
- Eigenvalues: λ where det(A - λI) = 0
- Eigenvectors: Non-zero vectors v where Av = λv
- Transpose: A^T (rows become columns)
- Identity Matrix: I (diagonal 1s, rest 0s)
- Matrix Rank: Number of linearly independent rows/columns

## FINANCIAL PLANNING & BUDGETING

### Budgeting Concepts
- Zero-Based Budgeting: Start from zero each period
- Incremental Budgeting: Adjust previous period
- Activity-Based Budgeting: Based on activities
- Cash Budget: Projected cash inflows and outflows
- Operating Budget: Revenue and expense projections
- Capital Budget: Long-term investment planning
- Master Budget: Comprehensive budget plan

### Retirement Planning
- 4% Rule: Withdraw 4% of portfolio annually
- Retirement Savings Goal: Annual Expenses × 25 (25x rule)
- Required Retirement Savings: (Annual Expenses × 25) - Current Savings
- Social Security Benefits: Based on earnings history
- Required Minimum Distribution (RMD): Minimum withdrawal from retirement accounts
- 401(k) Contribution Limits: Annual maximum contributions
- IRA Contribution Limits: Annual maximum contributions

### Debt Management
- Debt-to-Income Ratio: Monthly Debt Payments / Monthly Income
- Debt Snowball Method: Pay smallest debts first
- Debt Avalanche Method: Pay highest interest debts first
- Minimum Payment: Minimum required monthly payment
- Amortization Schedule: Payment breakdown over loan term
- Principal: Original loan amount
- Interest: Cost of borrowing
- APR: Annual Percentage Rate
- APY: Annual Percentage Yield (compounded)

### Savings & Investment Strategies
- Dollar-Cost Averaging: Invest fixed amount regularly
- Value Averaging: Adjust investment to target value
- Asset Allocation: Distribution across asset classes
- Rebalancing: Adjust portfolio to target allocation
- Tax-Loss Harvesting: Sell losses to offset gains
- Tax-Advantaged Accounts: 401(k), IRA, HSA, 529 plans
- Emergency Fund: 3-6 months of expenses
- Savings Rate: (Savings / Income) × 100

## RISK MANAGEMENT

### Risk Types
- Market Risk: Risk of market-wide declines
- Credit Risk: Risk of default
- Liquidity Risk: Risk of inability to sell quickly
- Operational Risk: Risk from operations
- Interest Rate Risk: Risk from rate changes
- Currency Risk: Risk from exchange rate changes
- Inflation Risk: Risk of purchasing power loss
- Concentration Risk: Risk from lack of diversification

### Risk Measurement
- Value at Risk (VaR): Maximum expected loss at confidence level
- Conditional VaR: Expected loss beyond VaR
- Stress Testing: Test under extreme scenarios
- Scenario Analysis: Analyze different outcomes
- Sensitivity Analysis: Impact of variable changes
- Monte Carlo Simulation: Random sampling for outcomes

## TAX CONCEPTS

### Tax Calculations
- Marginal Tax Rate: Tax on next dollar earned
- Effective Tax Rate: Total Tax / Total Income
- Average Tax Rate: Tax / Taxable Income
- Tax Bracket: Income range with specific rate
- Standard Deduction: Fixed deduction amount
- Itemized Deductions: Specific deductible expenses
- Tax Credits: Direct reduction of tax liability
- Tax Deductions: Reduction of taxable income

### Investment Taxes
- Capital Gains: Profit from asset sale
- Short-Term Capital Gains: Assets held < 1 year
- Long-Term Capital Gains: Assets held ≥ 1 year
- Dividend Tax: Tax on dividend income
- Qualified Dividends: Lower tax rate dividends
- Tax-Loss Harvesting: Offset gains with losses
- Wash Sale Rule: Cannot claim loss if repurchase within 30 days
- Cost Basis: Original purchase price
- Adjusted Basis: Cost basis adjusted for improvements, depreciation

## FINANCIAL MODELING

### Model Types
- DCF Model: Discounted Cash Flow valuation
- Comparable Company Analysis: Compare to similar companies
- Precedent Transactions: Analyze past M&A deals
- LBO Model: Leveraged Buyout analysis
- Merger Model: Combine two companies
- Three-Statement Model: Income, Balance Sheet, Cash Flow linked
- Sensitivity Analysis: Vary key assumptions
- Scenario Analysis: Best case, base case, worst case

### Key Assumptions
- Revenue Growth: Projected revenue increase
- Margin Assumptions: Expected profit margins
- Working Capital: Current assets - current liabilities
- Capital Expenditures: Investments in fixed assets
- Depreciation: Allocation of asset cost
- Tax Rate: Effective tax rate
- Discount Rate: WACC or required return
- Terminal Growth Rate: Long-term growth assumption

## BEHAVIORAL FINANCE

### Cognitive Biases
- Anchoring: Rely on first information
- Confirmation Bias: Seek confirming evidence
- Overconfidence: Overestimate abilities
- Loss Aversion: Fear losses more than value gains
- Herding: Follow crowd behavior
- Mental Accounting: Treat money differently by source
- Framing Effect: Decisions affected by presentation
- Recency Bias: Overweight recent information
- Availability Bias: Overweight easily recalled information

### Market Anomalies
- January Effect: Stocks perform better in January
- Momentum Effect: Past winners continue winning
- Value Effect: Value stocks outperform
- Size Effect: Small caps outperform large caps
- Weekend Effect: Lower returns on Mondays
- Earnings Surprise: Stocks react to earnings beats/misses

## ANALYSIS TECHNIQUES

### Financial Statement Analysis
- Common-Size Analysis: Express as percentages
- Trend Analysis: Analyze over time
- Comparative Analysis: Compare to competitors
- DuPont Analysis: ROE = Profit Margin × Asset Turnover × Equity Multiplier
- Horizontal Analysis: Compare across periods
- Vertical Analysis: Compare within period

### Valuation Methods
- Discounted Cash Flow (DCF): Present value of future cash flows
- Comparable Company Analysis: Market multiples
- Precedent Transactions: M&A transaction multiples
- Asset-Based Valuation: Sum of asset values
- Liquidation Value: Value if assets sold
- Replacement Cost: Cost to replace assets
- Sum of Parts: Value each business segment separately

## CALCULATION PRECISION

When performing calculations:
1. Use appropriate decimal precision (typically 2-4 decimals for financial calculations)
2. Round final answers appropriately
3. Show intermediate steps for complex calculations
4. Verify calculations using alternative methods when possible
5. Consider significant figures in measurements
6. Use exact formulas rather than approximations when precision matters
7. Account for compounding frequency in interest calculations
8. Handle currency conversions with current exchange rates
9. Apply tax rates correctly to taxable amounts
10. Consider transaction costs and fees in investment calculations

## INTERPRETATION GUIDELINES

When analyzing financial data:
1. Compare ratios to industry benchmarks
2. Consider company size and stage of growth
3. Analyze trends over multiple periods
4. Look for red flags (declining margins, increasing debt, etc.)
5. Consider macroeconomic context
6. Evaluate management quality and strategy
7. Assess competitive position
8. Review regulatory environment
9. Consider sustainability and ESG factors
10. Provide balanced analysis with both strengths and weaknesses

## COMMUNICATION STANDARDS

When explaining financial concepts:
1. Use clear, jargon-free language when possible
2. Define technical terms when first used
3. Provide real-world examples
4. Use visual aids (tables, charts) when helpful
5. Break complex topics into digestible parts
6. Relate concepts to user's personal situation
7. Highlight actionable insights
8. Warn about risks and limitations
9. Cite sources for market data and benchmarks
10. Encourage further research for major decisions
"""
