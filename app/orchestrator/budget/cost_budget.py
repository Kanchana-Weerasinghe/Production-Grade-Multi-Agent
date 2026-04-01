# app/orchestrator/budget/cost_budget.py

def estimate_cost(tokens: int, price_per_million: float):
    """
    Convert token usage into dollar cost.
    """
    return (tokens / 1_000_000) * price_per_million


def check_cost_budget(budget, new_cost: float):
    """
    Ensure cost does not exceed max allowed.
    """
    if budget.used_cost + new_cost > budget.max_cost:
        return False, "Cost budget exceeded"
    return True, None


def register_cost(budget, new_cost: float):
    """
    Update cost usage.
    """
    budget.used_cost += new_cost
    return budget
