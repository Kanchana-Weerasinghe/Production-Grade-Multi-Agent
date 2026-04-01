# app/agents/specialist/summarizer_agent.py

import dspy
from strands import Agent
from opentelemetry import trace

from app.agents.base import BaseAgent
from app.orchestrator.budget.hooks import BudgetHooks
from app.orchestrator.graph.state import AgentState
from app.utils.logger import logger

BASE_AGENT = BaseAgent()


# DSPy signature for summarization
class SummarizerSignature(dspy.Signature):
    content = dspy.InputField(desc="Content to summarize")
    summary = dspy.OutputField(desc="A concise summary")


class SummarizerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarizer = dspy.ChainOfThought(SummarizerSignature)

    def forward(self, content: str):
        return self.summarizer(content=content)


def summarizer_agent_task(state: AgentState):
    logger.agent_start("SUMMARIZER")

    tracer = trace.get_tracer("strands")

    # Get research output
    research_data = state.get("research_output", None)
    
    logger.summarizer_input_received(type(research_data).__name__)
    
    if not research_data:
        logger.summarizer_error("No research data available to summarize")
        logger.agent_end("SUMMARIZER", "ERROR")
        return {
            "is_safe": False,
            "last_error": "No research data available to summarize.",
            "messages": [("assistant", "❌ No research data to summarize.")]
        }
    summarizer_agent = Agent(
        name="SummarizerAgent",
        model=BASE_AGENT.lm,
    )

    with tracer.start_as_current_span("summarizer-execution") as span:
        span.set_attribute("agent.name", summarizer_agent.name)

        # Run DSPy summarizer with budget hooks
        summarizer_logic = SummarizerModule()
        try:
            BudgetHooks.before_llm(state, str(research_data))
            result = summarizer_logic(content=str(research_data))
            BudgetHooks.after_llm(state, str(result))
        except Exception as error:
            BudgetHooks.on_error(state, error)
            raise

    summary = result.summary

    logger.summarizer_result(len(summary))
    logger.agent_end("SUMMARIZER", "SUCCESS")

    return {
        "messages": [
            ("assistant", f"📝 Summary:\n{summary}")
        ],
        "summary_output": summary,  # ✅ Store summary in state
        "current_step_index": state["current_step_index"] + 1,
        "budget": state["budget"],
    }
