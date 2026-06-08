# Eval-First Contract

Use this contract before implementation. In EDD, the evaluation contract is the project's first engineering artifact, not a QA step after code exists.

## Contract Shape

Define these before implementation:

- Behavior: What must be true from the user's point of view.
- Inputs: Valid inputs, invalid inputs, and boundary values.
- Outputs: Exact return shape, side effects, files, or UI state.
- Invariants: Properties that should always hold.
- Regressions: Past or likely failures that must not return.
- Verification command: The smallest command that proves the behavior.
- Hidden scoring layer: What the agent must not see during implementation.

## Good Eval Cases

Good cases are small, named, and targeted. Include:

- One ordinary success case.
- One boundary case.
- One invalid input or failure-mode case.
- One regression case for each bug found during the loop.
- One integration case if behavior crosses a module boundary.

Avoid cases that only mirror the implementation. Tests should encode the contract, not the algorithm.

Put new regression coverage in a clearly named file such as `tests/test_regressions.py` unless the project already has a better convention. This makes it easier to separate agent-added coverage from starter or legacy tests.

Hidden benchmark failures should not stay hidden forever. After scoring, convert each useful hidden failure into an agent-visible regression before the next loop.

## Report Template

Use this structure for `EDD_REPORT.md`:

```md
# EDD Report

## Contract
- ...

## Red
- Command: `...`
- Result: failed as expected because ...

## Green
- Command: `...`
- Result: passed

## Regressions Added
- ...

## Gaps
- ...
```

## Scoring Skill Impact

Score two dimensions separately:

- Functional quality: hidden tests, benchmark cases, invariants, runtime behavior.
- Process quality: tests/evals written before implementation, red/green evidence, regression cases, final report.

Do not give process credit for claims without artifacts.
