from django import forms

from .models import FinancialDocument


class FinancialDocumentForm(forms.ModelForm):
    class Meta:
        model = FinancialDocument
        exclude = ["user", "original_name"]
        fields = ["record_type", "sub_record_type", "year", "document"]
