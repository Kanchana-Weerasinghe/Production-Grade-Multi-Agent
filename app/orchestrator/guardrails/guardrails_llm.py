import re

class LLMGuardrails:

    @staticmethod
    def validate_prompt(prompt: str):
        # Block empty or malformed prompts
        if not prompt or len(prompt.strip()) == 0:
            raise ValueError("LLM prompt is empty or invalid.")

        # Block prompt injection attempts
        if "ignore previous instructions" in prompt.lower():
            raise ValueError("Prompt injection detected.")

        return True

    @staticmethod
    def validate_output(output: str):
        # Block unsafe content
        banned = ["kill", "suicide", "harm yourself"]
        if any(b in output.lower() for b in banned):
            raise ValueError("Unsafe LLM output detected.")

        # Block hallucinated tool names
        if "call_tool(" in output:
            raise ValueError("LLM attempted to call a tool directly.")

        return True
