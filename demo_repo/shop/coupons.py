COUPON_PERCENTAGES = {
    "SAVE10": 10,
    "SAVE20": 20,
}


def apply_coupon(
    amount_paise: int,
    coupon_code: str | None,
) -> int:
    """Apply a supported coupon to an amount in paise."""

    if coupon_code is None:
        return amount_paise

    if coupon_code not in COUPON_PERCENTAGES:
        raise ValueError("Unknown coupon")

    percentage = COUPON_PERCENTAGES[coupon_code]
    discount_paise = amount_paise * percentage // 100

    return amount_paise - discount_paise