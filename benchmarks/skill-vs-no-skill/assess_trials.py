#!/usr/bin/env python3
"""Assess whether trial results support a skill-effect claim."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def mean(values: list[float]) -> float:
    return round(float(statistics.fmean(values)), 2) if values else 0.0


def median(values: list[float]) -> float:
    return round(float(statistics.median(values)), 2) if values else 0.0


def rate(count: int, total: int) -> float:
    return round((count / total) * 100, 2) if total else 0.0


def load_trials_summary(path: Path) -> dict:
    if path.is_dir():
        path = path / "trials-summary.json"
    if not path.exists():
        raise SystemExit(f"trials summary not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assess(data: dict, min_trials: int, min_task_families: int, min_process_delta: float) -> dict:
    trials = data.get("trials", [])
    task_names = sorted({task for trial in trials for task in trial.get("tasks", {})})
    process_deltas = [trial["summary"]["mean_process_delta"] for trial in trials]
    functional_deltas = [trial["summary"]["mean_functional_delta"] for trial in trials]
    score_deltas = [trial["summary"]["mean_score_delta"] for trial in trials]

    baseline_hidden = 0
    with_skill_hidden = 0
    hidden_total = 0
    for trial in trials:
        for result in trial.get("tasks", {}).values():
            hidden_total += 1
            baseline_hidden += 1 if result["baseline"]["hidden_passed"] else 0
            with_skill_hidden += 1 if result["with_skill"]["hidden_passed"] else 0

    credible_volume = len(trials) >= min_trials and len(task_names) >= min_task_families
    process_win_rate = rate(sum(1 for value in process_deltas if value > 0), len(process_deltas))
    functional_win_rate = rate(sum(1 for value in functional_deltas if value > 0), len(functional_deltas))
    functional_regression_rate = rate(sum(1 for value in functional_deltas if value < 0), len(functional_deltas))
    hidden_delta = with_skill_hidden - baseline_hidden

    median_process_delta = median(process_deltas)
    median_functional_delta = median(functional_deltas)
    supports_process = credible_volume and median_process_delta >= min_process_delta and process_win_rate >= 80
    supports_functional = credible_volume and median_functional_delta > 0 and hidden_delta > 0 and functional_win_rate >= 60
    functional_regression = credible_volume and (median_functional_delta < 0 or hidden_delta < 0)

    if not credible_volume:
        verdict = "insufficient_evidence"
    elif functional_regression:
        verdict = "functional_regression"
    elif supports_functional and supports_process:
        verdict = "functional_and_process_supported"
    elif supports_functional:
        verdict = "functional_supported"
    elif supports_process:
        verdict = "process_only_supported"
    else:
        verdict = "not_supported"

    return {
        "verdict": verdict,
        "criteria": {
            "min_trials": min_trials,
            "min_task_families": min_task_families,
            "min_process_delta": min_process_delta,
        },
        "observed": {
            "trial_count": len(trials),
            "task_family_count": len(task_names),
            "task_families": task_names,
            "mean_score_delta": mean(score_deltas),
            "median_score_delta": median(score_deltas),
            "mean_functional_delta": mean(functional_deltas),
            "median_functional_delta": median_functional_delta,
            "mean_process_delta": mean(process_deltas),
            "median_process_delta": median_process_delta,
            "process_win_rate": process_win_rate,
            "functional_win_rate": functional_win_rate,
            "functional_regression_rate": functional_regression_rate,
            "baseline_hidden_passed": baseline_hidden,
            "with_skill_hidden_passed": with_skill_hidden,
            "hidden_total": hidden_total,
            "hidden_pass_delta": hidden_delta,
        },
        "supports": {
            "credible_volume": credible_volume,
            "process_effect": supports_process,
            "functional_effect": supports_functional,
            "functional_regression": functional_regression,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials-root",
        required=True,
        help="Directory containing trials-summary.json, or the JSON file itself",
    )
    parser.add_argument("--min-trials", type=int, default=5)
    parser.add_argument("--min-task-families", type=int, default=4)
    parser.add_argument("--min-process-delta", type=float, default=20)
    parser.add_argument("--json-output", help="Optional path to write the assessment JSON")
    args = parser.parse_args()

    result = assess(
        load_trials_summary(Path(args.trials_root).resolve()),
        min_trials=args.min_trials,
        min_task_families=args.min_task_families,
        min_process_delta=args.min_process_delta,
    )

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
