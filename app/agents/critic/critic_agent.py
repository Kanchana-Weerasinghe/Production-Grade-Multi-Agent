import json
import dspy
from strands import Agent
from opentelemetry import trace

from app.agents.base import BaseAgent
from app.orchestrator.budget.hooks import BudgetHooks
from app.orchestrator.guardrails.guardrails_llm import LLMGuardrails
from app.orchestrator.guardrails.guardrails_state import StateGuardrails
from app.orchestrator.graph.state import AgentState
from app.utils.logger import logger

BASE_AGENT = BaseAgent()


# ---------------------------------------------------------
# DSPy Signature
# ---------------------------------------------------------
class CriticSignature(dspy.Signature):
    step_index = dspy.InputField()
    total_steps = dspy.InputField()
    output_to_evaluate = dspy.InputField()

    critic_json = dspy.OutputField(
        desc="JSON: {is_safe, should_continue, notes}"
    )


# ---------------------------------------------------------
# DSPy Module
# ---------------------------------------------------------
class CriticModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.critic = dspy.ChainOfThought(CriticSignature)

    def forward(self, step_index, total_steps, output_to_evaluate):
        return self.critic(
            step_index=step_index,
            total_steps=total_steps,
            output_to_evaluate=output_to_evaluate
        )


# ---------------------------------------------------------
# Critic Agent Task
# ---------------------------------------------------------
def critic_task(state: AgentState):
    logger.agent_start("CRITIC")
    
    step_index = state["current_step_index"]
    total_steps = len(state["next_steps"])
    logger.critic_start(step_index, total_steps)

    tracer = trace.get_tracer("strands")

    # 1. State Guardrails
    StateGuardrails.validate_state(state)

    # 2. Extract context
    last_message_obj = state["messages"][-1] if state["messages"] else None
    last_message = last_message_obj.content if hasattr(last_message_obj, 'content') else (last_message_obj[1] if isinstance(last_message_obj, tuple) and len(last_message_obj) > 1 else str(last_message_obj))

    # 3. Validate prompt
    LLMGuardrails.validate_prompt(last_message)

    # 4. Create agent for telemetry/tracing
    critic_agent = Agent(
        name="CriticAgent",
        model=BASE_AGENT.lm,
    )

    # 5. Run DSPy critic
    critic_module = CriticModule()

    with tracer.start_as_current_span("critic-evaluation") as span:
        span.set_attribute("agent.name", critic_agent.name)
        span.set_attribute("step.index", step_index)

        try:
            BudgetHooks.before_llm(state, last_message)
            raw_output = critic_module(
                step_index=step_index,
                total_steps=total_steps,
                output_to_evaluate=last_message
            ).critic_json
            BudgetHooks.after_llm(state, raw_output)
        except Exception as error:
            BudgetHooks.on_error(state, error)
            raise

    # 6. Validate output
    LLMGuardrails.validate_output(raw_output)

    # 7. Parse JSON safely
    try:
        parsed = json.loads(raw_output)
    except Exception:
        parsed = {
            "is_safe": True,
            "should_continue": True,
            "notes": "Fallback: Could not parse LLM output."
        }

    # 8. Update state
    state["is_safe"] = parsed.get("is_safe", True)

    logger.critic_decision(parsed["is_safe"], parsed["should_continue"], parsed["notes"])
    logger.agent_end("CRITIC", "SUCCESS")

    # 9. Return LangGraph output
    return {
        "is_safe": parsed["is_safe"],
        "messages": [
            ("assistant", f"⚖️ Critic Notes: {parsed['notes']}")
        ],
        "budget": state["budget"],
    }
