import dspy
from strands import Agent
from opentelemetry import trace

from app.orchestrator.graph.state import AgentState
from app.agents.base import BaseAgent
from app.orchestrator.budget.hooks import BudgetHooks
from app.orchestrator.agent_capabilities import AGENT_CAPABILITIES
from app.utils.logger import logger

BASE_AGENT = BaseAgent()


# -----------------------------
# 1. DSPy Signature
# -----------------------------
class PlannerSignature(dspy.Signature):
    user_request = dspy.InputField(
        desc=(
            "The user's goal. You MUST create a plan using ONLY these capabilities: "
            f"{', '.join(AGENT_CAPABILITIES.keys())}. "
            "Each step MUST follow the format '<capability>: <instruction>'. "
            "If the request cannot be completed with these capabilities, output a single step: "
            "'unsupported: <reason>'."
        )
    )
    rationale = dspy.OutputField(desc="Reasoning steps used to derive the plan")
    plan_steps = dspy.OutputField(
        desc=(
            "A list of steps. Each step MUST start with a capability keyword "
            f"({', '.join(AGENT_CAPABILITIES.keys())}) or 'unsupported'. "
            "Format: '<capability>: <instruction>'."
        )
    )


# -----------------------------
# 2. DSPy Planner Module
# -----------------------------
class PlannerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.base = BASE_AGENT
        self.planner = dspy.ChainOfThought(PlannerSignature)

    def forward(self, user_request: str):
        return self.planner(user_request=user_request)


# -----------------------------
# 3. Step Validation
# -----------------------------
def validate_steps(steps):
    valid_capabilities = set(AGENT_CAPABILITIES.keys())

    for step in steps:
        if ":" not in step:
            return False, f"Invalid step format: {step}"

        capability = step.split(":", 1)[0].strip().lower()

        if capability == "unsupported":
            reason = step.split(":", 1)[1].strip()
            return False, f"Unsupported request: {reason}"

        if capability not in valid_capabilities:
            return False, f"No agent available for capability '{capability}'."

    return True, None


# -----------------------------
# 4. Planner Orchestrator Node
# -----------------------------
def plan_task(state: AgentState):
    logger.agent_start("PLANNER")

    # Security: Verify agent identity and get JIT privilege
    from app.security.agent_identities import agent_identity_manager
    from app.security.jit_manager import jit_manager
    from app.security.zero_trust import zero_trust_enforcer

    agent_identity = agent_identity_manager.get_identity("PlannerAgent")
    if not agent_identity:
        logger.security_error("PlannerAgent identity not found")
        return {"next_steps": [], "messages": [("assistant", "Security error: Agent identity not found")]}

    # Request JIT privilege for planning
    jit_token = jit_manager.request_privilege(
        subject="PlannerAgent",
        resource="planning",
        action="execute_plan",
        duration_seconds=120  # 2 minutes for planning
    )

    if not jit_token:
        logger.security_error("JIT privilege denied for PlannerAgent")
        return {"next_steps": [], "messages": [("assistant", "Security error: Access denied")]}

    # Add to active tokens
    active_tokens = state.get("active_jit_tokens", [])
    active_tokens.append(jit_token.token_id)
    state["active_jit_tokens"] = active_tokens

    tracer = trace.get_tracer("strands")

    last_message = state["messages"][-1]
    user_input = (
        last_message.content
        if hasattr(last_message, "content")
        else (last_message[1] if isinstance(last_message, tuple) else str(last_message))
    )
    
    logger.planner_input(user_input)

    planner_agent = Agent(
        name="LeadPlanner",
        model=BASE_AGENT.lm,
    )


    with tracer.start_as_current_span("planner-execution") as span:
        span.set_attribute("agent.name", planner_agent.name)
        span.set_attribute("user_input", str(user_input))

        planner_logic = PlannerModule()

        try:
            BudgetHooks.before_llm(state, str(user_input))
            result = planner_logic(user_request=user_input)
            BudgetHooks.after_llm(state, str(result))
        except Exception as error:
            BudgetHooks.on_error(state, error)
            raise

    # Normalize steps
    steps = result.plan_steps
    logger.planner_steps_raw(steps)
    
    if isinstance(steps, str):
        steps = [s.strip() for s in steps.split("\n") if s.strip()]
    elif isinstance(steps, list):
        steps = [str(s).strip() for s in steps if str(s).strip()]
    else:
        steps = [str(steps).strip()] if str(steps).strip() else []

    logger.planner_steps_normalized(steps)

    # Validate steps
    is_valid, error_message = validate_steps(steps)

    if not is_valid:
        logger.planner_error(error_message)
        logger.agent_end("PLANNER", "ERROR")
        return {
            "next_steps": [],
            "current_step_index": 0,
            "messages": [
                ("assistant", f"❌ I cannot execute this request: {error_message}")
            ],
            "budget": state["budget"],
            "active_jit_tokens": active_tokens,
            "security_context": {
                **state.get("security_context", {}),
                "last_agent": "PlannerAgent",
                "error": "Planning validation failed"
            }
        }

    logger.agent_end("PLANNER", "SUCCESS")

    return {
        "next_steps": steps,
        "current_step_index": 0,
        "messages": [
            ("assistant", "📝 Here is your strategic plan:\n" + "\n".join(steps))
        ],
        "budget": state["budget"],
        "active_jit_tokens": active_tokens,
        "security_context": {
            **state.get("security_context", {}),
            "last_agent": "PlannerAgent",
            "agent_signature": agent_identity.sign_message("Planning completed successfully")
        }
    }
