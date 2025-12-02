import json
from datetime import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import FinancialDocumentForm
from .models import ExtractedField, FinancialDocument
from .services import build_document_library, get_document_metrics
from .plaid_data_distribution import PlaidDataDistributionService


def upload_view(request):
    current_year = datetime.now().year
    year_choices = list(range(2000, 2101))
    year_choices.reverse()

    subcategory_options = {
        record_type: dict(options) for record_type, options in FinancialDocument.SUBCATEGORY_OPTIONS.items()
    }
    subcategory_options_json = json.dumps(subcategory_options)

    documents = FinancialDocument.objects.all().order_by("record_type", "sub_record_type", "year")

    preselected_record_type = request.GET.get("record_type", "")
    preselected_sub_record_type = request.GET.get("sub_record_type", "")

    if request.method == "POST":
        form = FinancialDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            # Auto-generate original_name from record_type, sub_record_type, and year
            record_type_label = dict(FinancialDocument.RECORD_TYPE_CHOICES).get(
                document.record_type, document.record_type
            )
            subcategory_options = FinancialDocument.SUBCATEGORY_OPTIONS.get(document.record_type, [])
            subcategory_dict = dict(subcategory_options)
            sub_record_type_label = subcategory_dict.get(document.sub_record_type, document.sub_record_type)
            # Concatenate: record_type_label_sub_record_type_label_year
            document.original_name = f"{record_type_label}_{sub_record_type_label}_{document.year}"
            document.save()

            # OCR field extraction (if needed)
            from .utils import extract_fields_from_document

            extracted_fields = extract_fields_from_document(document.document.path)
            for name, value in extracted_fields:
                ExtractedField.objects.create(
                    document=document, field_name=name.strip(), field_value=value.strip()
                )

            document.processed = True
            document.save(update_fields=["processed"])

            return redirect("records:upload")

    else:
        form = FinancialDocumentForm()

    # Organize documents for display
    organized_docs = {}
    for doc in documents:
        if doc.record_type not in organized_docs:
            organized_docs[doc.record_type] = {
                'label': dict(FinancialDocument.RECORD_TYPE_CHOICES).get(doc.record_type, doc.record_type),
                'subcategories': {}
            }

        if doc.sub_record_type not in organized_docs[doc.record_type]['subcategories']:
            subcategory_label = subcategory_options.get(doc.record_type, {}).get(doc.sub_record_type, doc.sub_record_type)
            organized_docs[doc.record_type]['subcategories'][doc.sub_record_type] = {
                'label': subcategory_label,
                'documents': []
            }

        organized_docs[doc.record_type]['subcategories'][doc.sub_record_type]['documents'].append(doc)

    return render(
        request,
        "records/upload.html",
        {
            "active_tab": "records_upload",
            "form": form,
            "organized_docs": organized_docs,
            "documents": documents,
            "year_choices": year_choices,
            "subcategory_options_json": subcategory_options_json,
            "record_type_choices": FinancialDocument.RECORD_TYPE_CHOICES,
            "preselected_record_type": preselected_record_type,
            "preselected_sub_record_type": preselected_sub_record_type,
        },
    )


def insights_view(request):
    metrics = get_document_metrics()
    charts_json = json.dumps(metrics["charts_payload"], cls=DjangoJSONEncoder)
    return render(
        request,
        "records/insights.html",
        {
            **metrics,
            "charts_json": charts_json,
            "active_tab": "records_insights",
        },
    )


def explorer_view(request):
    record_tree = build_document_library()
    metrics = get_document_metrics()
    return render(
        request,
        "records/explorer.html",
        {
            "record_tree": record_tree,
            "coverage_by_type": metrics["coverage_by_type"],
            "active_tab": "records_explorer",
        },
    )

def document_list_partial(request):
    documents = FinancialDocument.objects.all()
    return render(request, "records/partials/document_list.html", {"documents": documents})

@require_POST
def delete_document(request, pk):
    try:
        document = FinancialDocument.objects.get(pk=pk)
        document.delete()
        return redirect("records:upload")
    except FinancialDocument.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Document not found"}, status=404)


def personal_details(request, pk):
    document = FinancialDocument.objects.get(pk=pk)
    fields = document.fields.all()
    return render(
        request,
        "records/personal_sensitive_details.html",
        {
            "document": document,
            "fields": fields,
        },
    )


def personal_sensitive_view(request):
    documents = FinancialDocument.objects.filter(record_type="government").prefetch_related("fields")
    plaid_personal_data = PlaidDataDistributionService.get_organized_plaid_data(request.user).get('personal_sensitive', {}) or {}
    plaid_personal_json = json.dumps(plaid_personal_data)
    
    context = {
        "active_tab": "records_personal_sensitive",
        "documents": documents,
        "plaid_data": plaid_personal_json,
        "plaid_personal_defaults": plaid_personal_data,
    }
    return render(request, "records/personal_sensitive_information.html", context)
