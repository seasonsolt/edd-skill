# Skill vs No-Skill Benchmark

This benchmark measures whether `$eval-driven-ai-tdd` improves an AI coding agent's behavior on paired coding tasks.

## Conditions

Run each task twice from clean copies:

- Baseline: do not mention or enable the skill.
- Skill: explicitly ask the agent to use `$eval-driven-ai-tdd`.

Use the same model, approval settings, time budget, and starter files for both runs.

## Suite Setup

Use this for the stronger multi-task benchmark:

```bash
python3 benchmarks/skill-vs-no-skill/prepare_suite.py --force
```

This creates paired runs under:

- `runs/skill-vs-no-skill-suite/quote-engine/`
- `runs/skill-vs-no-skill-suite/feature-flags/`
- `runs/skill-vs-no-skill-suite/tool-call-planner/`

Each task has:

- `baseline/`
- `with-skill/`

Each run directory contains its own `PROMPT.md`. Open a fresh agent thread for each run and give it only that run directory plus its prompt.

## Single-Task Setup

Use this only for quick smoke testing of the original quote-engine task:

```bash
python3 benchmarks/skill-vs-no-skill/prepare_runs.py --force
```

This creates:

- `runs/skill-vs-no-skill/baseline`
- `runs/skill-vs-no-skill/with-skill`

Each run directory contains a `PROMPT.md`. Open a fresh agent thread for each copy and give it that directory plus its prompt.

The skill condition prepends:

```text
Use $eval-driven-ai-tdd.
```

Do not show `hidden_tests/` or `score_candidate.py` to the agent during the run.

## Suite Scoring

After every suite run is complete:

```bash
python3 benchmarks/skill-vs-no-skill/score_suite.py
```

This writes `runs/skill-vs-no-skill-suite/suite-comparison.json`.

For repeated trials, prepare each trial under a separate directory:

```bash
python3 benchmarks/skill-vs-no-skill/prepare_trials.py --trial-count 5 --force --clean-root
```

After agents complete each trial, aggregate them:

```bash
python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials --expected-trial-count 5
```

This writes `runs/skill-vs-no-skill-trials/trials-summary.json`.

Five trials across the current three task families require 30 independent agent runs:

```text
5 trials * 3 task families * 2 conditions = 30 runs
```

## Benchmark Integrity Check

Before trusting a benchmark revision, run:

```bash
python3 benchmarks/skill-vs-no-skill/verify_benchmark.py
```

This checks two properties for every task family:

- Starter task scores `0` and fails public/hidden tests.
- A reference implementation passes public/hidden tests.

## Single-Task Scoring

After the quote-engine smoke run is complete:


```bash
python3 benchmarks/skill-vs-no-skill/score_pair.py
```

The score has two parts:

- Functional score: public tests plus private contract cases.
- Process score: evidence of eval-first behavior, tests, red/green logs, and report quality.

The expected signal is not that the skill always wins every hidden test. The expected signal is that the skill run leaves better regression coverage and more reproducible evidence, while at least matching functional quality.

## Interpreting Results

Treat one pair as a smoke test, not proof. A credible claim needs:

- At least two task families.
- At least 5 paired runs per task family for a stable claim.
- Identical model, approval settings, and time budget across paired runs.
- Passing benchmark integrity checks.
- Median total score, functional score, process score, hidden-test pass rate, and worst-case score.
- Preserved raw artifacts: prompts, final files, score JSON, red/green logs, and reports.

Useful follow-up measurements:

- Track median total score, hidden-test pass rate, process score, and added regression count.
- Inspect whether process artifacts catch failures that hidden tests also catch.
- Tighten the skill only when the failure repeats across multiple runs.
