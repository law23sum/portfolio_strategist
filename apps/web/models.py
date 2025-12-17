from django.db import models

from apps.utils.models import BaseModel


class EquationCategory(BaseModel):
    """Category for organizing equations (e.g., Probability Distributions, Financial Metrics)"""

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    order = models.IntegerField(default=0, help_text="Display order")
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")

    class Meta:
        verbose_name_plural = "Equation Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Equation(BaseModel):
    """Mathematical equation with formula, parameters, and metadata"""

    category = models.ForeignKey(EquationCategory, on_delete=models.CASCADE, related_name="equations")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    # Formula representation
    formula_latex = models.TextField(help_text="LaTeX representation of the formula")
    formula_text = models.CharField(max_length=500, help_text="Plain text representation")

    # Parameters/Variables
    parameters_json = models.JSONField(
        default=dict, help_text="JSON object with parameter definitions: {name: {type, default, min, max, description}}"
    )

    # Implementation
    implementation_type = models.CharField(
        max_length=50,
        choices=[
            ("python", "Python Function"),
            ("javascript", "JavaScript Function"),
            ("formula", "Mathematical Formula"),
        ],
        default="python",
    )
    implementation_code = models.TextField(blank=True, help_text="Code to evaluate the equation (Python or JavaScript)")

    # Metadata
    use_cases = models.TextField(blank=True, help_text="When to use this equation")
    references = models.TextField(blank=True, help_text="References and citations")
    order = models.IntegerField(default=0, help_text="Display order within category")
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")
    is_featured = models.BooleanField(default=False, help_text="Show in featured section")

    # Visualization settings
    supports_graph = models.BooleanField(default=False, help_text="Can generate graphs")
    graph_type = models.CharField(
        max_length=50,
        choices=[
            ("line", "Line Chart"),
            ("scatter", "Scatter Plot"),
            ("histogram", "Histogram"),
            ("distribution", "Probability Distribution"),
            ("surface", "3D Surface"),
        ],
        blank=True,
    )
    graph_config_json = models.JSONField(
        default=dict, help_text="Graph configuration: {x_label, y_label, x_range, y_range, etc.}"
    )

    class Meta:
        ordering = ["category__order", "order", "name"]
        indexes = [
            models.Index(fields=["category", "is_featured"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.category.name}: {self.name}"


class EquationVariable(BaseModel):
    """Variable/parameter definition for equations"""

    equation = models.ForeignKey(Equation, on_delete=models.CASCADE, related_name="variables")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, help_text="Mathematical symbol (e.g., μ, σ)")
    description = models.TextField()
    variable_type = models.CharField(
        max_length=50,
        choices=[
            ("float", "Number"),
            ("integer", "Integer"),
            ("boolean", "Boolean"),
            ("string", "Text"),
        ],
        default="float",
    )
    default_value = models.CharField(max_length=200, blank=True)
    min_value = models.CharField(max_length=200, blank=True, help_text="Minimum allowed value")
    max_value = models.CharField(max_length=200, blank=True, help_text="Maximum allowed value")
    step = models.CharField(max_length=200, blank=True, help_text="Step size for sliders")
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement")
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["equation", "order", "name"]
        unique_together = [["equation", "name"]]

    def __str__(self):
        return f"{self.equation.name}: {self.name} ({self.symbol})"
