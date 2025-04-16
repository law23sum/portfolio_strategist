from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from ..tasks import progress_bar_task



@require_POST
def tasks_api(request):
    result = progress_bar_task.delay(5)
    return HttpResponse(result.task_id)