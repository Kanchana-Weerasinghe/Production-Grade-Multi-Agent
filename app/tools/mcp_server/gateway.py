# app/tools/mcp_server/gateway.py

from app.tools.mcp_server.registry import get_tool
from app.orchestrator.budget.tool_call_budget import check_tool_call_budget, register_tool_call
from app.orchestrator.budget.circuit_breaker import circuit_breaker
from app.orchestrator.guardrails.guardrails_tools import ToolGuardrails


def call_tool(state, tool_name: str, args: dict):
    """
    Secure Action Gateway:
    - Enforces circuit breaker
    - Enforces tool-call budget
    - Validates tool existence
    - Validates tool arguments (Guardrails)
    - Executes tool
    - Validates tool output (Guardrails)
    - Updates budget + state
    """

    budget = state["budget"]

    # 1. Circuit Breaker (system-level safety)
    ok, err = circuit_breaker(state)
    if not ok:
        raise Exception(f"CircuitBreakerError: {err}")

    # 2. Budget Guardrail (tool-call budget)
    ok, err = check_tool_call_budget(budget)
    if not ok:
        raise Exception(f"ToolBudgetError: {err}")

    # 3. Tool existence check
    tool = get_tool(tool_name)
    if not tool:
        raise Exception(f"ToolNotFoundError: Tool '{tool_name}' not registered")

    # 4. Guardrails: Validate tool arguments
    ToolGuardrails.validate_args(tool_name, args)

    # 5. Execute tool
    try:
        result = tool(**args)
    except Exception as e:
        raise Exception(f"ToolExecutionError: {str(e)}")

    # 6. Guardrails: Validate tool output
    ToolGuardrails.validate_output(tool_name, result)

    # 7. Update budget + state
    register_tool_call(budget)
    state["total_tool_calls"] += 1

    return result
