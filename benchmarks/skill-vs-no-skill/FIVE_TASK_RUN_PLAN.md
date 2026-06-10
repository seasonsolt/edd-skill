# Five-Task Benchmark Run Plan

This plan is for the current suite:

- `quote-engine`
- `feature-flags`
- `tool-call-planner`
- `tool-call-planner-v2`
- `evidence-answerer`

The goal is not to prove that EDD Skill works. The goal is to produce a
credible answer.

## Gate 0: Prepare And Verify

Commands:

```bash
python3 benchmarks/skill-vs-no-skill/verify_benchmark.py
python3 benchmarks/skill-vs-no-skill/prepare_trials.py --trials-root runs/skill-vs-no-skill-trials-5task --clean-root --trial-count 5
python3 benchmarks/skill-vs-no-skill/trial_status.py --trials-root runs/skill-vs-no-skill-trials-5task --expected-trial-count 5
```

Expected result:

- `verify_benchmark.py` passes.
- Trial root contains 5 trials.
- Status reports 50 expected runs.
- Status reports 50 `prepared` runs and 0 score JSON runs.

Do not run `score_trials.py` before agents have completed their assigned run
directories.

## Run 1: Five-Task Paired Trial

Run one isolated agent for each prepared run directory:

```text
5 trials * 5 task families * 2 conditions = 50 agent runs
```

Rules:

- Give each agent only its own run directory and `PROMPT.md`.
- Do not expose `hidden_tests/`, scorer scripts, sibling run directories, prior results, or this plan.
- Use identical model, approval settings, and time budget for baseline and with-skill conditions.
- Do not manually repair run directories after the agent finishes.
- Preserve all artifacts left by the agent.

Progress command:

```bash
python3 benchmarks/skill-vs-no-skill/trial_status.py --trials-root runs/skill-vs-no-skill-trials-5task --expected-trial-count 5
```

Proceed to scoring only when every run is `completed_unscored`. If a run is
still `prepared`, it has not been touched by an agent. If a run is
`scored_unmodified`, discard and rerun that trial root because scoring happened
before agent execution.

## Evaluation 1

Commands:

```bash
python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials-5task --expected-trial-count 5
python3 benchmarks/skill-vs-no-skill/assess_trials.py --trials-root runs/skill-vs-no-skill-trials-5task --json-output runs/skill-vs-no-skill-trials-5task/assessment.json
python3 benchmarks/skill-vs-no-skill/analyze_trials.py --trials-root runs/skill-vs-no-skill-trials-5task --json-output runs/skill-vs-no-skill-trials-5task/diagnostics.json
python3 benchmarks/skill-vs-no-skill/trial_status.py --trials-root runs/skill-vs-no-skill-trials-5task --expected-trial-count 5 --strict-complete
```

Report:

- Assessment verdict.
- Hidden pass delta.
- Median functional delta.
- Median process delta.
- Baseline artifact leakage.
- `tool-call-planner-v2` per-condition hidden pass rate.

## Decision Gate

Use the fixed assessment verdict first.

- `functional_and_process_supported`: run a second confirmation trial set with the same suite.
- `functional_supported`: run a second confirmation trial set and inspect process gaps.
- `process_only_supported`: do not claim functional uplift; rerun only if process reproducibility is the claim.
- `not_supported`: do failure review before changing the skill.
- `functional_regression`: stop and analyze regressions before any rerun.
- `insufficient_evidence`: fix trial volume or task discovery, then rerun.

## Run 1 Result

- Date: 2026-06-10
- Runs: 50 / 50 completed and scored.
- Assessment verdict: `process_only_supported`.
- Hidden pass delta: 0. Baseline and with-skill both passed 20 / 25 hidden runs.
- Median functional delta: 0.
- Median process delta: +25.8.
- Baseline artifact leakage: 0 / 25 complete evidence runs.
- With-skill complete evidence: 25 / 25 runs.
- `tool-call-planner-v2` hidden pass rate: baseline 5 / 5, with-skill 5 / 5.

Interpretation:

- The run supports a process/reproducibility claim.
- The run does not support a hidden functional correctness claim.
- `tool-call-planner-v2` validates the failure-to-visible-contract loop, but not
  a skill-specific functional lift because both conditions solved it.
- A second run should not repeat the same suite blindly. Either confirm the
  process-only claim with an independent root, or change exactly one variable
  before attempting a functional-uplift rerun.

## Run 2: Confirmation Or Failure-Focused Rerun

If Run 1 supports a claim, prepare an independent confirmation root:

```bash
python3 benchmarks/skill-vs-no-skill/prepare_trials.py --trials-root runs/skill-vs-no-skill-trials-5task-confirm --clean-root --trial-count 5
```

Then repeat Run 1 and Evaluation 1 against the `-confirm` root.

If Run 1 is `not_supported` or regresses, do not immediately alter thresholds.
First write a failure review and decide whether the next rerun should change:

- task contract,
- process scoring,
- skill instructions,
- model/settings,
- or nothing.

Only one variable should change between Run 1 and a failure-focused rerun.
