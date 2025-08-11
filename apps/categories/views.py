from django.shortcuts import render

from apps.records.models import FinancialDocument


def personal_sensitive_view(request):
    documents = FinancialDocument.objects.filter(record_type="government").prefetch_related("fields")
    context = {
        "active_tab": "personal_sensitive",
        "documents": documents,
    }
    return render(request, "categories/personal_sensitive_information.html", context)
