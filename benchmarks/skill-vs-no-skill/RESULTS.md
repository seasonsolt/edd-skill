# Skill vs No-Skill Results

Record each A/B run here after scoring.

## Five-Trial Paired Experiment

- Date: 2026-06-09
- Model: inherited current Codex model for all worker agents
- Task families: `quote-engine`, `feature-flags`
- Trials: 5 paired trials, 10 baseline task runs, 10 with-skill task runs
- Command: `python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials --expected-trial-count 5`

### Aggregate Scores

| Metric | Baseline | With EDD Skill | Delta |
| --- | ---: | ---: | ---: |
| Mean total score | 68.0 | 99.5 | +31.5 |
| Median total score | 65.0 | 99.5 | +33.5 |
| Worst trial mean score | 65.0 | 98.5 | +33.5 by condition |
| Worst paired trial delta | - | - | +27.0 |
| Functional score | 65 / 65 | 65 / 65 | 0 |
| Process score range | 0-15 / 35 | 32-35 / 35 | +31.5 mean |
| Process median delta | mixed | stable high | +33.5 |
| Hidden pass rate | 10 / 10 | 10 / 10 | 0 |

### Trial Deltas

| Trial | Baseline mean | With-skill mean | Score delta | Process delta | Functional delta | Hidden pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| trial-001 | 65.0 | 100.0 | +35.0 | +35.0 | 0 | both 100% |
| trial-002 | 65.0 | 99.5 | +34.5 | +34.5 | 0 | both 100% |
| trial-003 | 72.5 | 99.5 | +27.0 | +27.0 | 0 | both 100% |
| trial-004 | 72.5 | 100.0 | +27.5 | +27.5 | 0 | both 100% |
| trial-005 | 65.0 | 98.5 | +33.5 | +33.5 | 0 | both 100% |

### Interpretation

- The median delta is stable across 5 trials: +33.5 total score, with worst trial delta +27.0.
- The improvement is entirely process evidence: eval contracts, red/green logs, regression tests, reports, and reproducibility artifacts.
- The benchmark does not show functional correctness uplift in this run. Baseline and with-skill both passed every public and hidden test.
- This is still useful evidence: EDD Skill changes the agent coding loop in a measurable way without depending on transcript claims.
- The next stronger benchmark should run the newly added `tool-call-planner` task family, where hidden tests can expose policy and planning misses.

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
- Task families: `quote-engine`, `feature-flags`, `tool-call-planner`
- Command: `python3 benchmarks/skill-vs-no-skill/verify_benchmark.py`
- Result: passed
- Starter score: 0 for all three task families.
- Reference implementation: public and hidden tests pass for all three task families.

## Credibility Status

- Current evidence: 5 paired trials across `quote-engine` and `feature-flags`.
- Benchmark coverage: three task families with public tests, hidden tests, reference implementations, and an integrity check.
- Claim strength: credible for process/auditability improvement, not credible yet for functional correctness uplift.
- Next threshold: run 5 paired trials across all three task families and report whether hidden-pass-rate delta changes.
