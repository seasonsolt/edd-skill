#!/usr/bin/env python3
"""Report preparation/completion status for paired trial directories."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from score_candidate import TASKS, count_test_defs
from score_suite import KNOWN_TASKS


CONDITIONS = ("baseline", "with-skill")


def condition_key(condition: str) -> str:
    return condition.replace("-", "_")


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def has_evidence_artifact(run_root: Path) -> bool:
    return any(
        path.exists()
        for path in (
            run_root / "EDD_REPORT.md",
            run_root / "AI_TDD_REPORT.md",
            run_root / "evals" / "red.log",
            run_root / "evals" / "green.log",
        )
    )


def added_test_count(run_root: Path, task: str) -> int:
    tests_dir = run_root / "tests"
    if not tests_dir.exists():
        return 0
    starter_public_test = TASKS[task]["starter_public_test"]
    starter_text = starter_public_test.read_text(encoding="utf-8")
    starter_count = count_test_defs(starter_text)
    total = 0
    for path in tests_dir.rglob("test_*.py"):
        total += count_test_defs(path.read_text(encoding="utf-8"))
    return max(0, total - starter_count)


def implementation_changed(run_root: Path, task: str) -> bool:
    task_config = TASKS[task]
    marker = Path(task_config["marker"])
    candidate_text = read_text(run_root / marker)
    starter_text = read_text(task_config["starter_root"] / marker)
    return candidate_text is not None and starter_text is not None and candidate_text != starter_text


def score_path_for(run_root: Path, condition: str) -> Path:
    return run_root.parent / f"{condition}.score.json"


def load_run_metadata(run_root: Path) -> dict[str, Any] | None:
    path = run_root / "RUN_METADATA.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def score_status(score_path: Path) -> dict[str, Any] | None:
    if not score_path.exists():
        return None
    score = json.loads(score_path.read_text(encoding="utf-8"))
    return {
        "score": score["score"],
        "functional_score": score["functional"]["score"],
        "process_score": score["process"]["score"],
        "public_passed": score["functional"]["public_passed"],
        "hidden_passed": score["functional"]["hidden_passed"],
    }


def run_status(trial: str, task: str, condition: str, run_root: Path) -> dict[str, Any]:
    score_path = score_path_for(run_root, condition)
    score = score_status(score_path)
    metadata = load_run_metadata(run_root) if run_root.exists() else None
    exists = run_root.exists()
    prompt_exists = (run_root / "PROMPT.md").exists()
    marker_exists = exists and (run_root / TASKS[task]["marker"]).exists()
    changed = exists and implementation_changed(run_root, task)
    evidence = exists and has_evidence_artifact(run_root)
    tests_added = added_test_count(run_root, task) if exists else 0
    has_candidate_activity = changed or evidence or tests_added > 0

    if not exists:
        status = "missing"
    elif score and has_candidate_activity:
        status = "scored"
    elif score:
        status = "scored_unmodified"
    elif has_candidate_activity:
        status = "completed_unscored"
    else:
        status = "prepared"

    return {
        "trial": trial,
        "task": task,
        "condition": condition,
        "path": str(run_root),
        "prompt": str(run_root / "PROMPT.md"),
        "status": status,
        "exists": exists,
        "prompt_exists": prompt_exists,
        "marker_exists": marker_exists,
        "implementation_changed": changed,
        "has_evidence_artifact": evidence,
        "added_test_count": tests_added,
        "score_path": str(score_path),
        "score": score,
        "metadata": metadata,
        "metadata_status": metadata.get("status") if metadata else None,
    }


def discover_trials(trials_root: Path) -> list[Path]:
    return sorted(path for path in trials_root.iterdir() if path.is_dir())


def analyze(trials_root: Path, expected_trial_count: int | None) -> dict[str, Any]:
    if not trials_root.exists():
        raise SystemExit(f"trials root not found: {trials_root}")

    trial_dirs = discover_trials(trials_root)
    if expected_trial_count is not None and len(trial_dirs) != expected_trial_count:
        raise SystemExit(
            f"expected {expected_trial_count} trial directories under {trials_root}, found {len(trial_dirs)}"
        )

    runs = []
    for trial_dir in trial_dirs:
        for task in KNOWN_TASKS:
            for condition in CONDITIONS:
                runs.append(run_status(trial_dir.name, task, condition, trial_dir / task / condition))

    status_counts = Counter(run["status"] for run in runs)
    by_condition = {
        condition_key(condition): dict(
            sorted(Counter(run["status"] for run in runs if run["condition"] == condition).items())
        )
        for condition in CONDITIONS
    }
    by_task = {
        task: dict(sorted(Counter(run["status"] for run in runs if run["task"] == task).items()))
        for task in KNOWN_TASKS
    }
    expected_runs = len(trial_dirs) * len(KNOWN_TASKS) * len(CONDITIONS)
    score_json_runs = status_counts["scored"] + status_counts["scored_unmodified"]
    completed_scored_runs = status_counts["scored"]

    return {
        "trials_root": str(trials_root),
        "trial_count": len(trial_dirs),
        "task_count": len(KNOWN_TASKS),
        "expected_runs": expected_runs,
        "score_json_runs": score_json_runs,
        "completed_scored_runs": completed_scored_runs,
        "scored_runs": score_json_runs,
        "unscored_runs": expected_runs - score_json_runs,
        "not_complete_runs": expected_runs - completed_scored_runs,
        "status_counts": dict(sorted(status_counts.items())),
        "by_condition": by_condition,
        "by_task": by_task,
        "pending": [
            {
                "trial": run["trial"],
                "task": run["task"],
                "condition": run["condition"],
                "status": run["status"],
                "path": run["path"],
                "prompt": run["prompt"],
            }
            for run in runs
            if run["status"] != "scored"
        ],
        "runs": runs,
    }


def print_report(result: dict[str, Any], only_pending: bool) -> None:
    print("Skill vs no-skill trial status")
    print(f"Trials root: {result['trials_root']}")
    print(
        f"Volume: {result['trial_count']} trials, {result['task_count']} task families, "
        f"{result['expected_runs']} expected runs"
    )
    print(f"Score JSON: {result['score_json_runs']}/{result['expected_runs']}")
    print(f"Completed scored: {result['completed_scored_runs']}/{result['expected_runs']}")
    print(f"Status counts: {result['status_counts']}")
    print(f"By condition: {result['by_condition']}")
    print(f"By task: {result['by_task']}")

    pending = result["pending"]
    if pending:
        print("\nPending runs:")
        for run in pending:
            print(f"- {run['trial']} {run['task']} {run['condition']}: {run['status']} | {run['path']}")
    elif not only_pending:
        print("\nNo pending runs.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials-root", required=True, help="Directory created by prepare_trials.py")
    parser.add_argument("--expected-trial-count", type=int)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text report")
    parser.add_argument("--json-output", help="Optional path to write status JSON")
    parser.add_argument("--only-pending", action="store_true", help="Only include pending runs in text output")
    parser.add_argument("--strict-complete", action="store_true", help="Exit nonzero unless all expected runs are scored")
    args = parser.parse_args()

    result = analyze(Path(args.trials_root).resolve(), args.expected_trial_count)
    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_report(result, args.only_pending)

    if args.strict_complete and result["not_complete_runs"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
