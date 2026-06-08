# Skill vs No-Skill Results

Record each A/B run here after scoring.

## Run 1

- Date: 2026-06-09
- Model: inherited current Codex model for both worker agents
- Baseline score: 79 / 100
- With-skill score: 99 / 100
- Delta: +20
- Functional delta: 0
- Process delta: +20

### Observations

- Both runs passed public and hidden functional tests: 65 / 65.
- Baseline added 4 regression tests and covered boundary, minimum, discount, rounding, and invalid-input cases, but left no red/green logs, eval directory, or report.
- With-skill added the same amount of regression coverage and also left `AI_TDD_REPORT.md`, `evals/red.log`, and `evals/green.log`.
- In this run, `$eval-driven-ai-tdd` did not improve final functional correctness because the baseline agent solved the task fully. It did improve reproducibility and auditability.
- The result supports the skill's process value, but one run is not enough to claim a stable quality advantage.

### Skill Changes To Consider

- Ask agents to create a separate regression test file, such as `tests/test_regressions.py`, instead of modifying only starter public tests. This makes process evidence easier to score and inspect.
- Add stronger language that red logs should capture newly added failing regression tests, not only the existing `NotImplementedError` state.
- Add multi-run guidance: run at least 5 pairs and compare median score, hidden pass rate, and process score.

## Benchmark Integrity

- Date: 2026-06-09
- Task families: `quote-engine`, `feature-flags`
- Command: `python3 benchmarks/skill-vs-no-skill/verify_benchmark.py`
- Result: passed
- Starter score: 0 for both task families.
- Reference implementation: public and hidden tests pass for both task families.

## Credibility Status

- Current evidence: one completed pair for `quote-engine`, zero completed pairs for `feature-flags`.
- Benchmark coverage: two task families are now available.
- Claim strength: enough for workflow smoke testing, not enough for a broad quality claim.
- Next threshold: run at least 5 paired trials per task family and report medians, hidden-pass rates, process deltas, and worst-case scores.
