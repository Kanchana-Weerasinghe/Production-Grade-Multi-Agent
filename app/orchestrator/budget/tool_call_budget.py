
from app.orchestrator.budget.models import Budget

def check_tool_call_budget(budget: Budget):
    """
    Ensure we have remaining tool-call budget.
    """
    if budget.used_tool_calls >= budget.max_tool_calls:
        return False, "Tool-call budget exceeded"
    return True, None


def register_tool_call(budget: Budget):
    """
    Increment tool-call usage.
    """
    budget.used_tool_calls += 1
    return budget
