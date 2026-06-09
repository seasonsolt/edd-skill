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
- The benchmark has two task families and hidden tests.
- `verify_benchmark.py` proves starter tasks fail and reference implementations pass.
- The 5-trial paired run showed a stable process-score lift: median total delta +33.5, mean total delta +31.5.
- Both conditions passed all hidden tests in the 5-trial run, which keeps the claim honest: the current evidence supports auditability and reproducibility, not functional correctness uplift.

## Weak Spots

- The internal skill name is still `$eval-driven-ai-tdd`; this is compatible but less aligned with the product name `EDD Skill`.
- The benchmark measures process artifacts well, but it does not yet track cost, elapsed time, token use, or tool-call count.
- The hidden-failure-to-regression workflow is described but not automated.
- The artifact checker still keeps backward compatibility with `AI_TDD_REPORT.md`; new runs should prefer `EDD_REPORT.md`.
- The current task families were easy enough that baseline agents also passed hidden tests; this makes the benchmark good for process evidence, but weak for proving functional uplift.

## Next Improvements

1. Add a third task family that is closer to AI app work, such as prompt classification, RAG answer grading, or tool-call planning.
2. Add cost/time metadata to each run's score JSON.
3. Add a script that converts selected hidden failures into visible regression templates after scoring.
4. Consider adding an alias skill or renamed skill folder for `$edd-skill` once compatibility is less important.
5. Add a result card or README figure that separates functional correctness, process evidence, and claim strength.
