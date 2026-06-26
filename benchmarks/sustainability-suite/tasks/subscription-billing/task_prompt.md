Implement the subscription billing engine in `subscription_billing/engine.py`.

The starter contract in `TASK.md` is intentionally product-style rather than exhaustive. Focus on behavior that keeps billing safe over time: trial-to-paid renewal, plan/seat changes, proration, cancellation, payment failure grace periods, discounts, invalid input, and idempotency.

You may add tests and supporting files. Useful verification includes replayed events, trial boundaries, upgrade proration with rounding, downgrades that do not credit, cancellation modes, and payment failure status transitions.

Before finishing, run the relevant tests and report the command results.
