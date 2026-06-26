#!/usr/bin/env python3
"""Score baseline and with-skill candidates and print a compact comparison."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
SCORER = ROOT / "score_candidate.py"


def update_run_metadata(run_dir: Path, score: dict, score_path: Path) -> None:
    metadata_path = run_dir / "RUN_METADATA.json"
    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(
        {
            "status": "scored",
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "score_path": str(score_path),
            "score": score["score"],
            "functional_score": score["functional"]["score"],
            "process_score": score["process"]["score"],
            "public_passed": score["functional"]["public_passed"],
            "hidden_passed": score["functional"]["hidden_passed"],
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def score_candidate(candidate: Path, output_path: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCORER), "--candidate", str(candidate), "--json-output", str(output_path)],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if output_path.exists():
        return json.loads(output_path.read_text(encoding="utf-8"))
    raise RuntimeError(
        f"scoring failed for {candidate}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        default=str(REPO_ROOT / "runs" / "skill-vs-no-skill"),
        help="Directory containing baseline and with-skill runs",
    )
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    baseline = runs_root / "baseline"
    with_skill = runs_root / "with-skill"
    if not baseline.exists() or not with_skill.exists():
        raise SystemExit(f"expected {baseline} and {with_skill}; run prepare_runs.py first")

    baseline_score_path = runs_root / "baseline.score.json"
    skill_score_path = runs_root / "with-skill.score.json"
    baseline_score = score_candidate(baseline, baseline_score_path)
    skill_score = score_candidate(with_skill, skill_score_path)
    update_run_metadata(baseline, baseline_score, baseline_score_path)
    update_run_metadata(with_skill, skill_score, skill_score_path)

    comparison = {
        "baseline": {
            "score": baseline_score["score"],
            "functional": baseline_score["functional"]["score"],
            "process": baseline_score["process"]["score"],
            "public_passed": baseline_score["functional"]["public_passed"],
            "hidden_passed": baseline_score["functional"]["hidden_passed"],
        },
        "with_skill": {
            "score": skill_score["score"],
            "functional": skill_score["functional"]["score"],
            "process": skill_score["process"]["score"],
            "public_passed": skill_score["functional"]["public_passed"],
            "hidden_passed": skill_score["functional"]["hidden_passed"],
        },
    }
    comparison["delta"] = {
        "score": comparison["with_skill"]["score"] - comparison["baseline"]["score"],
        "functional": comparison["with_skill"]["functional"] - comparison["baseline"]["functional"],
        "process": comparison["with_skill"]["process"] - comparison["baseline"]["process"],
    }

    (runs_root / "comparison.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
