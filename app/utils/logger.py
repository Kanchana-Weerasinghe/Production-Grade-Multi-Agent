"""
Centralized logging utility for Travo multi-agent system.
Provides structured, meaningful logging with different verbosity levels.
"""
from enum import Enum
from typing import Any, Dict, Optional
import json


class LogLevel(Enum):
    """Log verbosity levels"""
    SILENT = 0
    ERROR = 1
    WARN = 2
    INFO = 3
    DEBUG = 4
    TRACE = 5


class TravoLogger:
    """Centralized logger for Travo agents and orchestrator"""
    
    _current_level = LogLevel.INFO
    
    @classmethod
    def set_level(cls, level: LogLevel) -> None:
        """Set global log level"""
        cls._current_level = level
        
    @classmethod
    def _format_message(cls, level: str, category: str, title: str, data: Dict[str, Any] = None) -> str:
        """Format log message consistently"""
        msg = f"\n{level} [{category}] {title}"
        if data:
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    msg += f"\n   {key}: {json.dumps(value, default=str, indent=2)[:200]}..."
                else:
                    msg += f"\n   {key}: {value}"
        return msg + "\n"
    
    @classmethod
    def agent_start(cls, agent_name: str) -> None:
        """Log agent startup"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(f"\n{'='*60}")
            print(f"🤖 AGENT START: {agent_name}")
            print(f"{'='*60}\n")
    
    @classmethod
    def agent_end(cls, agent_name: str, status: str = "SUCCESS") -> None:
        """Log agent completion"""
        if cls._current_level.value >= LogLevel.INFO.value:
            icon = "✅" if status == "SUCCESS" else "❌"
            print(f"\n{icon} AGENT END: {agent_name} ({status})\n")
    
    # PLANNER LOGS
    @classmethod
    def planner_input(cls, user_input: str) -> None:
        """Log planner input"""
        if cls._current_level.value >= LogLevel.DEBUG.value:
            print(cls._format_message("🧠", "PLANNER", "User Input Received", {
                "input": user_input[:100]
            }))
    
    @classmethod
    def planner_steps_raw(cls, steps: Any) -> None:
        """Log raw planner output"""
        if cls._current_level.value >= LogLevel.TRACE.value:
            print(cls._format_message("🧠", "PLANNER", "Raw Steps from LLM", {
                "steps": str(steps)[:200]
            }))
    
    @classmethod
    def planner_steps_normalized(cls, steps: list) -> None:
        """Log normalized steps"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("🧠", "PLANNER", "Plan Created", {
                "step_count": len(steps),
                "steps": "\n".join([f"  {i+1}. {s}" for i, s in enumerate(steps)])
            }))
    
    @classmethod
    def planner_error(cls, error: str) -> None:
        """Log planner error"""
        if cls._current_level.value >= LogLevel.ERROR.value:
            print(cls._format_message("❌", "PLANNER", "Plan Validation Failed", {
                "error": error
            }))
    
    # DELEGATOR LOGS
    @classmethod
    def delegator_start(cls, step_index: int, total_steps: int) -> None:
        """Log delegator starting"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("🎯", "DELEGATOR", "Task Assignment Started", {
                "step": f"{step_index + 1}/{total_steps}"
            }))
    
    @classmethod
    def delegator_selected(cls, agent: str, task: str) -> None:
        """Log agent selection"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("🎯", "DELEGATOR", "Agent Selected", {
                "agent": agent,
                "task": task[:100]
            }))
    
    @classmethod
    def delegator_error(cls, error: str) -> None:
        """Log delegator error"""
        if cls._current_level.value >= LogLevel.ERROR.value:
            print(cls._format_message("❌", "DELEGATOR", "Selection Failed", {
                "error": error
            }))
    
    # RESEARCH AGENT LOGS
    @classmethod
    def research_start(cls, instruction: str) -> None:
        """Log research starting"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("🔍", "RESEARCH", "Task Started", {
                "instruction": instruction[:100]
            }))
    
    @classmethod
    def research_tools_available(cls, tools: list) -> None:
        """Log available tools"""
        if cls._current_level.value >= LogLevel.DEBUG.value:
            print(cls._format_message("🔍", "RESEARCH", "Available Tools", {
                "tools": ", ".join(tools)
            }))
    
    @classmethod
    def research_tool_selected(cls, tool_name: str) -> None:
        """Log selected tool"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("🔍", "RESEARCH", "Tool Selected", {
                "tool": tool_name
            }))
    
    @classmethod
    def research_tool_executing(cls, tool_name: str, query: str) -> None:
        """Log tool execution"""
        if cls._current_level.value >= LogLevel.DEBUG.value:
            print(cls._format_message("🔍", "RESEARCH", "Executing Tool", {
                "tool": tool_name,
                "query": query[:100]
            }))
    
    @classmethod
    def research_tool_result(cls, result_count: int = None) -> None:
        """Log tool result"""
        if cls._current_level.value >= LogLevel.INFO.value:
            data = {}
            if result_count:
                data["results_found"] = result_count
            print(cls._format_message("🔍", "RESEARCH", "Tool Execution Complete", data))
    
    @classmethod
    def research_error(cls, error: str) -> None:
        """Log research error"""
        if cls._current_level.value >= LogLevel.ERROR.value:
            print(cls._format_message("❌", "RESEARCH", "Execution Failed", {
                "error": error
            }))
    
    # SUMMARIZER LOGS
    @classmethod
    def summarizer_start(cls) -> None:
        """Log summarizer starting"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("📝", "SUMMARIZER", "Summarization Started", {}))
    
    @classmethod
    def summarizer_input_received(cls, data_type: str, data_size: str = None) -> None:
        """Log input data received"""
        if cls._current_level.value >= LogLevel.DEBUG.value:
            data = {"input_type": data_type}
            if data_size:
                data["size"] = data_size
            print(cls._format_message("📝", "SUMMARIZER", "Input Data Received", data))
    
    @classmethod
    def summarizer_result(cls, summary_length: int) -> None:
        """Log summarizer result"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("📝", "SUMMARIZER", "Summary Generated", {
                "summary_length": f"{summary_length} chars"
            }))
    
    @classmethod
    def summarizer_error(cls, error: str) -> None:
        """Log summarizer error"""
        if cls._current_level.value >= LogLevel.ERROR.value:
            print(cls._format_message("❌", "SUMMARIZER", "Summarization Failed", {
                "error": error
            }))
    
    # CRITIC LOGS
    @classmethod
    def critic_start(cls, step_index: int, total_steps: int) -> None:
        """Log critic starting"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("⚖️", "CRITIC", "Evaluation Started", {
                "step": f"{step_index}/{total_steps}"
            }))
    
    @classmethod
    def critic_decision(cls, is_safe: bool, should_continue: bool, notes: str = None) -> None:
        """Log critic decision"""
        if cls._current_level.value >= LogLevel.INFO.value:
            decision_str = "CONTINUE" if should_continue else "END"
            icon = "✅" if is_safe else "⚠️"
            print(cls._format_message(icon, "CRITIC", f"Decision: {decision_str}", {
                "safe": is_safe,
                "continue": should_continue,
                "notes": notes[:100] if notes else None
            }))
    
    @classmethod
    def critic_error(cls, error: str) -> None:
        """Log critic error"""
        if cls._current_level.value >= LogLevel.ERROR.value:
            print(cls._format_message("❌", "CRITIC", "Evaluation Failed", {
                "error": error
            }))
    
    # GRAPH LOGS
    @classmethod
    def graph_building(cls) -> None:
        """Log graph building start"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(f"\n{'='*60}")
            print(f"🏗️  BUILDING GRAPH")
            print(f"{'='*60}\n")
    
    @classmethod
    def graph_built(cls) -> None:
        """Log graph completion"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(f"\n✅ GRAPH READY\n")
    
    @classmethod
    def graph_execution_start(cls, config_name: str) -> None:
        """Log graph execution start"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(f"\n{'='*60}")
            print(f"🚀 STARTING EXECUTION: {config_name}")
            print(f"{'='*60}\n")
    
    @classmethod
    def graph_node_complete(cls, node_name: str) -> None:
        """Log node completion"""
        if cls._current_level.value >= LogLevel.DEBUG.value:
            print(f"  ✓ {node_name}")
    
    @classmethod
    def graph_execution_end(cls) -> None:
        """Log graph execution end"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(f"\n{'='*60}")
            print(f"✅ EXECUTION COMPLETE")
            print(f"{'='*60}\n")
    
    # BUDGET LOGS
    @classmethod
    def budget_check(cls, budget_type: str, current: int, max_allowed: int) -> None:
        """Log budget check"""
        if cls._current_level.value >= LogLevel.DEBUG.value:
            percentage = (current / max_allowed * 100) if max_allowed > 0 else 0
            status = "✅" if current < max_allowed else "⚠️"
            print(f"{status} [BUDGET] {budget_type}: {current}/{max_allowed} ({percentage:.1f}%)")
    
    # TRACE LOGS (verbose)
    @classmethod
    def trace_state_keys(cls, keys: list) -> None:
        """Log state keys"""
        if cls._current_level.value >= LogLevel.TRACE.value:
            print(f"  🔍 State keys: {', '.join(keys)}")
    
    @classmethod
    def trace_value(cls, name: str, value: Any) -> None:
        """Log trace value"""
        if cls._current_level.value >= LogLevel.TRACE.value:
            if isinstance(value, (dict, list)):
                print(f"  📊 {name}: {type(value).__name__}")
            else:
                print(f"  📊 {name}: {value}")
    
    # SECURITY LOGS
    @classmethod
    def security_check(cls, message: str, **kwargs) -> None:
        """Log security validation success"""
        if cls._current_level.value >= LogLevel.INFO.value:
            print(cls._format_message("🔒", "SECURITY", message, kwargs))
    
    @classmethod
    def security_warning(cls, message: str, **kwargs) -> None:
        """Log security warning"""
        if cls._current_level.value >= LogLevel.WARN.value:
            print(cls._format_message("⚠️", "SECURITY", message, kwargs))
    
    @classmethod
    def security_error(cls, message: str, **kwargs) -> None:
        """Log security error"""
        if cls._current_level.value >= LogLevel.ERROR.value:
            print(cls._format_message("🚨", "SECURITY", message, kwargs))
    
    @classmethod
    def security_alert(cls, message: str, **kwargs) -> None:
        """Log security alert (always shown)"""
        print(cls._format_message("🚨🚨", "SECURITY ALERT", message, kwargs))


# Global logger instance
logger = TravoLogger()
