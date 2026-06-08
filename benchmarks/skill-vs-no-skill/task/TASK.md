# Task: Usage Quote Engine

Implement `quote_usage_invoice` in `quote_engine/quote.py`.

## API

```python
def quote_usage_invoice(
    usage_units: int,
    tiers: list[dict],
    discounts: list[dict] | None = None,
    minimum_cents: int = 0,
    tax_rate_bps: int = 0,
) -> dict:
    ...
```

## Rules

- `usage_units` must be a non-negative integer.
- `tiers` must be a non-empty list of dictionaries with:
  - `up_to`: positive integer upper bound, or `None` for the final open-ended tier.
  - `unit_price_cents`: positive integer price per unit.
- Tiers use graduated pricing. For tiers `100 @ 10`, `200 @ 8`, `None @ 5`, usage of `250` costs `100*10 + 100*8 + 50*5`.
- Tier upper bounds are inclusive.
- The final tier must have `up_to: None`.
- `minimum_cents` is applied after usage subtotal and before discounts.
- `discounts` are applied in list order after the minimum:
  - Percent discount: `{"type": "percent", "value_bps": 1000}` means 10%.
  - Fixed discount: `{"type": "fixed", "amount_cents": 300}` means subtract 300 cents.
  - Each discount is rounded half up to cents when needed.
  - The running subtotal must never go below zero.
- `tax_rate_bps` is applied after discounts and rounded half up to cents.
- Invalid inputs raise `ValueError`.

## Return Shape

Return this dictionary:

```python
{
    "usage_units": int,
    "line_items": [
        {
            "from": int,
            "to": int | None,
            "units": int,
            "unit_price_cents": int,
            "amount_cents": int,
        }
    ],
    "usage_subtotal_cents": int,
    "minimum_adjustment_cents": int,
    "discount_cents": int,
    "tax_cents": int,
    "total_cents": int,
}
```

Line items should include only tiers that bill at least one unit.
