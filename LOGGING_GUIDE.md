# Logging System Guide

## Overview
The Travo system now uses a **centralized, structured logging utility** that provides meaningful, organized output with configurable verbosity levels.

## Quick Start

### Set Log Level in `dry_run.py`
```python
from app.utils.logger import logger, LogLevel

# Choose one:
logger.set_level(LogLevel.SILENT)      # ❌ No output
logger.set_level(LogLevel.ERROR)       # 🔴 Errors only
logger.set_level(LogLevel.WARN)        # 🟡 Warnings & errors
logger.set_level(LogLevel.INFO)        # 🟢 (DEFAULT) Info, warnings, errors
logger.set_level(LogLevel.DEBUG)       # 🔵 Detailed debugging info
logger.set_level(LogLevel.TRACE)       # 🟣 Very verbose, all details
```

## Log Levels Explained

| Level | Usage | Example Output |
|-------|-------|-----------------|
| **SILENT** | Production mode - no logs | (nothing) |
| **ERROR** | Critical failures only | ❌ [AGENT] Error message |
| **WARN** | Errors + warnings | ⚠️ Issues that don't stop execution |
| **INFO** | **Default** - main events | ✅ Agent started, task completed |
| **DEBUG** | Detailed info for debugging | Tool selection, budget checks |
| **TRACE** | Extremely verbose | All state changes, router decisions |

## Available Logger Methods

### Graph Lifecycle
```python
logger.graph_building()              # Start building graph
logger.graph_built()                 # Graph construction complete
logger.graph_execution_start(name)   # Begin execution
logger.graph_node_complete(node)     # Node finished
logger.graph_execution_end()         # All execution done
```

### Agent Lifecycle
```python
logger.agent_start("AGENT_NAME")     # Agent started
logger.agent_end("AGENT_NAME", "SUCCESS")  # Agent completed
logger.agent_end("AGENT_NAME", "ERROR")    # Agent failed
```

### Planner Logging
```python
logger.planner_input(user_input)              # User question
logger.planner_steps_raw(steps)               # Raw LLM output (TRACE level)
logger.planner_steps_normalized(steps)        # Processed steps
logger.planner_error(error_message)           # Validation failed
```

### Research Agent Logging
```python
logger.research_start(instruction)            # Task started
logger.research_tools_available(tool_list)    # Available tools
logger.research_tool_selected(tool_name)      # Tool choice made
logger.research_tool_executing(tool, query)   # Running tool
logger.research_tool_result(count)            # Results received
logger.research_error(error_msg)              # Tool failed
```

### Summarizer Logging
```python
logger.summarizer_start()                     # Started
logger.summarizer_input_received(type)        # Data type received
logger.summarizer_result(length)              # Summary length
logger.summarizer_error(error_msg)            # Failed
```

### Delegator Logging
```python
logger.delegator_start(index, total)          # Starting delegation
logger.delegator_selected(agent, task)        # Agent selected
logger.delegator_error(error_msg)             # Failed to delegate
```

### Critic Logging
```python
logger.critic_start(index, total)             # Evaluation started
logger.critic_decision(safe, continue, notes) # Evaluation result
logger.critic_error(error_msg)                # Evaluation failed
```

### Utility Logging
```python
logger.budget_check("tokens", 500, 10000)    # Budget status
logger.trace_value("variable_name", value)   # Debug trace
logger.trace_state_keys(key_list)            # State contents
```

## Output Examples

### INFO Level (Default)
```
============================================================
🚀 STARTING EXECUTION: Travo_System_Dry_Run
============================================================

============================================================
🤖 AGENT START: PLANNER
============================================================

🧠 [PLANNER] User Input Received
   input: What is MCP

🧠 [PLANNER] Plan Created
   step_count: 2
   steps: 
  1. search: Find information about MCP protocol
  2. summarize: Create a concise explanation

🤖 AGENT END: PLANNER (SUCCESS)

🎯 [DELEGATOR] Task Assignment Started
   step: 1/2

🎯 [DELEGATOR] Agent Selected
   agent: ResearchAgent
   task: search: Find information about MCP protocol
```

### DEBUG Level
```
... (all INFO level logs, plus:)

🔍 [RESEARCH] Available Tools
   tools: google_search

🔍 [RESEARCH] Executing Tool
   tool: google_search
   query: Find information about MCP protocol
```

### TRACE Level
```
... (all DEBUG level logs, plus:)

📊 State keys: messages, next_steps, current_step_index, ...
📊 Current step: search: find information about mcp protocol
📊 Router selected agent: ResearchAgent
```

## Best Practices

### ✅ DO
- Use `logger.set_level(LogLevel.INFO)` for normal runs
- Use `logger.set_level(LogLevel.DEBUG)` when investigating issues  
- Use `logger.set_level(LogLevel.SILENT)` for production
- Always call `logger.agent_start()` and `logger.agent_end()` in agents

### ❌ DON'T
- Mix old `print()` statements with new logger (been removed)
- Use external logging libraries (use centralized logger)
- Add random debug prints (use logger methods instead)

## Changing Log Levels at Runtime

```python
# Start with DEBUG
logger.set_level(LogLevel.DEBUG)

# Later, switch to INFO
logger.set_level(LogLevel.INFO)
```

## Custom Messages

For special cases not covered by existing methods:
```python
# Format a custom message
msg = logger._format_message(
    level="🟠",
    category="CUSTOM",
    title="My Event",
    data={"key": "value"}
)
print(msg)
```

## Performance

- **SILENT level**: ~0% overhead (no string formatting)
- **INFO level**: ~1% overhead (only format important messages)
- **DEBUG level**: ~5% overhead (format more messages)
- **TRACE level**: ~15% overhead (format all messages)

## Troubleshooting

**Q: I don't see any logs**  
A: Set log level higher: `logger.set_level(LogLevel.TRACE)`

**Q: Too much noise in output**  
A: Lower log level: `logger.set_level(LogLevel.WARN)`

**Q: Missing information for debugging**  
A: Use TRACE level: `logger.set_level(LogLevel.TRACE)`

**Q: Where are the old print statements?**  
A: All replaced with structured logging! Check the logger methods above.
