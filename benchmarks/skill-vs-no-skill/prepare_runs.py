#!/usr/bin/env python3
"""Prepare clean baseline and with-skill run directories."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TASK_ROOT = ROOT / "task"
TASK_PROMPT = ROOT / "task_prompt.md"


def copy_task(destination: Path, prompt: str) -> None:
    shutil.copytree(TASK_ROOT, destination)
    (destination / "PROMPT.md").write_text(prompt, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        default=str(REPO_ROOT / "runs" / "skill-vs-no-skill"),
        help="Directory where baseline and with-skill runs are created",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing run directories")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    baseline = runs_root / "baseline"
    with_skill = runs_root / "with-skill"

    if runs_root.exists() and args.force:
        shutil.rmtree(runs_root)
    elif baseline.exists() or with_skill.exists():
        raise SystemExit(f"{runs_root} already contains runs; pass --force to replace them")

    runs_root.mkdir(parents=True, exist_ok=True)
    base_prompt = TASK_PROMPT.read_text(encoding="utf-8")
    skill_prompt = "Use $eval-driven-ai-tdd.\n\n" + base_prompt

    copy_task(baseline, base_prompt)
    copy_task(with_skill, skill_prompt)

    print(f"created {baseline}")
    print(f"created {with_skill}")
    print("give each agent only its run directory and PROMPT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
