#!/usr/bin/env python3
"""Functional/process scorer for subscription-billing-evolution candidates."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HIDDEN_TESTS = r'''
import unittest

from subscription_billing import calculate_invoice


BASE = {
    "customer_id": "cus_hidden",
    "plan": "starter",
    "seats": 2,
    "status": "active",
    "period_start_day": 0,
    "period_end_day": 30,
}


class SubscriptionBillingHiddenTests(unittest.TestCase):
    def test_idempotent_replay_returns_zero_and_preserves_subscription(self):
        subscription = {**BASE, "last_event_id": "evt_same"}
        result = calculate_invoice(subscription, {"event_id": "evt_same", "type": "renewal", "day": 30})
        self.assertEqual(result["amount_cents"], 0)
        self.assertEqual(result["reason"], "idempotent_replay")
        self.assertEqual(result["next_subscription"], subscription)

    def test_trial_renewal_on_trial_end_converts_to_active_and_charges(self):
        subscription = {**BASE, "status": "trialing", "plan": "pro", "trial_end_day": 14}
        result = calculate_invoice(subscription, {"event_id": "evt_trial", "type": "renewal", "day": 14})
        self.assertEqual(result["amount_cents"], 6000)
        self.assertEqual(result["reason"], "renewal")
        self.assertEqual(result["next_subscription"]["status"], "active")

    def test_upgrade_prorates_positive_difference_with_half_up_rounding(self):
        subscription = {**BASE, "plan": "starter", "seats": 1, "coupon_percent": 10}
        result = calculate_invoice(
            subscription,
            {"event_id": "evt_up", "type": "upgrade", "day": 16, "new_plan": "pro", "new_seats": 2},
        )
        self.assertEqual(result["amount_cents"], 2100)
        self.assertEqual(result["reason"], "upgrade_proration")
        self.assertEqual(result["next_subscription"]["plan"], "pro")
        self.assertEqual(result["next_subscription"]["seats"], 2)

    def test_upgrade_proration_rounds_half_cents_up_not_down(self):
        subscription = {**BASE, "plan": "starter", "seats": 1, "period_start_day": 0, "period_end_day": 128}
        result = calculate_invoice(
            subscription,
            {"event_id": "evt_round", "type": "upgrade", "day": 127, "new_plan": "pro"},
        )
        self.assertEqual(result["amount_cents"], 16)

        rounding = calculate_invoice(
            {**BASE, "plan": "starter", "seats": 1},
            {"event_id": "evt_round", "type": "upgrade", "day": 29, "new_plan": "pro"},
        )
        self.assertEqual(rounding["amount_cents"], 67)

    def test_downgrade_never_issues_credit_but_updates_plan_and_seats(self):
        subscription = {**BASE, "plan": "enterprise", "seats": 3}
        result = calculate_invoice(
            subscription,
            {"event_id": "evt_down", "type": "downgrade", "day": 10, "new_plan": "starter", "new_seats": 1},
        )
        self.assertEqual(result["amount_cents"], 0)
        self.assertEqual(result["reason"], "downgrade_no_credit")
        self.assertEqual(result["next_subscription"]["plan"], "starter")
        self.assertEqual(result["next_subscription"]["seats"], 1)

    def test_cancel_modes_and_canceled_renewal_do_not_charge(self):
        defer = calculate_invoice(BASE, {"event_id": "evt_defer", "type": "cancel", "day": 5, "cancel_at_period_end": True})
        self.assertEqual(defer["reason"], "cancel_at_period_end")
        self.assertEqual(defer["next_subscription"]["status"], "active")
        self.assertTrue(defer["next_subscription"]["cancel_at_period_end"])
        now = calculate_invoice(BASE, {"event_id": "evt_now", "type": "cancel", "day": 5})
        self.assertEqual(now["reason"], "cancel_now")
        self.assertEqual(now["next_subscription"]["status"], "canceled")
        canceled = calculate_invoice({**BASE, "status": "canceled"}, {"event_id": "evt_renew", "type": "renewal", "day": 30})
        self.assertEqual(canceled["amount_cents"], 0)
        self.assertEqual(canceled["reason"], "canceled_no_charge")

    def test_payment_failure_sets_past_due_and_grace_period(self):
        result = calculate_invoice(BASE, {"event_id": "evt_fail", "type": "payment_failed", "day": 22})
        self.assertEqual(result["amount_cents"], 0)
        self.assertEqual(result["reason"], "payment_failed")
        self.assertEqual(result["next_subscription"]["status"], "past_due")
        self.assertEqual(result["next_subscription"]["grace_period_end_day"], 29)

    def test_invalid_inputs_raise_value_error(self):
        invalid_calls = [
            lambda: calculate_invoice({}, {"event_id": "evt", "type": "renewal", "day": 1}),
            lambda: calculate_invoice({**BASE, "plan": "invalid"}, {"event_id": "evt", "type": "renewal", "day": 1}),
            lambda: calculate_invoice({**BASE, "seats": 0}, {"event_id": "evt", "type": "renewal", "day": 1}),
            lambda: calculate_invoice({**BASE, "period_start_day": 30, "period_end_day": 30}, {"event_id": "evt", "type": "renewal", "day": 1}),
            lambda: calculate_invoice({**BASE, "coupon_percent": 101}, {"event_id": "evt", "type": "renewal", "day": 1}),
            lambda: calculate_invoice(BASE, {"event_id": "", "type": "renewal", "day": 1}),
            lambda: calculate_invoice(BASE, {"event_id": "evt", "type": "upgrade", "day": 1}),
        ]
        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaises(ValueError):
                    invalid_call()


if __name__ == "__main__":
    unittest.main()
'''


def run_command(command: list[str], cwd: Path, timeout: int = 60) -> dict:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
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
        "command": " ".join(command),
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "timeout_seconds": timeout,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def count_test_defs(text: str) -> int:
    return len(re.findall(r"\bdef\s+test_", text))


def process_score(candidate: Path) -> dict:
    report_paths = [path for path in [candidate / "EDD_REPORT.md", candidate / "AI_TDD_REPORT.md"] if path.exists()]
    evals = candidate / "evals"
    tests = list((candidate / "tests").glob("test*.py")) if (candidate / "tests").exists() else []
    agent_tests = [path for path in tests if path.name != "test_public_billing.py"]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for path in agent_tests)
    edge_terms = {
        "idempotency": ["idempot", "replay", "last_event_id"],
        "trial": ["trial", "trial_end"],
        "proration": ["prorat", "remaining", "round"],
        "downgrade": ["downgrade", "credit", "no_credit"],
        "cancel": ["cancel", "canceled"],
        "payment_failure": ["payment_failed", "grace", "past_due"],
        "invalid": ["invalid", "valueerror", "raises"],
    }
    edge_hits = sorted(name for name, terms in edge_terms.items() if any(term in text for term in terms))
    test_count = count_test_defs(text)
    score = 0
    score += 5 if report_paths else 0
    score += 5 if evals.exists() else 0
    score += 5 if (evals / "red.log").exists() else 0
    score += 5 if (evals / "green.log").exists() else 0
    score += min(5, max(0, test_count - 2))
    score += min(10, len(edge_hits) * 2)
    return {
        "score": score,
        "max_score": 35,
        "has_report": bool(report_paths),
        "report_path": str(report_paths[0].relative_to(candidate)) if report_paths else None,
        "has_evals_dir": evals.exists(),
        "has_red_log": (evals / "red.log").exists(),
        "has_green_log": (evals / "green.log").exists(),
        "test_case_count": test_count,
        "edge_coverage": edge_hits,
    }


def score_candidate(candidate: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "candidate"
        shutil.copytree(candidate, project)
        hidden_dir = project / "hidden_tests"
        hidden_dir.mkdir()
        (hidden_dir / "test_hidden_subscription_billing.py").write_text(HIDDEN_TESTS, encoding="utf-8")
        public = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"], project)
        hidden = run_command([sys.executable, "-m", "unittest", "discover", "-s", "hidden_tests"], project)
    public_passed = public["returncode"] == 0
    hidden_passed = hidden["returncode"] == 0
    functional_score = (15 if public_passed else 0) + (50 if hidden_passed else 0)
    process = process_score(candidate)
    return {
        "functional": {
            "score": functional_score,
            "max_score": 65,
            "public_passed": public_passed,
            "hidden_passed": hidden_passed,
            "public": public,
            "hidden": hidden,
        },
        "process": process,
        "score": functional_score + process["score"],
        "max_score": 100,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--json-output")
    args = parser.parse_args()
    result = score_candidate(Path(args.candidate).resolve())
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
