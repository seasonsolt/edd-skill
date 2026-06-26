from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_run_metadata(
    run_dir: Path,
    *,
    trial: str | None,
    task: str,
    condition: str,
    prompt_prefix: str,
    model_id: str | None = None,
    model_provider: str | None = None,
    runner: str = "manual",
    extra: dict[str, Any] | None = None,
) -> None:
    metadata = {
        "trial": trial,
        "task": task,
        "condition": condition,
        "prompt_prefix": prompt_prefix,
        "model_id": model_id,
        "model_provider": model_provider,
        "runner": runner,
        "status": "prepared",
        "prepared_at": utc_now(),
    }
    if extra:
        metadata.update(extra)
    (run_dir / "RUN_METADATA.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
