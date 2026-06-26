#!/usr/bin/env python3
"""Run a prepared sustainability matrix with an OpenAI-compatible chat API."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
EDD_SKILL_PATH = REPO_ROOT / ".agents" / "skills" / "eval-driven-ai-tdd" / "SKILL.md"
ALLOWED_WRITE_PREFIXES = (
    "tool_call_planner/",
    "tests/",
    "evals/",
)
ALLOWED_WRITE_FILES = {
    "EDD_REPORT.md",
    "AI_TDD_REPORT.md",
}
MAX_WRITTEN_FILE_BYTES = 200_000


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_runs(runs_root: Path) -> list[Path]:
    return sorted(path.parent for path in runs_root.rglob("RUN_METADATA.json"))


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_prompt(run_dir: Path, metadata: dict[str, Any]) -> str:
    files = {
        "PROMPT.md": read_optional(run_dir / "PROMPT.md"),
        "TASK.md": read_optional(run_dir / "TASK.md"),
        "tool_call_planner/planner.py": read_optional(run_dir / "tool_call_planner" / "planner.py"),
        "tests/test_public_planner.py": read_optional(run_dir / "tests" / "test_public_planner.py"),
    }
    file_blocks = "\n\n".join(
        f"### {path}\n```text\n{content}\n```" for path, content in files.items()
    )
    skill_block = ""
    if metadata.get("condition") == "with-skill":
        skill_text = read_optional(EDD_SKILL_PATH)
        skill_block = f"""
EDD Skill instructions for this run:

```text
{skill_text}
```
"""

    return f"""You are completing a small Python coding task in a repository.

Return only a JSON object with this shape:

{{
  "files": [
    {{"path": "relative/path.py", "content": "full file content"}}
  ],
  "notes": "brief summary"
}}

Rules:
- Do not return Markdown fences.
- Include full contents for every file you create or modify.
- You may modify files under `tool_call_planner/`, files under `tests/`, files under `evals/`, and `EDD_REPORT.md`.
- Keep the public API exactly as specified.
- Do not mention hidden tests or scorer internals.

Current task files:

{file_blocks}

{skill_block}
"""


def call_chat_api(base_url: str, api_key: str, model: str, prompt: str, timeout: int, retries: int) -> str:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise coding agent. Return machine-readable JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 12000,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(min(2 * attempt, 10))
    raise RuntimeError(f"chat API failed after {retries} attempts: {last_error}")


def extract_json(text: str) -> tuple[dict[str, Any], str]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned), "strict"
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start = cleaned.find("{")
        if start < 0:
            raise
        parsed, end = decoder.raw_decode(cleaned[start:])
        trailing = cleaned[start + end :].strip()
        if trailing:
            raise ValueError("model response contained non-JSON trailing content after first JSON object")
        return parsed, "fallback_raw_decode"


def is_allowed_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("/")
    if ".." in Path(normalized).parts:
        return False
    return normalized in ALLOWED_WRITE_FILES or normalized.startswith(ALLOWED_WRITE_PREFIXES)


def apply_files(run_dir: Path, response: dict[str, Any]) -> list[str]:
    files = response.get("files")
    if not isinstance(files, list):
        raise ValueError("model response must contain a files list")

    written = []
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("each file item must be an object")
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError("each file item needs string path and content")
        content_size = len(content.encode("utf-8"))
        if content_size > MAX_WRITTEN_FILE_BYTES:
            raise ValueError(
                f"model tried to write oversized file: {path} ({content_size} bytes > {MAX_WRITTEN_FILE_BYTES})"
            )
        if not is_allowed_path(path):
            raise ValueError(f"model tried to write disallowed path: {path}")
        destination = run_dir / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def run_one(run_dir: Path, base_url: str, api_key: str, timeout: int, retries: int) -> dict[str, Any]:
    metadata_path = run_dir / "RUN_METADATA.json"
    metadata = load_json(metadata_path)
    model = metadata.get("model_id")
    if not model:
        raise ValueError(f"run has no model_id: {run_dir}")

    prompt = build_prompt(run_dir, metadata)
    raw = call_chat_api(base_url, api_key, model, prompt, timeout, retries)
    response, parse_mode = extract_json(raw)
    written = apply_files(run_dir, response)
    metadata["status"] = "completed"
    metadata["completed_by"] = "run_model_matrix.py"
    metadata["response_parse_mode"] = parse_mode
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "MODEL_RESPONSE.json").write_text(
        json.dumps(
            {"raw": raw, "parsed": response, "parse_mode": parse_mode, "written": written},
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return {
        "run_dir": str(run_dir),
        "model": model,
        "written": written,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--limit", type=int, help="Run only the first N discovered runs")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise SystemExit("OPENAI_BASE_URL and OPENAI_API_KEY must be set")

    run_dirs = discover_runs(Path(args.runs_root).resolve())
    if args.limit is not None:
        run_dirs = run_dirs[: args.limit]
    if not run_dirs:
        raise SystemExit("no prepared runs found")

    results = []
    for index, run_dir in enumerate(run_dirs, start=1):
        print(f"[{index}/{len(run_dirs)}] running {run_dir}", flush=True)
        results.append(run_one(run_dir, base_url, api_key, args.timeout, args.retries))

    print(json.dumps({"run_count": len(results), "runs": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
