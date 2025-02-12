from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "pegasus_examples"

urlpatterns = [
    path("", views.ExamplesHomeView.as_view(), name="examples_home"),
    path(
        "pricing-page/",
        TemplateView.as_view(
            template_name="pegasus/examples/example_pricing_page.html", extra_context={"active_tab": "pricing_page"}
        ),
        name="pricing_page",
    ),
    # these are experimental examples that aren't currently exposed in the UI.
    path("alpine/", TemplateView.as_view(template_name="pegasus/examples/alpine_demo.html"), name="alpine_demo"),
    path("forms/", views.ExampleFormView.as_view(), name="form_demo"),
    path("forms/alpine/", views.AlpineFormView.as_view(), name="alpine_form_demo"),
    # tasks
    path("tasks/", views.TasksView.as_view(), name="tasks"),
    path("tasks/api/", views.tasks_api, name="tasks_api"),
    # flags
    path("flags/", views.FeatureFlagExampleView.as_view(), name="flags"),
]
