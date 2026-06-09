def plan_tool_calls(
    request: dict,
    available_tools: list[dict],
    policy: dict,
    context: dict,
) -> list[dict]:
    raise NotImplementedError
