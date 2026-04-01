from typing import Annotated, List, Optional, Dict
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from app.orchestrator.budget.models import Budget

class AgentState(TypedDict, total=False):
    # 1. Conversation history (LangGraph auto-appends)
    messages: Annotated[List[BaseMessage], add_messages]

    # 2. Planner output
    next_steps: List[str]
    current_step_index: int

    # 3. Budget object (token, tool-call, wall-time)
    budget: Budget

    # 4. Execution vitals
    total_tokens: int
    total_tool_calls: int
    retry_attempts: int

    # 5. Safety & governance
    is_safe: bool
    last_error: Optional[str]

    # 6. Memory context
    context_data: Dict
    episodic_memory_hits: int
    semantic_memory_hits: int

    # 7. Agent outputs (blackboard for inter-agent communication)
    research_output: Optional[Dict]
    summary_output: Optional[str]
    selected_agent: str
    current_task: str

    # 8. Observability
    request_id: str
    trace_id: str
    span_id: str

    # 9. Security (Zero Trust)
    agent_identities: Dict[str, str]  # agent_name -> agent_id
    active_jit_tokens: List[str]  # List of active JIT token IDs
    security_context: Dict[str, Any]  # Additional security metadata
