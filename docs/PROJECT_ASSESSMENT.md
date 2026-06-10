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
- The latest 5-trial paired run across all five task families reached the planned benchmark volume: 50 isolated worker runs.
- `tool-call-planner` added a harder AI-app-like task surface with policy precedence, risk choice, approval, missing arguments, and prompt-injection resistance.
- `tool-call-planner-v2` converts the repeated no-matching-tool hidden miss into a visible public contract and has now been included in a formal paired-trial run.
- `evidence-answerer` adds a RAG-like deterministic task surface with citations, insufficient evidence, trusted/untrusted sources, conflicting facts, and instruction-like text inside passages.
- `assess_trials.py` now turns scored trial output into an explicit evidence verdict instead of relying on README interpretation.
- The five-task run exposed the current boundary cleanly: baseline and with-skill each passed 20 / 25 hidden task runs, with both failing all `tool-call-planner` hidden runs.
- The current fixed verdict is `process_only_supported`: the skill produced stable process/evidence lift without hidden functional uplift.

## Weak Spots

- The internal skill name is still `$eval-driven-ai-tdd`; this is compatible but less aligned with the product name `EDD Skill`.
- The benchmark measures process artifacts well, but it does not yet track cost, elapsed time, token use, or tool-call count.
- The hidden-failure-to-regression workflow is still mostly manual. `tool-call-planner-v2` proves one manual conversion, but there is no reusable converter yet.
- The artifact checker still keeps backward compatibility with `AI_TDD_REPORT.md`; new runs should prefer `EDD_REPORT.md`.
- The skill has not improved hidden functional correctness in the current benchmark: functional delta is 0 and hidden pass delta is 0.
- The current five-task result is `process_only_supported` under the fixed assessment gate. Median process delta was +25.8, but median functional delta was 0.
- In the five-task run, baseline no longer produced complete EDD artifact leakage: baseline complete evidence was 0 / 25 while with-skill complete evidence was 25 / 25.
- The new `analyze_trials.py` diagnostic makes this explicit: baseline mean process score is 7.84 / 35, with-skill mean process score is 33.72 / 35, and hidden pass delta is still 0.
- `tool-call-planner` still has a stable public-green/hidden-red failure category in both conditions. `tool-call-planner-v2` passed in both conditions after that miss was converted into a visible contract, which validates the benchmark loop but not a skill-specific functional lift.

## Next Improvements

1. Treat the five-task `process_only_supported` verdict as the current truth, not as a messaging problem.
2. Decide the claim before rerunning: confirm process/reproducibility with an independent root, or attempt functional uplift with a single changed variable.
3. Add cost/time metadata to each run's score JSON.
4. Add a script that converts selected hidden failures into visible regression templates after scoring.
5. Investigate why process lift does not convert into hidden functional lift on `tool-call-planner`. The next useful comparison is prompt and artifact analysis, not only aggregate score comparison.
