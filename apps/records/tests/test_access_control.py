import importlib

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import clear_url_caches, reverse

from apps.records.models import FinancialDocument, Receipt

def _png_bytes():
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (2, 2), "white").save(buf, format="PNG")
    return buf.getvalue()


PNG_BYTES = _png_bytes()


def make_user(email):
    return get_user_model().objects.create_user(username=email, email=email, password="pw-for-tests-only")


class RecordsViewsRequireLoginTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.doc = FinancialDocument.objects.create(
            user=self.owner, record_type="earnings", sub_record_type="pay_stubs", year=2024, document="d/x.pdf"
        )

    def _assert_redirects_to_login(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response["Location"])
        self.assertIn("next=", response["Location"])

    def test_anonymous_get_is_redirected_to_login(self):
        for name, kwargs in [
            ("records:upload", {}),
            ("records:document_list_partial", {}),
            ("records:personal_details", {"pk": self.doc.pk}),
        ]:
            with self.subTest(view=name):
                self._assert_redirects_to_login(self.client.get(reverse(name, kwargs=kwargs)))

    def test_anonymous_post_to_upload_and_delete_is_redirected_and_changes_nothing(self):
        self._assert_redirects_to_login(self.client.post(reverse("records:upload"), {}))
        self._assert_redirects_to_login(self.client.post(reverse("records:delete_document", args=[self.doc.pk])))
        self.assertTrue(FinancialDocument.objects.filter(pk=self.doc.pk).exists())

    def test_anonymous_users_do_not_get_a_500(self):
        # Previously request.user was AnonymousUser and the ORM filter raised TypeError.
        self.assertLess(self.client.get(reverse("records:upload")).status_code, 400)

    def test_owner_can_use_the_views(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("records:document_list_partial")).status_code, 200)
        self.assertEqual(self.client.get(reverse("records:personal_details", args=[self.doc.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("records:upload")).status_code, 200)

    def test_other_users_cannot_see_or_delete_a_document(self):
        self.client.force_login(make_user("other@example.com"))
        self.assertEqual(self.client.get(reverse("records:personal_details", args=[self.doc.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("records:delete_document", args=[self.doc.pk])).status_code, 404)
        self.assertTrue(FinancialDocument.objects.filter(pk=self.doc.pk).exists())

    def test_owner_delete_works_and_get_is_not_allowed(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("records:delete_document", args=[self.doc.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("records:delete_document", args=[self.doc.pk])).status_code, 302)
        self.assertFalse(FinancialDocument.objects.filter(pk=self.doc.pk).exists())


class ReceiptApiTests(TestCase):
    def setUp(self):
        self.user = make_user("api@example.com")

    def _payload(self, **extra):
        return {
            "image": SimpleUploadedFile("r.png", PNG_BYTES, content_type="image/png"),
            "title": "Coffee",
            "amount": "4.50",
            "date": "2026-01-02",
            **extra,
        }

    def test_serializer_exposes_user_read_only(self):
        from apps.records.serializers import ReceiptSerializer

        serializer = ReceiptSerializer()
        self.assertIn("user", serializer.fields)
        self.assertTrue(serializer.fields["user"].read_only)

    def test_post_associates_receipt_with_authenticated_user(self):
        from rest_framework.test import APIRequestFactory, force_authenticate

        from apps.records.api_views import ReceiptUploadView

        request = APIRequestFactory().post("/receipts/", self._payload(), format="multipart")
        force_authenticate(request, user=self.user)
        with override_settings(MEDIA_ROOT=self._tmp_media()):
            response = ReceiptUploadView.as_view()(request)
        self.assertEqual(response.status_code, 201, response.data)
        receipt = Receipt.objects.get()
        self.assertEqual(receipt.user, self.user)
        self.assertEqual(response.data["user"], self.user.id)

    def test_client_supplied_user_is_ignored(self):
        from rest_framework.test import APIRequestFactory, force_authenticate

        from apps.records.api_views import ReceiptUploadView

        victim = make_user("victim@example.com")
        request = APIRequestFactory().post("/receipts/", self._payload(user=str(victim.id)), format="multipart")
        force_authenticate(request, user=self.user)
        with override_settings(MEDIA_ROOT=self._tmp_media()):
            response = ReceiptUploadView.as_view()(request)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Receipt.objects.get().user, self.user)

    def test_anonymous_post_is_rejected(self):
        from rest_framework.test import APIRequestFactory

        from apps.records.api_views import ReceiptUploadView

        request = APIRequestFactory().post("/receipts/", self._payload(), format="multipart")
        response = ReceiptUploadView.as_view()(request)
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(Receipt.objects.count(), 0)

    def test_invalid_payload_returns_400_with_errors(self):
        from rest_framework.test import APIRequestFactory, force_authenticate

        from apps.records.api_views import ReceiptUploadView

        request = APIRequestFactory().post("/receipts/", {"title": "x"}, format="multipart")
        force_authenticate(request, user=self.user)
        response = ReceiptUploadView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.data)

    def _tmp_media(self):
        import tempfile

        d = tempfile.mkdtemp(prefix="receipts-test-")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        return d


class MediaServingTests(TestCase):
    def _reload_urls(self):
        import portfolio_strategist.urls as urls_module

        clear_url_caches()
        return importlib.reload(urls_module)

    def tearDown(self):
        self._reload_urls()

    def _media_patterns(self, module):
        return [p for p in module.urlpatterns if str(p.pattern).lstrip("^").startswith("media/")]

    def test_media_is_not_routed_when_debug_is_off(self):
        with override_settings(DEBUG=False):
            module = self._reload_urls()
            self.assertEqual(self._media_patterns(module), [])
            self.assertEqual(self.client.get("/media/receipts/anything.png").status_code, 404)

    def test_media_is_routed_only_when_debug_is_on(self):
        with override_settings(DEBUG=True):
            module = self._reload_urls()
            self.assertEqual(len(self._media_patterns(module)), 1)
