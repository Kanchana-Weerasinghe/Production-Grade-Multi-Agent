from app.orchestrator.agent_capabilities import AGENT_CAPABILITIES

def delegate_task(state):
    print("\n==============================")
    print("🧭 DELEGATOR NODE EXECUTED")
    print("==============================")

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

    # ⭐ RETURN partial state update (LangGraph merges this)
    update = {
        "selected_agent": agent_name,
        "current_task": instruction
    }

    print(f"\n🟧 Delegator returning state update: {update}\n")
    print("==============================\n")

    return update
