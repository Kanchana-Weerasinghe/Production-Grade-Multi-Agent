"""
Security module - authentication and authorization
"""
from app.security.models import (
    UserRole, Action, TokenPayload, UserCredentials, UserInfo,
    ActionRequest, AuthorizationResult
)
from app.security.authentication import auth_service, AuthenticationService
from app.security.authorization import auth_service as authz_service, AuthorizationService
from app.security.middleware import (
    AuthenticationMiddleware, get_current_user, check_action_authorization
)
from app.security.orchestration_hooks import (
    OrchestrationAuthorizationHooks, orchestration_auth_hooks
)

__all__ = [
    # Models
    "UserRole",
    "Action",
    "TokenPayload",
    "UserCredentials",
    "UserInfo",
    "ActionRequest",
    "AuthorizationResult",
    # Services
    "auth_service",
    "AuthenticationService",
    "authz_service",
    "AuthorizationService",
    # Middleware
    "AuthenticationMiddleware",
    "get_current_user",
    "check_action_authorization",
    # Hooks
    "OrchestrationAuthorizationHooks",
    "orchestration_auth_hooks",
]
