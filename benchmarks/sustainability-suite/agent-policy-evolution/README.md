# Agent Policy Evolution

This task is the first candidate for the EDD Sustainability Suite.

It reuses the spirit of `tool-call-planner`, but changes the benchmark target. Instead of asking only whether the final implementation passes hidden tests, this task asks whether the agent creates verification logic that would catch realistic policy bugs.

## Scenario

Build a planner that decides whether an AI assistant should call a tool, ask for clarification, request approval, or refuse.

The planner receives:

- a user request with an `intent`, optional `args`, and optional free-form `text`;
- available tool metadata;
- policy constraints;
- session context.

The planner must treat structured fields and policy as authoritative. Free-form text must never override the declared intent, policy, or tool metadata.

## Evolution Rounds

### Round 1: Basic Selection

Select a matching tool by capability and merge known args with request args.

### Round 2: Policy And Approval

Add blocked capabilities, blocked tools, destructive-tool handling, risk ordering, and approval requirements.

### Round 3: Safety Regressions

Add regression coverage for:

- no matching tool;
- prompt-injection text trying to override policy;
- policy checks occurring before tool execution;
- approval being required until the exact tool is approved.

## Prototype Scoring

`score_seeded_bugs.py` runs a candidate's tests against scorer-only flawed implementations. The seeds are near-correct reference-shaped implementations with one intended mutation, and the scorer only counts a seed as killed when the failure output mentions that seed's mutation surface. This avoids false credit when a candidate test suite rejects a seeded implementation for an unrelated behavior difference.

The useful question is:

```text
Would the tests/evals created by the agent catch plausible policy bugs?
```

This is intentionally different from counting test files or checking for an EDD report.
