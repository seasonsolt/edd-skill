#!/usr/bin/env python3
"""Prepare the two-model sustainability benchmark run matrix."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "model_matrix.json"
DEFAULT_TASKS = ("agent-policy-evolution", "subscription-billing-evolution")
TASKS = {
    "agent-policy-evolution": {
        "starter_root": ROOT.parent / "skill-vs-no-skill" / "tasks" / "tool-call-planner",
        "prompt": ROOT / "agent-policy-evolution" / "task_prompt.md",
    },
    "subscription-billing-evolution": {
        "starter_root": ROOT / "tasks" / "subscription-billing",
        "prompt": ROOT / "subscription-billing-evolution" / "task_prompt.md",
    },
}


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_config(config: dict) -> None:
    tiers = config.get("model_tiers", [])
    conditions = config.get("conditions", [])
    if not tiers:
        raise SystemExit("model_matrix.json must define at least one model tier")
    if not conditions:
        raise SystemExit("model_matrix.json must define at least one condition")
    for tier in tiers:
        if not tier.get("tier") or not tier.get("label"):
            raise SystemExit("each model tier must define tier and label")
    for condition in conditions:
        if not condition.get("condition"):
            raise SystemExit("each condition must define condition")


def write_run_metadata(
    run_dir: Path,
    trial: str,
    task: str,
    tier: dict,
    condition: dict,
) -> None:
    metadata = {
        "trial": trial,
        "task": task,
        "model_tier": tier["tier"],
        "model_label": tier["label"],
        "model_id": tier.get("model_id"),
        "condition": condition["condition"],
        "prompt_prefix": condition.get("prompt_prefix", ""),
        "status": "prepared",
    }
    (run_dir / "RUN_METADATA.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def prepare_run(
    run_dir: Path,
    task: str,
    tier: dict,
    condition: dict,
) -> None:
    task_config = TASKS.get(task)
    if task_config is None:
        raise SystemExit(f"unknown task: {task}")

    starter_root = task_config["starter_root"]
    if not starter_root.exists():
        raise SystemExit(f"starter root not found: {starter_root}")

    shutil.copytree(starter_root, run_dir)
    base_prompt = task_config["prompt"].read_text(encoding="utf-8")
    prompt = condition.get("prompt_prefix", "") + base_prompt
    (run_dir / "PROMPT.md").write_text(prompt, encoding="utf-8")


def prepare_matrix(runs_root: Path, config: dict, tasks: list[str], trial_count: int) -> list[Path]:
    created = []
    for trial_index in range(1, trial_count + 1):
        trial = f"trial-{trial_index:03d}"
        for task in tasks:
            for tier in config["model_tiers"]:
                for condition in config["conditions"]:
                    run_dir = runs_root / trial / task / tier["tier"] / condition["condition"]
                    prepare_run(run_dir, task, tier, condition)
                    write_run_metadata(run_dir, trial, task, tier, condition)
                    created.append(run_dir)
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        default=str(ROOT.parents[1] / "runs" / "sustainability-suite-model-matrix"),
        help="Directory where model-tiered run folders are created",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--trial-count", type=int)
    parser.add_argument("--tasks", nargs="+", default=list(DEFAULT_TASKS))
    parser.add_argument("--force", action="store_true", help="Replace an existing runs root")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    validate_config(config)
    trial_count = args.trial_count or int(config.get("minimum_trials", 5))
    if trial_count <= 0:
        raise SystemExit("--trial-count must be positive")

    runs_root = Path(args.runs_root).resolve()
    if runs_root.exists() and args.force:
        shutil.rmtree(runs_root)
    elif runs_root.exists() and any(runs_root.iterdir()):
        raise SystemExit(f"{runs_root} already exists; pass --force to replace it")
    runs_root.mkdir(parents=True, exist_ok=True)

    created = prepare_matrix(runs_root, config, args.tasks, trial_count)
    summary = {
        "runs_root": str(runs_root),
        "config": str(config_path),
        "trial_count": trial_count,
        "task_count": len(args.tasks),
        "model_tier_count": len(config["model_tiers"]),
        "condition_count": len(config["conditions"]),
        "run_count": len(created),
        "runs": [str(path) for path in created],
        "instructions": "Give each agent only its own run directory and PROMPT.md. Do not expose scorer scripts, seed implementations, sibling runs, or prior results.",
    }
    (runs_root / "matrix-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
