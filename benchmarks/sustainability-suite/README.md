# EDD Sustainability Suite

This suite is a second benchmark track for EDD Skill.

The existing `skill-vs-no-skill` suite is a kata-style benchmark: each task has a clear contract, public tests, hidden tests, and process scoring. It is useful, but it mostly measures whether an agent can implement an already-specified behavior and leave evidence.

This suite targets a narrower EDD claim:

```text
AI coding becomes sustainable when the agent first turns expected outcomes into executable verification logic.
```

## Scoring Contract

The suite should score four dimensions separately.

| Dimension | Score | Purpose |
| --- | ---: | --- |
| Final hidden behavior | 35 | Does the final implementation satisfy scorer-only behavior tests? |
| Verification kills seeded bugs | 30 | Do agent-written tests/evals catch known flawed implementations? |
| Multi-turn regression preservation | 20 | Do earlier behaviors remain protected after later changes? |
| Process evidence | 15 | Did the run leave red/green evidence, regressions, and an EDD report? |

Total: `100`.

The important change from the kata suite is that verification logic becomes a functional scoring target. Test files are not valuable only because they exist; they are valuable if they catch plausible bugs.

## Model Tiers

Every paired experiment should run across two model tiers:

| Tier | Example label | Purpose |
| --- | --- | --- |
| SOTA model | `gpt5.5` | Tests whether EDD still helps when the model is already strong enough to infer many missing cases. |
| Economical model | `gpt5.4mini` | Tests whether EDD gives smaller, cheaper models enough structure to become reliable. |

Treat these labels as benchmark configuration names. Before running a real experiment, map them to the exact model IDs available in the execution environment and record those IDs in the run metadata.

Do not average the two tiers into one headline number. Report each model tier separately, then optionally report a combined view.

Minimum result table:

| Model tier | Condition | Final hidden | Seeded bugs killed | Regression preservation | Process | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SOTA | baseline | | | | | |
| SOTA | with EDD Skill | | | | | |
| Economical | baseline | | | | | |
| Economical | with EDD Skill | | | | | |

Primary deltas:

- SOTA delta: `with_skill_sota - baseline_sota`
- Economical delta: `with_skill_economical - baseline_economical`
- Skill leverage gap: `economical_delta - sota_delta`

The skill leverage gap matters because EDD may be more valuable when model capability is constrained. A SOTA model might solve many tasks without explicit process, while an economical model may need verification scaffolding to stay reliable.

## Trial Matrix

For each task family and trial index, run four isolated agents:

```text
SOTA baseline
SOTA with EDD Skill
Economical baseline
Economical with EDD Skill
```

With 5 trials and 2 task families, the minimum credible run count is:

```text
5 trials * 2 task families * 2 model tiers * 2 skill conditions = 40 runs
```

Use identical prompts, starter files, approval settings, time budgets, and hidden scorers across the two skill conditions within the same model tier.

## Task Shape

Each task should have:

- a short product-style prompt, not a complete formal specification;
- one or two public smoke tests;
- hidden final behavior tests;
- scorer-only seeded buggy implementations;
- a multi-turn change sequence;
- a command that runs agent-written verification against the seeded bugs.

## First Task

The first task is `agent-policy-evolution`.

It evolves the current `tool-call-planner` task into a more realistic AI-app scenario:

1. Basic tool selection.
2. Policy precedence and approval.
3. Prompt-injection resistance and missing-tool clarification.

The first prototype in this directory focused on the `Verification kills seeded bugs` dimension. The suite now includes two task families by default:

- `agent-policy-evolution`: tool-use policy and safety boundary verification.
- `subscription-billing-evolution`: deterministic business-rule verification for money, proration, idempotency, trials, cancellation, and payment-failure transitions.

## Current Pilot Result

The completed single-task pilot used 20 provider-backed runs:

```text
5 trials * 1 task family * 2 model tiers * 2 conditions = 20 runs
```

| Group | Hidden passed | Seeded-bug score | Process score |
| --- | ---: | ---: | ---: |
| `gpt-5.5` baseline | 0 / 5 | 0.0 / 30 | 0.0 / 35 |
| `gpt-5.5` with EDD | 0 / 5 | 30.0 / 30 | 33.8 / 35 |
| `gpt-5.4-mini` baseline | 0 / 5 | 6.0 / 30 | 3.0 / 35 |
| `gpt-5.4-mini` with EDD | 0 / 5 | 0.0 / 30 | 1.0 / 35 |

This supports a narrow result: EDD improved verification quality for the SOTA tier on this task. It did not improve hidden functional correctness, and it did not help the economical tier in this setup.

## Current Two-Task Smoke

A one-trial provider-backed smoke has now run the default two-task matrix end-to-end:

```text
1 trial * 2 task families * 2 model tiers * 2 conditions = 8 runs
```

All 8 runs scored. See [`docs/TWO_TASK_LIVE_SMOKE.md`](../../docs/TWO_TASK_LIVE_SMOKE.md) for the table and interpretation. Treat this as a runner/scorer smoke, not as a headline benchmark claim.

## Current Full Matrix Result

The full two-task matrix has also run end-to-end:

```text
5 trials * 2 task families * 2 model tiers * 2 conditions = 40 runs
```

All 40 runs scored. See [`docs/TWO_TASK_FULL_MATRIX_RESULTS.md`](../../docs/TWO_TASK_FULL_MATRIX_RESULTS.md).

Summary: EDD strongly improved process evidence in every task/model-tier group, but it did not produce reliable hidden functional correctness uplift. Aggregate seeded-bug deltas were small (`+0.25` economical, `-0.5` SOTA), while process deltas were large.

## Runnable Prototype

Prepare agent-ready run directories. By default this creates the two-task minimum matrix:

```bash
python3 benchmarks/sustainability-suite/prepare_model_matrix.py --force
```

For the default config this is:

```text
5 trials * 2 task families * 2 model tiers * 2 conditions = 40 runs
```

Each run directory contains:

- starter source files;
- public smoke tests;
- `TASK.md`;
- `PROMPT.md`;
- `RUN_METADATA.json`.

`run_model_matrix.py` expects a single JSON object response, records whether parsing was strict or fallback raw-decode, rejects trailing non-JSON content, limits writes to allowed task paths, and rejects oversized generated files.

After agents complete those directories, aggregate seeded-bug scores:

```bash
python3 benchmarks/sustainability-suite/score_model_matrix.py \
  --runs-root runs/sustainability-suite-model-matrix \
  --json-output runs/sustainability-suite-model-matrix/matrix-score.json
```

Untouched prepared runs should score `0` on seeded-bug verification. A higher score means the run added tests or evals that catch scorer-only flawed implementations.

Check status before scoring:

```bash
python3 benchmarks/sustainability-suite/matrix_status.py \
  --runs-root runs/sustainability-suite-model-matrix \
  --strict-complete
```
