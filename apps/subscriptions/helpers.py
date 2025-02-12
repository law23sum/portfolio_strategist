import logging

from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djstripe.enums import SubscriptionStatus
from djstripe.models import Price, Subscription
from djstripe.settings import djstripe_settings
from stripe.api_resources.billing_portal.session import Session as BillingPortalSession
from stripe.api_resources.checkout import Session as CheckoutSession
from stripe.error import InvalidRequestError

from apps.users.models import CustomUser
from apps.utils.billing import get_stripe_module
from apps.web.meta import absolute_url

from .exceptions import SubscriptionConfigError

log = logging.getLogger("portfolio_strategist.subscription")


def subscription_is_active(subscription: Subscription) -> bool:
    return subscription.status in [SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due]


def subscription_is_trialing(subscription: Subscription) -> bool:
    return subscription.status == SubscriptionStatus.trialing and subscription.trial_end > timezone.now()


def get_subscription_urls(subscription_holder):
    # get URLs for subscription helpers
    url_bases = [
        "subscription_details",
        "create_stripe_portal_session",
        "subscription_demo",
        "subscription_gated_page",
        "metered_billing_demo",
        # checkout urls
        "checkout_canceled",
    ]

    def _construct_url(base):
        return reverse(f"subscriptions:{base}")

    return {url_base: _construct_url(url_base) for url_base in url_bases}


def create_stripe_checkout_session(
    subscription_holder: CustomUser, stripe_price_id: str, user: CustomUser
) -> CheckoutSession:
    stripe = get_stripe_module()
    success_url = absolute_url(reverse("subscriptions:subscription_confirm"))

    cancel_url = absolute_url(reverse("subscriptions:checkout_canceled"))

    customer_kwargs = {}
    if subscription_holder.customer:
        customer_kwargs["customer"] = subscription_holder.customer.id
    else:
        customer_kwargs["customer_email"] = user.email

    checkout_session = stripe.checkout.Session.create(
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        payment_method_types=["card"],
        mode="subscription",
        client_reference_id=subscription_holder.id,
        line_items=[
            {
                "price": stripe_price_id,
                "quantity": _get_quantity(stripe_price_id, subscription_holder),
            }
        ],
        allow_promotion_codes=True,
        subscription_data={
            "description": str(subscription_holder),
            "metadata": get_checkout_metadata(user),
        },
        metadata={
            "source": "subscriptions",
        },
        **customer_kwargs,
    )
    return checkout_session


def get_checkout_metadata(user: CustomUser) -> dict:
    return {
        f"{djstripe_settings.SUBSCRIBER_CUSTOMER_KEY}": user.id,
        "user_id": user.id,
        "user_email": user.email,
        "user_name": user.get_full_name(),
    }


def _get_quantity(stripe_price_id, subscription_holder):
    """
    Get quantity for a given Stripe price and subscription holder
    """
    price = Price.objects.get(id=stripe_price_id)
    # if it's metered billing we shouldn't pass a quantity
    if price.recurring.get("usage_type", None) == "metered":
        return None
    # otherwise we pass it from the subscription holder
    return subscription_holder.get_quantity()


def create_stripe_portal_session(subscription_holder: CustomUser) -> BillingPortalSession:
    stripe = get_stripe_module()
    if not subscription_holder.subscription or not subscription_holder.subscription.customer:
        raise SubscriptionConfigError(_("Whoops, we couldn't find a subscription associated with your account!"))

    subscription_urls = get_subscription_urls(subscription_holder)
    portal_session = stripe.billing_portal.Session.create(
        customer=subscription_holder.subscription.customer.id,
        return_url=absolute_url(subscription_urls["subscription_details"]),
    )
    return portal_session


@transaction.atomic
def provision_subscription(subscription_holder: CustomUser, subscription_id: str) -> Subscription:
    stripe = get_stripe_module()
    subscription = stripe.Subscription.retrieve(subscription_id)
    djstripe_subscription = Subscription.sync_from_stripe_data(subscription)
    subscription_holder.subscription = djstripe_subscription
    subscription_holder.save()
    # attach customer if not set
    if not subscription_holder.customer:
        subscription_holder.customer = djstripe_subscription.customer
        subscription_holder.save()
    return djstripe_subscription


def cancel_subscription(subscription_id: str):
    try:
        subscription = get_stripe_module().Subscription.delete(subscription_id)
    except InvalidRequestError as e:
        if e.code != "resource_missing":
            log.error("Error deleting Stripe subscription: %s", e.user_message)
    else:
        Subscription.sync_from_stripe_data(subscription)
