# Four-Task Benchmark Review

Date: 2026-06-10

This review explains why the current four-task benchmark result is
`not_supported`, even though the with-skill condition has a clear process-score
lift.

## Commands

```bash
python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials-4task --expected-trial-count 5
python3 benchmarks/skill-vs-no-skill/assess_trials.py --trials-root runs/skill-vs-no-skill-trials-4task --json-output runs/skill-vs-no-skill-trials-4task/assessment.json
python3 benchmarks/skill-vs-no-skill/analyze_trials.py --trials-root runs/skill-vs-no-skill-trials-4task --json-output runs/skill-vs-no-skill-trials-4task/diagnostics.json
```

## Diagnostic Result

| Metric | Baseline | With EDD Skill |
| --- | ---: | ---: |
| Scored runs | 20 | 20 |
| Mean total score | 67.45 | 86.45 |
| Mean process score | 14.95 / 35 | 33.95 / 35 |
| Hidden passed | 15 / 20 | 15 / 20 |
| Complete evidence runs | 1 / 20 | 20 / 20 |
| High-process runs | 1 / 20 | 20 / 20 |

Assessment verdict: `not_supported`.

The process signal is real but not enough for a claim. The fixed gate requires
median process delta `>= 20`; the observed median process delta is `+19.75`.
More importantly, hidden functional pass count does not improve: both
conditions pass `15 / 20`.

## Baseline Artifact Leakage

The baseline condition produced one complete EDD-like artifact set:

| Trial | Task | Process score | Total score | Report |
| --- | --- | ---: | ---: | --- |
| `trial-005` | `feature-flags` | 35 / 35 | 100 / 100 | `EDD_REPORT.md` |

This does not invalidate the benchmark, but it weakens the claim that the skill
is uniquely responsible for process discipline. The task prompt and current
model can sometimes induce the same behavior without the skill.

## Hidden Failure Pattern

`tool-call-planner` is the useful hard task in this suite:

| Task | Baseline hidden | With-skill hidden | Failure pattern |
| --- | ---: | ---: | --- |
| `tool-call-planner` | 0 / 5 | 0 / 5 | `no_matching_tool_clarification_boundary` |

All ten `tool-call-planner` runs pass public tests and fail hidden tests on the
same behavioral boundary: when no tool matches, the planner should return a
clarification that explicitly marks the tool as missing.

This is the strongest next benchmark input. The next loop should create a v2
visible regression or task variant from that behavior class after this run has
already been scored. It should not copy hidden tests directly into the agent
prompt.

## Interpretation

- The skill improves auditability in this run: with-skill leaves complete
  evidence in `20 / 20` runs.
- The skill has not shown hidden functional uplift: hidden pass delta is `0`.
- The process claim is close but still below the predefined gate.
- One baseline run produced full EDD-like evidence, so process scoring needs
  leakage diagnostics before any promotional claim.
- The next useful experiment is not a lower threshold. It is a harder visible
  `tool-call-planner` v2 and another paired trial set.
