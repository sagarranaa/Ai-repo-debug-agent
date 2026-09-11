import pytest

from shop.checkout import checkout


def test_checkout_without_coupon():
    items = [
        {"unit_price_paise": 100_000, "quantity": 1},
    ]

    result = checkout(items)

    assert result["subtotal_paise"] == 100_000
    assert result["total_paise"] == 100_000


def test_checkout_multiple_items():
    items = [
        {"unit_price_paise": 25_000, "quantity": 2},
        {"unit_price_paise": 10_000, "quantity": 3},
    ]

    result = checkout(items)

    assert result["total_paise"] == 80_000


def test_checkout_with_save10():
    items = [
        {"unit_price_paise": 100_000, "quantity": 1},
    ]

    result = checkout(items, coupon_code="SAVE10")

    assert result["subtotal_paise"] == 100_000
    assert result["total_paise"] == 90_000


def test_checkout_rejects_unknown_coupon():
    items = [
        {"unit_price_paise": 100_000, "quantity": 1},
    ]

    with pytest.raises(ValueError, match="Unknown coupon"):
        checkout(items, coupon_code="INVALID")

@pytest.mark.parametrize(
    "coupon_code, subtotal_paise, expected_total",
    [
        ("SAVE20", 100_000, 80_000),
        ("SAVE10", 999, 900),
        ("SAVE20", 999, 800),
    ],
)
def test_checkout_coupon_amounts(
    coupon_code,
    subtotal_paise,
    expected_total,
):
    items = [
        {
            "unit_price_paise": subtotal_paise,
            "quantity": 1,
        },
    ]

    result = checkout(items, coupon_code=coupon_code)

    assert result["subtotal_paise"] == subtotal_paise
    assert result["total_paise"] == expected_total