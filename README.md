# EDD Skill

EDD Skill is a Codex skill for AI coding work. It pushes the agent to define how the result will be checked before it starts changing the implementation.

The problem it tries to solve: AI can write code quickly, but long AI coding sessions drift unless the expected behavior is testable. Without a verification target, you keep getting plausible code, fragile fixes, and bugs that come back in the next turn.

EDD changes the loop:

```text
expected behavior -> tests/evals -> implementation -> evidence -> regressions
```

## Why It Helps

The evidence so far supports a practical claim: EDD makes agents leave better verification evidence. It has not yet proven broad hidden functional improvement.

### Five-task benchmark

This run compared baseline agents with agents using EDD Skill:

```text
5 trials * 5 task families * 2 conditions = 50 agent runs
```

| Metric | Baseline | With EDD Skill | Delta |
| --- | ---: | ---: | ---: |
| Mean total score | 62.84 / 100 | 88.72 / 100 | +25.88 |
| Median process delta | - | - | +25.8 |
| Hidden pass rate | 20 / 25 | 20 / 25 | 0 |
| Verdict | - | - | `process_only_supported` |

With EDD, agents left complete reports, red/green logs, and regression evidence in 25 / 25 runs. Hidden functional correctness did not improve in this benchmark. See [RESULTS.md](benchmarks/skill-vs-no-skill/RESULTS.md).

### Two-model pilot

This pilot asked whether agent-written tests catch seeded bugs:

```text
5 trials * 1 task family * 2 model tiers * 2 conditions = 20 agent runs
```

| Group | Hidden passed | Seeded-bug score | Process score |
| --- | ---: | ---: | ---: |
| `gpt-5.5` baseline | 0 / 5 | 0.0 / 30 | 0.0 / 35 |
| `gpt-5.5` with EDD | 0 / 5 | 30.0 / 30 | 33.8 / 35 |
| `gpt-5.4-mini` baseline | 0 / 5 | 6.0 / 30 | 3.0 / 35 |
| `gpt-5.4-mini` with EDD | 0 / 5 | 0.0 / 30 | 1.0 / 35 |

On `gpt-5.5`, EDD made the agent write verification that killed every seeded bug. On `gpt-5.4-mini`, this setup did not help. No group passed the original hidden functional tests.

## Current Evidence Boundary

Supported by the current benchmark:

- Better process artifacts and auditability.
- More consistent red/green logs, eval directories, reports, and regression evidence.

Not yet proven:

- Broad hidden functional correctness improvement.
- Reliable uplift for economical/smaller model tiers.

Always read total-score gains together with functional score and hidden pass rate.

## Quickstart

Run the benchmark integrity check:

```bash
python3 benchmarks/skill-vs-no-skill/verify_benchmark.py
```

Prepare a one-trial smoke run:

```bash
python3 benchmarks/skill-vs-no-skill/prepare_trials.py \
  --trials-root runs/demo-trials \
  --trial-count 1 \
  --clean-root
python3 benchmarks/skill-vs-no-skill/trial_status.py \
  --trials-root runs/demo-trials \
  --expected-trial-count 1
```

Give each agent only its own generated run directory and `PROMPT.md`. Do not expose hidden tests, scorer scripts, sibling runs, or prior results. Prepared run directories include `RUN_METADATA.json`; scoring updates that file with score/status fields.

## Use It

1. Install or reference the skill in Codex:

   ```text
   Use $eval-driven-ai-tdd.
   ```

   The installable skill name is currently `$eval-driven-ai-tdd`; `EDD Skill` is the project/product name.

2. Ask the agent to start from the expected result:

   ```text
   Before changing implementation code, define the tests or evals that prove the behavior.
   ```

3. Keep the evidence:

   ```text
   EDD_REPORT.md
   evals/red.log
   evals/green.log
   tests/test_regressions.py
   ```

The useful habit is simple: make the agent prove what done means before it claims the code is done.

## Repo Pointers

- Skill: [.agents/skills/eval-driven-ai-tdd/SKILL.md](.agents/skills/eval-driven-ai-tdd/SKILL.md)
- Main benchmark results: [benchmarks/skill-vs-no-skill/RESULTS.md](benchmarks/skill-vs-no-skill/RESULTS.md)
- Benchmark case review: [docs/EDD_BENCHMARK_CASE_REVIEW.md](docs/EDD_BENCHMARK_CASE_REVIEW.md)
- Benchmark threat model: [docs/BENCHMARK_THREATS.md](docs/BENCHMARK_THREATS.md)
- Sustainability pilot: [benchmarks/sustainability-suite/](benchmarks/sustainability-suite/)
- Two-task live smoke: [docs/TWO_TASK_LIVE_SMOKE.md](docs/TWO_TASK_LIVE_SMOKE.md)

## Next

The second sustainability task family, `subscription-billing-evolution`, is now implemented and the two-task runner has completed a one-trial live smoke:

```text
1 trial * 2 task families * 2 model tiers * 2 conditions = 8 agent runs
```

See [docs/TWO_TASK_LIVE_SMOKE.md](docs/TWO_TASK_LIVE_SMOKE.md). Treat that smoke as runner/scorer validation, not as a headline benchmark claim.

The next useful benchmark is the full planned two-task matrix:

```text
5 trials * 2 task families * 2 model tiers * 2 conditions = 40 agent runs
```

That would test whether the verification-first loop holds beyond one task family with enough trials to compare task-family and model-tier behavior.

Other high-value next steps:

- Promote seeded-bug / mutation scoring into the main benchmark instead of relying heavily on process-keyword hits.
- Track cost, elapsed time, token use, tool-call count, and file-change counts per run.
- Split long-term reports into a main suite and an evolution suite so `tool-call-planner-v2` is not treated as fully independent from `tool-call-planner`.
