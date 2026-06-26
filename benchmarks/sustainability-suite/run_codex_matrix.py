#!/usr/bin/env python3
"""Run a prepared sustainability matrix with Codex CLI.

This runner is useful when Codex auth is available locally but OpenAI-compatible
API environment variables are not. It uses the same prompt construction and file
application rules as run_model_matrix.py, so scoring remains comparable.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import run_model_matrix


def run_codex(prompt: str, run_dir: Path, model: str, timeout: int) -> tuple[str, int, str, str]:
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".txt", delete=False) as output:
        output_path = Path(output.name)

    command = [
        "codex",
        "exec",
        "--cd",
        str(run_dir),
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--output-last-message",
        str(output_path),
    ]
    if model:
        command.extend(["--model", model])
    command.append(prompt)

    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        raw = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout
        return raw, completed.returncode, completed.stdout, completed.stderr
    finally:
        output_path.unlink(missing_ok=True)


def run_one(run_dir: Path, timeout: int) -> dict[str, Any]:
    metadata_path = run_dir / "RUN_METADATA.json"
    metadata = run_model_matrix.load_json(metadata_path)
    task = metadata.get("task")
    if not isinstance(task, str):
        raise ValueError(f"run metadata has invalid task: {task}")
    model = metadata.get("model_id") or ""
    prompt = run_model_matrix.build_prompt(run_dir, metadata)
    raw, returncode, stdout, stderr = run_codex(prompt, run_dir, model, timeout)
    if returncode != 0:
        metadata["status"] = "failed"
        metadata["completed_by"] = "run_codex_matrix.py"
        metadata["codex_returncode"] = returncode
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (run_dir / "CODEX_RUN_ERROR.txt").write_text(
            f"returncode: {returncode}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n\nLAST_MESSAGE:\n{raw}\n",
            encoding="utf-8",
        )
        raise RuntimeError(f"codex failed for {run_dir} with returncode {returncode}")

    response, parse_mode = run_model_matrix.extract_json(raw)
    written = run_model_matrix.apply_files(run_dir, response, task)
    metadata["status"] = "completed"
    metadata["completed_by"] = "run_codex_matrix.py"
    metadata["response_parse_mode"] = parse_mode
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "MODEL_RESPONSE.json").write_text(
        json.dumps(
            {
                "raw": raw,
                "parsed": response,
                "parse_mode": parse_mode,
                "written": written,
                "codex_stdout_tail": stdout[-4000:],
                "codex_stderr_tail": stderr[-4000:],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"run_dir": str(run_dir), "model": model, "written": written, "parse_mode": parse_mode}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--limit", type=int, help="Run only the first N discovered runs")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    run_dirs = run_model_matrix.discover_runs(Path(args.runs_root).resolve())
    if args.limit is not None:
        run_dirs = run_dirs[: args.limit]
    if not run_dirs:
        raise SystemExit("no prepared runs found")

    results = []
    for index, run_dir in enumerate(run_dirs, start=1):
        print(f"[{index}/{len(run_dirs)}] running {run_dir}", flush=True)
        results.append(run_one(run_dir, args.timeout))

    print(json.dumps({"run_count": len(results), "runs": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
