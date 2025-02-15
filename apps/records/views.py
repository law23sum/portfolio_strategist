# solutions/views.py

from django.shortcuts import render


def upload_records_view(request):
    context = {'active_tab': 'upload_records'}
    return render(request, 'records/upload_records.html', context)