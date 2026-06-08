#!/usr/bin/env python3
"""Check whether a project left basic eval-driven TDD evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TEST_PATTERNS = ("test_*.py", "*_test.py", "*.test.ts", "*.spec.ts", "*.test.js", "*.spec.js")


def count_test_cases(root: Path) -> int:
    count = 0
    for pattern in TEST_PATTERNS:
        for path in root.rglob(pattern):
            if any(part in {".git", "node_modules", ".venv", "__pycache__"} for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            count += len(re.findall(r"\bdef\s+test_", text))
            count += len(re.findall(r"\bit\(\s*['\"]", text))
            count += len(re.findall(r"\btest\(\s*['\"]", text))
    return count


def report_sections(report: Path) -> list[str]:
    if not report.exists():
        return []
    text = report.read_text(encoding="utf-8", errors="replace").lower()
    sections = []
    for name in ("contract", "red", "green", "regression", "gap"):
        if name in text:
            sections.append(name)
    return sections


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".", help="Project root to inspect")
    parser.add_argument("--min-test-cases", type=int, default=3)
    parser.add_argument("--require-regression-file", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    evals_dir = root / "evals"
    report = root / "AI_TDD_REPORT.md"

    eval_files = []
    if evals_dir.exists():
        eval_files = [
            str(path.relative_to(root))
            for path in evals_dir.rglob("*")
            if path.is_file() and path.name not in {".DS_Store"}
        ]

    test_cases = count_test_cases(root)
    regression_files = [
        path
        for path in [
            root / "tests" / "test_regressions.py",
            root / "tests" / "test_regression.py",
            root / "evals" / "regressions.jsonl",
        ]
        if path.exists()
    ]
    checks = {
        "project_root": str(root),
        "has_report": report.exists(),
        "report_sections": report_sections(report),
        "has_evals_dir": evals_dir.exists(),
        "has_red_log": (evals_dir / "red.log").exists(),
        "has_green_log": (evals_dir / "green.log").exists(),
        "has_regression_file": bool(regression_files),
        "regression_files": [str(path.relative_to(root)) for path in regression_files],
        "eval_files": eval_files,
        "test_case_count": test_cases,
        "min_test_cases": args.min_test_cases,
        "require_regression_file": args.require_regression_file,
    }

    passed = (
        checks["has_report"]
        and checks["has_evals_dir"]
        and checks["has_red_log"]
        and checks["has_green_log"]
        and test_cases >= args.min_test_cases
        and (not args.require_regression_file or checks["has_regression_file"])
    )
    checks["passed"] = passed

    print(json.dumps(checks, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
