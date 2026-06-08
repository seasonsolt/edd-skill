import unittest

from feature_flags import evaluate_flag


class FeatureFlagPublicTests(unittest.TestCase):
    def test_disabled_flag_short_circuits(self):
        result = evaluate_flag(
            {
                "key": "checkout",
                "default": True,
                "enabled": False,
                "allowlist": ["u1"],
            },
            {"key": "u1"},
        )

        self.assertEqual(
            result,
            {"key": "checkout", "enabled": False, "reason": "disabled", "bucket_bps": None},
        )

    def test_allowlist_enables_user(self):
        result = evaluate_flag(
            {
                "key": "search",
                "default": False,
                "allowlist": ["u2"],
            },
            {"key": "u2"},
        )

        self.assertEqual(result["enabled"], True)
        self.assertEqual(result["reason"], "allowlist")
        self.assertIsNone(result["bucket_bps"])


if __name__ == "__main__":
    unittest.main()
