# Two-Task Sustainability Live Smoke

This note records the first one-trial provider-backed smoke run after adding `subscription-billing-evolution` as the second sustainability task family.

## Run Shape

```text
1 trial * 2 task families * 2 model tiers * 2 conditions = 8 runs
```

Run root:

```text
/tmp/edd-two-task-live-smoke
```

Commands:

```bash
python3 benchmarks/sustainability-suite/prepare_model_matrix.py \
  --force \
  --runs-root /tmp/edd-two-task-live-smoke \
  --trial-count 1

python3 benchmarks/sustainability-suite/run_codex_matrix.py \
  --runs-root /tmp/edd-two-task-live-smoke \
  --limit 8 \
  --timeout 900

python3 benchmarks/sustainability-suite/score_model_matrix.py \
  --runs-root /tmp/edd-two-task-live-smoke \
  --json-output /tmp/edd-two-task-live-smoke/matrix-score.json
```

The first attempt exposed a runner bug: the JSON applicator was not yet accepting `subscription_billing/engine.py` for the new task. The run applicator was fixed to be task-aware and to validate all returned files before writing any of them. The Codex runner now also supports `--skip-completed` so interrupted matrices can resume without rerunning completed directories.

Final status:

```json
{
  "by_status": {"scored": 8},
  "run_count": 8
}
```

## Results

| Task | Model tier | Condition | Public | Hidden | Functional | Seeded bugs | Seeded score | Process | Total |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `agent-policy-evolution` | economical | baseline | yes | no | 15/65 | 2/4 | 15/30 | 15/35 | 30/100 |
| `agent-policy-evolution` | economical | with EDD | yes | no | 15/65 | 4/4 | 30/30 | 23/35 | 38/100 |
| `agent-policy-evolution` | sota | baseline | yes | no | 15/65 | 2/4 | 15/30 | 13/35 | 28/100 |
| `agent-policy-evolution` | sota | with EDD | yes | no | 15/65 | 2/4 | 15/30 | 33/35 | 48/100 |
| `subscription-billing-evolution` | economical | baseline | yes | no | 15/65 | 5/6 | 25/30 | 0/35 | 15/100 |
| `subscription-billing-evolution` | economical | with EDD | yes | yes | 65/65 | 5/6 | 25/30 | 20/35 | 85/100 |
| `subscription-billing-evolution` | sota | baseline | yes | yes | 65/65 | 5/6 | 25/30 | 0/35 | 65/100 |
| `subscription-billing-evolution` | sota | with EDD | yes | yes | 65/65 | 4/6 | 20/30 | 35/35 | 100/100 |

Grouped summary from `score_model_matrix.py`:

| Group | Hidden passed | Mean functional | Mean seeded score | Mean process |
| --- | ---: | ---: | ---: | ---: |
| economical / baseline | 0/2 | 15.0 | 20.0 | 7.5 |
| economical / with-skill | 1/2 | 40.0 | 27.5 | 21.5 |
| sota / baseline | 1/2 | 40.0 | 20.0 | 6.5 |
| sota / with-skill | 1/2 | 40.0 | 17.5 | 34.0 |

Seeded-bug deltas:

```json
{
  "economical_skill_delta": 7.5,
  "sota_skill_delta": -2.5,
  "skill_leverage_gap": 10.0
}
```

## Interpretation

This is only an 8-run smoke, not a benchmark claim.

What it supports:

- The two-task matrix now runs end-to-end and scores all runs.
- EDD continues to strongly improve process evidence in both task families.
- In this smoke, EDD helped the economical tier on seeded-bug score and hidden pass count, mainly because `subscription-billing-evolution/economical/with-skill` passed hidden tests while baseline did not.

What it does not support yet:

- A broad functional correctness claim. `agent-policy-evolution` remained hidden-red for all four groups.
- A SOTA seeded-bug uplift. The SOTA with-skill group had lower mean seeded-bug score than SOTA baseline in this single trial.
- A stable estimate. This needs the planned 40-run matrix before headline conclusions.

## Next Step

Run the full planned matrix:

```text
5 trials * 2 task families * 2 model tiers * 2 conditions = 40 runs
```

Then report task-family results separately before drawing cross-task conclusions.
