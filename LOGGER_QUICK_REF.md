# Logger Quick Reference Card

## 🎯 Set Log Level (do this once in `dry_run.py`)

```python
from app.utils.logger import logger, LogLevel

# Pick ONE:
logger.set_level(LogLevel.SILENT)    # 🔇 No output (production)
logger.set_level(LogLevel.ERROR)     # 🔴 Errors only
logger.set_level(LogLevel.WARN)      # 🟡 Warnings + errors
logger.set_level(LogLevel.INFO)      # 🟢 DEFAULT - recommended
logger.set_level(LogLevel.DEBUG)     # 🔵 Lots of details
logger.set_level(LogLevel.TRACE)     # 🟣 Everything (very verbose)
```

---

## 📊 Graph Logging

```python
logger.graph_building()                # Start building graph
logger.graph_built()                   # Graph construction complete
logger.graph_execution_start("name")   # Begin execution
logger.graph_node_complete("node_name")# Node finished
logger.graph_execution_end()           # All execution done
```

---

## 🤖 Agent Lifecycle

```python
logger.agent_start("AGENT_NAME")              # Agent started
logger.agent_end("AGENT_NAME", "SUCCESS")     # Agent completed successfully
logger.agent_end("AGENT_NAME", "ERROR")       # Agent failed
```

---

## 🧠 Planner Agent

```python
logger.planner_input("What is MCP")                 # User input
logger.planner_steps_raw(steps)                     # Raw LLM output (TRACE level)
logger.planner_steps_normalized(["search: ...", "summarize: ..."])  # Processed
logger.planner_error("Invalid plan: ...")          # Error occurred
```

---

## 🔍 Research Agent

```python
logger.research_start("Find MCP info")                      # Task started
logger.research_tools_available(["google_search"])          # Tools available
logger.research_tool_selected("google_search")              # Tool chosen
logger.research_tool_executing("google_search", "MCP")      # Running
logger.research_tool_result(5)                              # 5 results found
logger.research_error("Tool failed: ...")                   # Error
```

---

## 📝 Summarizer Agent

```python
logger.summarizer_start()                   # Started
logger.summarizer_input_received("dict")    # Data type received
logger.summarizer_result(250)               # 250 char summary
logger.summarizer_error("No data")          # Error
```

---

## 🎯 Delegator

```python
logger.delegator_start(0, 2)                        # Starting (step 0 of 2)
logger.delegator_selected("ResearchAgent", "...")   # Agent picked
logger.delegator_error("No steps found")            # Error
```

---

## ⚖️ Critic

```python
logger.critic_start(1, 2)                                  # Starting (step 1 of 2)
logger.critic_decision(True, True, "Quality: excellent")  # Evaluation result
logger.critic_error("Could not evaluate")                 # Error
```

---

## 🔧 Utility Methods

```python
logger.budget_check("tokens", 500, 10000)    # Show budget: 500/10000 (5%)
logger.trace_value("variable_name", value)   # Show trace value (TRACE level)
logger.trace_state_keys(["key1", "key2"])    # Show state keys (TRACE level)
```

---

## 📋 Comparison: Before vs After

### Before (Confusing) ❌
```
🟦 State keys: ['messages', 'next_steps', 'current_step_index', ...]
🟦 Instruction from next_steps: search: Find information about MCP protocol
🟩 Available tools for ResearchAgent: ['google_search']
🟨 Calling LLM ToolSelector...
🟧 Normalized selected_tool_name: 'google_search'
🟦 Final selected tool: google_search
🚀 Executing tool 'google_search' with query: Find information about MCP protocol
✅ Tool execution completed successfully.
⚖️ Critic Decision → safe=true continue=true
```

### After (Organized) ✅
```
============================================================
🤖 AGENT START: RESEARCH
============================================================

🔍 [RESEARCH] Task Started
   instruction: Find information about MCP protocol

🔍 [RESEARCH] Available Tools
   tools: google_search

🔍 [RESEARCH] Tool Selected
   tool: google_search

🔍 [RESEARCH] Executing Tool
   tool: google_search
   query: Find information about MCP protocol

🔍 [RESEARCH] Tool Execution Complete
   results_found: 5

✅ AGENT END: RESEARCH (SUCCESS)
```

---

## 🎮 Example: Complete Flow

```python
# In dry_run.py:
from app.utils.logger import logger, LogLevel

logger.set_level(LogLevel.INFO)  # ← Set once here

# During execution, these logs appear automatically:

# 1. Graph starts
logger.graph_execution_start("Travo_System_Dry_Run")

# 2. Planner runs
logger.agent_start("PLANNER")
logger.planner_input("What is MCP")
logger.planner_steps_normalized([...])
logger.agent_end("PLANNER", "SUCCESS")

# 3. Delegator runs
logger.delegator_start(0, 2)
logger.delegator_selected("ResearchAgent", "search: ...")

# 4. Research runs
logger.agent_start("RESEARCH")
logger.research_start("Find information...")
logger.research_tools_available(["google_search"])
logger.research_tool_selected("google_search")
logger.research_tool_result(5)
logger.agent_end("RESEARCH", "SUCCESS")

# 5. Summarizer runs
logger.agent_start("SUMMARIZER")
logger.summarizer_start()
logger.summarizer_result(200)
logger.agent_end("SUMMARIZER", "SUCCESS")

# 6. Critic runs
logger.agent_start("CRITIC")
logger.critic_start(1, 2)
logger.critic_decision(True, False, "All steps complete")
logger.agent_end("CRITIC", "SUCCESS")

# 7. Execution ends
logger.graph_execution_end()
```

---

## 🚀 Common Use Cases

### I want quiet output for production:
```python
logger.set_level(LogLevel.SILENT)
```

### I want to debug an issue:
```python
logger.set_level(LogLevel.DEBUG)  # More details
# or even:
logger.set_level(LogLevel.TRACE)  # Everything
```

### I want only errors:
```python
logger.set_level(LogLevel.ERROR)
```

### I want the normal experience:
```python
logger.set_level(LogLevel.INFO)  # ← This is the default
```

---

## 📚 More Info

See [LOGGING_GUIDE.md](LOGGING_GUIDE.md) for complete documentation with examples.

See [LOGGING_REFACTOR_SUMMARY.md](LOGGING_REFACTOR_SUMMARY.md) for all changes made.
