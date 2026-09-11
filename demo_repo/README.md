# Demo Checkout Service

This service calculates a cart subtotal and the final payable amount.

## Business rules

- All monetary values use integer paise.
- The subtotal equals the sum of unit price multiplied by quantity.
- SAVE10 gives a 10% discount.
- SAVE20 gives a 20% discount.
- A coupon must be applied exactly once per checkout.
- Discount amounts are rounded down to whole paise.
- An unknown coupon raises ValueError.
- There are no taxes or shipping charges.

## Reported issue

Checkout returns an incorrect payable amount when SAVE10 is used.

For a subtotal of 100000 paise, the expected payable amount
with SAVE10 is 90000 paise.

## Tests

Run from this demo_repo directory:

python -m pytest tests/test_checkout.py -q