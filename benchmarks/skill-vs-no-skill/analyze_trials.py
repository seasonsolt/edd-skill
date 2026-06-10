#!/usr/bin/env python3
"""Diagnose a scored skill-vs-no-skill trial set.

This script does not rerun hidden tests. It reads the score JSON files already
created by score_trials.py/score_suite.py and explains why the aggregate result
does or does not support a skill-effect claim.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


CONDITIONS = ("baseline", "with-skill")


def mean(values: list[float]) -> float:
    return round(float(statistics.fmean(values)), 2) if values else 0.0


def pct(count: int, total: int) -> float:
    return round((count / total) * 100, 2) if total else 0.0


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def condition_key(condition: str) -> str:
    return condition.replace("-", "_")


def first_hidden_failure(score: dict[str, Any]) -> str:
    hidden = score["commands"]["hidden"]
    if hidden["returncode"] == 0:
        return "pass"

    for line in hidden.get("stderr", "").splitlines():
        match = re.match(r"^(FAIL|ERROR):\s+([A-Za-z0-9_]+)", line)
        if match:
            return match.group(2)
    return "hidden_failed_unknown"


def failure_category(task: str, failure: str, score: dict[str, Any]) -> str:
    stderr = score["commands"]["hidden"].get("stderr", "")
    if failure == "pass":
        return "pass"
    if task in {"tool-call-planner", "tool-call-planner-v2"} and "no_matching_tool" in stderr:
        return "no_matching_tool_clarification_boundary"
    return failure


def build_run_record(
    trial: str,
    task: str,
    condition: str,
    score_path: Path,
    score: dict[str, Any],
) -> dict[str, Any]:
    process = score["process"]
    functional = score["functional"]
    artifact_flags = {
        "has_report": bool(process["has_report"]),
        "has_evals_dir": bool(process["has_evals_dir"]),
        "has_red_log": bool(process["has_red_log"]),
        "has_green_log": bool(process["has_green_log"]),
    }
    complete_evidence = all(artifact_flags.values())
    has_edd_like_artifact = any(artifact_flags.values())
    hidden_failure = first_hidden_failure(score)

    return {
        "trial": trial,
        "task": task,
        "condition": condition,
        "score_path": str(score_path),
        "candidate": score["candidate"],
        "score": score["score"],
        "functional_score": functional["score"],
        "process_score": process["score"],
        "public_passed": bool(functional["public_passed"]),
        "hidden_passed": bool(functional["hidden_passed"]),
        "hidden_failure": hidden_failure,
        "hidden_failure_category": failure_category(task, hidden_failure, score),
        "artifact_flags": artifact_flags,
        "has_edd_like_artifact": has_edd_like_artifact,
        "complete_evidence": complete_evidence,
        "report_path": process["report_path"],
        "eval_file_count": process["eval_file_count"],
        "test_case_count": process["test_case_count"],
        "edge_coverage": process["edge_coverage"],
    }


def discover_runs(trials_root: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for trial_dir in sorted(path for path in trials_root.iterdir() if path.is_dir()):
        for task_dir in sorted(path for path in trial_dir.iterdir() if path.is_dir()):
            for condition in CONDITIONS:
                score_path = task_dir / f"{condition}.score.json"
                if not score_path.exists():
                    continue
                score = load_json(score_path)
                runs.append(build_run_record(trial_dir.name, task_dir.name, condition, score_path, score))
    return runs


def compact_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "trial": run["trial"],
        "task": run["task"],
        "condition": run["condition"],
        "score": run["score"],
        "functional_score": run["functional_score"],
        "process_score": run["process_score"],
        "public_passed": run["public_passed"],
        "hidden_passed": run["hidden_passed"],
        "hidden_failure_category": run["hidden_failure_category"],
        "complete_evidence": run["complete_evidence"],
        "has_edd_like_artifact": run["has_edd_like_artifact"],
        "report_path": run["report_path"],
        "test_case_count": run["test_case_count"],
        "edge_coverage": run["edge_coverage"],
    }


def summarize_condition(runs: list[dict[str, Any]], high_process_threshold: int) -> dict[str, Any]:
    return {
        "run_count": len(runs),
        "mean_score": mean([run["score"] for run in runs]),
        "mean_functional_score": mean([run["functional_score"] for run in runs]),
        "mean_process_score": mean([run["process_score"] for run in runs]),
        "public_passed": sum(1 for run in runs if run["public_passed"]),
        "hidden_passed": sum(1 for run in runs if run["hidden_passed"]),
        "hidden_pass_rate": pct(sum(1 for run in runs if run["hidden_passed"]), len(runs)),
        "artifact_runs": sum(1 for run in runs if run["has_edd_like_artifact"]),
        "complete_evidence_runs": sum(1 for run in runs if run["complete_evidence"]),
        "high_process_runs": sum(1 for run in runs if run["process_score"] >= high_process_threshold),
        "high_process_threshold": high_process_threshold,
    }


def summarize_task(
    task: str,
    task_runs: list[dict[str, Any]],
    high_process_threshold: int,
) -> dict[str, Any]:
    by_condition = {
        condition_key(condition): summarize_condition(
            [run for run in task_runs if run["condition"] == condition],
            high_process_threshold,
        )
        for condition in CONDITIONS
    }
    baseline = by_condition["baseline"]
    with_skill = by_condition["with_skill"]
    failure_patterns = {}
    public_green_hidden_red = {}

    for condition in CONDITIONS:
        key = condition_key(condition)
        runs = [run for run in task_runs if run["condition"] == condition]
        failures = Counter(run["hidden_failure_category"] for run in runs if not run["hidden_passed"])
        failure_patterns[key] = dict(sorted(failures.items()))
        public_green_hidden_red[key] = sum(
            1 for run in runs if run["public_passed"] and not run["hidden_passed"]
        )

    return {
        "task": task,
        "baseline": baseline,
        "with_skill": with_skill,
        "delta": {
            "mean_score": round(with_skill["mean_score"] - baseline["mean_score"], 2),
            "mean_functional_score": round(
                with_skill["mean_functional_score"] - baseline["mean_functional_score"], 2
            ),
            "mean_process_score": round(
                with_skill["mean_process_score"] - baseline["mean_process_score"], 2
            ),
            "hidden_passed": with_skill["hidden_passed"] - baseline["hidden_passed"],
        },
        "hidden_failure_patterns": failure_patterns,
        "public_green_hidden_red": public_green_hidden_red,
    }


def load_optional(path: Path) -> dict[str, Any] | None:
    return load_json(path) if path.exists() else None


def conclusions(
    trials_summary: dict[str, Any] | None,
    assessment: dict[str, Any] | None,
    baseline_leakage: dict[str, Any],
    per_task: dict[str, Any],
) -> list[str]:
    notes: list[str] = []
    verdict = assessment.get("verdict") if assessment else None
    if verdict:
        notes.append(f"assessment verdict is {verdict}")

    hidden_delta = None
    if assessment:
        hidden_delta = assessment["observed"]["hidden_pass_delta"]
    elif trials_summary:
        hidden_delta = None
    if hidden_delta == 0:
        notes.append("hidden functional pass count did not improve")

    process_delta = assessment["observed"]["median_process_delta"] if assessment else None
    min_process_delta = assessment["criteria"]["min_process_delta"] if assessment else None
    if process_delta is not None and min_process_delta is not None and process_delta < min_process_delta:
        notes.append(
            f"median process delta {process_delta} missed the configured gate {min_process_delta}"
        )

    if baseline_leakage["complete_evidence_runs"]:
        notes.append("baseline produced complete EDD-like evidence in at least one run")

    tool_call = per_task.get("tool-call-planner")
    if tool_call:
        baseline_failures = tool_call["public_green_hidden_red"]["baseline"]
        skill_failures = tool_call["public_green_hidden_red"]["with_skill"]
        if baseline_failures and skill_failures:
            notes.append("tool-call-planner is a stable public-green/hidden-red task in both conditions")

    return notes


def analyze(trials_root: Path, high_process_threshold: int) -> dict[str, Any]:
    trials_summary = load_optional(trials_root / "trials-summary.json")
    assessment = load_optional(trials_root / "assessment.json")
    runs = discover_runs(trials_root)
    if not runs:
        raise SystemExit(f"no score JSON files found under {trials_root}")

    by_condition = {
        condition_key(condition): summarize_condition(
            [run for run in runs if run["condition"] == condition],
            high_process_threshold,
        )
        for condition in CONDITIONS
    }
    tasks = sorted({run["task"] for run in runs})
    per_task = {
        task: summarize_task(
            task,
            [run for run in runs if run["task"] == task],
            high_process_threshold,
        )
        for task in tasks
    }

    baseline_runs = [run for run in runs if run["condition"] == "baseline"]
    baseline_leakage_runs = [
        run
        for run in baseline_runs
        if run["has_edd_like_artifact"] or run["process_score"] >= high_process_threshold
    ]
    baseline_leakage_runs.sort(
        key=lambda run: (run["process_score"], run["score"], run["trial"], run["task"]),
        reverse=True,
    )
    baseline_leakage = {
        "artifact_runs": sum(1 for run in baseline_runs if run["has_edd_like_artifact"]),
        "complete_evidence_runs": sum(1 for run in baseline_runs if run["complete_evidence"]),
        "high_process_runs": sum(1 for run in baseline_runs if run["process_score"] >= high_process_threshold),
        "high_process_threshold": high_process_threshold,
        "runs": [compact_run(run) for run in baseline_leakage_runs],
    }

    hidden_failures = Counter()
    for run in runs:
        if not run["hidden_passed"]:
            key = f"{run['task']}::{condition_key(run['condition'])}::{run['hidden_failure_category']}"
            hidden_failures[key] += 1

    output = {
        "trials_root": str(trials_root),
        "trial_count": len({run["trial"] for run in runs}),
        "task_count": len(tasks),
        "run_count": len(runs),
        "trials_summary": trials_summary["summary"] if trials_summary else None,
        "assessment": assessment,
        "condition_summary": by_condition,
        "baseline_artifact_leakage": baseline_leakage,
        "per_task": per_task,
        "hidden_failure_summary": dict(sorted(hidden_failures.items())),
    }
    output["conclusions"] = conclusions(trials_summary, assessment, baseline_leakage, per_task)
    return output


def print_report(analysis_result: dict[str, Any]) -> None:
    assessment = analysis_result.get("assessment")
    observed = assessment.get("observed", {}) if assessment else {}
    print("Skill vs no-skill trial diagnostics")
    print(f"Trials root: {analysis_result['trials_root']}")
    print(
        f"Volume: {analysis_result['trial_count']} trials, "
        f"{analysis_result['task_count']} task families, {analysis_result['run_count']} scored runs"
    )
    if assessment:
        print(f"Assessment verdict: {assessment['verdict']}")
        print(
            "Observed: "
            f"hidden pass delta {observed['hidden_pass_delta']}, "
            f"median process delta {observed['median_process_delta']}, "
            f"median functional delta {observed['median_functional_delta']}"
        )

    print("\nCondition summary:")
    for condition in ("baseline", "with_skill"):
        summary = analysis_result["condition_summary"][condition]
        print(
            f"- {condition}: mean score {summary['mean_score']}, "
            f"mean process {summary['mean_process_score']}, "
            f"hidden {summary['hidden_passed']}/{summary['run_count']}, "
            f"complete evidence {summary['complete_evidence_runs']}/{summary['run_count']}, "
            f"high process {summary['high_process_runs']}/{summary['run_count']}"
        )

    leakage = analysis_result["baseline_artifact_leakage"]
    print("\nBaseline artifact leakage:")
    print(
        f"- artifact runs {leakage['artifact_runs']}, "
        f"complete evidence runs {leakage['complete_evidence_runs']}, "
        f"high process runs {leakage['high_process_runs']} "
        f"(threshold >= {leakage['high_process_threshold']})"
    )
    for run in leakage["runs"]:
        print(
            f"  - {run['trial']} {run['task']}: process {run['process_score']}, "
            f"score {run['score']}, report {run['report_path']}"
        )

    print("\nPer-task hidden pattern:")
    for task, summary in analysis_result["per_task"].items():
        baseline = summary["baseline"]
        with_skill = summary["with_skill"]
        print(
            f"- {task}: hidden baseline {baseline['hidden_passed']}/{baseline['run_count']}, "
            f"with-skill {with_skill['hidden_passed']}/{with_skill['run_count']}, "
            f"process delta {summary['delta']['mean_process_score']}"
        )
        patterns = summary["hidden_failure_patterns"]
        if patterns["baseline"] or patterns["with_skill"]:
            print(f"  failures: baseline={patterns['baseline']} with_skill={patterns['with_skill']}")

    print("\nConclusions:")
    for note in analysis_result["conclusions"]:
        print(f"- {note}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials-root",
        required=True,
        help="Directory containing scored trial subdirectories and trials-summary.json",
    )
    parser.add_argument(
        "--high-process-threshold",
        type=int,
        default=30,
        help="Process score treated as unusually high for baseline diagnostics",
    )
    parser.add_argument("--json-output", help="Optional path to write machine-readable diagnostics")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text report")
    args = parser.parse_args()

    result = analyze(Path(args.trials_root).resolve(), args.high_process_threshold)
    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
