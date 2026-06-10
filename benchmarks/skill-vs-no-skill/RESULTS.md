# Skill vs No-Skill Results

Record each A/B run here after scoring.

## Five-Trial Paired Experiment: Four-Task Suite

- Date: 2026-06-10
- Model: inherited current Codex model for all worker agents
- Task families: `quote-engine`, `feature-flags`, `tool-call-planner`, `evidence-answerer`
- Trials: 5 paired trials, 20 baseline task runs, 20 with-skill task runs
- Score command: `python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials-4task --expected-trial-count 5`
- Assessment command: `python3 benchmarks/skill-vs-no-skill/assess_trials.py --trials-root runs/skill-vs-no-skill-trials-4task`
- Assessment verdict: `not_supported`

### Aggregate Scores

| Metric | Baseline | With EDD Skill | Delta |
| --- | ---: | ---: | ---: |
| Mean total score | 67.45 | 86.45 | +19.0 |
| Median total score | 66.5 | 86.5 | +19.75 |
| Worst trial mean score | 66.25 | 86.0 | +19.75 by condition |
| Mean functional delta | - | - | 0 |
| Median functional delta | - | - | 0 |
| Mean process delta | - | - | +19.0 |
| Median process delta | - | - | +19.75 |
| Hidden pass rate | 15 / 20 | 15 / 20 | 0 |
| `tool-call-planner` hidden pass rate | 0 / 5 | 0 / 5 | 0 |

### Trial Deltas

| Trial | Baseline mean | With-skill mean | Score delta | Process delta | Functional delta | Hidden pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| trial-001 | 66.25 | 86.0 | +19.75 | +19.75 | 0 | both 75% |
| trial-002 | 66.5 | 86.5 | +20.0 | +20.0 | 0 | both 75% |
| trial-003 | 67.0 | 86.75 | +19.75 | +19.75 | 0 | both 75% |
| trial-004 | 66.5 | 86.75 | +20.25 | +20.25 | 0 | both 75% |
| trial-005 | 71.0 | 86.25 | +15.25 | +15.25 | 0 | both 75% |

### Per-Task Pattern

| Task | Baseline hidden | With-skill hidden | Mean score delta | Mean process delta | Functional delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `quote-engine` | 5 / 5 | 5 / 5 | +20.6 | +20.6 | 0 |
| `feature-flags` | 5 / 5 | 5 / 5 | +15.6 | +15.6 | 0 |
| `tool-call-planner` | 0 / 5 | 0 / 5 | +20.2 | +20.2 | 0 |
| `evidence-answerer` | 5 / 5 | 5 / 5 | +19.6 | +19.6 | 0 |

### Assessment Gate

`assess_trials.py` default criteria:

- `min_trials`: 5
- `min_task_families`: 4
- `min_process_delta`: 20

Observed:

- `credible_volume`: true
- `median_functional_delta`: 0
- `hidden_pass_delta`: 0
- `median_process_delta`: +19.75
- `process_win_rate`: 100%
- `functional_effect`: false
- `process_effect`: false

Verdict: `not_supported`.

### Interpretation

- This is a useful negative result. The four-task suite reached the planned benchmark volume and did not support an effectiveness claim for EDD Skill.
- There is still a numeric process-score lift, but it misses the default `+20` process gate by 0.25 points.
- The functional delta remains 0. Baseline and with-skill both passed all `quote-engine`, `feature-flags`, and `evidence-answerer` hidden runs, and both failed every `tool-call-planner` hidden run.
- Trial 005 shows an important confound: a baseline `feature-flags` run produced EDD-like artifacts and scored full process credit. That suggests the skill may not be uniquely responsible for process discipline under this prompt/model setup.
- The next loop should analyze why `tool-call-planner` remains hard and why baseline can already produce high process evidence, instead of lowering thresholds after seeing the result.

### Failure Review Diagnostic

Command:

```bash
python3 benchmarks/skill-vs-no-skill/analyze_trials.py --trials-root runs/skill-vs-no-skill-trials-4task --json-output runs/skill-vs-no-skill-trials-4task/diagnostics.json
```

Diagnostic output:

| Diagnostic | Baseline | With EDD Skill |
| --- | ---: | ---: |
| Mean process score | 14.95 / 35 | 33.95 / 35 |
| Complete evidence runs | 1 / 20 | 20 / 20 |
| High-process runs | 1 / 20 | 20 / 20 |
| Hidden passed | 15 / 20 | 15 / 20 |

Baseline artifact leakage:

- `trial-005` / `feature-flags` baseline scored 35 / 35 process and left `EDD_REPORT.md`, `evals/red.log`, and `evals/green.log`.

Hidden failure pattern:

- `tool-call-planner` is public-green/hidden-red in all 10 runs.
- The failure category is stable across both conditions: `no_matching_tool_clarification_boundary`.

Interpretation:

- The with-skill process lift is stable and file-backed, but hidden correctness did not improve.
- The process claim is also weakened by one complete baseline EDD-like artifact set.
- The next benchmark loop should create a visible `tool-call-planner` v2/regression around this behavior class after scoring, then rerun paired trials.

## Five-Trial Paired Experiment: Three-Task Suite

- Date: 2026-06-10
- Model: inherited current Codex model for all worker agents
- Task families: `quote-engine`, `feature-flags`, `tool-call-planner`
- Trials: 5 paired trials, 15 baseline task runs, 15 with-skill task runs
- Command: `python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials-3task --expected-trial-count 5`

### Aggregate Scores

| Metric | Baseline | With EDD Skill | Delta |
| --- | ---: | ---: | ---: |
| Mean total score | 53.8 | 82.4 | +28.6 |
| Median total score | 52.67 | 82.33 | +29.66 |
| Worst trial mean score | 52.67 | 81.67 | +29.0 by condition |
| Mean functional delta | - | - | 0 |
| Median functional delta | - | - | 0 |
| Mean process delta | - | - | +28.6 |
| Median process delta | - | - | +29.67 |
| Hidden pass rate | 10 / 15 | 10 / 15 | 0 |
| `tool-call-planner` hidden pass rate | 0 / 5 | 0 / 5 | 0 |

### Trial Deltas

| Trial | Baseline mean | With-skill mean | Score delta | Process delta | Functional delta | Hidden pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| trial-001 | 52.67 | 82.67 | +30.0 | +30.0 | 0 | both 66.67% |
| trial-002 | 58.33 | 82.33 | +24.0 | +24.0 | 0 | both 66.67% |
| trial-003 | 52.67 | 81.67 | +29.0 | +29.0 | 0 | both 66.67% |
| trial-004 | 52.67 | 82.33 | +29.66 | +29.67 | 0 | both 66.67% |
| trial-005 | 52.67 | 83.0 | +30.33 | +30.33 | 0 | both 66.67% |

### Interpretation

- The with-skill condition still shows a stable process/auditability lift: median total delta +29.66.
- The functional delta remains 0. Baseline and with-skill both passed every `quote-engine` and `feature-flags` hidden run, and both failed every `tool-call-planner` hidden run.
- `tool-call-planner` did its job as a harder benchmark: it exposed planning/policy misses that public tests did not catch.
- EDD Skill did not, by itself, make agents infer those hidden planning boundaries. The next loop should convert scored hidden misses into visible regressions or a v2 task, then rerun paired trials.

## Five-Trial Paired Experiment: Two-Task Suite

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

- Date: 2026-06-10
- Task families: `quote-engine`, `feature-flags`, `tool-call-planner`, `evidence-answerer`
- Command: `python3 benchmarks/skill-vs-no-skill/verify_benchmark.py`
- Result: passed
- Starter score: 0 for all four task families.
- Reference implementation: public and hidden tests pass for all four task families.

## Credibility Status

- Current evidence: 5 paired trials across `quote-engine`, `feature-flags`, `tool-call-planner`, and `evidence-answerer`.
- Benchmark coverage: four task families with public tests, hidden tests, reference implementations, and an integrity check.
- Claim strength: `not_supported` under the current fixed assessment gate. The skill has not shown hidden functional uplift, and process uplift did not meet the default threshold.
- Next threshold: convert `tool-call-planner` misses into visible regression/task v2 and explain baseline EDD-like artifact production before rerunning.
