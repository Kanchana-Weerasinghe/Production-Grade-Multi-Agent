# registry.py

# Import actual tool implementations
from app.tools.mcp_server.tools.google_search import google_search

# ---------------------------------------
# 1. TOOL POOL (tool_name → function)
# ---------------------------------------
TOOL_POOL = {
    "google_search": google_search,
}

# ---------------------------------------
# 2. AGENT → TOOL MAPPING
# ---------------------------------------
# Each agent lists the tools it is allowed to use.
# This keeps your system clean, scalable, and dynamic.
AGENT_TOOLS = {
    "ResearchAgent": ["google_search"],   # Research agent can use search tools
    "SummarizerAgent": [],                # Summarizer uses LLM only (no tools)
    "GeneralAgent": [],                   # Fallback agent
}

# ---------------------------------------
# 3. TOOL LOOKUP
# ---------------------------------------
def get_tool(name: str):
    """Return the tool function by name, or None if not found."""
    return TOOL_POOL.get(name)
