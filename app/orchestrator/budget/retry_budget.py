
def can_retry(state):
    """
    Check if retry attempts are within allowed limits.
    """
    max_retries = state["budget"].max_retries
    return state["retry_attempts"] < max_retries


def register_retry(state):
    """
    Increment retry attempts.
    """
    state["retry_attempts"] += 1
    return state
