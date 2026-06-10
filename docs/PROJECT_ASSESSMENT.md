# Project Assessment

This review updates the project's framing from "AI TDD" to EDD: evaluation starts the project, then the skill changes the agent coding loop.

## What Was Misleading

The old README flow was:

```text
write failing case -> implement minimal change -> run public and hidden tests -> leave red/green evidence -> record regressions
```

That was too close to classic TDD and it put hidden tests inside the loop. The agent should not see or run hidden tests. Hidden benchmarks belong to the independent scoring layer.

## Better Framing

EDD should be described as:

```text
evaluation contract -> agent coding loop -> visible verification evidence -> hidden benchmark scoring -> failures become regressions
```

The key point is narrower and stronger:

- Evaluation is the first project artifact.
- The skill changes the agent coding loop, not the whole app stack.
- Hidden benchmarks measure the loop from outside.
- Scoring failures become visible regressions for the next loop.

## Current Strengths

- The repo now has a real Codex skill, not just prose.
- The benchmark has four task families and hidden tests.
- `verify_benchmark.py` proves starter tasks fail and reference implementations pass.
- The latest 5-trial paired run across all three task families showed a stable process-score lift: median total delta +29.66, mean total delta +28.6.
- `tool-call-planner` added a harder AI-app-like task surface with policy precedence, risk choice, approval, missing arguments, and prompt-injection resistance.
- `evidence-answerer` adds a RAG-like deterministic task surface with citations, insufficient evidence, trusted/untrusted sources, conflicting facts, and instruction-like text inside passages.
- `assess_trials.py` now turns scored trial output into an explicit evidence verdict instead of relying on README interpretation.
- The harder task exposed hidden functional misses in both conditions: baseline and with-skill each passed 10 / 15 hidden task runs.

## Weak Spots

- The internal skill name is still `$eval-driven-ai-tdd`; this is compatible but less aligned with the product name `EDD Skill`.
- The benchmark measures process artifacts well, but it does not yet track cost, elapsed time, token use, or tool-call count.
- The hidden-failure-to-regression workflow is described but not automated, and `tool-call-planner` now gives concrete failures to feed into it.
- The artifact checker still keeps backward compatibility with `AI_TDD_REPORT.md`; new runs should prefer `EDD_REPORT.md`.
- The skill has not yet improved hidden functional correctness; its demonstrated value remains process evidence, auditability, and reproducibility.
- The new four-task suite has passed integrity checks, but it has not yet been run as a full paired trial set.

## Next Improvements

1. Run 5 paired trials on the four-task suite and record the `assess_trials.py` verdict.
2. Create `tool-call-planner` v2 by converting scored hidden misses into visible regressions without leaking the original hidden tests.
3. Add cost/time metadata to each run's score JSON.
4. Add a script that converts selected hidden failures into visible regression templates after scoring.
5. Consider adding an alias skill or renamed skill folder for `$edd-skill` once compatibility is less important.
