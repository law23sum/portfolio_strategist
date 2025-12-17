from django.urls import reverse

from .base import TestLoginRequiredViewBase


class TestProfileViews(TestLoginRequiredViewBase):
    def test_profile(self):
        self._run_tests(reverse("users:user_profile"))

    def test_password_change(self):
        self._run_tests(reverse("account_change_password"))

    def test_2fa_setup(self):
        self._run_tests(reverse("mfa_index"))


class TestFinancialDefinitionsView(TestLoginRequiredViewBase):
    def test_financial_definitions_requires_login(self):
        self._run_tests(reverse("web:financial_definitions"))

    def test_financial_definitions_context_defaults(self):
        url = reverse("web:financial_definitions")
        response = self.authenticated_client.get(url)
        self.assertIsNone(response.context["return_url"])
        self.assertEqual(response.context["default_return_url"], reverse("web:stocks_assessment"))

    def test_financial_definitions_accepts_safe_return_url(self):
        url = reverse("web:financial_definitions")
        response = self.authenticated_client.get(url, {"return_url": "/some/path/"})
        self.assertEqual(response.context["return_url"], "/some/path/")

    def test_financial_definitions_rejects_external_return_url(self):
        url = reverse("web:financial_definitions")
        response = self.authenticated_client.get(url, {"return_url": "https://example.com/other/"})
        self.assertIsNone(response.context["return_url"])

    def test_financial_definitions_rejects_path_traversal(self):
        url = reverse("web:financial_definitions")
        response = self.authenticated_client.get(url, {"return_url": "/../etc/passwd"})
        self.assertIsNone(response.context["return_url"])
