
from app.orchestrator.budget.models import Budget

def check_token_budget(budget: Budget, new_tokens: int):
    """
    Check if adding new_tokens would exceed the token budget.
    """
    if budget.used_tokens + new_tokens > budget.max_tokens:
        return False, "Token budget exceeded"
    return True, None


def register_token_usage(budget: Budget, new_tokens: int):
    """
    Update token usage after an LLM call.
    """
    budget.used_tokens += new_tokens
    return budget
