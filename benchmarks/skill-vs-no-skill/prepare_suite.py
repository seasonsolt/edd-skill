#!/usr/bin/env python3
"""Prepare clean paired runs for every benchmark task."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TASKS = {
    "quote-engine": {
        "starter_root": ROOT / "task",
        "prompt": ROOT / "task_prompt.md",
    },
    "feature-flags": {
        "starter_root": ROOT / "tasks" / "feature-flags",
        "prompt": ROOT / "tasks" / "feature-flags" / "task_prompt.md",
    },
    "tool-call-planner": {
        "starter_root": ROOT / "tasks" / "tool-call-planner",
        "prompt": ROOT / "tasks" / "tool-call-planner" / "task_prompt.md",
    },
    "evidence-answerer": {
        "starter_root": ROOT / "tasks" / "evidence-answerer",
        "prompt": ROOT / "tasks" / "evidence-answerer" / "task_prompt.md",
    },
}


def copy_task(source: Path, destination: Path, prompt: str) -> None:
    shutil.copytree(source, destination)
    (destination / "PROMPT.md").write_text(prompt, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        default=str(REPO_ROOT / "runs" / "skill-vs-no-skill-suite"),
        help="Directory where task/baseline and task/with-skill runs are created",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing suite runs")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    if runs_root.exists() and args.force:
        shutil.rmtree(runs_root)
    elif runs_root.exists() and any(runs_root.iterdir()):
        raise SystemExit(f"{runs_root} already exists; pass --force to replace it")

    runs_root.mkdir(parents=True, exist_ok=True)
    for task_name, task in TASKS.items():
        task_root = runs_root / task_name
        baseline = task_root / "baseline"
        with_skill = task_root / "with-skill"
        base_prompt = task["prompt"].read_text(encoding="utf-8")
        skill_prompt = "Use $eval-driven-ai-tdd.\n\n" + base_prompt

        copy_task(task["starter_root"], baseline, base_prompt)
        copy_task(task["starter_root"], with_skill, skill_prompt)
        print(f"created {baseline}")
        print(f"created {with_skill}")

    print("give each agent only its own run directory and PROMPT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
