from strands import Agent
from opentelemetry import trace

import dspy

from app.agents.base import BaseAgent
from app.orchestrator.budget.hooks import BudgetHooks
from app.tools.mcp_server.registry import AGENT_TOOLS, get_tool
from app.orchestrator.graph.state import AgentState
from app.utils.logger import logger

BASE_AGENT = BaseAgent()


# ---------------------------------------------------------
# 1. DSPy Signature for LLM Tool Selection
# ---------------------------------------------------------
class ToolSelectorSignature(dspy.Signature):
    instruction = dspy.InputField(desc="The research instruction")
    available_tools = dspy.InputField(desc="Comma-separated list of available tools")
    selected_tool = dspy.OutputField(
        desc=(
            "Return EXACTLY one tool name from the available tools list. "
            "Return only the tool name, no explanation."
        )
    )


# ---------------------------------------------------------
# 2. DSPy Module for Tool Selection
# ---------------------------------------------------------
class ToolSelector(dspy.Module):
    def __init__(self):
        super().__init__()
        self.selector = dspy.Predict(ToolSelectorSignature)

    def forward(self, instruction, available_tools):
        return self.selector(
            instruction=instruction,
            available_tools=", ".join(available_tools)
        )


# ---------------------------------------------------------
# 3. Research Agent Task (LLM-based tool selection + debug)
# ---------------------------------------------------------
def research_agent_task(state: AgentState):
    logger.agent_start("RESEARCH")

    tracer = trace.get_tracer("strands")

    # Get research instruction from next_steps
    instruction = state["next_steps"][state["current_step_index"]]
    logger.research_start(instruction)

    research_agent = Agent(
        name="ResearchAgent",
        model=BASE_AGENT.lm,
    )

    # Get tools available to this agent
    available_tools = AGENT_TOOLS.get("ResearchAgent", [])
    logger.research_tools_available(available_tools)

    if not available_tools:
        logger.research_error("No tools available")
        logger.agent_end("RESEARCH", "ERROR")
        return {
            "messages": [
                ("assistant", "❌ No tools available for ResearchAgent.")
            ],
            "current_step_index": state.get("current_step_index", 0) + 1,
        }

    # ---------------------------------------------------------
    # LLM decides which tool to use
    selector = ToolSelector()
    tool_choice = selector(instruction, available_tools)
    
    selected_tool_name = (getattr(tool_choice, "selected_tool", "") or "").strip()
    selected_tool_name = selected_tool_name.replace(" ", "").lower()
    
    if selected_tool_name not in available_tools:
        logger.trace_value("LLM tool selection fallback", selected_tool_name)
        selected_tool_name = available_tools[0]
    
    logger.research_tool_selected(selected_tool_name)

    selected_tool = get_tool(selected_tool_name)

    if not selected_tool:
        logger.research_error(f"Tool '{selected_tool_name}' not found in registry")
        logger.agent_end("RESEARCH", "ERROR")
        return {
            "messages": [
                ("assistant", f"❌ Tool '{selected_tool_name}' not found in registry.")
            ],
            "current_step_index": state.get("current_step_index", 0) + 1,
        }

    # ---------------------------------------------------------
    # Execute the selected tool
    # ---------------------------------------------------------
    logger.research_tool_executing(selected_tool_name, instruction)

    with tracer.start_as_current_span("research-execution") as span:
        span.set_attribute("agent.name", research_agent.name)
        span.set_attribute("instruction", instruction)
        span.set_attribute("selected_tool", selected_tool_name)

        try:
            BudgetHooks.before_tool(state, selected_tool_name, {"query": instruction})
            result = selected_tool(query=instruction)
            BudgetHooks.after_tool(state, selected_tool_name, result)
        except Exception as e:
            logger.research_error(str(e))
            logger.agent_end("RESEARCH", "ERROR")
            BudgetHooks.on_error(state, e)
            return {
                "messages": [("assistant", f"❌ Research failed: {e}")],
                "current_step_index": state.get("current_step_index", 0) + 1,
            }

    logger.research_tool_result(
        len(result.get("results", [])) if isinstance(result, dict) else None
    )
    logger.agent_end("RESEARCH", "SUCCESS")

    return {
        "messages": [
            ("assistant", f"🔍 I researched: '{instruction}' using {selected_tool_name}.")
        ],
        "research_output": result,  # ✅ Explicitly return for summarizer
        "current_step_index": state.get("current_step_index", 0) + 1,
        "budget": state["budget"],
    }
