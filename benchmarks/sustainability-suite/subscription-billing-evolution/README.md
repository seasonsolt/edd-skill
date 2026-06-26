# Subscription Billing Evolution

This is the second task family for the EDD Sustainability Suite.

It tests whether an agent turns billing rules into executable verification before claiming implementation success. The task is business-rule heavy: money, proration, idempotency, trials, cancellation, payment-failure grace periods, discounts, and state transitions all create realistic edge cases.

## Scenario

Build a pure Python billing engine that prices one subscription event at a time.

The calculator receives:

- subscription state;
- one billing event;
- fixed monthly plan prices in cents;
- event ids for idempotency.

It returns the amount to charge now plus the next subscription state.

`score_seeded_bugs.py` runs a candidate's tests against scorer-only near-correct implementations with one intentional mutation each. A seed is counted as killed only when the failure output mentions that seed's mutation surface.

The useful question is:

```text
Would the tests/evals created by the agent catch plausible billing bugs?
```

This complements `agent-policy-evolution`: one task is policy/agent-tooling flavored; this one is deterministic business logic.
