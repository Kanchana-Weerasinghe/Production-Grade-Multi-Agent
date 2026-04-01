# app/orchestrator/guardrails/guardrails_state.py

class StateGuardrails:

    @staticmethod
    def validate_state(state):
        # Ensure next_steps exists
        if "next_steps" not in state:
            raise ValueError("State missing 'next_steps'.")

        # Ensure index is valid
        idx = state.get("current_step_index", 0)
        if idx < 0 or idx > len(state["next_steps"]):
            raise ValueError("Invalid step index.")

        return True
