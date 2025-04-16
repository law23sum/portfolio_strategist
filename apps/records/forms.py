from django import forms
from .models import FinancialDocument

class FinancialDocumentForm(forms.ModelForm):
    class Meta:
        model = FinancialDocument
        fields = ['original_name', 'record_type', 'sub_record_type', 'year', 'document']