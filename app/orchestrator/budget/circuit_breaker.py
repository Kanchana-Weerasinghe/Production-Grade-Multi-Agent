# app/orchestrator/budget/circuit_breaker.py

def circuit_breaker(state):
    """
    Global circuit breaker that halts execution if:
    - token budget exceeded
    - tool-call budget exceeded
    - retry budget exceeded
    - safety flag triggered
    - last_error exists
    """
    budget = state["budget"]

    if budget.used_tokens > budget.max_tokens:
        return False, "Token budget exceeded"

    if budget.used_tool_calls > budget.max_tool_calls:
        return False, "Tool-call budget exceeded"

    if state["retry_attempts"] > budget.max_retries:
        return False, "Retry budget exceeded"

    if state.get("is_safe") is False:
        return False, "Safety violation"

    if state.get("last_error"):
        return False, state["last_error"]

    return True, None
