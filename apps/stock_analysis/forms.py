from django import forms

from .models import InvestmentPlan, PersonalLoanAnalysis


class StockAnalysisForm(forms.Form):
    symbol = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Enter stock symbol (e.g., AAPL, NVDA)",
                "autofocus": True,
            }
        ),
        help_text="Enter a valid stock ticker symbol",
    )
    forecast_days = forms.IntegerField(
        initial=365,
        min_value=1,
        max_value=1825,
        widget=forms.NumberInput(attrs={"class": "input"}),
        help_text="Number of days to forecast (1-1825)",
    )
    equation_type = forms.ChoiceField(
        choices=[
            ("Geometric Brownian Motion", "Geometric Brownian Motion"),
            ("Geometric Brownian Motion with Mean Reversion", "GBM with Mean Reversion"),
            ("Geometric Brownian Motion External Macroeconomic Factors", "GBM with External Factors"),
        ],
        initial="Geometric Brownian Motion External Macroeconomic Factors",
        widget=forms.Select(attrs={"class": "select"}),
        required=False,
    )


class InvestmentPlanForm(forms.ModelForm):
    class Meta:
        model = InvestmentPlan
        fields = ["investment_amount", "share_quantity", "current_price", "alert_enabled", "alert_email", "alert_phone"]
        widgets = {
            "investment_amount": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "share_quantity": forms.NumberInput(attrs={"class": "input", "step": "0.0001"}),
            "current_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "alert_enabled": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "alert_email": forms.EmailInput(attrs={"class": "input"}),
            "alert_phone": forms.TextInput(attrs={"class": "input"}),
        }


class PersonalLoanForm(forms.ModelForm):
    class Meta:
        model = PersonalLoanAnalysis
        fields = ["csv_file"]
        widgets = {
            "csv_file": forms.FileInput(
                attrs={
                    "class": "file-input",
                    "accept": ".csv",
                }
            ),
        }
