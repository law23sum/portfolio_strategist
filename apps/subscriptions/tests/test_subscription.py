from unittest import mock

from django.http import HttpResponse
from django.test import TestCase

from apps.subscriptions.decorators import active_subscription_required
from apps.subscriptions.metadata import ProductMetadata
from apps.subscriptions.tests.utils import create_subscription_for_user, get_mock_request
from apps.users.models import CustomUser

PASSWORD = "123"

MOCK_ACTIVE_PRODUCTS = [
    ProductMetadata(
        stripe_id="prod_abc",
        slug="plan-a",
        name="Plan A",
        features=[],
        price_displays={},
        description="This is Plan A",
        is_default=False,
    ),
    ProductMetadata(
        stripe_id="prod_def",
        slug="plan-b",
        name="Plan B",
        features=[],
        price_displays={},
        description="This is Plan B",
        is_default=False,
    ),
]


@mock.patch("apps.subscriptions.metadata.ACTIVE_PRODUCTS", MOCK_ACTIVE_PRODUCTS)
class SubscriptionTests(TestCase):
    """These tests demonstrate how to test subscription gated views by creating the subscription
    (and related objects) in the database. This is useful if some aspect of the test relies on the details
    of the subscription e.g. specific features to enable etc.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user_with_sub = CustomUser.objects.create(username="richard@example.com")
        cls.user_without_sub = CustomUser.objects.create(username="robin@example.com")
        cls.subscription = create_subscription_for_user(cls.user_with_sub, MOCK_ACTIVE_PRODUCTS[0], metered=True)

    def test_gated_view_has_active_subscription(self):
        request = get_mock_request(self.user_with_sub)
        response = mock_gated_view(request)
        self.assertEqual(response.status_code, 200)

    def test_gated_view_no_active_subscription(self):
        request = get_mock_request(self.user_without_sub)
        response = mock_gated_view(request)
        self.assertEqual(response.status_code, 302)

    def test_gated_view_limit_to_plan_allow(self):
        """The subscription has access to this view because it is on to the correct plan."""
        request = get_mock_request(self.user_with_sub)
        response = mock_view_limited_to_plan_a(request)
        self.assertEqual(response.status_code, 200)

    def test_gated_view_limit_to_plan_deny(self):
        """The subscription does not have access to this view because it is limited to a different plan."""
        request = get_mock_request(self.user_with_sub)
        response = mock_view_limited_to_plan_b(request)
        self.assertEqual(response.status_code, 302)


@active_subscription_required
def mock_gated_view(request):
    return HttpResponse()


@active_subscription_required(limit_to_plans=["plan-a"])
def mock_view_limited_to_plan_a(request):
    return HttpResponse()


@active_subscription_required(limit_to_plans=["plan-b"])
def mock_view_limited_to_plan_b(request):
    return HttpResponse()
