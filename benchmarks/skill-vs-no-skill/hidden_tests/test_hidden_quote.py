import unittest

from quote_engine import quote_usage_invoice


class QuoteUsageInvoiceHiddenTests(unittest.TestCase):
    def test_minimum_discounts_and_tax_round_half_up(self):
        result = quote_usage_invoice(
            usage_units=250,
            tiers=[
                {"up_to": 100, "unit_price_cents": 10},
                {"up_to": 200, "unit_price_cents": 8},
                {"up_to": None, "unit_price_cents": 5},
            ],
            discounts=[
                {"type": "percent", "value_bps": 1000},
                {"type": "fixed", "amount_cents": 300},
            ],
            minimum_cents=2500,
            tax_rate_bps=825,
        )

        self.assertEqual(result["usage_subtotal_cents"], 2050)
        self.assertEqual(result["minimum_adjustment_cents"], 450)
        self.assertEqual(result["discount_cents"], 550)
        self.assertEqual(result["tax_cents"], 161)
        self.assertEqual(result["total_cents"], 2111)
        self.assertEqual([item["units"] for item in result["line_items"]], [100, 100, 50])

    def test_zero_usage_minimum_and_fixed_discount_floor(self):
        result = quote_usage_invoice(
            usage_units=0,
            tiers=[{"up_to": None, "unit_price_cents": 99}],
            discounts=[{"type": "fixed", "amount_cents": 500}],
            minimum_cents=300,
        )

        self.assertEqual(result["line_items"], [])
        self.assertEqual(result["minimum_adjustment_cents"], 300)
        self.assertEqual(result["discount_cents"], 300)
        self.assertEqual(result["total_cents"], 0)

    def test_percent_discount_rounds_half_up(self):
        result = quote_usage_invoice(
            usage_units=1,
            tiers=[{"up_to": None, "unit_price_cents": 101}],
            discounts=[{"type": "percent", "value_bps": 5000}],
        )

        self.assertEqual(result["discount_cents"], 51)
        self.assertEqual(result["total_cents"], 50)

    def test_tax_rounds_half_up(self):
        result = quote_usage_invoice(
            usage_units=1,
            tiers=[{"up_to": None, "unit_price_cents": 100}],
            tax_rate_bps=1250,
        )

        self.assertEqual(result["tax_cents"], 13)
        self.assertEqual(result["total_cents"], 113)

    def test_invalid_tiers_raise_value_error(self):
        invalid_tier_sets = [
            [],
            [{"up_to": 100, "unit_price_cents": 10}],
            [{"up_to": 100, "unit_price_cents": 10}, {"up_to": 50, "unit_price_cents": 8}, {"up_to": None, "unit_price_cents": 5}],
            [{"up_to": None, "unit_price_cents": 0}],
        ]

        for tiers in invalid_tier_sets:
            with self.subTest(tiers=tiers):
                with self.assertRaises(ValueError):
                    quote_usage_invoice(usage_units=1, tiers=tiers)


if __name__ == "__main__":
    unittest.main()
