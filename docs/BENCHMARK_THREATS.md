# Benchmark Threat Model

This document records the main validity threats for EDD Skill benchmark results and the intended controls.

## What the Current Evidence Supports

Supported by the current scored runs:

- EDD Skill improves process artifacts, auditability, and red/green evidence in the measured suite.
- The current five-task result supports `process_only_supported` under the fixed assessment gate.

Not yet supported:

- Broad hidden functional correctness improvement.
- A general claim that EDD makes all coding agents more correct.
- A claim that smaller/economical models reliably benefit from EDD.

## Threats and Controls

| Threat | Risk | Current control | Recommended next control |
| --- | --- | --- | --- |
| Hidden-test leakage | Agent can optimize directly for scorer-only cases. | Prompts say not to expose `hidden_tests/` or scorer scripts. | Run agents in directories that physically omit hidden tests and scorer files. |
| Process keyword gaming | Tests can mention scorer keywords without verifying behavior. | Functional and process scores are reported separately. | Promote seeded-bug / mutation scoring into the main benchmark. |
| Baseline contamination | Baseline may independently create EDD-like artifacts. | `analyze_trials.py` reports baseline artifact leakage. | Track prompt/model settings and compare artifact leakage across independent roots. |
| Task-family dependence | `tool-call-planner-v2` is derived from `tool-call-planner`. | Results call out the v1/v2 relationship. | Treat evolution tasks as a separate suite instead of counting them as independent forever. |
| Model variance | One inherited model setting may not generalize. | Sustainability suite introduces model tiers. | Record exact model IDs/providers/settings for every run. |
| Cost blindness | Process gains may cost more time/tokens/tool calls. | Weak spot documented in project assessment. | Add timing, token, tool-call, and file-change metadata to run records. |
| Scorer overfitting | Agents may learn the benchmark shape over repeated runs. | Hidden tests stay outside agent-visible directories. | Rotate task families and add fresh independent confirmation roots. |
| Public-green/hidden-red cliffs | Some tasks are too easy or too hard to show skill-specific lift. | Diagnostics identify stable hidden failure categories. | Add multi-turn evolution and ambiguous-spec tasks where eval-first behavior can matter. |

## Reporting Rule

Always report functional and process scores separately. A higher total score is not a hidden-correctness claim unless hidden pass rate or functional score also improves.

## Main-Suite vs Evolution-Suite Guidance

`tool-call-planner-v2` is valuable because it demonstrates the hidden-failure-to-visible-regression loop. Long-term benchmark reports should avoid treating `tool-call-planner` and `tool-call-planner-v2` as fully independent task families. Prefer:

- a main suite with the latest version of each task family;
- an evolution suite that shows v1 -> v2 regression conversion history.
