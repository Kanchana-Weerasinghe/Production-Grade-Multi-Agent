"""
Enhanced delegator with authorization checks
"""
from app.orchestrator.agent_capabilities import AGENT_CAPABILITIES
from app.security.orchestration_hooks import orchestration_auth_hooks
from app.utils.logger import logger


def delegate_task_with_auth(state):
    """
    Delegator node that includes authorization checks
    
    Args:
        state: Orchestration state
        
    Returns:
        dict: Updated state with selected agent and task, or error if not authorized
    """
    print("\n==============================")
    print("🧭 DELEGATOR NODE EXECUTED (WITH AUTH)")
    print("==============================")
    
    # Check if auth context exists
    auth_context = state.get("_auth_context")
    if not auth_context:
        print("⚠️ No authentication context found in state")
        print("   Skipping authorization checks (running unauthenticated)")
    
    print(f"📌 current_step_index: {state.get('current_step_index')}")
    print(f"📌 next_steps: {state.get('next_steps')}")
    
    # Get the current step
    raw_step = state["next_steps"][state["current_step_index"]]
    print(f"\n🟦 Raw step received: {raw_step!r}")
    
    step = raw_step.strip()
    
    # Extract capability + instruction
    if ":" in step:
        capability, instruction = step.split(":", 1)
        capability = capability.strip().lower()
        instruction = instruction.strip()
    else:
        capability = None
        instruction = step
    
    print(f"🟩 Extracted capability: {capability!r}")
    print(f"🟩 Extracted instruction: {instruction!r}")
    
    # Map capability → agent
    agent_name = AGENT_CAPABILITIES.get(capability)
    print(f"🟦 AGENT_CAPABILITIES: {AGENT_CAPABILITIES}")
    print(f"🟦 Selected agent: {agent_name!r}")
    
    # Fallback if capability not found
    if agent_name is None:
        print("❌ No agent found for capability — using SummarizerAgent as fallback")
        agent_name = "SummarizerAgent"
    
    # ========================================================================
    # AUTHORIZATION CHECK
    # ========================================================================
    if auth_context:
        # Get token payload from context (we need to reconstruct it)
        from app.security.models import TokenPayload, UserRole, Action
        from datetime import datetime
        
        # Reconstruct token payload from auth context
        token_payload = TokenPayload(
            sub=auth_context["user_id"],
            user_id=auth_context["user_id"],
            username=auth_context["username"],
            roles=[UserRole(r) for r in auth_context["roles"]],
            permissions=[Action(p) for p in auth_context["permissions"]],
            iat=datetime.fromisoformat(auth_context["token_issued_at"]),
            exp=datetime.fromisoformat(auth_context["token_expires_at"]),
        )
        
        # Check authorization for agent execution
        print(f"\n🔐 Checking authorization for agent: {agent_name}")
        authorized = orchestration_auth_hooks.before_agent_execution(
            token_payload,
            agent_name,
            state
        )
        
        if not authorized:
            print(f"❌ Authorization failed for {agent_name}")
            state = orchestration_auth_hooks.on_authorization_failure(
                token_payload,
                f"Execute agent: {agent_name}",
                f"User does not have permission to use {agent_name}",
                state
            )
            return state
        
        print(f"✅ Authorization granted for {agent_name}")
    
    # ⭐ RETURN partial state update (LangGraph merges this)
    update = {
        "selected_agent": agent_name,
        "current_task": instruction
    }
    
    print(f"\n🟧 Delegator returning state update: {update}\n")
    print("==============================\n")
    
    return update


# For backward compatibility, keep original function name
delegate_task = delegate_task_with_auth
