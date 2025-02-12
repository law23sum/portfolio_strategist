from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView

from pegasus.apps.examples.forms import ExampleForm, ExampleFormAlpine


class ExampleFormView(FormView):
    template_name = "pegasus/examples/example_form.html"
    form_class = ExampleForm

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        messages.success(self.request, "Thanks for filling in the form!")
        return redirect("pegasus_examples:examples_home")


class AlpineFormView(FormView):
    template_name = "pegasus/examples/example_form_alpine.html"
    form_class = ExampleFormAlpine

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        messages.success(self.request, "Thanks for filling in the form!")
        return redirect("pegasus_examples:examples_home")
