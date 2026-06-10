#!/usr/bin/env python3
"""Prepare multiple clean suite trials for paired agent runs."""

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
    "tool-call-planner-v2": {
        "starter_root": ROOT / "tasks" / "tool-call-planner-v2",
        "prompt": ROOT / "tasks" / "tool-call-planner-v2" / "task_prompt.md",
    },
    "evidence-answerer": {
        "starter_root": ROOT / "tasks" / "evidence-answerer",
        "prompt": ROOT / "tasks" / "evidence-answerer" / "task_prompt.md",
    },
}


def copy_task(source: Path, destination: Path, prompt: str) -> None:
    shutil.copytree(source, destination)
    (destination / "PROMPT.md").write_text(prompt, encoding="utf-8")


def prepare_trial(trial_root: Path) -> list[Path]:
    created = []
    for task_name, task in TASKS.items():
        task_root = trial_root / task_name
        baseline = task_root / "baseline"
        with_skill = task_root / "with-skill"
        base_prompt = task["prompt"].read_text(encoding="utf-8")
        skill_prompt = "Use $eval-driven-ai-tdd.\n\n" + base_prompt

        copy_task(task["starter_root"], baseline, base_prompt)
        copy_task(task["starter_root"], with_skill, skill_prompt)
        created.extend([baseline, with_skill])
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials-root",
        default=str(REPO_ROOT / "runs" / "skill-vs-no-skill-trials"),
        help="Directory where trial-XXX directories are created",
    )
    parser.add_argument("--trial-count", type=int, default=5)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--force", action="store_true", help="Replace existing selected trial directories")
    parser.add_argument("--clean-root", action="store_true", help="Delete the trials root before preparing trials")
    args = parser.parse_args()

    if args.trial_count <= 0:
        raise SystemExit("--trial-count must be positive")
    if args.start_index <= 0:
        raise SystemExit("--start-index must be positive")

    trials_root = Path(args.trials_root).resolve()
    if trials_root.exists() and args.clean_root:
        shutil.rmtree(trials_root)
    trials_root.mkdir(parents=True, exist_ok=True)
    all_created = []

    for offset in range(args.trial_count):
        trial_number = args.start_index + offset
        trial_root = trials_root / f"trial-{trial_number:03d}"
        if trial_root.exists() and args.force:
            shutil.rmtree(trial_root)
        elif trial_root.exists():
            raise SystemExit(f"{trial_root} already exists; pass --force to replace it")
        trial_root.mkdir(parents=True)
        created = prepare_trial(trial_root)
        all_created.extend(created)
        print(f"created {trial_root}")

    print()
    print(f"prepared {args.trial_count} trials under {trials_root}")
    print(f"agent runs required: {len(all_created)}")
    for path in all_created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
