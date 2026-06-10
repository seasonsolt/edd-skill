#!/usr/bin/env python3
"""Self-check benchmark integrity without using any agent output."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCORER = ROOT / "score_candidate.py"

TASKS = {
    "quote-engine": {
        "starter": ROOT / "task",
        "implementation": Path("quote_engine/quote.py"),
        "reference": r'''
from __future__ import annotations


def _is_int(value):
    return type(value) is int


def _round_half_up_bps(amount_cents, bps):
    return (amount_cents * bps + 5000) // 10000


def _validate_tiers(tiers):
    if not isinstance(tiers, list) or not tiers:
        raise ValueError("tiers must be a non-empty list")
    previous = 0
    for index, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            raise ValueError("tier must be a dict")
        price = tier.get("unit_price_cents")
        if not _is_int(price) or price <= 0:
            raise ValueError("unit_price_cents must be positive")
        up_to = tier.get("up_to")
        is_final = index == len(tiers) - 1
        if is_final:
            if up_to is not None:
                raise ValueError("final tier must be open-ended")
        else:
            if not _is_int(up_to) or up_to <= previous:
                raise ValueError("tier upper bounds must increase")
            previous = up_to


def quote_usage_invoice(
    usage_units: int,
    tiers: list[dict],
    discounts: list[dict] | None = None,
    minimum_cents: int = 0,
    tax_rate_bps: int = 0,
) -> dict:
    if not _is_int(usage_units) or usage_units < 0:
        raise ValueError("usage_units must be a non-negative integer")
    if not _is_int(minimum_cents) or minimum_cents < 0:
        raise ValueError("minimum_cents must be a non-negative integer")
    if not _is_int(tax_rate_bps) or tax_rate_bps < 0:
        raise ValueError("tax_rate_bps must be a non-negative integer")
    _validate_tiers(tiers)
    if discounts is None:
        discounts = []
    if not isinstance(discounts, list):
        raise ValueError("discounts must be a list")

    previous_upper = 0
    remaining = usage_units
    line_items = []
    usage_subtotal = 0
    for tier in tiers:
        if remaining <= 0:
            break
        up_to = tier["up_to"]
        tier_capacity = remaining if up_to is None else up_to - previous_upper
        units = min(remaining, tier_capacity)
        if units > 0:
            amount = units * tier["unit_price_cents"]
            usage_subtotal += amount
            line_items.append(
                {
                    "from": previous_upper + 1,
                    "to": up_to,
                    "units": units,
                    "unit_price_cents": tier["unit_price_cents"],
                    "amount_cents": amount,
                }
            )
            remaining -= units
        if up_to is not None:
            previous_upper = up_to

    minimum_adjustment = max(0, minimum_cents - usage_subtotal)
    running = usage_subtotal + minimum_adjustment
    discount_cents = 0
    for discount in discounts:
        if not isinstance(discount, dict):
            raise ValueError("discount must be a dict")
        discount_type = discount.get("type")
        if discount_type == "percent":
            value_bps = discount.get("value_bps")
            if not _is_int(value_bps) or value_bps < 0:
                raise ValueError("value_bps must be non-negative")
            amount = min(running, _round_half_up_bps(running, value_bps))
        elif discount_type == "fixed":
            amount = discount.get("amount_cents")
            if not _is_int(amount) or amount < 0:
                raise ValueError("amount_cents must be non-negative")
            amount = min(running, amount)
        else:
            raise ValueError("unknown discount type")
        running -= amount
        discount_cents += amount

    tax_cents = _round_half_up_bps(running, tax_rate_bps)
    return {
        "usage_units": usage_units,
        "line_items": line_items,
        "usage_subtotal_cents": usage_subtotal,
        "minimum_adjustment_cents": minimum_adjustment,
        "discount_cents": discount_cents,
        "tax_cents": tax_cents,
        "total_cents": running + tax_cents,
    }
''',
    },
    "feature-flags": {
        "starter": ROOT / "tasks" / "feature-flags",
        "implementation": Path("feature_flags/evaluator.py"),
        "reference": r'''
import hashlib


def _is_bool(value):
    return type(value) is bool


def _is_int(value):
    return type(value) is int


def _bucket(flag_key, user_key):
    digest = hashlib.sha256(f"{flag_key}:{user_key}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 10000


def _validate(flag, user):
    if not isinstance(flag, dict) or not isinstance(user, dict):
        raise ValueError("flag and user must be dicts")
    if not isinstance(flag.get("key"), str) or not flag["key"]:
        raise ValueError("flag key is required")
    if not _is_bool(flag.get("default")):
        raise ValueError("flag default must be boolean")
    if not isinstance(user.get("key"), str) or not user["key"]:
        raise ValueError("user key is required")
    if "enabled" in flag and not _is_bool(flag["enabled"]):
        raise ValueError("enabled must be boolean")
    if "archived" in flag and not _is_bool(flag["archived"]):
        raise ValueError("archived must be boolean")
    for list_name in ("denylist", "allowlist"):
        if list_name in flag and not isinstance(flag[list_name], list):
            raise ValueError(f"{list_name} must be a list")
    if "rollout_bps" in flag:
        rollout_bps = flag["rollout_bps"]
        if not _is_int(rollout_bps) or rollout_bps < 0 or rollout_bps > 10000:
            raise ValueError("rollout_bps must be between 0 and 10000")
    if "rules" in flag:
        if not isinstance(flag["rules"], list):
            raise ValueError("rules must be a list")
        for rule in flag["rules"]:
            if not isinstance(rule, dict):
                raise ValueError("rule must be a dict")
            if not isinstance(rule.get("name"), str) or not rule["name"]:
                raise ValueError("rule name is required")
            if not isinstance(rule.get("attribute"), str) or not rule["attribute"]:
                raise ValueError("rule attribute is required")
            if rule.get("op") not in {"equals", "in", "gte", "lte"}:
                raise ValueError("unknown rule op")
            if not _is_bool(rule.get("enabled")):
                raise ValueError("rule enabled must be boolean")
            if rule["op"] == "in" and not isinstance(rule.get("value"), list):
                raise ValueError("in rule value must be a list")


def _rule_matches(rule, user):
    attribute = rule["attribute"]
    if attribute not in user:
        return False
    actual = user[attribute]
    expected = rule.get("value")
    op = rule["op"]
    if op == "equals":
        return actual == expected
    if op == "in":
        return actual in expected
    if op == "gte":
        return actual >= expected
    if op == "lte":
        return actual <= expected
    raise ValueError("unknown rule op")


def evaluate_flag(flag: dict, user: dict) -> dict:
    _validate(flag, user)
    key = flag["key"]
    if flag.get("archived") is True:
        return {"key": key, "enabled": False, "reason": "archived", "bucket_bps": None}
    if flag.get("enabled", True) is False:
        return {"key": key, "enabled": False, "reason": "disabled", "bucket_bps": None}
    if user["key"] in flag.get("denylist", []):
        return {"key": key, "enabled": False, "reason": "denylist", "bucket_bps": None}
    if user["key"] in flag.get("allowlist", []):
        return {"key": key, "enabled": True, "reason": "allowlist", "bucket_bps": None}
    for rule in flag.get("rules", []):
        if _rule_matches(rule, user):
            return {"key": key, "enabled": rule["enabled"], "reason": f"rule:{rule['name']}", "bucket_bps": None}
    if "rollout_bps" in flag:
        bucket = _bucket(key, user["key"])
        enabled = bucket < flag["rollout_bps"]
        return {"key": key, "enabled": enabled, "reason": "rollout" if enabled else "default", "bucket_bps": bucket}
    return {"key": key, "enabled": flag["default"], "reason": "default", "bucket_bps": None}
''',
    },
    "tool-call-planner": {
        "starter": ROOT / "tasks" / "tool-call-planner",
        "implementation": Path("tool_call_planner/planner.py"),
        "reference": r'''
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _is_bool(value):
    return type(value) is bool


def _non_empty_string(value):
    return isinstance(value, str) and bool(value)


def _optional_string_list(mapping, key):
    if key not in mapping:
        return []
    value = mapping[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


def _validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be a dict")
    if not _non_empty_string(request.get("intent")):
        raise ValueError("request intent is required")
    if "args" in request and not isinstance(request["args"], dict):
        raise ValueError("request args must be a dict")


def _validate_tool(tool):
    if not isinstance(tool, dict):
        raise ValueError("tool must be a dict")
    if not _non_empty_string(tool.get("name")):
        raise ValueError("tool name is required")
    if not _non_empty_string(tool.get("capability")):
        raise ValueError("tool capability is required")
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
''',
    },
    "evidence-answerer": {
        "starter": ROOT / "tasks" / "evidence-answerer",
        "implementation": Path("evidence_answerer/answerer.py"),
        "reference": r'''
import re


def _normalize_key(value):
    return value.strip().lower()


def _dedupe(values):
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _requested_key(question):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    match = re.match(r"^What is\s+(.+?)\?$", question.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("unsupported question shape")
    return _normalize_key(match.group(1))


def _validate_passage(passage):
    if not isinstance(passage, dict):
        raise ValueError("passage must be a dict")
    if not isinstance(passage.get("id"), str) or not passage["id"]:
        raise ValueError("passage id is required")
    if not isinstance(passage.get("text"), str):
        raise ValueError("passage text must be a string")
    trusted = passage.get("trusted", True)
    if type(trusted) is not bool:
        raise ValueError("trusted must be boolean")
    return trusted


def _facts_for_key(text, key):
    facts = []
    for line in text.splitlines():
        match = re.match(r"^Fact:\s*(.*?)\s*=\s*(.*?)\s*$", line)
        if match and _normalize_key(match.group(1)) == key:
            facts.append(match.group(2).strip())
    return facts


def answer_question(question: str, passages: list[dict]) -> dict:
    key = _requested_key(question)
    if not isinstance(passages, list):
        raise ValueError("passages must be a list")

    observations = []
    for passage in passages:
        trusted = _validate_passage(passage)
        if not trusted:
            continue
        seen_values = set()
        for value in _facts_for_key(passage["text"], key):
            if value not in seen_values:
                observations.append((passage["id"], value))
                seen_values.add(value)

    if not observations:
        return {"status": "insufficient_evidence", "answer": None, "citations": []}

    values = _dedupe([value for _, value in observations])
    citations = _dedupe([source_id for source_id, _ in observations])
    if len(values) > 1:
        return {"status": "conflict", "answer": None, "citations": citations}

    return {"status": "answered", "answer": values[0], "citations": citations}
''',
    },
}


def score(task: str, candidate: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCORER), "--task", task, "--candidate", str(candidate)],
        text=True,
        capture_output=True,
    )
    return {
        "returncode": completed.returncode,
        "score": json.loads(completed.stdout),
    }


def main() -> int:
    results = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for task_name, task in TASKS.items():
            starter_score = score(task_name, task["starter"])

            solved = tmp / task_name
            shutil.copytree(task["starter"], solved)
            (solved / task["implementation"]).write_text(task["reference"].lstrip(), encoding="utf-8")
            solved_score = score(task_name, solved)

            results[task_name] = {
                "starter_score": starter_score["score"]["score"],
                "starter_public_passed": starter_score["score"]["functional"]["public_passed"],
                "starter_hidden_passed": starter_score["score"]["functional"]["hidden_passed"],
                "solved_score": solved_score["score"]["score"],
                "solved_public_passed": solved_score["score"]["functional"]["public_passed"],
                "solved_hidden_passed": solved_score["score"]["functional"]["hidden_passed"],
            }

    passed = all(
        result["starter_score"] == 0
        and not result["starter_public_passed"]
        and not result["starter_hidden_passed"]
        and result["solved_score"] >= 65
        and result["solved_public_passed"]
        and result["solved_hidden_passed"]
        for result in results.values()
    )
    output = {"passed": passed, "tasks": results}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
