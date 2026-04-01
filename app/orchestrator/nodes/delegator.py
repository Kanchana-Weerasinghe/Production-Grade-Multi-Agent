from app.orchestrator.agent_capabilities import AGENT_CAPABILITIES
from app.utils.logger import logger

def delegate_task(state):
    try:
        step_index = state.get('current_step_index', 0)
        next_steps = state.get('next_steps', [])
        logger.delegator_start(step_index, len(next_steps))

        if not next_steps or step_index is None:
            logger.delegator_error("No steps or invalid index")
            return {"selected_agent": "NO_AGENT"}

        try:
            step = state["next_steps"][state["current_step_index"]].lower()
            logger.trace_value("Current step", step)
        except IndexError:
            logger.delegator_error(f"Index out of bounds: {state['current_step_index']} >= {len(state['next_steps'])}")
            return {"selected_agent": "NO_AGENT"}

        for keyword, agent_name in AGENT_CAPABILITIES.items():
            if keyword in step:
                result = {
                    "selected_agent": agent_name,
                    "current_task": state["next_steps"][state["current_step_index"]]
                }
                logger.delegator_selected(agent_name, result['current_task'])
                return result

        # fallback
        result = {
            "selected_agent": "ResearchAgent",
            "current_task": state["next_steps"][state["current_step_index"]]
        }
        logger.delegator_selected("ResearchAgent (fallback)", result['current_task'])
        return result
    except Exception as e:
        logger.delegator_error(str(e))
        return {"selected_agent": "NO_AGENT"}
