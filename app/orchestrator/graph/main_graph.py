from langgraph.graph import StateGraph, END
from .state import AgentState

# Agents
from app.agents.planner.planner_agent import plan_task
from app.orchestrator.nodes.delegator import delegate_task
from app.agents.researcher.research_agent import research_agent_task
from app.agents.summarizer.summarizer_agent import summarizer_agent_task
from app.agents.critic.critic_agent import critic_task
from app.utils.logger import logger
from app.security.zero_trust import zero_trust_enforcer
from app.security.agent_identities import agent_identity_manager


def secure_edge_transition(from_node: str, to_node: str):
    """Create a secure edge with zero trust validation"""
    def transition_func(state: AgentState) -> str:
        # Verify state transition
        trust_result = zero_trust_enforcer.enforce_trust("state_transition", {
            "from_state": from_node,
            "to_state": to_node,
            "agent": state.get("selected_agent", "system")
        })

        if not trust_result["trusted"]:
            logger.security_error("State transition blocked",
                                from_node=from_node,
                                to_node=to_node,
                                reason=trust_result["reason"])
            # Return to delegator for safe handling
            return "delegator"

        return to_node
    return transition_func


def critic_router(state: AgentState):
    if state["current_step_index"] >= len(state["next_steps"]):
        logger.trace_value("Critic router decision", "END (all steps complete)")
        return "end"
    logger.trace_value("Critic router decision", "DELEGATOR (more steps)")
    return "delegator"


def build_graph():
    logger.graph_building()
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", plan_task)
    workflow.add_node("delegator", delegate_task)
    workflow.add_node("research", research_agent_task)
    workflow.add_node("summarizer", summarizer_agent_task)
    workflow.add_node("critic", critic_task)

    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add edges with security
    workflow.add_edge("planner", "delegator")

    # Delegator routes to appropriate agent with security checks
    workflow.add_conditional_edges(
        "delegator",
        lambda state: debug_router(state),
        {
            "ResearchAgent": secure_edge_transition("delegator", "research"),
            "SummarizerAgent": secure_edge_transition("delegator", "summarizer"),
            "NO_AGENT": "delegator",
        },
    )

    # Workers route to critic with security
    workflow.add_edge("research", secure_edge_transition("research", "critic"))
    workflow.add_edge("summarizer", secure_edge_transition("summarizer", "critic"))

    # Critic decides: continue or end
    workflow.add_conditional_edges(
        "critic",
        critic_router,
        {
            "end": END,
            "delegator": "delegator",
        },
    )


def debug_router(state):
    logger.trace_value("Router selected agent", state.get("selected_agent"))
    return state.get("selected_agent", "NO_AGENT")


# Build the app ONCE
app = build_graph()
