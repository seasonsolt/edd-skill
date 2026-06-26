# Two-Model Sustainability Run Plan

This plan evaluates EDD Skill across two model tiers:

- SOTA model tier, labeled `gpt5.5`.
- Economical model tier, labeled `gpt5.4mini`.

The labels are benchmark configuration names. Before running real agents, fill in the exact executable model IDs in `model_matrix.json` or record them in each run's metadata.

## Matrix

For every trial and task family, run four isolated agents:

```text
sota / baseline
sota / with-skill
economical / baseline
economical / with-skill
```

Completed single-task prototype:

```text
5 trials * 1 task family * 2 model tiers * 2 conditions = 20 runs
```

Completed two-task live smoke:

```text
1 trial * 2 task families * 2 model tiers * 2 conditions = 8 runs
```

See [`docs/TWO_TASK_LIVE_SMOKE.md`](../../docs/TWO_TASK_LIVE_SMOKE.md). Use it as runner/scorer validation only; it is not enough for headline claims.

Next minimum credible sustainability benchmark:

```text
5 trials * 2 task families * 2 model tiers * 2 conditions = 40 runs
```

## Prepare Matrix

Prototype command:

```bash
python3 benchmarks/sustainability-suite/prepare_model_matrix.py --force
```

This writes run folders under:

```text
runs/sustainability-suite-model-matrix/
```

Each run folder contains `RUN_METADATA.json` with:

- trial id;
- task family;
- model tier;
- model label;
- exact model id when configured;
- skill condition;
- prompt prefix.

Each run folder also contains the task starter files and `PROMPT.md`. Give a worker agent only that run folder.

Check run status:

```bash
python3 benchmarks/sustainability-suite/matrix_status.py \
  --runs-root runs/sustainability-suite-model-matrix
```

Use `--strict-complete` before scoring. It exits non-zero while any run is still untouched.

## Score Matrix

After agent runs are complete:

```bash
python3 benchmarks/sustainability-suite/score_model_matrix.py \
  --runs-root runs/sustainability-suite-model-matrix \
  --json-output runs/sustainability-suite-model-matrix/matrix-score.json
```

The current scorer aggregates functional score, seeded-bug score, and process score for both default task families:

- `agent-policy-evolution`
- `subscription-billing-evolution`

Report task-family rows as well as model-tier aggregates before drawing cross-task conclusions.

## Reporting

Report each model tier separately:

| Model tier | Condition | Final hidden | Seeded bugs killed | Regression preservation | Process | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SOTA | baseline | | | | | |
| SOTA | with EDD Skill | | | | | |
| Economical | baseline | | | | | |
| Economical | with EDD Skill | | | | | |

Then report:

```text
SOTA skill delta = SOTA with-skill - SOTA baseline
Economical skill delta = economical with-skill - economical baseline
Skill leverage gap = economical skill delta - SOTA skill delta
```

The primary hypothesis is not that EDD always improves the SOTA tier. The stronger hypothesis is that EDD improves reliability per dollar by giving economical models a verification-first workflow.
