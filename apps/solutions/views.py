# solutions/views.py

from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

def budgeting_view(request):
    context = {'active_tab': 'budgeting'}
    return render(request, 'solutions/budgeting.html', context)


@method_decorator(login_required, name="dispatch")
class ChartsView(TemplateView):
    template_name = "reports/charts.html"

    def get_context_data(self, **kwargs):
        return {
            "active_tab": "charts",
        }