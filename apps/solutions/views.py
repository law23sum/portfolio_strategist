# solutions/views.py

from django.shortcuts import render


def budgeting_view(request):
    context = {'active_tab': 'budgeting'}
    return render(request, 'solutions/budgeting.html', context)