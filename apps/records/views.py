import json
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import FinancialDocumentForm
from .models import ExtractedField, FinancialDocument


def upload_view(request):
    current_year = datetime.now().year
    year_choices = list(range(2000, current_year + 6))
    year_choices.reverse()

    subcategory_options = {
        record_type: dict(options) for record_type, options in FinancialDocument.SUBCATEGORY_OPTIONS.items()
    }
    subcategory_options_json = json.dumps(subcategory_options)

    documents = FinancialDocument.objects.all().order_by("record_type", "sub_record_type", "year")

    if request.method == "POST":
        form = FinancialDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()

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
            "form": form,
            "organized_docs": organized_docs,
            "documents": documents,
            "year_choices": year_choices,
            "subcategory_options_json": subcategory_options_json,
            "record_type_choices": FinancialDocument.RECORD_TYPE_CHOICES,
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
