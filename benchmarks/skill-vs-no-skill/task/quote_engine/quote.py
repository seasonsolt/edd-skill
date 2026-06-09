"""Usage-based invoice quote calculation."""

from __future__ import annotations


def quote_usage_invoice(
    usage_units: int,
    tiers: list[dict],
    discounts: list[dict] | None = None,
    minimum_cents: int = 0,
    tax_rate_bps: int = 0,
) -> dict:
    """Return an invoice quote for graduated usage pricing."""
    raise NotImplementedError("Implement the quote engine")
