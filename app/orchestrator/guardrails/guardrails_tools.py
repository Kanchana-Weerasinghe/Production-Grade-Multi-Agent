
class ToolGuardrails:

    @staticmethod
    def validate_args(tool_name: str, args: dict):
        if not isinstance(args, dict):
            raise ValueError(f"Tool '{tool_name}' received invalid args.")

        # Prevent empty queries
        if tool_name == "google_search" and len(args.get("query", "")) < 3:
            raise ValueError("Search query too short.")

        return True

    @staticmethod
    def validate_output(tool_name: str, output):
        if output is None:
            raise ValueError(f"Tool '{tool_name}' returned no output.")

        # Prevent tools from returning huge payloads
        if isinstance(output, dict) and len(str(output)) > 50000:
            raise ValueError(f"Tool '{tool_name}' returned oversized output.")

        return True
