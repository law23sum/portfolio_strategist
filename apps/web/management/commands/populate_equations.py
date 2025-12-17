"""
Management command to populate formula library from statistics PDF data.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Populate formula library with statistics distributions and formulas"

    def handle(self, *args, **options):
        from apps.web.models import Equation, EquationCategory, EquationVariable

        self.stdout.write("Creating formula categories...")

        # Create categories
        categories_data = [
            {
                "name": "Probability Distributions",
                "slug": "probability-distributions",
                "description": "Continuous and discrete probability distributions",
                "icon": "fa-chart-line",
                "order": 1,
            },
            {
                "name": "Statistical Tests",
                "slug": "statistical-tests",
                "description": "Hypothesis testing and goodness-of-fit tests",
                "icon": "fa-flask",
                "order": 2,
            },
            {
                "name": "Descriptive Statistics",
                "slug": "descriptive-statistics",
                "description": "Measures of central tendency and dispersion",
                "icon": "fa-calculator",
                "order": 3,
            },
            {
                "name": "Financial Metrics",
                "slug": "financial-metrics",
                "description": "Financial ratios and investment calculations",
                "icon": "fa-dollar-sign",
                "order": 4,
            },
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = EquationCategory.objects.get_or_create(slug=cat_data["slug"], defaults=cat_data)
            categories[cat_data["slug"]] = cat
            if created:
                self.stdout.write(f"  Created category: {cat.name}")

        # Define equations from the PDF
        equations_data = self._get_equations_data()

        self.stdout.write(f"\nCreating {len(equations_data)} formulas...")

        for eq_data in equations_data:
            category_slug = eq_data.pop("category", "probability-distributions")
            category = categories.get(category_slug, categories["probability-distributions"])

            # Extract variables
            variables_data = eq_data.pop("variables", [])

            # Create or update equation
            eq, created = Equation.objects.update_or_create(slug=eq_data["slug"], defaults=eq_data)
            eq.category = category
            eq.save()

            if created:
                self.stdout.write(f"  Created formula: {eq.name}")
            else:
                self.stdout.write(f"  Updated formula: {eq.name}")

            # Create variables
            for var_data in variables_data:
                var, _ = EquationVariable.objects.update_or_create(
                    equation=eq, name=var_data["name"], defaults=var_data
                )

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully populated {len(equations_data)} formulas!"))

    def _get_equations_data(self):
        """Get all equations data from the PDF"""
        equations_data = [
            # Normal Distribution
            {
                "name": "Normal Distribution",
                "slug": "normal-distribution",
                "category": "probability-distributions",
                "description": "Gaussian distribution - models data clustering around a mean, with probabilities decreasing symmetrically as values deviate. Essential for statistical inference, hypothesis testing, and machine learning.",
                "formula_latex": r"f(x; \mu, \sigma^2) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)",
                "formula_text": "(1/sqrt(2*pi*sigma**2)) * exp(-((x-mu)**2)/(2*sigma**2))",
                "parameters_json": {
                    "mu": {"type": "float", "default": 0, "description": "Mean"},
                    "sigma": {"type": "float", "default": 1, "min": 0.001, "description": "Standard deviation"},
                    "x": {"type": "float", "default": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
result = (1 / math.sqrt(2 * math.pi * sigma**2)) * math.exp(-((x - mu)**2) / (2 * sigma**2))
""",
                "use_cases": "Models data clustering around a mean. Essential for statistical inference, hypothesis testing, and machine learning. Driven by the Central Limit Theorem (CLT).",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -5,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "mu",
                        "symbol": "μ",
                        "description": "Mean (location parameter)",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "sigma",
                        "symbol": "σ",
                        "description": "Standard deviation (scale parameter)",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value at which to evaluate the PDF",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 3,
                    },
                ],
                "is_featured": True,
            },
            # Standard Normal Distribution
            {
                "name": "Standard Normal Distribution",
                "slug": "standard-normal-distribution",
                "category": "probability-distributions",
                "description": "A universal reference for measuring deviations from the mean. Allows transformation of any normal distribution to a common scale via standardization (Z-score).",
                "formula_latex": r"z = \frac{x-\mu}{\sigma}, \quad f(z) = \frac{1}{\sqrt{2\pi}} e^{-z^2/2}",
                "formula_text": "z = (x-mu)/sigma; f(z) = (1/sqrt(2*pi)) * exp(-z**2/2)",
                "parameters_json": {
                    "x": {"type": "float", "default": 0, "description": "Value"},
                    "mu": {"type": "float", "default": 0, "description": "Mean"},
                    "sigma": {"type": "float", "default": 1, "min": 0.001, "description": "Standard deviation"},
                },
                "implementation_type": "python",
                "implementation_code": """
z = (x - mu) / sigma
result = (1 / math.sqrt(2 * math.pi)) * math.exp(-z**2 / 2)
""",
                "use_cases": "A universal reference for measuring deviations from the mean. Enables probability estimation and comparisons across datasets.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -4,
                    "x_max": 4,
                    "num_points": 200,
                    "x_label": "z",
                    "y_label": "f(z)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value to standardize",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "mu",
                        "symbol": "μ",
                        "description": "Mean",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "sigma",
                        "symbol": "σ",
                        "description": "Standard deviation",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Uniform Distribution
            {
                "name": "Uniform Distribution",
                "slug": "uniform-distribution",
                "category": "probability-distributions",
                "description": "All outcomes are equally likely within a range.",
                "formula_latex": r"f(x; a, b) = \frac{1}{b-a} \quad \text{for } a \leq x \leq b",
                "formula_text": "1/(b-a) if a <= x <= b else 0",
                "parameters_json": {
                    "a": {"type": "float", "default": 0, "description": "Minimum"},
                    "b": {"type": "float", "default": 1, "description": "Maximum"},
                    "x": {"type": "float", "default": 0.5, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
if a <= x <= b:
    result = 1 / (b - a)
else:
    result = 0
""",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -1,
                    "x_max": 2,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "a",
                        "symbol": "a",
                        "description": "Minimum value",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "b",
                        "symbol": "b",
                        "description": "Maximum value",
                        "variable_type": "float",
                        "default_value": "1",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value at which to evaluate",
                        "variable_type": "float",
                        "default_value": "0.5",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Exponential Distribution
            {
                "name": "Exponential Distribution",
                "slug": "exponential-distribution",
                "category": "probability-distributions",
                "description": "Used in modeling time between events in a Poisson process.",
                "formula_latex": r"f(x; \lambda) = \lambda e^{-\lambda x} \quad \text{for } x \geq 0",
                "formula_text": "lambda * exp(-lambda * x) if x >= 0 else 0",
                "parameters_json": {
                    "lambda": {"type": "float", "default": 1, "min": 0.001, "description": "Rate parameter"},
                    "x": {"type": "float", "default": 1, "min": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
if x >= 0:
    result = lambda_param * math.exp(-lambda_param * x)
else:
    result = 0
""",
                "use_cases": "Used in modeling time between events in a Poisson process.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": 0,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "lambda",
                        "symbol": "λ",
                        "description": "Rate parameter",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value (must be >= 0)",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0",
                        "is_required": True,
                        "order": 2,
                    },
                ],
            },
            # Rayleigh Distribution
            {
                "name": "Rayleigh Distribution",
                "slug": "rayleigh-distribution",
                "category": "probability-distributions",
                "description": "Used in modeling wave heights and wind speeds.",
                "formula_latex": r"f(x; \sigma) = \frac{x}{\sigma^2} e^{-x^2/(2\sigma^2)} \quad \text{for } x \geq 0",
                "formula_text": "(x/sigma**2) * exp(-x**2/(2*sigma**2)) if x >= 0 else 0",
                "parameters_json": {
                    "sigma": {"type": "float", "default": 1, "min": 0.001, "description": "Scale parameter"},
                    "x": {"type": "float", "default": 1, "min": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
if x >= 0:
    result = (x / sigma**2) * math.exp(-x**2 / (2 * sigma**2))
else:
    result = 0
""",
                "use_cases": "Used in modeling wave heights and wind speeds.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": 0,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "sigma",
                        "symbol": "σ",
                        "description": "Scale parameter",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value (must be >= 0)",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0",
                        "is_required": True,
                        "order": 2,
                    },
                ],
            },
            # Cauchy Distribution
            {
                "name": "Cauchy Distribution",
                "slug": "cauchy-distribution",
                "category": "probability-distributions",
                "description": "Used in modeling data with heavy tails and undefined variance.",
                "formula_latex": r"f(x; x_0, \gamma) = \frac{1}{\pi\gamma} \frac{1}{1 + \left(\frac{x-x_0}{\gamma}\right)^2}",
                "formula_text": "(1/(pi*gamma)) * (1/(1 + ((x-x0)/gamma)**2))",
                "parameters_json": {
                    "x0": {"type": "float", "default": 0, "description": "Location parameter"},
                    "gamma": {"type": "float", "default": 1, "min": 0.001, "description": "Scale parameter"},
                    "x": {"type": "float", "default": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
result = (1 / (math.pi * gamma)) * (1 / (1 + ((x - x0) / gamma)**2))
""",
                "use_cases": "Used in modeling data with heavy tails and undefined variance.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -5,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "x0",
                        "symbol": "x₀",
                        "description": "Location parameter",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "gamma",
                        "symbol": "γ",
                        "description": "Scale parameter",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Laplace Distribution
            {
                "name": "Laplace Distribution",
                "slug": "laplace-distribution",
                "category": "probability-distributions",
                "description": "Double exponential distribution.",
                "formula_latex": r"f(x; \mu, b) = \frac{1}{2b} \exp\left(-\frac{|x-\mu|}{b}\right)",
                "formula_text": "(1/(2*b)) * exp(-abs(x-mu)/b)",
                "parameters_json": {
                    "mu": {"type": "float", "default": 0, "description": "Location parameter"},
                    "b": {"type": "float", "default": 1, "min": 0.001, "description": "Scale parameter"},
                    "x": {"type": "float", "default": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
result = (1 / (2 * b)) * math.exp(-abs(x - mu) / b)
""",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -5,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "mu",
                        "symbol": "μ",
                        "description": "Location parameter",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "b",
                        "symbol": "b",
                        "description": "Scale parameter",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Logistic Distribution
            {
                "name": "Logistic Distribution",
                "slug": "logistic-distribution",
                "category": "probability-distributions",
                "description": "Used in machine learning, logistic regression, and growth modeling.",
                "formula_latex": r"f(x; \mu, s) = \frac{e^{-(x-\mu)/s}}{s(1+e^{-(x-\mu)/s})^2}",
                "formula_text": "exp(-(x-mu)/s) / (s * (1 + exp(-(x-mu)/s))**2)",
                "parameters_json": {
                    "mu": {"type": "float", "default": 0, "description": "Location parameter"},
                    "s": {"type": "float", "default": 1, "min": 0.001, "description": "Scale parameter"},
                    "x": {"type": "float", "default": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
result = math.exp(-(x - mu) / s) / (s * (1 + math.exp(-(x - mu) / s))**2)
""",
                "use_cases": "Used in machine learning, logistic regression, and growth modeling.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -5,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "mu",
                        "symbol": "μ",
                        "description": "Location parameter",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "s",
                        "symbol": "s",
                        "description": "Scale parameter",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Gamma Distribution
            {
                "name": "Gamma Distribution",
                "slug": "gamma-distribution",
                "category": "probability-distributions",
                "description": "Generalization of exponential distribution. Used in queuing theory and reliability analysis.",
                "formula_latex": r"f(x; k, \theta) = \frac{x^{k-1}e^{-x/\theta}}{\theta^k \Gamma(k)} \quad \text{for } x > 0",
                "formula_text": "(x**(k-1) * exp(-x/theta)) / (theta**k * gamma(k)) if x > 0 else 0",
                "parameters_json": {
                    "k": {"type": "float", "default": 2, "min": 0.001, "description": "Shape parameter"},
                    "theta": {"type": "float", "default": 1, "min": 0.001, "description": "Scale parameter"},
                    "x": {"type": "float", "default": 1, "min": 0.001, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
if x > 0:
    from scipy.special import gamma as gamma_func
    result = (x**(k-1) * math.exp(-x/theta)) / (theta**k * gamma_func(k))
else:
    result = 0
""",
                "use_cases": "Generalization of exponential distribution. Used in queuing theory and reliability analysis.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": 0,
                    "x_max": 10,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "k",
                        "symbol": "k",
                        "description": "Shape parameter",
                        "variable_type": "float",
                        "default_value": "2",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "theta",
                        "symbol": "θ",
                        "description": "Scale parameter",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value (must be > 0)",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Beta Distribution
            {
                "name": "Beta Distribution",
                "slug": "beta-distribution",
                "category": "probability-distributions",
                "description": "Used to model random variables limited to intervals of finite length. Common in Bayesian statistics.",
                "formula_latex": r"f(x; \alpha, \beta) = \frac{x^{\alpha-1}(1-x)^{\beta-1}}{B(\alpha, \beta)} \quad \text{for } 0 \leq x \leq 1",
                "formula_text": "(x**(alpha-1) * (1-x)**(beta-1)) / beta(alpha, beta) if 0 <= x <= 1 else 0",
                "parameters_json": {
                    "alpha": {"type": "float", "default": 2, "min": 0.001, "description": "Shape parameter α"},
                    "beta": {"type": "float", "default": 2, "min": 0.001, "description": "Shape parameter β"},
                    "x": {"type": "float", "default": 0.5, "min": 0, "max": 1, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
if 0 <= x <= 1:
    from scipy.special import beta as beta_func
    result = (x**(alpha-1) * (1-x)**(beta-1)) / beta_func(alpha, beta)
else:
    result = 0
""",
                "use_cases": "Used to model random variables limited to intervals of finite length. Common in Bayesian statistics.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": 0,
                    "x_max": 1,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "alpha",
                        "symbol": "α",
                        "description": "Shape parameter α",
                        "variable_type": "float",
                        "default_value": "2",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "beta",
                        "symbol": "β",
                        "description": "Shape parameter β",
                        "variable_type": "float",
                        "default_value": "2",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value (0 ≤ x ≤ 1)",
                        "variable_type": "float",
                        "default_value": "0.5",
                        "min_value": "0",
                        "max_value": "1",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Chi-Squared Distribution
            {
                "name": "Chi-Squared Distribution",
                "slug": "chi-squared-distribution",
                "category": "probability-distributions",
                "description": "Used in hypothesis testing and confidence intervals. Special case of gamma distribution.",
                "formula_latex": r"f(x; k) = \frac{x^{k/2-1}e^{-x/2}}{2^{k/2}\Gamma(k/2)} \quad \text{for } x > 0",
                "formula_text": "(x**(k/2-1) * exp(-x/2)) / (2**(k/2) * gamma(k/2)) if x > 0 else 0",
                "parameters_json": {
                    "k": {"type": "float", "default": 2, "min": 0.001, "description": "Degrees of freedom"},
                    "x": {"type": "float", "default": 1, "min": 0.001, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
if x > 0:
    from scipy.special import gamma as gamma_func
    result = (x**(k/2-1) * math.exp(-x/2)) / (2**(k/2) * gamma_func(k/2))
else:
    result = 0
""",
                "use_cases": "Used in hypothesis testing and confidence intervals. Special case of gamma distribution.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": 0,
                    "x_max": 10,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "k",
                        "symbol": "k",
                        "description": "Degrees of freedom",
                        "variable_type": "float",
                        "default_value": "2",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value (must be > 0)",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                ],
            },
            # Student's t-Distribution
            {
                "name": "Student's t-Distribution",
                "slug": "student-t-distribution",
                "category": "probability-distributions",
                "description": "Used in t-tests and confidence intervals when sample size is small or population variance is unknown.",
                "formula_latex": r"f(t; \nu) = \frac{\Gamma((\nu+1)/2)}{\sqrt{\nu\pi}\Gamma(\nu/2)} \left(1+\frac{t^2}{\nu}\right)^{-(\nu+1)/2}",
                "formula_text": "Use scipy.stats.t.pdf",
                "parameters_json": {
                    "nu": {"type": "float", "default": 10, "min": 0.001, "description": "Degrees of freedom"},
                    "t": {"type": "float", "default": 0, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
from scipy import stats
result = stats.t.pdf(t, nu)
""",
                "use_cases": "Used in t-tests and confidence intervals when sample size is small or population variance is unknown.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": -5,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "t",
                    "y_label": "f(t)",
                    "x_variable": "t",
                },
                "variables": [
                    {
                        "name": "nu",
                        "symbol": "ν",
                        "description": "Degrees of freedom",
                        "variable_type": "float",
                        "default_value": "10",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "t",
                        "symbol": "t",
                        "description": "Value",
                        "variable_type": "float",
                        "default_value": "0",
                        "is_required": True,
                        "order": 2,
                    },
                ],
            },
            # F-Distribution
            {
                "name": "F-Distribution",
                "slug": "f-distribution",
                "category": "probability-distributions",
                "description": "Used in ANOVA and regression analysis.",
                "formula_latex": r"f(x; d_1, d_2) = \frac{\sqrt{\frac{(d_1x)^{d_1}d_2^{d_2}}{(d_1x+d_2)^{d_1+d_2}}}}{xB(d_1/2, d_2/2)}",
                "formula_text": "Use scipy.stats.f.pdf",
                "parameters_json": {
                    "d1": {"type": "float", "default": 5, "min": 0.001, "description": "Degrees of freedom 1"},
                    "d2": {"type": "float", "default": 10, "min": 0.001, "description": "Degrees of freedom 2"},
                    "x": {"type": "float", "default": 1, "min": 0.001, "description": "Value"},
                },
                "implementation_type": "python",
                "implementation_code": """
from scipy import stats
result = stats.f.pdf(x, d1, d2)
""",
                "use_cases": "Used in ANOVA and regression analysis.",
                "supports_graph": True,
                "graph_type": "distribution",
                "graph_config_json": {
                    "x_min": 0,
                    "x_max": 5,
                    "num_points": 200,
                    "x_label": "x",
                    "y_label": "f(x)",
                    "x_variable": "x",
                },
                "variables": [
                    {
                        "name": "d1",
                        "symbol": "d₁",
                        "description": "Degrees of freedom 1",
                        "variable_type": "float",
                        "default_value": "5",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 1,
                    },
                    {
                        "name": "d2",
                        "symbol": "d₂",
                        "description": "Degrees of freedom 2",
                        "variable_type": "float",
                        "default_value": "10",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 2,
                    },
                    {
                        "name": "x",
                        "symbol": "x",
                        "description": "Value (must be > 0)",
                        "variable_type": "float",
                        "default_value": "1",
                        "min_value": "0.001",
                        "is_required": True,
                        "order": 3,
                    },
                ],
            },
            # Mean (Descriptive Statistics)
            {
                "name": "Arithmetic Mean",
                "slug": "arithmetic-mean",
                "category": "descriptive-statistics",
                "description": "Average value of a dataset.",
                "formula_latex": r"\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i",
                "formula_text": "sum(x) / len(x)",
                "parameters_json": {
                    "values": {"type": "string", "default": "1,2,3,4,5", "description": "Comma-separated values"},
                },
                "implementation_type": "python",
                "implementation_code": """
values_list = [float(v.strip()) for v in values.split(',')]
result = sum(values_list) / len(values_list)
""",
                "variables": [
                    {
                        "name": "values",
                        "symbol": "x₁,...,xₙ",
                        "description": "Comma-separated values",
                        "variable_type": "string",
                        "default_value": "1,2,3,4,5",
                        "is_required": True,
                        "order": 1,
                    },
                ],
            },
            # Standard Deviation
            {
                "name": "Standard Deviation",
                "slug": "standard-deviation",
                "category": "descriptive-statistics",
                "description": "Measure of the amount of variation or dispersion of a set of values.",
                "formula_latex": r"s = \sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2}",
                "formula_text": "sqrt(sum((x - mean)**2) / (n-1))",
                "parameters_json": {
                    "values": {"type": "string", "default": "1,2,3,4,5", "description": "Comma-separated values"},
                },
                "implementation_type": "python",
                "implementation_code": """
values_list = [float(v.strip()) for v in values.split(',')]
n = len(values_list)
mean = sum(values_list) / n
result = math.sqrt(sum((x - mean)**2 for x in values_list) / (n - 1))
""",
                "variables": [
                    {
                        "name": "values",
                        "symbol": "x₁,...,xₙ",
                        "description": "Comma-separated values",
                        "variable_type": "string",
                        "default_value": "1,2,3,4,5",
                        "is_required": True,
                        "order": 1,
                    },
                ],
            },
        ]

        # Fix lambda parameter name conflict in exponential distribution
        for eq in equations_data:
            if eq["slug"] == "exponential-distribution":
                # Update variable name from 'lambda' to 'lambda_param'
                for var in eq.get("variables", []):
                    if var["name"] == "lambda":
                        var["name"] = "lambda_param"
                        var["symbol"] = "λ"
                # Update parameters_json
                if "lambda" in eq["parameters_json"]:
                    eq["parameters_json"]["lambda_param"] = eq["parameters_json"].pop("lambda")
                # Update implementation code
                eq["implementation_code"] = eq["implementation_code"].replace("lambda *", "lambda_param *")
                eq["implementation_code"] = eq["implementation_code"].replace("-lambda *", "-lambda_param *")

        return equations_data
