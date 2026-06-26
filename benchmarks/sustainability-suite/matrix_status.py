#!/usr/bin/env python3
"""Report completion status for a sustainability model matrix."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_RUN_FILES = (
    "RUN_METADATA.json",
    "PROMPT.md",
    "TASK.md",
    "tool_call_planner/planner.py",
    "tests/test_public_planner.py",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_runs(runs_root: Path) -> list[Path]:
    return sorted(path.parent for path in runs_root.rglob("RUN_METADATA.json"))


def implementation_changed(run_dir: Path) -> bool:
    planner = run_dir / "tool_call_planner" / "planner.py"
    if not planner.exists():
        return False
    text = planner.read_text(encoding="utf-8")
    return "raise NotImplementedError" not in text


def added_agent_tests(run_dir: Path) -> int:
    tests_dir = run_dir / "tests"
    if not tests_dir.exists():
        return 0
    public_test = tests_dir / "test_public_planner.py"
    count = 0
    for path in tests_dir.rglob("test_*.py"):
        if path == public_test:
            text = path.read_text(encoding="utf-8")
            count += max(0, text.count("def test_") - 2)
        else:
            count += path.read_text(encoding="utf-8").count("def test_")
    return count


def run_status(run_dir: Path) -> dict[str, Any]:
    metadata = load_json(run_dir / "RUN_METADATA.json")
    missing_files = [name for name in REQUIRED_RUN_FILES if not (run_dir / name).exists()]
    has_score = (run_dir / "seeded-bugs.score.json").exists()
    changed = implementation_changed(run_dir)
    test_count = added_agent_tests(run_dir)

    if missing_files:
        status = "invalid"
    elif has_score:
        status = "scored"
    elif changed or test_count > 0:
        status = "completed_unscored"
    else:
        status = "prepared"

    return {
        "run_dir": str(run_dir),
        "status": status,
        "metadata": metadata,
        "implementation_changed": changed,
        "added_agent_tests": test_count,
        "has_seeded_bug_score": has_score,
        "missing_files": missing_files,
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(record["status"] for record in records)
    by_group: Counter[str] = Counter()
    for record in records:
        metadata = record["metadata"]
        group = f"{metadata['model_tier']}/{metadata['condition']}/{record['status']}"
        by_group[group] += 1
    return {
        "run_count": len(records),
        "by_status": dict(sorted(by_status.items())),
        "by_group_status": dict(sorted(by_group.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--json-output", help="Optional path to write JSON status")
    parser.add_argument("--strict-complete", action="store_true", help="Exit non-zero unless every run is completed or scored")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    run_dirs = discover_runs(runs_root)
    if not run_dirs:
        raise SystemExit(f"no RUN_METADATA.json files found under {runs_root}")

    records = [run_status(run_dir) for run_dir in run_dirs]
    output = {
        "runs_root": str(runs_root),
        "summary": summarize(records),
        "runs": records,
    }
    text = json.dumps(output, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")

    if args.strict_complete and any(record["status"] == "prepared" for record in records):
        return 1
    if any(record["status"] == "invalid" for record in records):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
