"""
Zero Trust implementation for agent system
"""
from typing import Dict, Optional, Any
from app.utils.logger import logger
from app.security.agent_identities import agent_identity_manager
from app.security.jit_manager import jit_manager
from app.security.authorization import authz_service
from app.security.models import Action


class ZeroTrustEnforcer:
    """Enforces zero trust principles across the system"""

    def __init__(self):
        self.trust_policies = {
            "agent_communication": self._verify_agent_communication,
            "tool_access": self._verify_tool_access,
            "state_transition": self._verify_state_transition,
        }

    def enforce_trust(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce zero trust for an operation

        Args:
            operation: Type of operation (e.g., 'agent_communication', 'tool_access')
            context: Context data for the operation

        Returns:
            dict: Result with 'trusted', 'reason', and optional 'token'
        """
        policy = self.trust_policies.get(operation)
        if not policy:
            logger.security_error("Unknown zero trust operation", operation=operation)
            return {"trusted": False, "reason": f"Unknown operation: {operation}"}

        try:
            return policy(context)
        except Exception as e:
            logger.security_error("Zero trust enforcement failed", operation=operation, error=str(e))
            return {"trusted": False, "reason": f"Enforcement error: {str(e)}"}

    def _verify_agent_communication(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify agent-to-agent communication"""
        from_agent = context.get("from_agent")
        to_agent = context.get("to_agent")
        message = context.get("message", "")
        signature = context.get("signature")

        if not all([from_agent, to_agent, signature]):
            return {"trusted": False, "reason": "Missing required fields for agent communication"}

        # Verify sender identity
        if not agent_identity_manager.authenticate_agent(from_agent, signature, message):
            return {"trusted": False, "reason": f"Invalid signature from {from_agent}"}

        # Check if communication is allowed (delegation policy)
        allowed_communications = {
            "PlannerAgent": ["ResearchAgent", "SummarizerAgent", "Delegator"],
            "ResearchAgent": ["CriticAgent"],
            "SummarizerAgent": ["CriticAgent"],
            "CriticAgent": ["Delegator"],
        }

        if to_agent not in allowed_communications.get(from_agent, []):
            return {"trusted": False, "reason": f"{from_agent} cannot communicate with {to_agent}"}

        # Issue JIT token for the communication
        jit_token = jit_manager.request_privilege(
            subject=from_agent,
            resource=to_agent,
            action="communicate",
            duration_seconds=60  # 1 minute for communication
        )

        if not jit_token:
            return {"trusted": False, "reason": "JIT privilege denied"}

        logger.security_check("Agent communication verified",
                            from_agent=from_agent,
                            to_agent=to_agent,
                            token_id=jit_token.token_id)

        return {
            "trusted": True,
            "reason": "Agent communication authorized",
            "jit_token": jit_token.token_id
        }

    def _verify_tool_access(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify tool access"""
        agent = context.get("agent")
        tool = context.get("tool")
        user_permissions = context.get("user_permissions", [])

        if not all([agent, tool]):
            return {"trusted": False, "reason": "Missing required fields for tool access"}

        # Map tools to required actions
        tool_action_map = {
            "web_search": Action.RESEARCH,
            "file_write": Action.EXECUTE_WORKFLOW,
            "data_analyze": Action.SUMMARIZE,
            "api_call": Action.RESEARCH,
        }

        required_action = tool_action_map.get(tool)
        if not required_action:
            return {"trusted": False, "reason": f"Unknown tool: {tool}"}

        # Check if user has permission
        if required_action not in user_permissions:
            return {"trusted": False, "reason": f"User lacks permission for {required_action.value}"}

        # Issue JIT token for tool access
        jit_token = jit_manager.request_privilege(
            subject=agent,
            resource=tool,
            action="use_tool",
            duration_seconds=30  # 30 seconds for tool use
        )

        if not jit_token:
            return {"trusted": False, "reason": "JIT privilege denied for tool access"}

        logger.security_check("Tool access verified",
                            agent=agent,
                            tool=tool,
                            token_id=jit_token.token_id)

        return {
            "trusted": True,
            "reason": "Tool access authorized",
            "jit_token": jit_token.token_id
        }

    def _verify_state_transition(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify state transitions in the graph"""
        from_state = context.get("from_state")
        to_state = context.get("to_state")
        agent = context.get("agent")

        if not all([from_state, to_state, agent]):
            return {"trusted": False, "reason": "Missing required fields for state transition"}

        # Define allowed state transitions
        allowed_transitions = {
            "planner": ["delegator"],
            "delegator": ["research", "summarizer"],
            "research": ["critic"],
            "summarizer": ["critic"],
            "critic": ["delegator", "end"],
        }

        if to_state not in allowed_transitions.get(from_state, []):
            return {"trusted": False, "reason": f"Invalid state transition: {from_state} -> {to_state}"}

        logger.security_check("State transition verified",
                            from_state=from_state,
                            to_state=to_state,
                            agent=agent)

        return {
            "trusted": True,
            "reason": "State transition authorized"
        }


# Global instance
zero_trust_enforcer = ZeroTrustEnforcer()