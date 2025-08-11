from django.shortcuts import render, redirect
from .models import FinancialDocument
from .forms import FinancialDocumentForm
import json
from datetime import datetime
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.http import JsonResponse

def upload_view(request):
    current_year = datetime.now().year
    year_choices = list(range(2000, current_year + 6))
    year_choices.reverse()

    subcategory_options = {
        record_type: dict(options)
        for record_type, options in FinancialDocument.SUBCATEGORY_OPTIONS.items()
    }
    subcategory_options_json = json.dumps(subcategory_options)

    # Get all documents ordered appropriately
    documents = FinancialDocument.objects.all().order_by('record_type', 'sub_record_type', 'year')

    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()

            # OCR field extraction (if needed)
            from .utils import extract_fields_from_document
            extracted_fields = extract_fields_from_document(document.document.path)
            for name, value in extracted_fields:
                ExtractedField.objects.create(
                    document=document,
                    field_name=name.strip(),
                    field_value=value.strip()
                )

            # Return JSON response for AJAX or redirect for normal form submission
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'document': {
                        'id': document.id,
                        'original_name': document.original_name,
                        'record_type': document.record_type,
                        'year': document.year,
                        'processed': document.processed,
                        'url': document.document.url
                    }
                })
            return redirect('records:upload')
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
        request, 'records/upload.html', {
            'form': form,
            'documents': documents,  # Add this line to pass documents to template
            'organized_docs': organized_docs,
            'year_choices': year_choices,
            'subcategory_options_json': subcategory_options_json,
            'record_type_choices': FinancialDocument.RECORD_TYPE_CHOICES,
        })


def document_list_partial(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status = 401)

    try:
        documents = FinancialDocument.objects.filter(user = request.user).order_by('-uploaded_at')
    except Exception as e:
        if 'user_id' in str(e):
            documents = FinancialDocument.objects.all().order_by('-uploaded_at')
        else:
            raise

    return render(
            request, 'records/partials/document_list.html',
            {'documents': documents})

@require_POST
def delete_document(request, pk):
    try:
        document = FinancialDocument.objects.get(pk=pk)
        document.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return redirect('records:upload')
    except FinancialDocument.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Document not found'}, status=404)