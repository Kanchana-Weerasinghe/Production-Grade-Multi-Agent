"""
FastAPI middleware for authentication and authorization
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.security.authentication import auth_service


class AuthenticationMiddleware:
    """ASGI middleware to validate JWT tokens on protected endpoints"""
    
    def __init__(self, app, excluded_paths: list = None):
        """
        Initialize middleware
        
        Args:
            app: ASGI application
            excluded_paths: List of paths that don't require authentication
        """
        self.app = app
        self.excluded_paths = excluded_paths or [
            "/health",
            "/auth/login",
            "/auth/register",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "")
        
        # Skip authentication for excluded paths
        if path in self.excluded_paths:
            await self.app(scope, receive, send)
            return
        
        # Extract Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode("utf-8")
        
        if not auth_header:
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"}
            )
            await error_response(scope, receive, send)
            return
        
        # Extract and validate token
        token = auth_service.extract_token_from_header(auth_header)
        if not token:
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"}
            )
            await error_response(scope, receive, send)
            return
        
        # Verify token
        token_payload = auth_service.verify_token(token)
        if not token_payload:
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
            await error_response(scope, receive, send)
            return
        
        # Store token in scope state
        scope["user"] = {
            "user_id": token_payload.user_id,
            "username": token_payload.username,
            "token_payload": token_payload
        }
        
        await self.app(scope, receive, send)


def get_current_user(request: Request):
    """Dependency to get current authenticated user"""
    # Try to get from scope first (ASGI middleware sets it here)
    if "user" in request.scope and "token_payload" in request.scope["user"]:
        return request.scope["user"]["token_payload"]
    
    # Fallback to request.state for compatibility
    if hasattr(request.state, "token_payload"):
        return request.state.token_payload
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )


async def check_action_authorization(request: Request, action):
    """
    Dependency to check action-level authorization
    
    Args:
        request: FastAPI request
        action: Action enum value to check
    """
    from app.security.authorization import auth_service as authz_service
    
    token_payload = get_current_user(request)
    result = authz_service.check_action_permission(token_payload, action)
    
    if not result.authorized:
        print(
            f"⚠️ Authorization denied for user {token_payload.username} "
            f"on action {action.value}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.reason or "Insufficient permissions"
        )
    
    return result
