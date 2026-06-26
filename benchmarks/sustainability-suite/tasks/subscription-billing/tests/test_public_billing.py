import unittest

from subscription_billing import calculate_invoice


class SubscriptionBillingPublicTests(unittest.TestCase):
    def test_active_renewal_charges_plan_times_seats(self):
        subscription = {
            "customer_id": "cus_1",
            "plan": "pro",
            "seats": 3,
            "status": "active",
            "period_start_day": 0,
            "period_end_day": 30,
        }

        result = calculate_invoice(subscription, {"event_id": "evt_1", "type": "renewal", "day": 30})

        self.assertEqual(result["amount_cents"], 9000)
        self.assertEqual(result["reason"], "renewal")
        self.assertEqual(result["next_subscription"]["last_event_id"], "evt_1")

    def test_trial_before_trial_end_is_not_charged(self):
        subscription = {
            "customer_id": "cus_2",
            "plan": "starter",
            "seats": 2,
            "status": "trialing",
            "trial_end_day": 14,
            "period_start_day": 0,
            "period_end_day": 30,
        }

        result = calculate_invoice(subscription, {"event_id": "evt_2", "type": "renewal", "day": 7})

        self.assertEqual(result["amount_cents"], 0)
        self.assertEqual(result["reason"], "trial_no_charge")
        self.assertEqual(result["next_subscription"]["status"], "trialing")


if __name__ == "__main__":
    unittest.main()
