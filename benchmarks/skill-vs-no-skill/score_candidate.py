#!/usr/bin/env python3
"""Score a completed candidate for the skill-vs-no-skill benchmark."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TASKS = {
    "quote-engine": {
        "starter_root": ROOT / "task",
        "marker": "quote_engine/quote.py",
        "starter_public_test": ROOT / "task" / "tests" / "test_public_quote.py",
        "hidden_test": ROOT / "hidden_tests" / "test_hidden_quote.py",
        "edge_keywords": {
            "boundary": ["usage_units=250", "partial", "201", "multi_tier", "multi-tier", "inclusive"],
            "minimum": ["minimum", "minimum_cents"],
            "discount": ['"type": "percent"', '"type": "fixed"', "percent", "fixed"],
            "rounding": ["round", "half", "3333", "333", "5000", "825", "1250"],
            "invalid": ["invalid", "raises", "ValueError"],
        },
    },
    "feature-flags": {
        "starter_root": ROOT / "tasks" / "feature-flags",
        "marker": "feature_flags/evaluator.py",
        "starter_public_test": ROOT / "tasks" / "feature-flags" / "tests" / "test_public_evaluator.py",
        "hidden_test": ROOT / "hidden_tests" / "test_hidden_feature_flags.py",
        "edge_keywords": {
            "precedence": ["denylist", "allowlist", "precedence"],
            "rules": ['"op": "equals"', '"op": "in"', '"op": "gte"', '"op": "lte"', "rule:"],
            "rollout": ["rollout", "bucket", "sha256", "5000"],
            "missing": ["missing", "does not match", "default"],
            "invalid": ["invalid", "raises", "ValueError"],
        },
    },
    "tool-call-planner": {
        "starter_root": ROOT / "tasks" / "tool-call-planner",
        "marker": "tool_call_planner/planner.py",
        "starter_public_test": ROOT / "tasks" / "tool-call-planner" / "tests" / "test_public_planner.py",
        "hidden_test": ROOT / "hidden_tests" / "test_hidden_tool_call_planner.py",
        "edge_keywords": {
            "policy": ["blocked_tools", "blocked_capabilities", "policy_blocked", "destructive_blocked"],
            "missing": ["missing_args", "required_args", "clarify"],
            "approval": ["approval_required", "approved_tools", "request_approval"],
            "risk": ["lowest", "risk", "low", "medium", "high"],
            "injection": ["ignore policy", "instruction", "prompt", "free text"],
        },
    },
    "evidence-answerer": {
        "starter_root": ROOT / "tasks" / "evidence-answerer",
        "marker": "evidence_answerer/answerer.py",
        "starter_public_test": ROOT / "tasks" / "evidence-answerer" / "tests" / "test_public_answerer.py",
        "hidden_test": ROOT / "hidden_tests" / "test_hidden_evidence_answerer.py",
        "edge_keywords": {
            "citations": ["citation", "citations", "source", "sources"],
            "conflict": ["conflict", "distinct", "disagree"],
            "trust": ["trusted", "untrusted", "ignore"],
            "facts": ["Fact:", "fact", "key", "value"],
            "invalid": ["invalid", "raises", "ValueError"],
        },
    },
}


def count_test_defs(text: str) -> int:
    return len(re.findall(r"\bdef\s+test_", text))


def test_names(text: str) -> set[str]:
    return set(re.findall(r"\bdef\s+(test_[A-Za-z0-9_]+)\s*\(", text))


def added_test_text(candidate: Path, starter_public_test: Path) -> str:
    tests_dir = candidate / "tests"
    if not tests_dir.exists():
        return ""

    starter_names = test_names(starter_public_test.read_text(encoding="utf-8"))
    chunks = []
    for path in tests_dir.rglob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name != starter_public_test.name:
            chunks.append(text)
            continue

        matches = list(re.finditer(r"(?m)^    def\s+(test_[A-Za-z0-9_]+)\s*\(", text))
        for index, match in enumerate(matches):
            name = match.group(1)
            if name in starter_names:
                continue
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            chunks.append(text[match.start() : end])
    return "\n".join(chunks)


def edge_hits_for_text(text: str, keywords: dict[str, list[str]]) -> set[str]:
    return {name for name, terms in keywords.items() if any(term in text for term in terms)}


def run_command(command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def count_agent_tests(candidate: Path, task: dict) -> int:
    return count_test_defs(added_test_text(candidate, task["starter_public_test"]))


def edge_keyword_hits(candidate: Path, task: dict) -> list[str]:
    return sorted(edge_hits_for_text(added_test_text(candidate, task["starter_public_test"]), task["edge_keywords"]))


def score_process(candidate: Path, task: dict) -> dict:
    report_paths = [path for path in [candidate / "EDD_REPORT.md", candidate / "AI_TDD_REPORT.md"] if path.exists()]
    has_report = bool(report_paths)
    evals_dir = candidate / "evals"
    has_red = (evals_dir / "red.log").exists()
    has_green = (evals_dir / "green.log").exists()
    eval_files = list(evals_dir.rglob("*")) if evals_dir.exists() else []
    test_count = count_agent_tests(candidate, task)
    edge_hits = edge_keyword_hits(candidate, task)

    score = 0
    score += 5 if has_report else 0
    score += 5 if evals_dir.exists() else 0
    score += 5 if has_red else 0
    score += 5 if has_green else 0
    score += min(5, test_count)
    score += min(10, len(edge_hits) * 2)

    return {
        "score": score,
        "max_score": 35,
        "has_report": has_report,
        "report_path": str(report_paths[0].relative_to(candidate)) if report_paths else None,
        "has_evals_dir": evals_dir.exists(),
        "has_red_log": has_red,
        "has_green_log": has_green,
        "eval_file_count": len([path for path in eval_files if path.is_file()]),
        "test_case_count": test_count,
        "edge_coverage": edge_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, help="Completed task directory to score")
    parser.add_argument("--task", choices=sorted(TASKS), default="quote-engine")
    parser.add_argument("--json-output", help="Optional path to write JSON results")
    args = parser.parse_args()

    task = TASKS[args.task]
    candidate = Path(args.candidate).resolve()
    if not (candidate / task["marker"]).exists():
        raise SystemExit(f"candidate does not look like the {args.task} task root: {candidate}")

    public_result = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"], candidate)

    with tempfile.TemporaryDirectory() as tmpdir:
        scored = Path(tmpdir) / "candidate"
        shutil.copytree(candidate, scored)
        shutil.copy2(task["hidden_test"], scored / "tests" / task["hidden_test"].name)
        hidden_result = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"], scored)

    public_score = 15 if public_result["returncode"] == 0 else 0
    hidden_score = 50 if hidden_result["returncode"] == 0 else 0
    process = score_process(candidate, task)

    result = {
        "candidate": str(candidate),
        "task": args.task,
        "score": public_score + hidden_score + process["score"],
        "max_score": 100,
        "functional": {
            "score": public_score + hidden_score,
            "max_score": 65,
            "public_passed": public_result["returncode"] == 0,
            "hidden_passed": hidden_result["returncode"] == 0,
        },
        "process": process,
        "commands": {
            "public": public_result,
            "hidden": hidden_result,
        },
    }

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    return 0 if result["score"] == result["max_score"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
