#!/usr/bin/env python3
"""Score candidate verification by running tests against seeded planner bugs.

This scorer measures one EDD-specific question: whether candidate tests catch
plausible flawed implementations. Each seed is a near-correct implementation
with one intentional behavior bug, so a killed seed is more likely to mean the
agent wrote targeted verification instead of merely tripping over an incomplete
stub.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


BASE_IMPLEMENTATION = r'''
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _is_bool(value):
    return isinstance(value, bool)


def _optional_string_list(container, key):
    values = container.get(key, [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError(f"{key} must be a list of strings")
    return values


def _validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be a dict")
    if not isinstance(request.get("intent"), str) or not request["intent"]:
        raise ValueError("intent must be a non-empty string")
    if "args" in request and not isinstance(request["args"], dict):
        raise ValueError("args must be a dict")
    if "text" in request and not isinstance(request["text"], str):
        raise ValueError("text must be a string")


def _validate_tool(tool):
    if not isinstance(tool, dict):
        raise ValueError("tool must be a dict")
    for key in ("name", "capability"):
        if not isinstance(tool.get(key), str) or not tool[key]:
            raise ValueError(f"{key} must be a non-empty string")
    required_args = tool.get("required_args", [])
    if not isinstance(required_args, list) or not all(isinstance(arg, str) for arg in required_args):
        raise ValueError("required_args must be a list of strings")
    risk = tool.get("risk", "low")
    if risk not in RISK_ORDER:
        raise ValueError("unknown risk")
    if "destructive" in tool and not _is_bool(tool["destructive"]):
        raise ValueError("destructive must be boolean")
    if "requires_approval" in tool and not _is_bool(tool["requires_approval"]):
        raise ValueError("requires_approval must be boolean")


def _validate_policy(policy):
    if not isinstance(policy, dict):
        raise ValueError("policy must be a dict")
    _optional_string_list(policy, "blocked_tools")
    _optional_string_list(policy, "blocked_capabilities")
    risks = _optional_string_list(policy, "approval_required_risks")
    if any(risk not in RISK_ORDER for risk in risks):
        raise ValueError("unknown approval risk")
    if "allow_destructive" in policy and not _is_bool(policy["allow_destructive"]):
        raise ValueError("allow_destructive must be boolean")


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "known_args" in context and not isinstance(context["known_args"], dict):
        raise ValueError("known_args must be a dict")
    _optional_string_list(context, "approved_tools")


def _risk(tool):
    return tool.get("risk", "low")


def plan_tool_calls(request: dict, available_tools: list[dict], policy: dict, context: dict) -> list[dict]:
    _validate_request(request)
    if not isinstance(available_tools, list):
        raise ValueError("available_tools must be a list")
    for tool in available_tools:
        _validate_tool(tool)
    _validate_policy(policy)
    _validate_context(context)

    intent = request["intent"]
    matching = [(index, tool) for index, tool in enumerate(available_tools) if tool["capability"] == intent]
    if not matching:
        return [{"type": "clarify", "tool": None, "missing": ["tool"], "reason": "no_matching_tool"}]

    if intent in policy.get("blocked_capabilities", []):
        return [{"type": "refuse", "tool": None, "reason": "policy_blocked"}]

    blocked_tools = set(policy.get("blocked_tools", []))
    allowed = [(index, tool) for index, tool in matching if tool["name"] not in blocked_tools]
    if not allowed:
        return [{"type": "refuse", "tool": None, "reason": "policy_blocked"}]

    _, chosen = min(allowed, key=lambda item: (RISK_ORDER[_risk(item[1])], item[0]))
    if chosen.get("destructive", False) and policy.get("allow_destructive") is not True:
        return [{"type": "refuse", "tool": chosen["name"], "reason": "destructive_blocked"}]

    args = {}
    args.update(context.get("known_args", {}))
    args.update(request.get("args", {}))
    required_args = chosen.get("required_args", [])
    missing = [arg for arg in required_args if arg not in args]
    if missing:
        return [{"type": "clarify", "tool": chosen["name"], "missing": missing, "reason": "missing_args"}]

    needs_approval = chosen.get("requires_approval", False) or _risk(chosen) in policy.get("approval_required_risks", [])
    if needs_approval and chosen["name"] not in context.get("approved_tools", []):
        return [{"type": "request_approval", "tool": chosen["name"], "reason": "approval_required"}]

    return [{"type": "call_tool", "tool": chosen["name"], "args": args, "reason": "selected"}]
'''


def mutate(old: str, new: str) -> str:
    if old not in BASE_IMPLEMENTATION:
        raise RuntimeError(f"seed mutation target not found: {old}")
    return BASE_IMPLEMENTATION.replace(old, new, 1)


SEEDS = {
    "missing_tool_reports_empty_missing": mutate(
        'return [{"type": "clarify", "tool": None, "missing": ["tool"], "reason": "no_matching_tool"}]',
        'return [{"type": "clarify", "tool": None, "missing": [], "reason": "no_matching_tool"}]',
    ),
    "ignores_blocked_capabilities": mutate(
        'if intent in policy.get("blocked_capabilities", []):\n        return [{"type": "refuse", "tool": None, "reason": "policy_blocked"}]',
        'if False and intent in policy.get("blocked_capabilities", []):\n        return [{"type": "refuse", "tool": None, "reason": "policy_blocked"}]',
    ),
    "text_can_override_intent": mutate(
        'intent = request["intent"]',
        'intent = request["intent"]\n    for tool in available_tools:\n        if tool.get("capability") in request.get("text", ""):\n            intent = tool["capability"]\n            break',
    ),
    "approval_by_capability_not_tool": mutate(
        'if needs_approval and chosen["name"] not in context.get("approved_tools", []):',
        'if needs_approval and chosen["capability"] not in context.get("approved_tools", []):',
    ),
}

# A seed is counted as killed only when the candidate tests fail in a way that
# mentions the intended mutation surface. This avoids false credit when a
# candidate test suite rejects the reference-shaped seeded implementation for an
# unrelated reason.
SEED_FAILURE_MARKERS = {
    "missing_tool_reports_empty_missing": ("no_matching_tool", "missing"),
    "ignores_blocked_capabilities": ("policy_blocked", "blocked_capability", "blocked capability"),
    "text_can_override_intent": ("override", "structured", "account.delete"),
    "approval_by_capability_not_tool": ("approval_required", "approved_tool", "approved tool"),
}


def run_tests(project: Path, timeout: int) -> dict:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=project,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as error:
        returncode = 124
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr_prefix = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        stderr = stderr_prefix + f"\nCommand timed out after {timeout}s"
        timed_out = True
    return {
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "timeout_seconds": timeout,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def seed_failure_matches(seed_name: str, result: dict) -> bool:
    if result["returncode"] == 0:
        return False
    combined = f"{result['stdout']}\n{result['stderr']}".lower()
    markers = SEED_FAILURE_MARKERS.get(seed_name, ())
    return any(marker.lower() in combined for marker in markers)


def score_seed(candidate: Path, seed_name: str, implementation: str, timeout: int) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "candidate"
        shutil.copytree(candidate, project)
        implementation_path = project / "tool_call_planner" / "planner.py"
        if not implementation_path.exists():
            raise SystemExit(f"candidate is missing {implementation_path.relative_to(project)}")
        implementation_path.write_text(implementation.lstrip(), encoding="utf-8")
        result = run_tests(project, timeout=timeout)

    raw_failed = result["returncode"] != 0
    killed = seed_failure_matches(seed_name, result)
    return {
        "seed": seed_name,
        "killed": killed,
        "raw_failed": raw_failed,
        "command": "python -m unittest discover -s tests",
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "timed_out": result["timed_out"],
        "timeout_seconds": result["timeout_seconds"],
        "duration_seconds": result["duration_seconds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, help="Completed tool-call-planner style project")
    parser.add_argument("--json-output", help="Optional path to write JSON results")
    parser.add_argument("--timeout", type=int, default=60, help="Seconds allowed per seeded test run")
    args = parser.parse_args()

    candidate = Path(args.candidate).resolve()
    seed_results = [score_seed(candidate, name, code, timeout=args.timeout) for name, code in SEEDS.items()]
    killed = sum(1 for result in seed_results if result["killed"])
    output = {
        "candidate": str(candidate),
        "seed_count": len(seed_results),
        "killed_count": killed,
        "score": round((killed / len(seed_results)) * 30, 2),
        "max_score": 30,
        "seeds": seed_results,
    }

    text = json.dumps(output, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
