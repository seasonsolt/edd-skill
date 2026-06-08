#!/usr/bin/env python3
"""Score multiple suite trials and aggregate cross-trial statistics."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCORE_SUITE = ROOT / "score_suite.py"


def median(values: list[float]) -> float:
    return round(float(statistics.median(values)), 2) if values else 0.0


def mean(values: list[float]) -> float:
    return round(float(statistics.fmean(values)), 2) if values else 0.0


def score_trial(trial_root: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCORE_SUITE), "--runs-root", str(trial_root)],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"score_suite.py failed for {trial_root}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return json.loads((trial_root / "suite-comparison.json").read_text(encoding="utf-8"))


def summarize_trials(trials: list[dict]) -> dict:
    deltas = [trial["summary"]["mean_score_delta"] for trial in trials]
    functional_deltas = [trial["summary"]["mean_functional_delta"] for trial in trials]
    process_deltas = [trial["summary"]["mean_process_delta"] for trial in trials]
    baseline_scores = [trial["summary"]["baseline_mean_score"] for trial in trials]
    skill_scores = [trial["summary"]["with_skill_mean_score"] for trial in trials]

    return {
        "trial_count": len(trials),
        "mean_score_delta": mean(deltas),
        "median_score_delta": median(deltas),
        "mean_functional_delta": mean(functional_deltas),
        "median_functional_delta": median(functional_deltas),
        "mean_process_delta": mean(process_deltas),
        "median_process_delta": median(process_deltas),
        "baseline_mean_score": mean(baseline_scores),
        "baseline_median_score": median(baseline_scores),
        "baseline_worst_mean_score": min(baseline_scores) if baseline_scores else 0,
        "with_skill_mean_score": mean(skill_scores),
        "with_skill_median_score": median(skill_scores),
        "with_skill_worst_mean_score": min(skill_scores) if skill_scores else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials-root",
        required=True,
        help="Directory containing trial subdirectories, each prepared by prepare_suite.py",
    )
    args = parser.parse_args()

    trials_root = Path(args.trials_root).resolve()
    trial_dirs = sorted(path for path in trials_root.iterdir() if path.is_dir())
    if not trial_dirs:
        raise SystemExit(f"no trial directories found under {trials_root}")

    trials = []
    for trial_dir in trial_dirs:
        scored = score_trial(trial_dir)
        trials.append({"trial": trial_dir.name, **scored})

    output = {
        "summary": summarize_trials(trials),
        "trials": trials,
    }
    (trials_root / "trials-summary.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
