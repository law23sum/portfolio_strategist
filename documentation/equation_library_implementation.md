# Equation Library Implementation

## Overview

The Equation Library is a premium feature that provides an interactive, curated collection of statistical and financial equations. It exposes equations selectively while keeping the core computational engine hidden and modifiable.

## Features

✅ **Transparency** - Users can see the mathematical formulas  
✅ **Prestige** - Premium feature with curated content  
✅ **Learning Value** - Educational descriptions and use cases  
✅ **Intellectual Appeal** - Beautiful LaTeX-rendered formulas  
✅ **Clean UX** - Modern, interactive interface  
✅ **Powerful Backend** - Flexible, modifiable calculation engine  

## Structure

### Models

1. **EquationCategory** - Organizes equations into categories
   - Categories: Probability Distributions, Statistical Tests, Descriptive Statistics, Financial Metrics
   - Supports premium gating per category

2. **Equation** - Core equation model
   - Formula representation (LaTeX and plain text)
   - Parameters definition (JSON)
   - Implementation code (Python/JavaScript)
   - Graph support configuration
   - Premium/featured flags

3. **EquationVariable** - Parameter definitions
   - Variable metadata (symbol, type, constraints)
   - Default values, min/max, step sizes
   - Unit information

### Categories

1. **Probability Distributions** (15+ equations)
   - Normal Distribution
   - Standard Normal Distribution
   - Uniform Distribution
   - Exponential Distribution
   - Rayleigh Distribution
   - Cauchy Distribution
   - Laplace Distribution
   - Logistic Distribution
   - Gamma Distribution
   - Beta Distribution
   - Chi-Squared Distribution
   - Student's t-Distribution
   - F-Distribution
   - And more...

2. **Statistical Tests** (Coming soon)
   - Kolmogorov-Smirnov Test
   - Chi-Squared Test
   - t-Test
   - ANOVA
   - And more...

3. **Descriptive Statistics** (5+ equations)
   - Arithmetic Mean
   - Standard Deviation
   - Variance
   - Median
   - And more...

4. **Financial Metrics** (Coming soon)
   - Future Value
   - Present Value
   - NPV
   - IRR
   - And more...

## API Endpoints

### GET `/api/equation-library/categories/`
Returns all equation categories with premium filtering.

### GET `/api/equation-library/equations/`
Returns equations, optionally filtered by category.
- Query params: `category` (slug), `featured` (true/false)

### POST `/api/equation-library/calculate/`
Calculates equation result with given parameters.
```json
{
  "equation_id": 1,
  "parameters": {
    "mu": 0,
    "sigma": 1,
    "x": 0.5
  }
}
```

### POST `/api/equation-library/graph/`
Generates graph data for an equation.
```json
{
  "equation_id": 1,
  "parameters": {...},
  "graph_config": {...}
}
```

## Frontend Features

### Interactive Elements

1. **Category Filtering** - Sidebar with category selection
2. **Search** - Real-time search across equations
3. **Input Fields** - Number inputs with validation
4. **Sliders** - Range sliders for continuous parameters
5. **Live Calculation** - Instant results on button click
6. **Graphs** - Interactive Chart.js visualizations
7. **LaTeX Rendering** - MathJax for beautiful formula display

### Premium Gating

- Premium equations are marked with badges
- Non-premium users see upgrade prompts
- Calculations are blocked for premium equations without subscription

## Setup Instructions

### 1. Run Migrations

```bash
python manage.py makemigrations web
python manage.py migrate
```

### 2. Populate Equations

```bash
python manage.py populate_equations
```

This command creates:
- 4 categories
- 15+ equations from the statistics PDF
- All variable definitions
- Graph configurations

### 3. Access the Library

Navigate to: `/equation-library/`

## Adding New Equations

### Method 1: Via Django Admin

1. Go to Django Admin → Web → Equations
2. Create new equation
3. Add variables
4. Set implementation code

### Method 2: Via Management Command

Edit `apps/web/management/commands/populate_equations.py` and add to `_get_equations_data()`.

### Example Equation Definition

```python
{
    'name': 'Normal Distribution',
    'slug': 'normal-distribution',
    'category': 'probability-distributions',
    'description': 'Gaussian distribution...',
    'formula_latex': r'f(x; \mu, \sigma^2) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)',
    'formula_text': '(1/sqrt(2*pi*sigma**2)) * exp(-((x-mu)**2)/(2*sigma**2))',
    'parameters_json': {
        'mu': {'type': 'float', 'default': 0, 'description': 'Mean'},
        'sigma': {'type': 'float', 'default': 1, 'min': 0.001, 'description': 'Standard deviation'},
        'x': {'type': 'float', 'default': 0, 'description': 'Value'},
    },
    'implementation_type': 'python',
    'implementation_code': '''
result = (1 / math.sqrt(2 * math.pi * sigma**2)) * math.exp(-((x - mu)**2) / (2 * sigma**2))
''',
    'supports_graph': True,
    'graph_type': 'distribution',
    'graph_config_json': {
        'x_min': -5,
        'x_max': 5,
        'num_points': 200,
        'x_label': 'x',
        'y_label': 'f(x)',
        'x_variable': 'x',
    },
    'variables': [
        {'name': 'mu', 'symbol': 'μ', 'description': 'Mean', 'variable_type': 'float', 'default_value': '0', 'is_required': True, 'order': 1},
        {'name': 'sigma', 'symbol': 'σ', 'description': 'Standard deviation', 'variable_type': 'float', 'default_value': '1', 'min_value': '0.001', 'is_required': True, 'order': 2},
        {'name': 'x', 'symbol': 'x', 'description': 'Value', 'variable_type': 'float', 'default_value': '0', 'is_required': True, 'order': 3},
    ],
}
```

## Implementation Details

### Calculation Engine

The `EquationCalculator` service:
- Parses and validates parameters
- Executes Python code in a safe environment
- Supports scipy, numpy, math libraries
- Handles lambda parameter name conflicts
- Formats results for display

### Graph Generation

- Uses Chart.js for visualization
- Supports line, scatter, histogram, distribution charts
- Configurable ranges and labels
- Real-time updates on parameter changes

### Security

- Code execution in restricted environment
- CSRF protection on API endpoints
- Premium feature gating
- Input validation and sanitization

## Future Enhancements

1. **More Equations** - Expand to 100+ equations
2. **3D Visualizations** - Surface plots for multi-variable equations
3. **Export Features** - PDF export, CSV data export
4. **Equation Collections** - User-created collections
5. **History** - Save calculation history
6. **Comparison Mode** - Compare multiple equations side-by-side
7. **Mobile Optimization** - Enhanced mobile experience

## Top 100 Formulas Roadmap

### Phase 1: Probability Distributions (30 equations)
- ✅ Normal, Standard Normal, Uniform, Exponential
- ✅ Rayleigh, Cauchy, Laplace, Logistic
- ✅ Gamma, Beta, Chi-Squared, t-Distribution, F-Distribution
- ⏳ Poisson, Binomial, Negative Binomial
- ⏳ Weibull, Lognormal, Pareto
- ⏳ Hypergeometric, Multinomial
- ⏳ And more...

### Phase 2: Statistical Tests (20 equations)
- ⏳ Kolmogorov-Smirnov Test
- ⏳ Chi-Squared Goodness-of-Fit
- ⏳ t-Test (one-sample, two-sample, paired)
- ⏳ ANOVA (one-way, two-way)
- ⏳ Mann-Whitney U Test
- ⏳ Wilcoxon Signed-Rank Test
- ⏳ And more...

### Phase 3: Descriptive Statistics (15 equations)
- ✅ Mean, Standard Deviation
- ⏳ Variance, Skewness, Kurtosis
- ⏳ Median, Mode, Quartiles
- ⏳ Correlation, Covariance
- ⏳ And more...

### Phase 4: Financial Metrics (20 equations)
- ⏳ Future Value, Present Value
- ⏳ Annuity calculations
- ⏳ NPV, IRR, Payback Period
- ⏳ Sharpe Ratio, Sortino Ratio
- ⏳ Beta, Alpha, R-squared
- ⏳ And more...

### Phase 5: Advanced Statistics (15 equations)
- ⏳ Regression coefficients
- ⏳ Confidence intervals
- ⏳ Hypothesis testing formulas
- ⏳ Bayesian statistics
- ⏳ And more...

## Notes

- All equations from "The Statistics.pdf" are being integrated
- Premium equations require active premium subscription
- Implementation code is hidden from users (transparency without exposing internals)
- Graph generation is optional per equation
- LaTeX rendering requires MathJax (loaded via CDN)

