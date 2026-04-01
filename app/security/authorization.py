"""
Authorization service - handles action-level permissions and RBAC
"""
from typing import Optional, List, Dict
from app.security.models import (
    TokenPayload, Action, UserRole, AuthorizationResult
)


class AuthorizationService:
    """Manages authorization and permission checking"""
    
    def __init__(self):
        """Initialize authorization with role-to-action mappings"""
        self.role_permissions: Dict[UserRole, List[Action]] = {
            UserRole.ADMIN: [
                Action.RESEARCH, Action.SUMMARIZE, Action.PLAN, Action.CRITIQUE,
                Action.EXECUTE_WORKFLOW, Action.VIEW_RESULTS, Action.MANAGE_USERS,
                Action.MODIFY_POLICIES
            ],
            UserRole.MANAGER: [
                Action.RESEARCH, Action.SUMMARIZE, Action.PLAN, Action.CRITIQUE,
                Action.EXECUTE_WORKFLOW, Action.VIEW_RESULTS
            ],
            UserRole.USER: [
                Action.RESEARCH, Action.SUMMARIZE, Action.PLAN, Action.CRITIQUE,
                Action.EXECUTE_WORKFLOW, Action.VIEW_RESULTS
            ],
            UserRole.GUEST: [
                Action.VIEW_RESULTS
            ]
        }
        
        # Agent-to-action mapping
        self.agent_actions: Dict[str, Action] = {
            "ResearchAgent": Action.RESEARCH,
            "SummarizerAgent": Action.SUMMARIZE,
            "PlannerAgent": Action.PLAN,
            "CriticAgent": Action.CRITIQUE,
        }
        
        # Action-based rate limits (requests per hour)
        self.action_rate_limits: Dict[Action, int] = {
            Action.RESEARCH: 100,
            Action.SUMMARIZE: 200,
            Action.PLAN: 50,
            Action.CRITIQUE: 75,
            Action.EXECUTE_WORKFLOW: 25,
            Action.VIEW_RESULTS: 1000,
            Action.MANAGE_USERS: 50,
            Action.MODIFY_POLICIES: 10,
        }
    
    def check_action_permission(
        self,
        token_payload: TokenPayload,
        action: Action
    ) -> AuthorizationResult:
        """Check if user has permission to perform action"""
        
        # Check if action is in user's permissions
        if action in token_payload.permissions:
            return AuthorizationResult(
                authorized=True,
                action=action,
                user_roles=token_payload.roles,
                permissions=token_payload.permissions
            )
        
        # Find which role would be required
        required_role = None
        for role in token_payload.roles:
            if action in self.role_permissions[role]:
                required_role = role
                break
        
        reason = f"User {token_payload.username} does not have permission for action: {action.value}"
        print(f"⚠️ {reason}")
        
        return AuthorizationResult(
            authorized=False,
            reason=reason,
            required_role=required_role,
            action=action,
            user_roles=token_payload.roles,
            permissions=token_payload.permissions
        )
    
    def check_agent_access(
        self,
        token_payload: TokenPayload,
        agent_name: str
    ) -> AuthorizationResult:
        """Check if user has permission to use an agent"""
        
        action = self.agent_actions.get(agent_name)
        if action is None:
            reason = f"Unknown agent: {agent_name}"
            print(f"❌ {reason}")
            return AuthorizationResult(
                authorized=False,
                reason=reason,
                action=Action.RESEARCH,  # Default action
                user_roles=token_payload.roles,
                permissions=token_payload.permissions
            )
        
        return self.check_action_permission(token_payload, action)
    
    def get_user_permissions(self, token_payload: TokenPayload) -> List[Action]:
        """Get all permissions for a user based on their roles"""
        permissions = set()
        for role in token_payload.roles:
            permissions.update(self.role_permissions[role])
        return list(permissions)
    
    def grant_action_permission(
        self,
        token_payload: TokenPayload,
        user_id: str,
        action: Action
    ) -> bool:
        """Grant specific action permission to user (requires ADMIN role)"""
        
        # Check if requester is admin
        if UserRole.ADMIN not in token_payload.roles:
            print(
                f"⚠️ User {token_payload.username} attempted to grant permissions without admin role"
            )
            return False
        return True
    
    def get_rate_limit(self, action: Action) -> int:
        """Get rate limit for an action (requests per hour)"""
        return self.action_rate_limits.get(action, 100)
    
    def update_action_permissions(
        self,
        action: Action,
        allowed_roles: List[UserRole]
    ) -> bool:
        """Update which roles can perform an action (requires ADMIN)"""
        for role in allowed_roles:
            if action not in self.role_permissions[role]:
                self.role_permissions[role].append(action)
        
        return True


# Global instance
auth_service = AuthorizationService()
