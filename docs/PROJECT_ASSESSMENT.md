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
- The benchmark now has five task families and hidden tests. The fifth family is `tool-call-planner-v2`, created after the four-task result was scored.
- `verify_benchmark.py` proves starter tasks fail and reference implementations pass.
- The latest 5-trial paired run across all four task families reached the planned benchmark volume: 40 isolated worker runs.
- `tool-call-planner` added a harder AI-app-like task surface with policy precedence, risk choice, approval, missing arguments, and prompt-injection resistance.
- `tool-call-planner-v2` converts the repeated no-matching-tool hidden miss into a visible public contract for the next benchmark loop.
- `evidence-answerer` adds a RAG-like deterministic task surface with citations, insufficient evidence, trusted/untrusted sources, conflicting facts, and instruction-like text inside passages.
- `assess_trials.py` now turns scored trial output into an explicit evidence verdict instead of relying on README interpretation.
- The harder task exposed hidden functional misses in both conditions: baseline and with-skill each passed 15 / 20 hidden task runs, with both failing all `tool-call-planner` hidden runs.

## Weak Spots

- The internal skill name is still `$eval-driven-ai-tdd`; this is compatible but less aligned with the product name `EDD Skill`.
- The benchmark measures process artifacts well, but it does not yet track cost, elapsed time, token use, or tool-call count.
- The hidden-failure-to-regression workflow is still mostly manual. `tool-call-planner-v2` proves one manual conversion, but there is no reusable converter yet.
- The artifact checker still keeps backward compatibility with `AI_TDD_REPORT.md`; new runs should prefer `EDD_REPORT.md`.
- The skill has not improved hidden functional correctness in the current benchmark: functional delta is 0 and hidden pass delta is 0.
- The current four-task result is `not_supported` under the fixed assessment gate. Although with-skill had a numeric process-score lift, the median process delta was +19.75 against a +20 threshold.
- Baseline can already produce EDD-like artifacts in some runs. Trial 005 `feature-flags` baseline scored full process credit, which weakens the claim that the skill uniquely causes process discipline.
- The new `analyze_trials.py` diagnostic makes this explicit: baseline complete evidence is 1 / 20, with-skill complete evidence is 20 / 20, and hidden pass delta is still 0.
- `tool-call-planner` has a stable public-green/hidden-red failure category in both conditions. That miss has now been converted into `tool-call-planner-v2`.

## Next Improvements

1. Treat the four-task `not_supported` verdict as the current truth, not as a messaging problem.
2. Run 5 paired trials on the current five-task suite, including `tool-call-planner-v2`.
3. Add cost/time metadata to each run's score JSON.
4. Add a script that converts selected hidden failures into visible regression templates after scoring.
5. Investigate why baseline runs can produce EDD-like artifacts and whether the benchmark prompt itself is already enough to induce the desired loop. The first diagnostic is now available through `analyze_trials.py`; the next step is to compare prompts and generated artifacts, not just scores.
