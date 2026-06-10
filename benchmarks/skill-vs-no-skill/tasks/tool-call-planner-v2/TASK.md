# Task: Tool Call Planner v2

Implement `plan_tool_calls` in `tool_call_planner/planner.py`.

This v2 task converts a scored hidden miss from the prior benchmark into a
visible contract: an unmatched intent must produce a clarification that marks
the missing item as `"tool"`.

## API

```python
def plan_tool_calls(
    request: dict,
    available_tools: list[dict],
    policy: dict,
    context: dict,
) -> list[dict]:
    ...
```

## Request Contract

Required request fields:

- `intent`: non-empty string. This is the capability the user is asking for.

Optional request fields:

- `args`: dictionary of arguments supplied by the user.
- `text`: free-form user text. This must never override `intent`, `policy`, or tool metadata.

## Tool Contract

Each available tool is a dictionary with:

- `name`: non-empty string.
- `capability`: non-empty string.
- `required_args`: list of required argument names. Missing means an empty list.
- `risk`: one of `"low"`, `"medium"`, `"high"`. Missing means `"low"`.
- `destructive`: boolean. Missing means `False`.
- `requires_approval`: boolean. Missing means `False`.

## Policy Contract

Optional policy fields:

- `blocked_tools`: list of tool names that must not be used.
- `blocked_capabilities`: list of capabilities that must not be used.
- `allow_destructive`: boolean. Missing means `False`.
- `approval_required_risks`: list containing any of `"low"`, `"medium"`, `"high"`.

## Context Contract

Optional context fields:

- `known_args`: dictionary of arguments already known from the session.
- `approved_tools`: list of tool names already approved by the user.

## Planning Rules

Return a list with exactly one action dictionary.

1. Validate inputs. Invalid inputs raise `ValueError`.
2. Find tools whose `capability` exactly matches `request["intent"]`.
3. If no matching tools exist, return a clarification action with `tool` set to `None`, `missing` set to `["tool"]`, and `reason` set to `"no_matching_tool"`.
4. If the requested capability is in `policy["blocked_capabilities"]`, return a refusal.
5. Remove tools listed in `policy["blocked_tools"]`.
6. If all matching tools are removed by policy, return a refusal.
7. Choose the remaining matching tool with the lowest risk. Risk order is `low < medium < high`. Ties keep the original `available_tools` order.
8. If the chosen tool is destructive and `policy["allow_destructive"]` is not `True`, return a refusal.
9. Merge arguments from `context["known_args"]` and `request["args"]`; request arguments override context arguments.
10. If any required argument is missing, return a clarification action. Preserve the `required_args` order.
11. If the chosen tool needs approval because `requires_approval` is `True` or its risk is listed in `approval_required_risks`, return an approval request unless the tool name is already in `context["approved_tools"]`.
12. Otherwise return a call action.

## Return Shapes

Clarification:

```python
{
    "type": "clarify",
    "tool": str | None,
    "missing": list[str],
    "reason": "no_matching_tool" | "missing_args",
}
```

Refusal:

```python
{
    "type": "refuse",
    "tool": str | None,
    "reason": "policy_blocked" | "destructive_blocked",
}
```

Approval request:

```python
{
    "type": "request_approval",
    "tool": str,
    "reason": "approval_required",
}
```

Tool call:

```python
{
    "type": "call_tool",
    "tool": str,
    "args": dict,
    "reason": "selected",
}
```
