import os
import uuid
from app.orchestrator.graph.main_graph import app
from app.config.settings import settings
from app.orchestrator.budget.models import Budget
from app.utils.logger import logger, LogLevel

# 1. SETUP OBSERVABILITY (Layer 7)
# Setting these here ensures the entire Graph lifecycle is recorded in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

def run_dry_test():
    # Set logging level: SILENT, ERROR, WARN, INFO (default), DEBUG, TRACE
    logger.set_level(LogLevel.INFO)
    
    logger.graph_execution_start("Travo_System_Dry_Run")

    # 2. DEFINE INITIAL STATE (Matches your AgentState)
    initial_state = {
        "messages": [("user", "What is MCP")],
        "next_steps": [],
        "context_data": {},
        "is_safe": True,
        "total_tokens": 0,
        "total_tool_calls": 0,
        "retry_attempts": 0,
        "episodic_memory_hits": 0,
        "semantic_memory_hits": 0,
        "budget": Budget(
            max_tokens=10000,
            max_tool_calls=10,
            max_wall_time_sec=300,
            max_retries=3
        )
    }

    # 3. CONFIGURE THE RUN
    # This 'run_name' is what will show up as the top-level parent in LangSmith
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "run_name": "Travo_System_Dry_Run"
    }

    print("--- 🟢 STARTING GRAPH EXECUTION ---\n")
    
    # 4. EXECUTE AND STREAM
    try:
        for event in app.stream(initial_state, config=config):
            for node_name, output in event.items():
                logger.graph_node_complete(node_name)
                
                if node_name == "delegator":
                    print(f"🔍 DELEGATOR OUTPUT: {output}")
                    print(f"🔍 DELEGATOR TYPE: {type(output)}")
                    if output:
                        print(f"🔍 DELEGATOR KEYS: {output.keys() if isinstance(output, dict) else 'not dict'}")
                
                if output is None:
                    print(f"⚠️ Node '{node_name}' returned None — skipping output checks.")
                    print("-" * 30)
                    continue

                if not isinstance(output, dict):
                    print(f"⚠️ Node '{node_name}' returned non-dict output of type {type(output)}")
                    print("-" * 30)
                    continue

                # If the planner finished, let's see the steps it added to the state
                if "next_steps" in output:
                    print(f"📍 New Plan Steps: {output['next_steps']}")

                if "messages" in output and output["messages"]:
                    last_message = output["messages"][-1]
                    if isinstance(last_message, (list, tuple)) and len(last_message) > 1:
                        print(f"💬 Assistant: {last_message[1]}")
                    else:
                        print(f"💬 Assistant: {last_message}")

                print("-" * 30)

    except Exception as e:
        logger.graph_node_complete(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    logger.graph_execution_end()


if __name__ == "__main__":
    run_dry_test()