from django.urls import reverse

from apps.web.tests.base import TestLoginRequiredViewBase


class TestExamplesViews(TestLoginRequiredViewBase):
    def test_examples_home(self):
        self._run_tests(reverse("pegasus_examples:examples_home"))

    def test_tasks(self):
        self._run_tests(reverse("pegasus_examples:tasks"))

    def test_flags(self):
        self._run_tests(reverse("pegasus_examples:flags"))

    def test_object_lifecycle_home(self):
        self._run_tests(reverse("pegasus_employees:object_lifecycle_home"))

    def test_charts(self):
        self._run_tests(reverse("pegasus_employees:charts"))
