from shop.pricing import calculate_subtotal, calculate_total


def checkout(
    items: list[dict],
    coupon_code: str | None = None,
) -> dict:
    """Return the cart subtotal and payable amount."""

    subtotal = calculate_subtotal(items)

    total = calculate_total(
        subtotal,
        coupon_code,
    )

    return {
        "subtotal_paise": subtotal,
        "total_paise": total,
    }
