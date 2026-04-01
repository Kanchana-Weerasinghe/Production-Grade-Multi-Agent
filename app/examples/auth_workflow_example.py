"""
Example: Complete workflow with action-level authentication
This demonstrates how to use the auth system end-to-end
"""

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

from app.security import (
    get_current_user, check_action_authorization, Action,
    orchestration_auth_hooks, AuthenticationMiddleware
)
from app.api.auth_gateway import router as auth_router


app = FastAPI(title="Action-Level Auth Example")

# Add auth middleware
app.add_middleware(
    AuthenticationMiddleware,
    excluded_paths=["/health", "/auth/login"]
)
app.include_router(auth_router, prefix="/api", tags=["auth"])


# ============================================================================
# Example: Protected Agent Endpoint
# ============================================================================

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"


@app.post("/api/agents/research")
async def execute_research(
    request: ResearchRequest,
    current_user = Depends(get_current_user),
    # Check authorization for RESEARCH action
    auth_result = Depends(lambda req: check_action_authorization(req, Action.RESEARCH))
):
    """
    Execute research agent - requires RESEARCH permission
    
    This endpoint:
    1. Validates authentication (handled by middleware)
    2. Checks user has RESEARCH action permission (via dependency)
    3. Executes the research task
    
    Args:
        request: Research request parameters
        current_user: Validated token payload
        auth_result: Authorization check result
        
    Returns:
        dict: Research results
    """
    from app.utils.logger import logger
    
    logger.info(f"🔬 Research initiated by {current_user.username}")
    logger.debug(f"   Topic: {request.topic}")
    logger.debug(f"   Depth: {request.depth}")
    
    # Simulate research
    return {
        "status": "success",
        "user": current_user.username,
        "action": "research",
        "requested_by": current_user.user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "topic": request.topic,
        "depth": request.depth,
        "results": ["Finding 1", "Finding 2", "Finding 3"]
    }


# ============================================================================
# Example: Workflow with Auth Context
# ============================================================================

class WorkflowRequest(BaseModel):
    topic: str
    steps: list


@app.post("/api/workflows/execute")
async def execute_workflow(
    request: WorkflowRequest,
    current_user = Depends(get_current_user),
    auth_result = Depends(
        lambda req: check_action_authorization(req, Action.EXECUTE_WORKFLOW)
    )
):
    """
    Execute complete workflow with auth context injection
    
    This demonstrates injecting auth context into the orchestration state
    """
    from app.orchestrator.graph.state import AgentState
    
    # Create initial state
    state = AgentState(
        messages=[],
        next_steps=request.steps,
        current_step_index=0,
        selected_agent="ResearchAgent",
        current_task="",
    )
    
    # Inject authentication context
    state = orchestration_auth_hooks.inject_auth_context(state, current_user)
    
    return {
        "status": "workflow_started",
        "user": current_user.username,
        "topic": request.topic,
        "steps": len(request.steps),
        "auth_context": state.get("_auth_context"),
    }


# ============================================================================
# Example: Admin-Only Endpoint
# ============================================================================

class PermissionGrant(BaseModel):
    user_id: str
    action: str


@app.post("/api/admin/permissions/grant")
async def admin_grant_permission(
    grant: PermissionGrant,
    current_user = Depends(get_current_user),
):
    """
    Grant permission to user - ADMIN only
    
    This endpoint checks that the requester is an admin
    """
    from app.security.models import UserRole, Action
    from app.security.authorization import auth_service
    from app.utils.logger import logger
    
    # Check admin role
    if UserRole.ADMIN not in current_user.roles:
        logger.warning(
            f"Non-admin {current_user.username} attempted to grant permissions"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can grant permissions"
        )
    
    try:
        action = Action[grant.action.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {grant.action}"
        )
    
    # In production, this would update database
    logger.info(
        f"✅ Admin {current_user.username} granted "
        f"{action.value} to user {grant.user_id}"
    )
    
    return {
        "status": "success",
        "message": f"Permission {action.value} granted to {grant.user_id}",
        "granted_by": current_user.username,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Example: Multi-Step Authorization Checker
# ============================================================================

class AgentTask(BaseModel):
    agent_name: str
    instructions: str


@app.post("/api/agents/execute-task")
async def execute_agent_task(
    task: AgentTask,
    current_user = Depends(get_current_user),
):
    """
    Execute agent task with comprehensive authorization checks
    
    This demonstrates checking agent access before execution
    """
    from app.security.authorization import auth_service
    from app.utils.logger import logger
    
    # Check if user can access this agent
    result = auth_service.check_agent_access(current_user, task.agent_name)
    
    if not result.authorized:
        logger.error(f"❌ Access denied to {task.agent_name} for {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.reason
        )
    
    logger.info(f"✅ User {current_user.username} executing {task.agent_name}")
    
    return {
        "status": "executing",
        "agent": task.agent_name,
        "user": current_user.username,
        "instructions": task.instructions,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Example: Permission Dependency
# ============================================================================

async def require_summarize_permission(current_user = Depends(get_current_user)):
    """Custom dependency - requires SUMMARIZE permission"""
    from app.utils.logger import logger
    
    if Action.SUMMARIZE not in current_user.permissions:
        logger.warning(f"Access denied: SUMMARIZE for {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUMMARIZE permission required"
        )
    return current_user


@app.post("/api/agents/summarize")
async def summarize(
    request: dict,
    current_user = Depends(require_summarize_permission)
):
    """Summarize endpoint with permission dependency"""
    return {
        "status": "summarized",
        "user": current_user.username,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Example: List User Capabilities
# ============================================================================

@app.get("/api/me/capabilities")
async def get_user_capabilities(current_user = Depends(get_current_user)):
    """Get all capabilities available to current user"""
    from app.security.authorization import auth_service
    
    permissions = auth_service.get_user_permissions(current_user)
    
    # Map actions to agent capabilities
    agents = [
        agent for agent, action in auth_service.agent_actions.items()
        if action in permissions
    ]
    
    return {
        "user": current_user.username,
        "roles": [r.value for r in current_user.roles],
        "actions": [a.value for a in permissions],
        "available_agents": agents,
        "rate_limits": {
            p.value: auth_service.get_rate_limit(p)
            for p in permissions
        }
    }


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("ACTION-LEVEL AUTHENTICATION EXAMPLE")
    print("="*70)
    print("\n🔐 Testing Users:")
    print("   1. Admin: admin / admin123 (all permissions)")
    print("   2. User: user / user123 (research, summarize, plan, etc.)")
    print("   3. Guest: guest / guest123 (view_results only)")
    print("\n📝 Test Endpoints:")
    print("   1. POST /api/auth/login - Login to get token")
    print("   2. GET /api/auth/me - Get current user info")
    print("   3. GET /api/auth/permissions - List your permissions")
    print("   4. POST /api/agents/research - Execute research (requires RESEARCH)")
    print("   5. POST /api/admin/permissions/grant - Grant permission (ADMIN only)")
    print("\n💡 Quick Test:")
    print("\n   curl -X POST http://localhost:8000/api/auth/login \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username": "user", "password": "user123"}\'')
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
