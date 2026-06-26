# Task: Subscription Billing Engine

Implement `calculate_invoice` in `subscription_billing/engine.py`.

## API

```python
def calculate_invoice(subscription: dict, event: dict) -> dict:
    ...
```

## Product Contract

The billing engine prices one subscription event at a time. It returns the charge to collect now and the next subscription state.

Required subscription fields:

- `customer_id`: non-empty string.
- `plan`: one of `"starter"`, `"pro"`, `"enterprise"`.
- `seats`: positive integer.
- `status`: one of `"trialing"`, `"active"`, `"canceled"`, `"past_due"`.
- `period_start_day`: integer day number.
- `period_end_day`: integer day number greater than `period_start_day`.

Optional subscription fields:

- `trial_end_day`: integer day number.
- `grace_period_end_day`: integer day number.
- `coupon_percent`: integer from `0` to `100`.
- `last_event_id`: string used for idempotency.

Required event fields:

- `event_id`: non-empty string.
- `type`: one of `"renewal"`, `"upgrade"`, `"downgrade"`, `"cancel"`, `"payment_failed"`.
- `day`: integer day number.

Event-specific fields:

- `upgrade` and `downgrade` require `new_plan`.
- `upgrade` and `downgrade` may include `new_seats`.
- `cancel` may include `cancel_at_period_end` boolean.

## Pricing

Monthly plan prices per seat:

| Plan | Cents / seat / period |
| --- | ---: |
| starter | 1000 |
| pro | 3000 |
| enterprise | 10000 |

## Behavior

- Invalid inputs raise `ValueError`.
- Replaying an event whose `event_id` equals `subscription.last_event_id` is idempotent: return a zero-cent invoice and leave the subscription unchanged.
- `renewal` charges the current plan for all seats unless the subscription is `canceled`.
- A subscription in `trialing` status is not charged before `trial_end_day`; on or after `trial_end_day`, `renewal` charges normally and moves status to `active`.
- `upgrade` charges prorated positive difference for the remaining days in the current period and immediately changes plan/seats. Proration uses whole cents with half-up rounding.
- `downgrade` changes plan/seats immediately but does not issue a credit; `amount_cents` is `0`.
- `cancel` with `cancel_at_period_end=True` leaves the subscription active until period end and charges `0`. Otherwise it changes status to `canceled` immediately and charges `0`.
- `payment_failed` changes status to `past_due`, sets `grace_period_end_day` to `day + 7`, and charges `0`.
- Coupon discounts apply to positive charges after proration. Use half-up rounding.

## Return Shape

```python
{
    "customer_id": str,
    "amount_cents": int,
    "reason": str,
    "next_subscription": dict,
}
```

Reasons should be one of: `"renewal"`, `"trial_no_charge"`, `"upgrade_proration"`, `"downgrade_no_credit"`, `"cancel_now"`, `"cancel_at_period_end"`, `"payment_failed"`, `"idempotent_replay"`, `"canceled_no_charge"`.
