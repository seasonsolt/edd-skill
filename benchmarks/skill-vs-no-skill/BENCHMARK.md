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
- `runs/skill-vs-no-skill-suite/tool-call-planner-v2/`
- `runs/skill-vs-no-skill-suite/evidence-answerer/`

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
python3 benchmarks/skill-vs-no-skill/prepare_trials.py --trials-root runs/skill-vs-no-skill-trials-5task --trial-count 5 --clean-root
```

Before or during agent execution, inspect run status:

```bash
python3 benchmarks/skill-vs-no-skill/trial_status.py --trials-root runs/skill-vs-no-skill-trials-5task --expected-trial-count 5
```

Detailed execution rules are in
[`FIVE_TASK_RUN_PLAN.md`](FIVE_TASK_RUN_PLAN.md).

After agents complete each trial, aggregate them:

```bash
python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials-5task --expected-trial-count 5
```

This writes `runs/skill-vs-no-skill-trials-5task/trials-summary.json`.

Five trials across the current five task families require 50 independent agent runs:

```text
5 trials * 5 task families * 2 conditions = 50 runs
```

After scoring, run the fixed assessment gate:

```bash
python3 benchmarks/skill-vs-no-skill/assess_trials.py --trials-root runs/skill-vs-no-skill-trials-5task
```

The assessment can return:

- `functional_and_process_supported`: functional hidden/eval signal and process signal both improved.
- `functional_supported`: functional signal improved without enough process signal.
- `process_only_supported`: process/auditability improved, but hidden functional signal did not.
- `functional_regression`: with-skill regressed hidden or functional results.
- `not_supported`: enough benchmark volume, but thresholds were not met.
- `insufficient_evidence`: not enough trials or task families.

## Benchmark Integrity Check

Before trusting a benchmark revision, run:

```bash
python3 benchmarks/skill-vs-no-skill/verify_benchmark.py
```

This checks two properties for every task family:

- Starter task scores `0` and fails public/hidden tests.
- A reference implementation passes public/hidden tests.

The current suite includes a v2 task, `tool-call-planner-v2`, that converts a
previous hidden miss into an agent-visible public contract. Historical
four-task results remain comparable only to the pre-v2 suite.

## Single-Task Scoring

After the quote-engine smoke run is complete:


```bash
python3 benchmarks/skill-vs-no-skill/score_pair.py
```

The score has two parts:

- Functional score: public tests plus private contract cases.
- Process score: evidence of eval-first behavior, tests, red/green logs, and report quality.

Do not assume the skill will help. A valid experiment may show functional improvement, process-only improvement, no measurable effect, functional regression, or insufficient evidence. The benchmark loop exists to separate those outcomes.

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
