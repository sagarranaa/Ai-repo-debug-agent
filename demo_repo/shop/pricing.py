from shop.coupons import apply_coupon


def calculate_subtotal(items: list[dict]) -> int:
    """Calculate the total item value in paise."""

    return sum(
        item["unit_price_paise"] * item["quantity"]
        for item in items
    )


def calculate_total(
    subtotal_paise: int,
    coupon_code: str | None = None,
) -> int:
    """Calculate the payable amount after a coupon."""

    return apply_coupon(subtotal_paise, coupon_code)