from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, name="dispatch")
class ExamplesHomeView(TemplateView):
    template_name = "pegasus/examples/examples_home.html"

    def get_context_data(self, **kwargs):
        return {
            "active_tab": "home",
        }


# import other views
from .feature_flag_views import *  # noqa F401
from .form_views import *  # noqa F401
from .tasks_views import *  # noqa F401
