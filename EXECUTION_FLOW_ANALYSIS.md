# Travo Multi-Agent System - User Request Flow Analysis

## Overview
When you run `dry_run.py`, a user request **"What is MCP"** flows through a **LangGraph-based orchestration system** with specialized agents, budget management, and safety guardrails.

---

## 1. INITIALIZATION PHASE (dry_run.py)

### Initial State Setup
```python
initial_state = {
    "messages": [("user", "What is MCP")],  # The user request
    "next_steps": [],                        # To be populated by planner
    "current_step_index": 0,                 # Tracks which step we're on
    "context_data": {},                      # Shared working memory
    "is_safe": True,                         # Safety flag
    "total_tokens": 0,                       # Token tracking
    "total_tool_calls": 0,                   # Tool call counting
    "retry_attempts": 0,                     # Error retry counter
    "episodic_memory_hits": 0,              # Memory lookups
    "semantic_memory_hits": 0,
    "budget": Budget(                        # Resource constraints
        max_tokens=10000,
        max_tool_calls=10,
        max_wall_time_sec=300,
        max_retries=3
    )
}
```

### Graph Configuration
```python
config = {
    "configurable": {"thread_id": str(uuid.uuid4())},  # Unique execution ID
    "run_name": "Travo_System_Dry_Run"                  # LangSmith tracing label
}
```

### LangSmith Integration
- **Observability Layer**: All interactions are traced to LangSmith
- **Environment variables** setup:
  - `LANGCHAIN_TRACING_V2=true`
  - `LANGCHAIN_API_KEY` (from settings)
  - `LANGCHAIN_PROJECT` (from settings)

---

## 2. GRAPH EXECUTION FLOW

The graph follows this structure:

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ 1️⃣  PLANNER NODE                         │
│ • Receives: "What is MCP"                │
│ • Output: List of actionable steps       │
│ • Sets: next_steps, current_step_index=0 │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ 2️⃣  DELEGATOR NODE                       │
│ • Reads: next_steps[current_step_index]  │
│ • Matches: keyword → agent               │
│ • Selects: ResearchAgent or SummarizerAgent
└──────┬──────────────────────────────────┘
       │
       ├─ "search" keyword ──────────────┐
       │                                  │
       │                          ┌───────▼──────────────┐
       │                          │ 3️⃣  RESEARCH AGENT    │
       │                          │ • Executes MCP search │
       │                          │ • Uses google_search  │
       │                          └───────┬──────────────┘
       │                                  │
       └─ "summarize" keyword ────────┐   │
                                      │   │
                                      │   ▼
                                      │  ┌────────────────────┐
                                      │  │ 4️⃣  SUMMARIZER AGENT │
                                      │  │ • Summarizes result  │
                                      │  └────────┬───────────┘
                                      │           │
                                      └────┬──────┘
                                           │
                                           ▼
                                    ┌──────────────────┐
                                    │ 5️⃣  CRITIC NODE    │
                                    │ • Evaluates output│
                                    │ • Checks safety   │
                                    │ • Decides: continue or END
                                    └────────┬─────────┘
                                             │
                                       ┌─────┴────────┐
                                       │              │
                                    More steps?   No more steps?
                                       │              │
                                       ▼              ▼
                                    DELEGATOR       END
                                       │
                                       └─────────────┘
                                          (loop)
```

---

## 3. DETAILED NODE EXECUTION

### **NODE 1: PLANNER** 📋
**Location**: `app/agents/planner/planner_agent.py`

#### Input
- User message: `"What is MCP"`
- AgentState with budget

#### Process
1. **LLM Call with DSPy**:
   - Signature: `PlannerSignature` (user_request → rationale, plan_steps)
   - LM Model: `BASE_AGENT.lm` (configured in settings)
   - Constraint: Steps must use only available capabilities

2. **Available Capabilities**:
   ```python
   AGENT_CAPABILITIES = {
       "search": "ResearchAgent",      # For research tasks
       "summarize": "SummarizerAgent"  # For summarization tasks
   }
   ```

3. **Step Generation**:
   - For "What is MCP", LLM might generate:
     ```
     Step 1: search: Find information about MCP protocol
     Step 2: summarize: Create a concise explanation
     ```

4. **Validation**:
   - Each step must start with a valid capability keyword
   - Format: `<capability>: <instruction>`
   - If invalid → response: `"unsupported: <reason>"`

5. **Budget Hooks** (Strands Agent Integration):
   - `before_llm()`: Pre-flight budget check
   - `after_llm()`: Token counting & cost tracking
   - `on_error()`: Rollback on exception

#### Output
```python
{
    "next_steps": [
        "search: Find information about MCP protocol",
        "summarize: Create a concise explanation"
    ],
    "current_step_index": 0,
    "messages": [("assistant", "📝 Here is your strategic plan:\n...")],
    "budget": updated_budget  # Tokens incremented
}
```

---

### **NODE 2: DELEGATOR** 🎯
**Location**: `app/orchestrator/nodes/delegator.py`

#### Input
- State with `next_steps` and `current_step_index`
- Example: `next_steps[0] = "search: Find information about MCP protocol"`

#### Process
1. **Read Current Step**:
   ```python
   step = state["next_steps"][state["current_step_index"]].lower()
   # "search: find information about mcp protocol"
   ```

2. **Keyword Matching**:
   - Loop through `AGENT_CAPABILITIES` keys ("search", "summarize")
   - If keyword found in step → select corresponding agent
   
   ```python
   if "search" in step:
       selected_agent = "ResearchAgent"
   elif "summarize" in step:
       selected_agent = "SummarizerAgent"
   else:
       selected_agent = "ResearchAgent"  # Fallback
   ```

3. **State Mutation**:
   ```python
   return {
       "selected_agent": "ResearchAgent",
       "current_task": "search: Find information about MCP protocol"
   }
   ```

#### Output
- Routed to appropriate specialist agent
- Conditional edge `debug_router()` maps selection to node name

---

### **NODE 3: RESEARCH AGENT** 🔍
**Location**: `app/agents/researcher/research_agent.py`

#### Input
- Instruction: `"Find information about MCP protocol"`
- Available tools: `["google_search"]`

#### Process

**Step 1: LLM-Based Tool Selection**
- DSPy Signature: `ToolSelectorSignature`
- LLM chooses which tool to use (extensible for multiple tools)
- Example output: `"google_search"`

**Step 2: Tool Execution Registry**
```python
TOOL_POOL = {
    "google_search": google_search,  # Actual function
}

AGENT_TOOLS = {
    "ResearchAgent": ["google_search"],  # Allowed tools
    "SummarizerAgent": [],               # No tools
}
```

**Step 3: Execute Selected Tool**
```python
selected_tool = get_tool("google_search")
result = selected_tool(query="Find information about MCP protocol")
# Result: List of search results about MCP
```

**Step 4: Budget Tracking**
- `BudgetHooks.before_tool()`: Validate tool call budget
- Execute tool
- `BudgetHooks.after_tool()`: Track tool execution

#### Output
```python
{
    "messages": [("assistant", "🔍 I researched: '...' using google_search.")],
    "current_step_index": 1,  # Move to next step
    "research_output": result,  # Cached for summarizer
    "budget": updated_budget   # Tool call count incremented
}
```

---

### **NODE 4: SUMMARIZER AGENT** 📝
**Location**: `app/agents/summarizer/summarizer_agent.py`

#### Input
- Research data: Google search results (from prev step)
- DSPy Signature: `SummarizerSignature`

#### Process
1. **Extract Research Output**:
   ```python
   research_data = state.get("research_output", None)
   ```

2. **LLM Summarization**:
   - DSPy chains the research results into a concise summary
   - Uses `ChainOfThought` for reasoning transparency

3. **Budget Hooks**:
   - `before_llm()` / `after_llm()` for token tracking

#### Output
```python
{
    "messages": [("assistant", "📝 Summary:\n<concise explanation of MCP>")],
    "current_step_index": 2,  # Increment to next
    "summary_output": summary,  # Store for future use
    "budget": updated_budget
}
```

---

### **NODE 5: CRITIC AGENT** ⚖️
**Location**: `app/agents/critic/critic_agent.py`

#### Input
- Last message (output to evaluate)
- Current step index & total steps

#### Process

**1. Guardrails Validation**
```python
StateGuardrails.validate_state(state)  # Check state integrity
LLMGuardrails.validate_prompt(message) # Check prompt safety
```

**2. DSPy Evaluation**
- Signature: `CriticSignature`
- LLM evaluates:
  - `is_safe`: Boolean safety check
  - `should_continue`: Whether to proceed to next step
  - `notes`: Reasoning

**3. Output Parsing**
```python
raw_output = critic_module(...).critic_json
# Expected: {"is_safe": true, "should_continue": true, "notes": "..."}
parsed = json.loads(raw_output)
```

**4. Budget Hooks**
- Full cycle: `before_llm()`, `after_llm()`, `on_error()`

#### Output & Routing Decision
```python
if parsed["should_continue"] and current_step_index < len(next_steps):
    return "delegator"  # Continue loop → process next step
else:
    return "end"        # All steps done → EXIT GRAPH
```

---

## 4. COMPLETE EXECUTION TRACE FOR "What is MCP"

### Step 1: Planner Breakdown
```
Input:  "What is MCP"
↓
LLM Planning
↓
Output:
  Step 1: "search: Find information about MCP protocol"
  Step 2: "summarize: Create concise explanation"
```

### Step 2: First Delegation
```
current_step_index = 0
next_steps[0] = "search: Find information about MCP protocol"
↓
Delegator finds "search" keyword
↓
Route to: ResearchAgent
```

### Step 3: Research Execution
```
Instruction: "Find information about MCP protocol"
↓
LLM selects tool: "google_search"
↓
Tool call: google_search(query="Find information about MCP protocol")
↓
Result: [{"title": "MCP Protocol", "snippet": "..."}, ...]
```

### Step 4: Critic Evaluation (Loop 1)
```
Evaluated message: "Research found..."
is_safe: true
should_continue: true (more steps remain)
↓
Route back to: Delegator
```

### Step 5: Second Delegation
```
current_step_index = 1
next_steps[1] = "summarize: Create concise explanation"
↓
Delegator finds "summarize" keyword
↓
Route to: SummarizerAgent
```

### Step 6: Summarization
```
Input: research_output (cached search results)
↓
DSPy summarization with ChainOfThought
↓
Output: "MCP is a protocol for..."
```

### Step 7: Critic Evaluation (Loop 2)
```
Evaluated message: "Summary: MCP is..."
is_safe: true
should_continue: false (current_step_index >= len(next_steps))
↓
Route to: END
↓
Graph terminates
```

---

## 5. STATE FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│ Initial State                                                    │
│ messages: [("user", "What is MCP")]                            │
│ next_steps: []                                                  │
│ current_step_index: 0                                           │
│ budget: Budget(max_tokens=10000, max_tool_calls=10, ...)       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ After PLANNER                                                    │
│ messages: [..., ("assistant", "📝 Here is your strategic plan...")]
│ next_steps: ["search: ...", "summarize: ..."]                  │
│ current_step_index: 0                                           │
│ total_tokens: +50 (hypothetical)                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ After RESEARCH AGENT                                            │
│ messages: [..., ("assistant", "🔍 I researched...")]          │
│ research_output: [search results]                              │
│ current_step_index: 1                                           │
│ total_tokens: +75                                               │
│ total_tool_calls: 1                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ After SUMMARIZER AGENT                                          │
│ messages: [..., ("assistant", "📝 Summary: MCP is...")]       │
│ summary_output: concise explanation                            │
│ current_step_index: 2                                           │
│ total_tokens: +45                                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ After CRITIC AGENT                                              │
│ Decision: should_continue = false (no more steps)              │
│ Route: END                                                      │
│ Final token count: 170                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. KEY ARCHITECTURAL PATTERNS

### 6.1 DSPy Integration
Each agent uses **DSPy Signatures** for structured LLM prompts:
- **Planner**: `PlannerSignature` → plan_steps
- **Researcher**: `ToolSelectorSignature` → selected tool choice
- **Summarizer**: `SummarizerSignature` → summary text
- **Critic**: `CriticSignature` → JSON evaluation

### 6.2 Budget Management (via Strands Agents)
```python
# All agents have budget hooks attached:
Agent(
    name="AgentName",
    model=BASE_AGENT.lm,
    before_llm=lambda prompt: BudgetHooks.before_llm(state, prompt),
    after_llm=lambda output: BudgetHooks.after_llm(state, output),
    before_tool=lambda tool_name, args: BudgetHooks.before_tool(...),
    after_tool=lambda tool_name, result: BudgetHooks.after_tool(...),
    on_error=lambda error: BudgetHooks.on_error(state, error),
)
```
- Tracks: tokens, tool calls, wall time, retries
- Can stop execution if budgets exceeded

### 6.3 Guardrails System
**Three layers of safety**:
1. **LLM Guardrails** (`guardrails_llm.py`): Validate LLM inputs/outputs
2. **State Guardrails** (`guardrails_state.py`): Validate state integrity
3. **Tool Guardrails** (`guardrails_tools.py`): Validate tool safety

### 6.4 Observability (OpenTelemetry)
```python
tracer = trace.get_tracer("strands")
with tracer.start_as_current_span("agent-execution") as span:
    span.set_attribute("agent.name", agent.name)
    span.set_attribute("instruction", instruction)
    # LangSmith traces all this
```

### 6.5 Capability-Driven Routing
- **Planner creates steps** using only available capabilities
- **Delegator maps keywords** to agents
- **Extensible**: Add new capabilities by:
  1. Adding to `AGENT_CAPABILITIES`
  2. Add tools to registry
  3. Planner automatically considers it

---

## 7. ERROR HANDLING & RETRY LOGIC

### Retry Budget
- Max retries: 3
- Deployment circuits: If agent fails, `CircuitBreaker` in `budget/circuit_breaker.py`

### Error Flows
- LLM fails → `BudgetHooks.on_error()` → increment retry_attempts
- Tool fails → Caught, error message sent, step_index incremented
- Invalid plan → Planner returns error message, graph proceeds to END
- Critic safety violation → May loop or terminate based on `is_safe` flag

---

## 8. PERFORMANCE CHARACTERISTICS

| Phase | Typical Duration | Token Usage | Tool Calls |
|-------|------------------|-------------|------------|
| Planning | ~1-2s | ~50 tokens | 0 |
| Research | ~2-3s | ~75 tokens | 1 (google_search) |
| Summarization | ~1-2s | ~45 tokens | 0 |
| Critic (per step) | ~1s | ~30 tokens | 0 |
| **Total** | **~5-8s** | **~200 tokens** | **1-2 tools** |

---

## 9. SUMMARY

When `dry_run.py` runs with input **"What is MCP"**:

1. ✅ **Initialization**: State + Budget created
2. ✅ **Planner**: Breaks request into: `["search: ...", "summarize: ..."]`
3. ✅ **Delegator (1st)**: Routes "search" → ResearchAgent
4. ✅ **Research**: Calls google_search tool → MCP results
5. ✅ **Critic**: Evaluates → continue (more steps)
6. ✅ **Delegator (2nd)**: Routes "summarize" → SummarizerAgent
7. ✅ **Summarizer**: Condenses results → concise explanation
8. ✅ **Critic**: Evaluates → END (all steps done)
9. ✅ **Output**: Final message with MCP explanation + budget stats

**All interactions are traced to LangSmith** for observability and debugging.
