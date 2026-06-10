import unittest

from tool_call_planner import plan_tool_calls


class ToolCallPlannerV2PublicTests(unittest.TestCase):
    def test_calls_matching_tool_with_merged_args(self):
        result = plan_tool_calls(
            {"intent": "send_email", "args": {"body": "Hi"}},
            [
                {
                    "name": "email.send",
                    "capability": "send_email",
                    "required_args": ["to", "body"],
                    "risk": "low",
                }
            ],
            {},
            {"known_args": {"to": "team@example.com"}},
        )

        self.assertEqual(
            result,
            [
                {
                    "type": "call_tool",
                    "tool": "email.send",
                    "args": {"to": "team@example.com", "body": "Hi"},
                    "reason": "selected",
                }
            ],
        )

    def test_missing_required_args_requests_clarification(self):
        result = plan_tool_calls(
            {"intent": "create_ticket", "args": {"title": "Bug"}},
            [
                {
                    "name": "ticket.create",
                    "capability": "create_ticket",
                    "required_args": ["title", "priority"],
                }
            ],
            {},
            {},
        )

        self.assertEqual(
            result,
            [
                {
                    "type": "clarify",
                    "tool": "ticket.create",
                    "missing": ["priority"],
                    "reason": "missing_args",
                }
            ],
        )

    def test_unknown_intent_requests_tool_clarification(self):
        result = plan_tool_calls(
            {"intent": "export_audit_log", "args": {"format": "csv"}},
            [
                {
                    "name": "ticket.create",
                    "capability": "create_ticket",
                    "required_args": ["title"],
                }
            ],
            {},
            {},
        )

        self.assertEqual(
            result,
            [
                {
                    "type": "clarify",
                    "tool": None,
                    "missing": ["tool"],
                    "reason": "no_matching_tool",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
