#!/usr/bin/env python3
"""Score candidate verification by running tests against seeded planner bugs.

This prototype intentionally does not replace the existing skill-vs-no-skill
scorer. It measures one EDD-specific question: whether candidate tests catch
plausible flawed implementations.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SEEDS = {
    "missing_tool_reports_empty_missing": r'''
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def plan_tool_calls(request, available_tools, policy, context):
    intent = request["intent"]
    matches = [tool for tool in available_tools if tool.get("capability") == intent]
    if not matches:
        return [{"type": "clarify", "tool": None, "missing": [], "reason": "no_matching_tool"}]
    tool = matches[0]
    args = {}
    args.update(context.get("known_args", {}))
    args.update(request.get("args", {}))
    missing = [name for name in tool.get("required_args", []) if name not in args]
    if missing:
        return [{"type": "clarify", "tool": tool["name"], "missing": missing, "reason": "missing_args"}]
    return [{"type": "call_tool", "tool": tool["name"], "args": args, "reason": "selected"}]
''',
    "ignores_blocked_capabilities": r'''
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def plan_tool_calls(request, available_tools, policy, context):
    intent = request["intent"]
    matches = [tool for tool in available_tools if tool.get("capability") == intent]
    if not matches:
        return [{"type": "clarify", "tool": None, "missing": ["tool"], "reason": "no_matching_tool"}]
    blocked_tools = set(policy.get("blocked_tools", []))
    remaining = [tool for tool in matches if tool.get("name") not in blocked_tools]
    if not remaining:
        return [{"type": "refuse", "tool": None, "reason": "policy_blocked"}]
    tool = sorted(remaining, key=lambda item: RISK_ORDER.get(item.get("risk", "low"), 0))[0]
    args = {}
    args.update(context.get("known_args", {}))
    args.update(request.get("args", {}))
    missing = [name for name in tool.get("required_args", []) if name not in args]
    if missing:
        return [{"type": "clarify", "tool": tool["name"], "missing": missing, "reason": "missing_args"}]
    return [{"type": "call_tool", "tool": tool["name"], "args": args, "reason": "selected"}]
''',
    "text_can_override_intent": r'''
def plan_tool_calls(request, available_tools, policy, context):
    intent = request.get("intent")
    text = request.get("text", "")
    for tool in available_tools:
        if tool.get("capability") in text:
            intent = tool.get("capability")
            break
    matches = [tool for tool in available_tools if tool.get("capability") == intent]
    if not matches:
        return [{"type": "clarify", "tool": None, "missing": ["tool"], "reason": "no_matching_tool"}]
    tool = matches[0]
    args = {}
    args.update(context.get("known_args", {}))
    args.update(request.get("args", {}))
    missing = [name for name in tool.get("required_args", []) if name not in args]
    if missing:
        return [{"type": "clarify", "tool": tool["name"], "missing": missing, "reason": "missing_args"}]
    return [{"type": "call_tool", "tool": tool["name"], "args": args, "reason": "selected"}]
''',
    "approval_by_capability_not_tool": r'''
def plan_tool_calls(request, available_tools, policy, context):
    intent = request["intent"]
    matches = [tool for tool in available_tools if tool.get("capability") == intent]
    if not matches:
        return [{"type": "clarify", "tool": None, "missing": ["tool"], "reason": "no_matching_tool"}]
    tool = matches[0]
    args = {}
    args.update(context.get("known_args", {}))
    args.update(request.get("args", {}))
    missing = [name for name in tool.get("required_args", []) if name not in args]
    if missing:
        return [{"type": "clarify", "tool": tool["name"], "missing": missing, "reason": "missing_args"}]
    needs_approval = tool.get("requires_approval") or tool.get("risk", "low") in policy.get("approval_required_risks", [])
    if needs_approval and tool.get("capability") not in context.get("approved_tools", []):
        return [{"type": "request_approval", "tool": tool["name"], "reason": "approval_required"}]
    return [{"type": "call_tool", "tool": tool["name"], "args": args, "reason": "selected"}]
''',
}


def run_tests(project: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=project,
        text=True,
        capture_output=True,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def score_seed(candidate: Path, seed_name: str, implementation: str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "candidate"
        shutil.copytree(candidate, project)
        implementation_path = project / "tool_call_planner" / "planner.py"
        if not implementation_path.exists():
            raise SystemExit(f"candidate is missing {implementation_path.relative_to(project)}")
        implementation_path.write_text(implementation.lstrip(), encoding="utf-8")
        result = run_tests(project)

    killed = result["returncode"] != 0
    return {
        "seed": seed_name,
        "killed": killed,
        "command": "python -m unittest discover -s tests",
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, help="Completed tool-call-planner style project")
    parser.add_argument("--json-output", help="Optional path to write JSON results")
    args = parser.parse_args()

    candidate = Path(args.candidate).resolve()
    seed_results = [score_seed(candidate, name, code) for name, code in SEEDS.items()]
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
