import decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from djstripe.models import APIKey, Coupon, Price
    from djstripe.utils import CURRENCY_SIGILS


def get_stripe_module():
    """Gets the Stripe API module, with the API key properly populated"""
    import stripe
    from djstripe.settings import djstripe_settings

    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
    return stripe


def create_stripe_api_keys_if_necessary() -> bool:
    from djstripe.models import APIKey
    from djstripe.settings import djstripe_settings

    key, created = APIKey.objects.get_or_create_by_api_key(djstripe_settings.STRIPE_SECRET_KEY)
    return created


def get_discounted_price(amount: decimal.Decimal, coupon: "Coupon") -> decimal.Decimal:
    """Return ``amount`` after applying a ``coupon`` discount.

    ``amount`` and ``coupon.amount_off`` are expected to use the same currency
    units (typically the smallest unit, e.g. cents). The previous implementation
    subtracted ``coupon.amount_off`` after multiplying it by 100 which produced
    wildly incorrect results by discounting 100x the intended amount. We also
    ensure percent based discounts use ``Decimal`` arithmetic.
    """
    if coupon.amount_off:
        return max(amount - decimal.Decimal(coupon.amount_off), decimal.Decimal("0"))
    elif coupon.percent_off:
        return amount * (decimal.Decimal("1") - (decimal.Decimal(coupon.percent_off) / 100))
    return amount


def get_friendly_currency_amount(price: "Price", currency: str = None):
    # modified from djstripe's version to only include sigil or currency, but not both
    # and handle multiple currencies
    if not currency:
        currency = price.currency
    if currency != price.currency:
        amount = get_price_for_secondary_currency(price, currency)
    elif price.unit_amount_decimal is None:
        return "Unknown"
    else:
        amount = price.unit_amount_decimal
    return get_price_display_with_currency(amount / 100, currency)


def get_price_for_secondary_currency(price: "Price", currency: str):
    # we have to hit the Stripe API for this because djstripe doesn't save it.
    stripe_price = get_stripe_module().Price.retrieve(price.id, expand=["currency_options"])
    unit_amount_decimal = stripe_price.currency_options[currency]["unit_amount_decimal"]
    return int(float(unit_amount_decimal))


def get_price_display_with_currency(amount: float, currency: str) -> str:
    from djstripe.utils import CURRENCY_SIGILS

    currency = currency.upper()
    sigil = CURRENCY_SIGILS.get(currency, "")
    if sigil:
        return "{sigil}{amount:.2f}".format(sigil=sigil, amount=amount)
    else:
        return "{amount:.2f} {currency}".format(amount=amount, currency=currency)
