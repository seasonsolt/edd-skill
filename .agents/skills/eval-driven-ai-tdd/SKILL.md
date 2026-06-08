---
name: eval-driven-ai-tdd
description: "Use for AI coding tasks where correctness depends on evals, benchmarks, hidden edge cases, regression protection, or comparing agent performance. Makes evaluation the first project artifact and changes the agent coding loop so each implementation turn binds to an eval contract, runs visible verification, records evidence, and feeds failures back into regressions."
---

# EDD Skill

EDD means Eval-Driven Development. Use this skill to make evaluation the first artifact in an AI coding project, then keep every agent coding loop attached to that evaluation contract. The goal is not extra process. The goal is to give the agent a stable target and leave evidence that the loop followed it.

## Workflow

0. Start from evaluation.
   - If the project has no evals, benchmarks, tests, rubric, or scoring contract, create the smallest useful evaluation artifact first.
   - Put the contract where future agent turns can find it, such as `evals/contract.md`, `tests/`, or the project benchmark folder.
   - Do not begin implementation by changing product code when the expected behavior is still unmeasured.

1. Bind the coding turn to the evaluation contract.
   - Name the user-visible behavior, edge cases, invariants, and failure modes.
   - Prefer executable tests over prose. Use a benchmark file only when deterministic tests are not enough.
   - State which visible command proves this turn. Hidden tests are not part of the agent-visible loop.

2. Extend visible evals when the contract is incomplete.
   - Add or update the smallest tests/evals that should fail against the current code.
   - Prefer a separate regression file such as `tests/test_regressions.py` or `evals/regressions.jsonl` instead of only editing starter tests.
   - Run the focused command and capture the failure in `evals/red.log` when practical.
   - Make the red log show the newly added contract case failing whenever possible. A generic unimplemented failure is weaker evidence.
   - If the codebase already has a test convention, use it. Otherwise create a minimal convention.

3. Change the implementation only after the visible evaluation target exists.
   - Keep the implementation narrow.
   - Do not add optional behavior, frameworks, or broad refactors.
   - Add regression cases for every bug discovered during the loop.

4. Verify the green state.
   - Rerun the focused test/eval command.
   - Run the broader relevant suite if the change touches shared behavior.
   - Capture the final command output in `evals/green.log` when practical.

5. Refactor only under a green suite.
   - Simplify duplicated or unclear code only after tests pass.
   - Rerun the same verification after refactoring.

6. Leave evidence.
   - Create `EDD_REPORT.md` for non-trivial tasks.
   - Include the contract, red command/result, implementation summary, green command/result, regressions added, and known gaps.
   - State exactly which command proves the final behavior.
   - If a hidden benchmark fails later, convert the failure into an agent-visible regression before the next coding loop.

## Decision Rules

- If the task is a bug fix, write the reproducing regression test first.
- If the task is a feature, write at least one success case, one boundary case, and one invalid or failure-mode case first.
- If the task is refactoring, identify the existing tests that preserve behavior before editing; add characterization tests if coverage is weak.
- If the task involves prompts, RAG, agents, or probabilistic outputs, create eval cases and a rubric before changing prompts or retrieval logic.
- If the user asks for a benchmark or comparison, keep hidden tests and scoring code out of the agent-visible task copy.
- If the user asks to build a new AI project, propose the first eval suite before proposing the implementation architecture.

## Artifact Standards

Use these defaults unless the repository already has stronger conventions:

- Tests: `tests/` or the existing test folder.
- Regression tests: `tests/test_regressions.py` when no stronger local convention exists.
- Evals/benchmark cases: `evals/`.
- Evaluation contract: `evals/contract.md` when no stronger local convention exists.
- Red log: `evals/red.log`.
- Green log: `evals/green.log`.
- Report: `EDD_REPORT.md`. Existing `AI_TDD_REPORT.md` files are acceptable for older runs.

For AI/RAG/prompt tasks, use `evals/*.jsonl` with one case per line. For deterministic code, prefer normal unit tests.

Read `references/eval-first-contract.md` when designing a new benchmark, rubric, or scoring contract.
Read `references/benchmark-protocol.md` when comparing agent performance, skills, prompts, models, or tools.

Run `scripts/check_ai_tdd_artifacts.py --project-root <repo>` before finishing when this skill created new tests/evals or a report.

## Benchmarking Agent Performance

When comparing runs with and without this skill:

1. Use the same task prompt and starter files.
2. Start from clean copies of the task.
3. Hide private benchmark tests from both runs.
4. Score final behavior and process artifacts separately.
5. Treat transcript claims as weak evidence unless backed by files, logs, or command output.

The useful question is not whether the skill makes the agent write more text. The useful question is whether changing the agent coding loop improves hidden-case correctness, regression coverage, and reproducibility.

For credible claims, run more than one task and more than one paired trial. Report functional and process scores separately.
