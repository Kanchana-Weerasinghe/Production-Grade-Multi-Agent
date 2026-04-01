"""
Authorization hooks for orchestrator - integrates auth checks into agent workflow
"""
from typing import Optional
from app.security.models import TokenPayload, ActionRequest
from app.security.authorization import auth_service


class OrchestrationAuthorizationHooks:
    """Hooks to enforce authorization in the orchestration workflow"""
    
    @staticmethod
    def before_agent_execution(
        token_payload: TokenPayload,
        agent_name: str,
        state: dict
    ) -> bool:
        """
        Check authorization before executing an agent
        
        Args:
            token_payload: JWT token payload with user info
            agent_name: Name of agent to execute
            state: Current orchestration state
            
        Returns:
            bool: True if authorized, False otherwise
        """
        result = auth_service.check_agent_access(token_payload, agent_name)
        
        if not result.authorized:
            print(
                f"❌ Authorization failed for agent {agent_name}: {result.reason}"
            )
            return False
        
        print(
            f"✅ Authorization granted for user {token_payload.username} "
            f"to execute agent {agent_name}"
        )
        
        # Add authorization info to state
        state["_auth_info"] = {
            "user_id": token_payload.user_id,
            "username": token_payload.username,
            "agent": agent_name,
            "timestamp": str(__import__('datetime').datetime.utcnow()),
        }
        
        return True
    
    @staticmethod
    def before_tool_execution(
        token_payload: TokenPayload,
        tool_name: str,
        state: dict
    ) -> bool:
        """
        Check authorization before executing a tool
        
        Args:
            token_payload: JWT token payload
            tool_name: Name of tool to execute
            state: Orchestration state
            
        Returns:
            bool: True if authorized, False otherwise
        """
        # Tools inherit permissions from their parent agent
        # Get agent name from state
        agent_name = state.get("selected_agent", "Unknown")
        
        # Verify user has access to the parent agent's action
        result = auth_service.check_agent_access(token_payload, agent_name)
        
        if not result.authorized:
            print(
                f"❌ Tool authorization failed: {tool_name} (user: {token_payload.username})"
            )
            return False
        
        return True
    
    @staticmethod
    def on_authorization_failure(
        token_payload: Optional[TokenPayload],
        action: str,
        error_message: str,
        state: dict
    ) -> dict:
        """
        Handle authorization failures
        
        Args:
            token_payload: JWT token payload (may be None)
            action: Action that was attempted
            error_message: Failure reason
            state: Orchestration state
            
        Returns:
            dict: Updated state with error information
        """
        user_info = (
            f"{token_payload.username} ({token_payload.user_id})"
            if token_payload
            else "Unknown"
        )
        
        print(
            f"⚠️ Authorization failure: {action} for user {user_info} - {error_message}"
        )
        
        state["is_safe"] = False
        state["last_error"] = f"Authorization denied: {error_message}"
        state["messages"] = [
            ("assistant", f"🔒 Access denied: You don't have permission to perform this action.")
        ]
        
        return state
    
    @staticmethod
    def inject_auth_context(state: dict, token_payload: TokenPayload) -> dict:
        """
        Inject authentication context into state for tracking and auditing
        
        Args:
            state: Orchestration state
            token_payload: JWT token payload
            
        Returns:
            dict: State with auth context injected
        """
        state["_auth_context"] = {
            "user_id": token_payload.user_id,
            "username": token_payload.username,
            "roles": [r.value for r in token_payload.roles],
            "permissions": [p.value for p in token_payload.permissions],
            "token_issued_at": token_payload.iat.isoformat(),
            "token_expires_at": token_payload.exp.isoformat(),
        }
        
        return state


# Global instance
orchestration_auth_hooks = OrchestrationAuthorizationHooks()
