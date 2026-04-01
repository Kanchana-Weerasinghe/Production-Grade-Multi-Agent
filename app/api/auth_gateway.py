"""
Enhanced API gateway with authentication and authorization
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.security.models import (
    UserCredentials, UserInfo, Action, ActionRequest
)
from app.security.authentication import auth_service
from app.security.authorization import auth_service as authz_service
from app.security.middleware import get_current_user, check_action_authorization


class UserQueryRequest(BaseModel):
    """Request model for user queries to the orchestrator"""
    message: str


router = APIRouter()


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "Travo Agent"}


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/auth/login")
async def login(credentials: UserCredentials):
    """
    Login endpoint - authenticate user and return JWT token
    
    Args:
        credentials: UserCredentials with username and password
        
    Returns:
        dict: Token and user info on success
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user_info = auth_service.authenticate_user(credentials)
    
    if not user_info:
        print(f"⚠️ Failed login attempt: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = auth_service.create_token(user_info)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_info.user_id,
            "username": user_info.username,
            "roles": [r.value for r in user_info.roles],
            "permissions": [p.value for p in user_info.permissions],
        }
    }


@router.get("/auth/me")
async def get_current_user_info(token_payload = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Returns:
        dict: Current user info from token
    """
    return {
        "user_id": token_payload.user_id,
        "username": token_payload.username,
        "roles": [r.value for r in token_payload.roles],
        "permissions": [p.value for p in token_payload.permissions],
        "token_expires_at": token_payload.exp.isoformat(),
    }


# ============================================================================
# AUTHORIZATION ENDPOINTS
# ============================================================================

@router.get("/auth/permissions")
async def get_user_permissions(token_payload = Depends(get_current_user)):
    """
    Get all permissions available to current user
    
    Returns:
        dict: List of available actions and rate limits
    """
    permissions = authz_service.get_user_permissions(token_payload)
    
    return {
        "user_id": token_payload.user_id,
        "username": token_payload.username,
        "available_actions": [p.value for p in permissions],
        "rate_limits": {
            p.value: authz_service.get_rate_limit(p)
            for p in permissions
        }
    }


@router.post("/auth/check-permission/{action}")
async def check_permission(
    action: str,
    token_payload = Depends(get_current_user)
):
    """
    Check if user has permission for specific action
    
    Args:
        action: Action name to check (e.g., 'research', 'summarize')
        
    Returns:
        dict: Authorization result
    """
    try:
        action_enum = Action[action.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}"
        )
    
    result = authz_service.check_action_permission(token_payload, action_enum)
    
    return {
        "action": action,
        "authorized": result.authorized,
        "reason": result.reason,
        "user_roles": [r.value for r in result.user_roles],
        "user_permissions": [p.value for p in token_payload.permissions],
    }


@router.post("/auth/check-agent/{agent_name}")
async def check_agent_access(
    agent_name: str,
    token_payload = Depends(get_current_user)
):
    """
    Check if user has permission to access specific agent
    
    Args:
        agent_name: Name of agent (e.g., 'ResearchAgent', 'SummarizerAgent')
        
    Returns:
        dict: Authorization result
    """
    result = authz_service.check_agent_access(token_payload, agent_name)
    
    return {
        "agent": agent_name,
        "authorized": result.authorized,
        "reason": result.reason,
        "user_roles": [r.value for r in result.user_roles],
    }


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.post("/admin/grant-permission/{user_id}/{action}")
async def grant_permission(
    user_id: str,
    action: str,
    token_payload = Depends(get_current_user)
):
    """
    Grant specific action permission to user (ADMIN only)
    
    Args:
        user_id: User ID to grant permission to
        action: Action to grant (e.g., 'research', 'summarize')
        
    Raises:
        HTTPException: 403 if not admin
    """
    # Check if requester is admin
    from app.security.models import UserRole
    if UserRole.ADMIN not in token_payload.roles:
        print(
            f"⚠️ Non-admin user {token_payload.username} attempted to grant permissions"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can grant permissions"
        )
    
    try:
        action_enum = Action[action.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}"
        )
    
    success = authz_service.grant_action_permission(
        token_payload, user_id, action_enum
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Failed to grant permission"
        )
    
    return {
        "status": "success",
        "message": f"Permission {action} granted to user {user_id}",
        "granted_by": token_payload.username,
    }


@router.get("/admin/all-actions")
async def list_all_actions(token_payload = Depends(get_current_user)):
    """
    List all available actions in the system (ADMIN only)
    
    Returns:
        dict: All actions and their rate limits
    """
    from app.security.models import UserRole
    if UserRole.ADMIN not in token_payload.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all actions"
        )
    
    return {
        "actions": [
            {
                "name": action.value,
                "rate_limit": authz_service.get_rate_limit(action)
            }
            for action in Action
        ]
    }


# ============================================================================
# USER QUERY ENDPOINTS (Main Orchestrator Integration)
# ============================================================================

@router.post("/query")
async def process_user_query(
    query: UserQueryRequest,
    token_payload = Depends(get_current_user)
):
    """
    Submit user query to orchestrator and get agent output
    
    Args:
        query: Request body with 'message' field containing user query
        token_payload: Current authenticated user
        
    Returns:
        dict: Orchestrator output with agent responses
        
    Raises:
        HTTPException: 403 if user lacks RESEARCH permission
    """
    from app.security.models import UserRole, Action
    from langchain_core.messages import HumanMessage
    import uuid
    from datetime import datetime
    
    # Validate user has permission to execute research
    result = authz_service.check_action_permission(token_payload, Action.RESEARCH)
    if not result.authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User {token_payload.username} lacks RESEARCH permission"
        )
    
    # Extract query message
    user_message = query.message.strip()
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'message' field in query"
        )
    
    # Validate input for prompt injection
    from app.security.prompt_guard import prompt_guard
    validation_result = prompt_guard.validate_input(user_message)
    if not validation_result["safe"]:
        logger.security_alert("Prompt injection attempt blocked",
                            user=user_token_payload.username,
                            reason=validation_result["reason"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation failed: {validation_result['reason']}"
        )
    
    # Use sanitized and guarded input
    safe_message = prompt_guard.add_guardrails_to_prompt(validation_result["sanitized"])
    
    try:
        # Import orchestrator
        from app.orchestrator.graph.main_graph import build_graph
        from app.orchestrator.budget.models import Budget
        
        # Build orchestrator graph
        graph = build_graph()
        
        # Initialize state with user query
        initial_state = {
            "messages": [HumanMessage(content=safe_message)],
            "next_steps": [],
            "current_step_index": 0,
            "budget": Budget(
                max_tokens=10000,
                max_tool_calls=100,
                max_retries=3,
                max_wall_time_sec=300
            ),
            "total_tokens": 0,
            "total_tool_calls": 0,
            "retry_attempts": 0,
            "is_safe": True,
            "last_error": None,
            "context_data": {
                "user_id": token_payload.user_id,
                "username": token_payload.username,
                "user_roles": [r.value for r in token_payload.roles],
                "user_permissions": [p.value for p in token_payload.permissions],
                "timestamp": datetime.utcnow().isoformat(),
            },
            "episodic_memory_hits": 0,
            "semantic_memory_hits": 0,
            "research_output": None,
            "summary_output": None,
            "selected_agent": "",
            "current_task": safe_message,
            "request_id": str(uuid.uuid4()),
            "trace_id": str(uuid.uuid4()),
            "span_id": str(uuid.uuid4()),
            # Security fields
            "agent_identities": agent_identity_manager.get_all_public_keys(),
            "active_jit_tokens": [],
            "security_context": {
                "user_authenticated": True,
                "input_validated": True,
                "zero_trust_enabled": True,
            },
        }
        
        # Execute orchestrator graph
        final_state = graph.invoke(initial_state)
        
        # Extract results
        return {
            "status": "success",
            "request_id": final_state.get("request_id"),
            "user_query": user_message,
            "username": token_payload.username,
            "orchestrator_output": {
                "research_output": final_state.get("research_output"),
                "summary_output": final_state.get("summary_output"),
                "final_steps": final_state.get("next_steps", []),
                "total_tokens_used": final_state.get("total_tokens", 0),
                "total_tool_calls": final_state.get("total_tool_calls", 0),
                "is_safe": final_state.get("is_safe", True),
                "error": final_state.get("last_error"),
            },
            "execution_trace": {
                "request_id": final_state.get("request_id"),
                "trace_id": final_state.get("trace_id"),
                "span_id": final_state.get("span_id"),
            }
        }
        
    except Exception as e:
        print(f"❌ Orchestrator execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator execution failed: {str(e)}"
        )
