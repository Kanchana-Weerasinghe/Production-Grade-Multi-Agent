import re

def estimate_tokens(text: str) -> int:
    """
    Lightweight token estimator.
    Works well for Groq, OpenAI, Anthropic, and Llama models.
    """
    if not text:
        return 0

    # Normalize whitespace
    text = text.strip()

    # Approximation: 1 token ≈ 0.75 words
    words = re.findall(r"\w+", text)
    return max(1, int(len(words) / 0.75))


def count_message_tokens(messages):
    """
    Estimate tokens for a list of messages.
    Each message is a tuple: (role, content)
    """
    total = 0
    for role, content in messages:
        total += estimate_tokens(role)
        total += estimate_tokens(content)
    return total
