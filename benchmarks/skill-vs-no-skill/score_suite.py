#!/usr/bin/env python3
"""Score every task pair and aggregate suite-level deltas."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
SCORER = ROOT / "score_candidate.py"
KNOWN_TASKS = ("quote-engine", "feature-flags", "tool-call-planner", "evidence-answerer")


def score_candidate(task: str, candidate: Path, output_path: Path) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCORER),
            "--task",
            task,
            "--candidate",
            str(candidate),
            "--json-output",
            str(output_path),
        ],
        text=True,
        capture_output=True,
    )
    if output_path.exists():
        return json.loads(output_path.read_text(encoding="utf-8"))
    raise RuntimeError(
        f"scoring failed for {task} {candidate}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )


def compact(score: dict) -> dict:
    return {
        "score": score["score"],
        "functional": score["functional"]["score"],
        "process": score["process"]["score"],
        "public_passed": score["functional"]["public_passed"],
        "hidden_passed": score["functional"]["hidden_passed"],
    }


def mean(values: list[int]) -> float:
    return round(statistics.fmean(values), 2) if values else 0.0


def median(values: list[int]) -> float:
    return round(float(statistics.median(values)), 2) if values else 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        default=str(REPO_ROOT / "runs" / "skill-vs-no-skill-suite"),
        help="Directory containing task/baseline and task/with-skill runs",
    )
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    tasks = [task for task in KNOWN_TASKS if (runs_root / task).exists()]
    if not tasks:
        tasks = list(KNOWN_TASKS)

    results = {}
    baseline_scores = []
    skill_scores = []
    functional_deltas = []
    process_deltas = []

    for task in tasks:
        task_root = runs_root / task
        baseline = task_root / "baseline"
        with_skill = task_root / "with-skill"
        if not baseline.exists() or not with_skill.exists():
            raise SystemExit(f"expected paired runs under {task_root}; run prepare_suite.py first")

        baseline_score = score_candidate(task, baseline, task_root / "baseline.score.json")
        skill_score = score_candidate(task, with_skill, task_root / "with-skill.score.json")
        task_result = {
            "baseline": compact(baseline_score),
            "with_skill": compact(skill_score),
        }
        task_result["delta"] = {
            "score": task_result["with_skill"]["score"] - task_result["baseline"]["score"],
            "functional": task_result["with_skill"]["functional"] - task_result["baseline"]["functional"],
            "process": task_result["with_skill"]["process"] - task_result["baseline"]["process"],
        }
        results[task] = task_result
        baseline_scores.append(task_result["baseline"]["score"])
        skill_scores.append(task_result["with_skill"]["score"])
        functional_deltas.append(task_result["delta"]["functional"])
        process_deltas.append(task_result["delta"]["process"])

    summary = {
        "task_count": len(results),
        "baseline_mean_score": mean(baseline_scores),
        "baseline_median_score": median(baseline_scores),
        "baseline_worst_score": min(baseline_scores) if baseline_scores else 0,
        "with_skill_mean_score": mean(skill_scores),
        "with_skill_median_score": median(skill_scores),
        "with_skill_worst_score": min(skill_scores) if skill_scores else 0,
        "mean_score_delta": round(mean(skill_scores) - mean(baseline_scores), 2),
        "median_score_delta": round(median(skill_scores) - median(baseline_scores), 2),
        "mean_functional_delta": mean(functional_deltas),
        "mean_process_delta": mean(process_deltas),
        "baseline_hidden_pass_rate": mean([100 if r["baseline"]["hidden_passed"] else 0 for r in results.values()]),
        "with_skill_hidden_pass_rate": mean([100 if r["with_skill"]["hidden_passed"] else 0 for r in results.values()]),
    }
    output = {"summary": summary, "tasks": results}
    (runs_root / "suite-comparison.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
