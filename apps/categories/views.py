# solutions/views.py

from django.shortcuts import render


def government_view(request):
    context = {'active_tab': 'government'}
    return render(request, 'categories/government.html', context)