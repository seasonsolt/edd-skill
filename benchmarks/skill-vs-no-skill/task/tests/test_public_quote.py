import unittest

from quote_engine import quote_usage_invoice


class QuoteUsageInvoicePublicTests(unittest.TestCase):
    def test_single_tier_without_discount(self):
        result = quote_usage_invoice(
            usage_units=5,
            tiers=[{"up_to": None, "unit_price_cents": 20}],
        )

        self.assertEqual(result["usage_subtotal_cents"], 100)
        self.assertEqual(result["minimum_adjustment_cents"], 0)
        self.assertEqual(result["discount_cents"], 0)
        self.assertEqual(result["tax_cents"], 0)
        self.assertEqual(result["total_cents"], 100)
        self.assertEqual(
            result["line_items"],
            [{"from": 1, "to": None, "units": 5, "unit_price_cents": 20, "amount_cents": 100}],
        )

    def test_graduated_tier_boundary(self):
        result = quote_usage_invoice(
            usage_units=100,
            tiers=[
                {"up_to": 100, "unit_price_cents": 10},
                {"up_to": None, "unit_price_cents": 7},
            ],
        )

        self.assertEqual(result["usage_subtotal_cents"], 1000)
        self.assertEqual(len(result["line_items"]), 1)
        self.assertEqual(result["line_items"][0]["to"], 100)


if __name__ == "__main__":
    unittest.main()
