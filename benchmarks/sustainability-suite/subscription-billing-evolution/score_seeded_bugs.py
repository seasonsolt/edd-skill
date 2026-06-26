#!/usr/bin/env python3
"""Score subscription-billing verification against seeded billing bugs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REFERENCE_PATH = Path(__file__).with_name("billing_reference.py")
spec = importlib.util.spec_from_file_location("billing_reference", REFERENCE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load billing_reference.py")
billing_reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(billing_reference)
BASE_IMPLEMENTATION = billing_reference.REFERENCE_IMPLEMENTATION


def mutate(old: str, new: str) -> str:
    if old not in BASE_IMPLEMENTATION:
        raise RuntimeError(f"seed mutation target not found: {old}")
    return BASE_IMPLEMENTATION.replace(old, new, 1)


SEEDS = {
    "upgrade_rounding_floor": mutate(
        'return (numerator + denominator // 2) // denominator',
        'return numerator // denominator',
    ),
    "upgrade_charges_full_difference": mutate(
        'prorated = _round_div(max(0, new_amount - old_amount) * remaining, period)',
        'prorated = max(0, new_amount - old_amount)',
    ),
    "downgrade_issues_credit": mutate(
        'return _result(subscription, 0, "downgrade_no_credit", next_subscription)',
        'return _result(subscription, -abs(PRICES[subscription["plan"]] * subscription["seats"] - PRICES[event["new_plan"]] * event.get("new_seats", subscription["seats"])), "downgrade_no_credit", next_subscription)',
    ),
    "ignores_idempotency_key": mutate(
        'if subscription.get("last_event_id") == event["event_id"]:\n        return _result(subscription, 0, "idempotent_replay", next_subscription)',
        'if False and subscription.get("last_event_id") == event["event_id"]:\n        return _result(subscription, 0, "idempotent_replay", next_subscription)',
    ),
    "coupon_not_applied_to_upgrade": mutate(
        'return _result(subscription, _apply_coupon(prorated, subscription), "upgrade_proration", next_subscription)',
        'return _result(subscription, prorated, "upgrade_proration", next_subscription)',
    ),
    "trial_end_not_billed": mutate(
        'if subscription["status"] == "trialing" and day < subscription.get("trial_end_day", day):\n            return _result(subscription, 0, "trial_no_charge", next_subscription)',
        'if subscription["status"] == "trialing" and day <= subscription.get("trial_end_day", day):\n            return _result(subscription, 0, "trial_no_charge", next_subscription)',
    ),
}

SEED_FAILURE_MARKERS = {
    "upgrade_rounding_floor": ("round", "rounding", "2100", "2333"),
    "upgrade_charges_full_difference": ("prorat", "upgrade", "2100", "2333"),
    "downgrade_issues_credit": ("downgrade", "credit", "downgrade_no_credit"),
    "ignores_idempotency_key": ("idempot", "replay", "last_event"),
    "coupon_not_applied_to_upgrade": ("coupon", "discount", "2100"),
    "trial_end_not_billed": ("trial", "trial_no_charge", "trialing", "renewal"),
}


def run_tests(project: Path, timeout: int) -> dict:
    started = time.monotonic()
    try:
        completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=project, text=True, capture_output=True, timeout=timeout)
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
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr, "timed_out": timed_out, "timeout_seconds": timeout, "duration_seconds": round(time.monotonic() - started, 3)}


def seed_failure_matches(seed_name: str, result: dict) -> bool:
    if result["returncode"] == 0:
        return False
    combined = f"{result['stdout']}\n{result['stderr']}".lower()
    return any(marker.lower() in combined for marker in SEED_FAILURE_MARKERS.get(seed_name, ()))


def score_seed(candidate: Path, seed_name: str, implementation: str, timeout: int) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "candidate"
        shutil.copytree(candidate, project)
        implementation_path = project / "subscription_billing" / "engine.py"
        if not implementation_path.exists():
            raise SystemExit(f"candidate is missing {implementation_path.relative_to(project)}")
        implementation_path.write_text(implementation.lstrip(), encoding="utf-8")
        result = run_tests(project, timeout)

    raw_failed = result["returncode"] != 0
    killed = seed_failure_matches(seed_name, result)
    return {"seed": seed_name, "killed": killed, "raw_failed": raw_failed, "command": "python -m unittest discover -s tests", "returncode": result["returncode"], "stdout": result["stdout"], "stderr": result["stderr"], "timed_out": result["timed_out"], "timeout_seconds": result["timeout_seconds"], "duration_seconds": result["duration_seconds"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, help="Completed subscription-billing style project")
    parser.add_argument("--json-output", help="Optional path to write JSON results")
    parser.add_argument("--timeout", type=int, default=60, help="Seconds allowed per seeded test run")
    args = parser.parse_args()

    candidate = Path(args.candidate).resolve()
    seed_results = [score_seed(candidate, name, code, timeout=args.timeout) for name, code in SEEDS.items()]
    killed = sum(1 for result in seed_results if result["killed"])
    output = {"candidate": str(candidate), "seed_count": len(seed_results), "killed_count": killed, "score": round((killed / len(seed_results)) * 30, 2), "max_score": 30, "seeds": seed_results}
    text = json.dumps(output, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
