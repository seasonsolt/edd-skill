import hashlib
import unittest

from feature_flags import evaluate_flag


def bucket(flag_key, user_key):
    digest = hashlib.sha256(f"{flag_key}:{user_key}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 10000


class FeatureFlagHiddenTests(unittest.TestCase):
    def test_denylist_takes_precedence_over_allowlist(self):
        result = evaluate_flag(
            {
                "key": "search",
                "default": True,
                "denylist": ["u1"],
                "allowlist": ["u1"],
            },
            {"key": "u1"},
        )

        self.assertEqual(result["enabled"], False)
        self.assertEqual(result["reason"], "denylist")
        self.assertIsNone(result["bucket_bps"])

    def test_first_matching_rule_wins(self):
        result = evaluate_flag(
            {
                "key": "pricing",
                "default": False,
                "rules": [
                    {"name": "enterprise", "attribute": "plan", "op": "equals", "value": "enterprise", "enabled": True},
                    {"name": "us-block", "attribute": "country", "op": "equals", "value": "US", "enabled": False},
                ],
            },
            {"key": "u2", "plan": "enterprise", "country": "US"},
        )

        self.assertEqual(result["enabled"], True)
        self.assertEqual(result["reason"], "rule:enterprise")

    def test_missing_rule_attribute_does_not_match(self):
        result = evaluate_flag(
            {
                "key": "pricing",
                "default": False,
                "rules": [
                    {"name": "missing", "attribute": "plan", "op": "equals", "value": "enterprise", "enabled": True}
                ],
            },
            {"key": "u3"},
        )

        self.assertEqual(result["enabled"], False)
        self.assertEqual(result["reason"], "default")

    def test_rollout_uses_exact_bucket_algorithm(self):
        flag = {"key": "feed", "default": False, "rollout_bps": 5000}
        user = {"key": "user-42"}
        result = evaluate_flag(flag, user)

        expected_bucket = bucket("feed", "user-42")
        self.assertEqual(result["bucket_bps"], expected_bucket)
        self.assertEqual(result["enabled"], expected_bucket < 5000)
        self.assertEqual(result["reason"], "rollout" if expected_bucket < 5000 else "default")

    def test_rule_operators(self):
        cases = [
            ({"name": "tier", "attribute": "tier", "op": "in", "value": ["pro", "team"], "enabled": True}, {"tier": "team"}),
            ({"name": "age-min", "attribute": "age", "op": "gte", "value": 18, "enabled": True}, {"age": 18}),
            ({"name": "risk-max", "attribute": "risk", "op": "lte", "value": 3, "enabled": True}, {"risk": 2}),
        ]

        for rule, attributes in cases:
            with self.subTest(rule=rule):
                result = evaluate_flag(
                    {"key": "rules", "default": False, "rules": [rule]},
                    {"key": "u4", **attributes},
                )
                self.assertEqual(result["enabled"], True)
                self.assertEqual(result["reason"], f"rule:{rule['name']}")

    def test_invalid_inputs_raise_value_error(self):
        invalid_calls = [
            lambda: evaluate_flag({}, {"key": "u1"}),
            lambda: evaluate_flag({"key": "", "default": False}, {"key": "u1"}),
            lambda: evaluate_flag({"key": "x", "default": "no"}, {"key": "u1"}),
            lambda: evaluate_flag({"key": "x", "default": False, "rollout_bps": -1}, {"key": "u1"}),
            lambda: evaluate_flag({"key": "x", "default": False, "rollout_bps": 10001}, {"key": "u1"}),
            lambda: evaluate_flag({"key": "x", "default": False}, {"key": ""}),
            lambda: evaluate_flag(
                {"key": "x", "default": False, "rules": [{"name": "bad", "attribute": "a", "op": "contains", "value": "x", "enabled": True}]},
                {"key": "u1", "a": "x"},
            ),
        ]

        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaises(ValueError):
                    invalid_call()


if __name__ == "__main__":
    unittest.main()
