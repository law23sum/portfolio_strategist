# Formula Library Master Plan

## Purpose & Positioning
- **Transparency with control**: Premium clients see pristine formulas, variables, graphs, and narrative context, while the proprietary solver (computational engine) stays encapsulated.
- **Prestige UX**: Cards, typography, and curated decks mimic a private research library inside the Advanced Premium Studio.
- **Learning value**: Every formula card includes natural-language explanations, assumptions, and guidance, backed by `The Statistics..pdf` reference set.
- **Backend freedom**: Inputs route to an internal evaluation service so algorithms can evolve without altering the visible library.

## System Architecture
| Layer | Description |
| --- | --- |
| Premium Formula Library (frontend) | React/Vue micro-frontend within the Advanced Premium Studio. Renders cards, LaTeX (MathJax), sliders, graphs (Chart.js/Plotly). Hits read-only metadata API. |
| Formula CMS / Metadata API | Stores decks, categories, formulas, variables, and tags. Editors manage 100+ formulas. Responses include TeX, tooltips, input schema, default values, graph presets. |
| Secure Computational Engine | Internal service (Python/NumPy/SciPy or Julia) executing formulas. Receives sanitized variable payloads + hidden identifiers, returns results, series for graphs, and scenario deltas. |
| Access & Analytics | Membership middleware (JWT scopes) gates premium cards, logs usage, powers personalization and recommendation surfaces. |

## Decks & Categories
| Deck | Categories | Notes |
| --- | --- | --- |
| Foundation Deck | Descriptive Statistics & Moments; Probability Frameworks | Core literacy and onboarding. |
| Distribution Vault | Discrete Families; Continuous Families; Standardizations & Transforms | Derived straight from `The Statistics..pdf`; includes PDFs, CDFs, and parameter transforms. |
| Inference Studio | Sampling & Estimation; Hypothesis Testing & Power | Confidence intervals, MLE/MoM, p-values, power calculators. |
| Modeling Lab | Regression & Correlation; Time Series & Forecasting | Linear, logistic, ARIMA, smoothing, volatility models. |
| Bayesian & Information Hub | Bayesian Updates; Information Metrics | Priors/posteriors, entropy, KL, Bayes factors. |
| Portfolio & Risk Wing | Multi-asset Analytics; Options & Tail Risk | Modern portfolio metrics, VaR/CVaR, derivatives pricing. |

### Library Hierarchy (Navigation Blueprint)
```
Formula Library
├─ Foundation Deck
│  ├─ Descriptive Statistics & Moments
│  └─ Probability Frameworks
├─ Distribution Vault
│  ├─ Discrete Families
│  ├─ Continuous Families
│  └─ Standardizations & Transforms
├─ Inference Studio
│  ├─ Sampling & Estimation
│  └─ Hypothesis Testing & Power
├─ Modeling Lab
│  ├─ Regression & Correlation
│  └─ Time Series & Forecasting
├─ Bayesian & Information Hub
│  └─ Decision Metrics
└─ Portfolio & Risk Wing
   ├─ Multi-asset Analytics
   └─ Options & Tail Risk
```

## Top 100 Formula Cards (with user-variable inputs)
Each entry ships with: (1) LaTeX, (2) variable schema (type, min/max, default, step), (3) helper text, (4) solver reference ID, (5) optional graph presets. Below lists all 100 cards grouped roughly by deck.

### Foundation Deck (1–17)
1. **Arithmetic Mean** — $\bar{x} = \frac{1}{n}\sum x_i$ (Inputs: $n$, data vector) — central tendency.
2. **Weighted Mean** — $\mu_w = \frac{\sum w_i x_i}{\sum w_i}$ (Inputs: values, weights).
3. **Geometric Mean** — $G = (\prod x_i)^{1/n}$ (Inputs: positive values) — growth rates.
4. **Harmonic Mean** — $H = \frac{n}{\sum 1/x_i}$ (Inputs: positive values) — rates.
5. **Sample Variance** — $s^2 = \frac{1}{n-1}\sum (x_i-\bar{x})^2$ (Inputs: data vector).
6. **Population Variance** — $\sigma^2 = \frac{1}{n}\sum (x_i-\mu)^2$ (Inputs: mean, data).
7. **Standard Deviation** — $\sigma = \sqrt{\sigma^2}$ (Inputs: variance).
8. **Coefficient of Variation** — $CV = \sigma/\mu$ (Inputs: mean, std).
9. **Sample Skewness** — $g_1 = \frac{n}{(n-1)(n-2)}\sum ((x_i-\bar{x})/s)^3$.
10. **Sample Excess Kurtosis** — $g_2 = \frac{n(n+1)}{(n-1)(n-2)(n-3)}\sum ((x_i-\bar{x})/s)^4 - 3$.
11. **Conditional Probability** — $P(A|B)=P(A\cap B)/P(B)$.
12. **Law of Total Probability** — $P(B)=\sum P(B|A_i)P(A_i)$.
13. **Bayes' Theorem** — $P(A|B)=\frac{P(B|A)P(A)}{P(B)}$.
14. **Expected Value (discrete)** — $E[X]=\sum x p(x)$.
15. **Expected Value (continuous)** — $E[X]=\int x f(x) dx$.
16. **Covariance** — $Cov(X,Y)=E[(X-\mu_X)(Y-\mu_Y)]$.
17. **Correlation** — $\rho = Cov(X,Y)/(\sigma_X \sigma_Y)$.

### Distribution Vault — Discrete (Entries 18–27)
18. **Bernoulli PMF** — $p^x(1-p)^{1-x}$.
19. **Binomial PMF** — $C(n,k)p^k(1-p)^{n-k}$.
20. **Poisson PMF** — $\frac{\lambda^k e^{-\lambda}}{k!}$.
21. **Geometric PMF** — $(1-p)^{k-1}p$.
22. **Negative Binomial PMF** — $C(k+r-1,k-1)(1-p)^r p^k$.
23. **Hypergeometric PMF** — $\frac{C(K,k)C(N-K,n-k)}{C(N,n)}$.
24. **Multinomial PMF** — $\frac{n!}{\prod x_i!}\prod p_i^{x_i}$.
25. **Beta-Binomial PMF** — $C(n,k) \frac{B(k+\alpha,n-k+\beta)}{B(\alpha,\beta)}$.
26. **Discrete Uniform** — $P(X=k)=1/(b-a+1)$.
27. **Skellam Distribution** — $e^{-(\mu_1+\mu_2)} (\mu_1/\mu_2)^{k/2} I_{|k|}(2\sqrt{\mu_1\mu_2})$.

### Distribution Vault — Continuous (Entries 28–45)
28. **Continuous Uniform PDF** — $1/(b-a)$.
29. **Exponential PDF** — $\lambda e^{-\lambda x}$.
30. **Normal PDF** — $(1/\sqrt{2\pi\sigma^2}) e^{-(x-\mu)^2/(2\sigma^2)}$.
31. **Standard Normal CDF** — $\Phi(z)=\frac{1}{\sqrt{2\pi}}\int_{-\infty}^z e^{-t^2/2} dt$.
32. **Lognormal PDF** — $\frac{1}{x\sigma\sqrt{2\pi}} e^{-(\ln x - \mu)^2/(2\sigma^2)}$.
33. **Gamma PDF** — $\frac{\beta^\alpha}{\Gamma(\alpha)} x^{\alpha-1} e^{-\beta x}$.
34. **Beta PDF** — $\frac{1}{B(\alpha,\beta)} x^{\alpha-1} (1-x)^{\beta-1}$.
35. **Chi-square PDF** — $f(x;k)=\frac{1}{2^{k/2}\Gamma(k/2)} x^{k/2-1} e^{-x/2}$.
36. **Student's t PDF** — $f(t;\nu)=\frac{\Gamma((\nu+1)/2)}{\sqrt{\nu\pi}\Gamma(\nu/2)} (1+t^2/\nu)^{-(\nu+1)/2}$.
37. **F-distribution PDF** — per `The Statistics..pdf`.
38. **Rayleigh PDF** — $(x/\sigma^2) e^{-x^2/(2\sigma^2)}$.
39. **Laplace PDF** — $(1/(2b)) e^{-|x-\mu|/b}$.
40. **Cauchy PDF** — $\frac{1}{\pi \gamma [1+((x-x_0)/\gamma)^2]}$.
41. **Logistic PDF** — $f(x)=\frac{e^{-(x-\mu)/s}}{s(1+e^{-(x-\mu)/s})^2}$.
42. **Weibull PDF** — $(k/\lambda) (x/\lambda)^{k-1} e^{-(x/\lambda)^k}$.
43. **Pareto PDF** — $\alpha x_m^\alpha / x^{\alpha+1}$.
44. **Gumbel PDF** — $(1/\beta) e^{-(z + e^{-z})}$, $z=(x-\mu)/\beta$.
45. **Logistic CDF** — $L(x)=1/(1+e^{-(x-\mu)/s})$.

### Inference Studio (Entries 46–64)
46. **Sample Mean Estimator** — $\hat{\mu}=\bar{x}$.
47. **Standard Error** — $SE = s/\sqrt{n}$.
48. **Z-based Confidence Interval** — $\bar{x} \pm z_{\alpha/2} (\sigma/\sqrt{n})$.
49. **T-based Confidence Interval** — $\bar{x} \pm t_{\alpha/2,\nu} (s/\sqrt{n})$.
50. **Wilson Proportion Interval** — formula from stats PDF.
51. **MLE for Normal Mean** — $\hat{\mu}_{MLE}=\bar{x}$.
52. **Method of Moments** — $m_k = \frac{1}{n}\sum x_i^k$.
53. **Fisher Information** — $I(\theta)=-E[\partial^2 \ln L/\partial \theta^2]$.
54. **Cramér-Rao Bound** — $Var(\hat{\theta}) \ge 1/I(\theta)$.
55. **Bootstrap Estimator** — $\hat{\theta}^*=(1/B)\sum_{b=1}^B \theta^{*(b)}$.
56. **Z-test Statistic** — $z=(\bar{x}-\mu_0)/(\sigma/\sqrt{n})$.
57. **One-sample t-test** — $t=(\bar{x}-\mu_0)/(s/\sqrt{n})$.
58. **Chi-square Goodness-of-Fit** — $\chi^2=\sum (O_i-E_i)^2/E_i$.
59. **Variance Ratio F-test** — $F=s_1^2/s_2^2$.
60. **ANOVA F-statistic** — $MS_{between}/MS_{within}$.
61. **Likelihood Ratio** — $\Lambda=-2\ln(L_0/L_1)$.
62. **Test Power** — $1-\beta$ (function builder with effect size slider).
63. **Bonferroni Threshold** — $\alpha_i=\alpha/m$.
64. **Benjamini–Hochberg Rule** — reject when $p_{(i)} \le (i/m)q$.

### Modeling Lab (Entries 65–82)
65. **Regression Line** — $\hat{y}=\beta_0+\beta_1 x$.
66. **Slope Estimator** — $\beta_1=\frac{\sum (x_i-x̄)(y_i-ȳ)}{\sum (x_i-x̄)^2}$.
67. **Intercept Estimator** — $\beta_0=ȳ-\beta_1 x̄$.
68. **Multiple Regression (OLS)** — $\beta=(X^TX)^{-1}X^Ty$.
69. **R-squared** — $1-\frac{RSS}{TSS}$.
70. **Adjusted R-squared** — $1-(1-R^2)\frac{n-1}{n-p-1}$.
71. **Residual Sum of Squares** — $RSS=\sum (y_i-\hat{y}_i)^2$.
72. **Durbin–Watson** — $DW=\frac{\sum (e_t-e_{t-1})^2}{\sum e_t^2}$.
73. **Logistic Regression** — $P(y=1|x)=1/(1+e^{-(\beta_0+\beta^T x)})$.
74. **Odds Ratio** — $OR= e^{\beta_j}$.
75. **AR(1)** — $X_t=\phi X_{t-1}+\varepsilon_t$.
76. **ARIMA(p,d,q)** — $\phi(B)(1-B)^d X_t = \theta(B)\varepsilon_t$.
77. **Simple Exponential Smoothing** — $\hat{X}_{t+1}=\alpha X_t + (1-\alpha)\hat{X}_t$.
78. **Holt-Winters Level Update** — $L_t = \alpha (X_t - S_{t-s}) + (1-\alpha)(L_{t-1}+T_{t-1})$.
79. **Autocovariance** — $\gamma_k = \frac{1}{n}\sum (x_t-x̄)(x_{t-k}-x̄)$.
80. **Autocorrelation** — $\rho_k=\gamma_k/\gamma_0$.
81. **GARCH(1,1)** — $\sigma_t^2 = \omega + \alpha \varepsilon_{t-1}^2 + \beta \sigma_{t-1}^2$.
82. **Kalman Gain** — $K_t = P_{t|t-1}H^T (H P_{t|t-1}H^T + R)^{-1}$.

### Bayesian & Information Hub (Entries 83–87)
83. **Bayesian Update** — $p(\theta|x)=\frac{p(x|\theta)p(\theta)}{p(x)}$.
84. **Normal-Normal Posterior Mean** — $\mu_n = \frac{\sigma^2 \mu_0 + \tau^2 \sum x_i}{\sigma^2 + n \tau^2}$.
85. **Beta-Binomial Posterior** — $Beta(\alpha+k, \beta+n-k)$.
86. **Bayesian Predictive** — $p(x_{new}|x)=\int p(x_{new}|\theta)p(\theta|x)d\theta$.
87. **Posterior Predictive Check** — $p(T(y_{rep})|y)=\int p(T(y_{rep})|\theta)p(\theta|y)d\theta$.

### Decision Metrics & Information (Entries 88–90)
88. **KL Divergence** — $D_{KL}(P||Q)=\sum P \log(P/Q)$ (or integral).
89. **Entropy** — $H(X) = -\sum p(x) \log p(x)$.
90. **Mutual Information** — $I(X;Y)=\sum\sum p(x,y) \log \frac{p(x,y)}{p(x)p(y)}$.

### Portfolio & Risk Wing (Entries 91–100)
91. **Expected Portfolio Return** — $E[R_p]=\sum w_i E[R_i]$; includes slider for each weight (auto-normalized).
92. **Portfolio Variance** — $\sigma_p^2 = w^T \Sigma w$; includes matrix input UI.
93. **CAPM** — $E[R_i]=R_f+\beta_i(E[R_m]-R_f)$.
94. **Beta Estimate** — $\beta_i = Cov(R_i,R_m)/Var(R_m)$.
95. **Sharpe Ratio** — $(E[R_p]-R_f)/\sigma_p$.
96. **Sortino Ratio** — $(E[R_p]-R_f)/\sigma_d$.
97. **Parametric VaR** — $VaR_\alpha = \mu_p + z_\alpha \sigma_p$.
98. **Conditional VaR** — $CVaR_\alpha = \mu_p + \frac{\phi(z_\alpha)}{1-\alpha} \sigma_p$.
99. **Kelly Fraction** — $f^* = (bp - q)/b$.
100. **Black-Scholes Call** — $C = S_0 N(d_1) - K e^{-rT} N(d_2)$.

## Integration with Advanced Premium Studio
1. **Micro-frontend embedding**: mount `FormulaLibraryShell` component inside Studio layout; fetch metadata via `/api/formulas` (read) and evaluations via `/api/formulas/:id/evaluate` (write).
2. **Authentication & gating**: Studio issues JWT tokens; metadata endpoint returns `isPremium`, `requiresUnlock`, `availableGraphs`. Frontend hides solver panel unless scope `formula:execute` exists.
3. **Computation flow**: user edits inputs → UI validates → POST to evaluation API with (formula_id, variables, scenario_id) → engine responds with values, graph datasets, textual insights → UI updates card instantly.
4. **Preset management**: saved variable sets stored per user in `formula_presets` table; integrate with Studio’s workspace feature so a card can be “pinned” to dashboards.
5. **Analytics loop**: event bus logs formula views, calculations, slider adjustments; feed success metrics and offer suggestions.

## Interactivity Blueprint
- **Variable inputs**: auto-generated forms (number fields, sliders, dropdowns, vector/matrix editors). Schema enforces types, ranges, dependencies.
- **Live graphs**: distributions show PDF/CDF overlays; inference cards show confidence interval bands; regression/time-series cards show scatter plots, residuals, ACF/PACF bars.
- **Scenario sliders**: quick toggles for significance level, sample size, volatility, etc.; watchers throttle requests for smooth UX.
- **Comparison overlays**: allow linking two cards (e.g., Normal vs. t) and rendering on shared axes.
- **Explain mode**: tooltip reveals derivation snippets from `The Statistics..pdf` plus references; toggled separately so backend solver remains hidden.
- **Export hooks**: push evaluated results to Studio notebooks, CSV, or PDF snapshots; queue asynchronous exports via worker service.

## Implementation Checklist
- [ ] Seed CMS tables with deck/category/formula metadata (CSV or fixture referencing this plan).
- [ ] Build `/api/formulas` (read-only) and `/api/formulas/:id/evaluate` endpoints with premium gating.
- [ ] Stand up solver service package with SciPy/Numpy, hooking into management command seeds.
- [ ] Implement Formula Library micro-frontend (search, filter, cards, graphs, presets).
- [ ] QA flow with mock premium/non-premium accounts and variable validation.
- [ ] Plan roadmap to swap/extend formulas without breaking card IDs (version fields).
