from app.utils.token_counter import estimate_tokens
from app.orchestrator.budget.token_budget import check_token_budget, register_token_usage
from app.orchestrator.budget.tool_call_budget import check_tool_call_budget, register_tool_call
from app.orchestrator.budget.cost_budget import estimate_cost, check_cost_budget, register_cost
from app.orchestrator.budget.circuit_breaker import circuit_breaker
from app.orchestrator.guardrails.guardrails_llm import LLMGuardrails

class BudgetHooks:

    @staticmethod
    def before_llm(state, prompt: str):
        LLMGuardrails.validate_prompt(prompt)
        ok, err = circuit_breaker(state)
        if not ok:
            raise Exception(err)

        est_tokens = estimate_tokens(prompt)
        ok, err = check_token_budget(state["budget"], est_tokens)
        if not ok:
            raise Exception(err)

        register_token_usage(state["budget"], est_tokens)
        state["total_tokens"] += est_tokens

    @staticmethod
    def after_llm(state, output: str):
        LLMGuardrails.validate_output(output)
        est_tokens = estimate_tokens(output)
        register_token_usage(state["budget"], est_tokens)
        state["total_tokens"] += est_tokens

        if hasattr(state["budget"], "max_cost"):
            cost = estimate_cost(est_tokens, price_per_million=0.59)
            ok, err = check_cost_budget(state["budget"], cost)
            if not ok:
                raise Exception(err)
            register_cost(state["budget"], cost)

    @staticmethod
    def before_tool(state, tool_name: str, tool_args: dict):
        ok, err = check_tool_call_budget(state["budget"])
        if not ok:
            raise Exception(err)

        register_tool_call(state["budget"])
        state["total_tool_calls"] += 1

    @staticmethod
    def after_tool(state, tool_name: str, result):
        # Optional: add cost or token estimation for tool output
        return result

    @staticmethod
    def on_error(state, error: Exception):
        state["last_error"] = str(error)
        state["is_safe"] = False
        return state
