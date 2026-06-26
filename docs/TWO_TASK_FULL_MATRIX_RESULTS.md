# Two-Task Sustainability Full Matrix Results

This document records the first full two-task sustainability benchmark run after adding `subscription-billing-evolution`.

## Run Shape

```text
5 trials * 2 task families * 2 model tiers * 2 conditions = 40 runs
```

Run root:

```text
/tmp/edd-two-task-full-matrix
```

Timeline:

```text
prepared:      2026-06-26T06:43:34-07:00
Codex started: 2026-06-26T06:43:34-07:00
scoring:       2026-06-26T09:42:38-07:00
summary:       2026-06-26T09:42:48-07:00
```

Status:

```json
{
  "by_status": {"scored": 40},
  "run_count": 40
}
```

All runs were executed by `run_codex_matrix.py` and scored by `score_model_matrix.py`.

## Headline Summary

| Model tier | Condition | Hidden passed | Mean functional | Mean seeded-bug score | Mean killed seeds | Mean process | Runs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| economical | baseline | 1 / 10 | 20.0 / 65 | 19.25 / 30 | 3.3 | 7.9 / 35 | 10 |
| economical | with EDD | 0 / 10 | 15.0 / 65 | 19.5 / 30 | 3.4 | 23.9 / 35 | 10 |
| sota | baseline | 4 / 10 | 35.0 / 65 | 20.5 / 30 | 3.5 | 9.7 / 35 | 10 |
| sota | with EDD | 1 / 10 | 20.0 / 65 | 20.0 / 30 | 3.5 | 34.5 / 35 | 10 |

Seeded-bug deltas:

```json
{
  "economical_skill_delta": 0.25,
  "sota_skill_delta": -0.5,
  "skill_leverage_gap": 0.75
}
```

## Task-Family Breakdown

| Task | Model tier | Condition | Hidden passed | Public passed | Mean functional | Mean seeded-bug score | Mean killed seeds | Mean process | Mean total |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agent-policy-evolution | economical | baseline | 0 / 5 | 5 / 5 | 15.0 / 65 | 16.5 / 30 | 2.2 | 13.2 / 35 | 28.2 / 100 |
| agent-policy-evolution | economical | with EDD | 0 / 5 | 5 / 5 | 15.0 / 65 | 15.0 / 30 | 2.0 | 22.2 / 35 | 37.2 / 100 |
| agent-policy-evolution | sota | baseline | 0 / 5 | 5 / 5 | 15.0 / 65 | 18.0 / 30 | 2.4 | 13.4 / 35 | 28.4 / 100 |
| agent-policy-evolution | sota | with EDD | 0 / 5 | 5 / 5 | 15.0 / 65 | 15.0 / 30 | 2.0 | 34.2 / 35 | 49.2 / 100 |
| subscription-billing-evolution | economical | baseline | 1 / 5 | 5 / 5 | 25.0 / 65 | 22.0 / 30 | 4.4 | 2.6 / 35 | 27.6 / 100 |
| subscription-billing-evolution | economical | with EDD | 0 / 5 | 5 / 5 | 15.0 / 65 | 24.0 / 30 | 4.8 | 25.6 / 35 | 40.6 / 100 |
| subscription-billing-evolution | sota | baseline | 4 / 5 | 5 / 5 | 55.0 / 65 | 23.0 / 30 | 4.6 | 6.0 / 35 | 61.0 / 100 |
| subscription-billing-evolution | sota | with EDD | 1 / 5 | 5 / 5 | 25.0 / 65 | 25.0 / 30 | 5.0 | 34.8 / 35 | 59.8 / 100 |

## Per-Task Deltas

| Task | Model tier | Functional delta | Hidden-pass delta | Seeded-bug delta | Process delta |
| --- | --- | ---: | ---: | ---: | ---: |
| agent-policy-evolution | economical | +0.0 | +0 | -1.5 | +9.0 |
| agent-policy-evolution | sota | +0.0 | +0 | -3.0 | +20.8 |
| subscription-billing-evolution | economical | -10.0 | -1 | +2.0 | +23.0 |
| subscription-billing-evolution | sota | -30.0 | -3 | +2.0 | +28.8 |

## Main Interpretation

This run strengthens one claim and weakens another.

Supported:

- EDD strongly increases process evidence. Process score improved in every task/model tier group:
  - agent-policy economical: `+9.0`
  - agent-policy sota: `+20.8`
  - subscription-billing economical: `+23.0`
  - subscription-billing sota: `+28.8`
- Billing seeded-bug coverage improved with EDD in both tiers:
  - economical: `+2.0 / 30`
  - sota: `+2.0 / 30`

Not supported:

- Broad hidden functional correctness uplift. Hidden pass counts were worse with EDD in billing and unchanged at zero in agent-policy.
- Strong cross-task seeded-bug uplift. The aggregate seeded-bug deltas were small: `+0.25` economical and `-0.5` SOTA.
- The hypothesis that EDD reliably helps the economical tier in this setup. The economical seeded-bug delta was only `+0.25 / 30`, and hidden passes moved from `1/10` to `0/10`.

## Failure Patterns

Hidden functional failures concentrated in a few places:

| Task | Failure pattern | Count |
| --- | --- | ---: |
| agent-policy-evolution | `test_no_matching_tool_clarifies` | 20 |
| agent-policy-evolution | `test_destructive_tool_requires_policy_allow_even_if_text_demands_it` | 3 |
| subscription-billing-evolution | `test_cancel_modes_and_canceled_renewal_do_not_charge` | 14 |

Seeded bugs that often survived:

| Task | Seed | Notes |
| --- | --- | --- |
| agent-policy-evolution | `missing_tool_reports_empty_missing` | survived all groups; matches the hidden failure above |
| agent-policy-evolution | `text_can_override_intent` | survived frequently, especially SOTA with EDD |
| subscription-billing-evolution | `upgrade_rounding_floor` | survived frequently, including all SOTA with EDD runs |
| subscription-billing-evolution | `trial_end_not_billed` | survived baseline often; improved with EDD |

## Runner Notes

The hardened Codex runner discarded direct workspace writes from every run, then applied only the final JSON-declared files through the path validator. Discarded paths included Codex/OMX bookkeeping under `.omx/`, Python `__pycache__`, and direct edits to implementation/tests. This is expected after runner hardening and means the scored artifacts are the JSON-declared outputs, not arbitrary direct filesystem changes.

## Evidence Boundary

This benchmark result should be described as:

```text
EDD improves auditability/process evidence very consistently. It does not yet demonstrate reliable hidden functional correctness improvement or broad seeded-bug improvement across task families and model tiers.
```

A careful product claim remains:

```text
EDD makes agent work easier to audit and often improves verification artifacts. It is not a substitute for stronger hidden specifications, scorer feedback, or task-specific correctness checks.
```

## Recommended Next Steps

1. Fix the recurring task misses before running another expensive full matrix:
   - agent-policy: make no-matching-tool clarification explicit in the prompt/public tests.
   - subscription-billing: clarify cancellation semantics and add a visible public smoke test.
2. Decide whether those prompt/test changes create a new benchmark version; do not compare new scores directly against this run unless versioned.
3. Add cost/elapsed/model-output metadata per run so process gains can be weighed against runtime and spend.
4. Consider reporting per-task results as primary and model-tier aggregates as secondary; aggregation hides important behavior differences.
