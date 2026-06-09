import unittest

from tool_call_planner import plan_tool_calls


class ToolCallPlannerPublicTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
