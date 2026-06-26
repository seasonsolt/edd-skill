#!/usr/bin/env python3
"""Score a prepared sustainability model matrix."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
SEED_SCORERS = {
    "agent-policy-evolution": ROOT / "agent-policy-evolution" / "score_seeded_bugs.py",
    "subscription-billing-evolution": ROOT / "subscription-billing-evolution" / "score_seeded_bugs.py",
}
FUNCTIONAL_SCORERS = {
    "agent-policy-evolution": {
        "script": REPO_ROOT / "benchmarks" / "skill-vs-no-skill" / "score_candidate.py",
        "task": "tool-call-planner",
    },
    "subscription-billing-evolution": {
        "script": ROOT / "subscription-billing-evolution" / "score_billing_candidate.py",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mean(values: list[float]) -> float:
    return round(float(statistics.fmean(values)), 2) if values else 0.0


def discover_runs(runs_root: Path) -> list[Path]:
    return sorted(path.parent for path in runs_root.rglob("RUN_METADATA.json"))


def score_run(run_dir: Path) -> dict[str, Any]:
    metadata = load_json(run_dir / "RUN_METADATA.json")
    task = metadata["task"]
    scorer = SEED_SCORERS.get(task)
    if scorer is None:
        raise SystemExit(f"no seeded-bug scorer configured for task: {task}")

    output_path = run_dir / "seeded-bugs.score.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(scorer),
            "--candidate",
            str(run_dir),
            "--json-output",
            str(output_path),
        ],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if not output_path.exists():
        raise RuntimeError(
            f"scoring failed for {run_dir}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    score = load_json(output_path)
    functional = score_functional(run_dir, task)
    return {
        "run_dir": str(run_dir),
        "metadata": metadata,
        "functional": functional,
        "seeded_bugs": {
            "score": score["score"],
            "max_score": score["max_score"],
            "killed_count": score["killed_count"],
            "seed_count": score["seed_count"],
        },
    }


def score_functional(run_dir: Path, task: str) -> dict[str, Any]:
    scorer = FUNCTIONAL_SCORERS.get(task)
    if scorer is None:
        return {}

    output_path = run_dir / "functional.score.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(scorer["script"]),
            *(["--task", scorer["task"]] if "task" in scorer else []),
            "--candidate",
            str(run_dir),
            "--json-output",
            str(output_path),
        ],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if not output_path.exists():
        raise RuntimeError(
            f"functional scoring failed for {run_dir}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    result = load_json(output_path)
    return {
        "score": result["functional"]["score"],
        "max_score": result["functional"]["max_score"],
        "public_passed": result["functional"]["public_passed"],
        "hidden_passed": result["functional"]["hidden_passed"],
        "process_score": result["process"]["score"],
        "process_max_score": result["process"]["max_score"],
        "total_score": result["score"],
        "total_max_score": result["max_score"],
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        metadata = result["metadata"]
        groups[(metadata["model_tier"], metadata["condition"])].append(result)

    by_group = {}
    for (model_tier, condition), runs in sorted(groups.items()):
        scores = [run["seeded_bugs"]["score"] for run in runs]
        killed = [run["seeded_bugs"]["killed_count"] for run in runs]
        functional_scores = [run["functional"].get("score", 0) for run in runs if run.get("functional")]
        process_scores = [run["functional"].get("process_score", 0) for run in runs if run.get("functional")]
        hidden_passes = [1 if run["functional"].get("hidden_passed") else 0 for run in runs if run.get("functional")]
        key = f"{model_tier}/{condition}"
        by_group[key] = {
            "run_count": len(runs),
            "mean_seeded_bug_score": mean(scores),
            "mean_killed_count": mean(killed),
            "mean_functional_score": mean(functional_scores),
            "hidden_passed": sum(hidden_passes),
            "mean_process_score": mean(process_scores),
        }

    deltas = {}
    tiers = sorted({result["metadata"]["model_tier"] for result in results})
    for tier in tiers:
        baseline = by_group.get(f"{tier}/baseline", {}).get("mean_seeded_bug_score")
        with_skill = by_group.get(f"{tier}/with-skill", {}).get("mean_seeded_bug_score")
        if baseline is not None and with_skill is not None:
            deltas[f"{tier}_skill_delta"] = round(with_skill - baseline, 2)

    if "sota_skill_delta" in deltas and "economical_skill_delta" in deltas:
        deltas["skill_leverage_gap"] = round(
            deltas["economical_skill_delta"] - deltas["sota_skill_delta"],
            2,
        )

    return {
        "run_count": len(results),
        "groups": by_group,
        "deltas": deltas,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--json-output", help="Optional path to write JSON results")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    run_dirs = discover_runs(runs_root)
    if not run_dirs:
        raise SystemExit(f"no RUN_METADATA.json files found under {runs_root}")

    results = [score_run(run_dir) for run_dir in run_dirs]
    output = {
        "runs_root": str(runs_root),
        "summary": summarize(results),
        "runs": results,
    }
    text = json.dumps(output, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
