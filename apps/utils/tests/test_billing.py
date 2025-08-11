from decimal import Decimal
from types import SimpleNamespace

from apps.utils.billing import get_discounted_price


def test_get_discounted_price_amount_off():
    coupon = SimpleNamespace(amount_off=500, percent_off=None)
    assert get_discounted_price(Decimal("1500"), coupon) == Decimal("1000")


def test_get_discounted_price_percent_off():
    coupon = SimpleNamespace(amount_off=None, percent_off=20)
    result = get_discounted_price(Decimal("1000"), coupon)
    assert result == Decimal("800")
