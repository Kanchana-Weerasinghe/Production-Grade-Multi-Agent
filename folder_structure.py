import os

# -----------------------------------------
# Folder structure exactly as you specified
# -----------------------------------------

FOLDERS = [
    "app/api/routers",
    "app/api/schemas",

    "app/orchestrator/graph",
    "app/orchestrator/temporal",
    "app/orchestrator/budget",
    "app/orchestrator/failure_manager",

    "app/agents/planner",
    "app/agents/critic",
    "app/agents/summarizer",
    "app/agents/specialists",

    "app/tools/mcp_server/schemas",
    "app/tools/mcp_server/tools",
    "app/tools/adapters",

    "app/memory/short_term",
    "app/memory/episodic",
    "app/memory/semantic",
    "app/memory/summarization",

    "app/policies",

    "app/dlq",

    "app/observability/dashboards",

    "app/config/env",
    "app/config/secrets",

    "app/utils",
]

FILES = [
    "app/main.py",

    "app/api/gateway.py",

    "app/orchestrator/graph/main_graph.py",
    "app/orchestrator/graph/state.py",
    "app/orchestrator/graph/policies.py",

    "app/agents/base.py",
    "app/agents/planner/planner_agent.py",
    "app/agents/critic/critic_agent.py",
    "app/agents/summarizer/summarizer_agent.py",

    "app/tools/mcp_server/registry.py",

    "app/memory/context_builder.py",

    "app/policies/safety_rules.yaml",
    "app/policies/tool_permissions.yaml",
    "app/policies/budget_profiles.yaml",
    "app/policies/retry_policies.yaml",

    "app/dlq/consumer.py",
    "app/dlq/replay.py",
    "app/dlq/schemas.py",

    "app/observability/logging.py",
    "app/observability/metrics.py",
    "app/observability/tracing.py",

    "app/config/settings.py",

    "app/utils/token_counter.py",
    "app/utils/json_validator.py",
    "app/utils/error_types.py",
    "app/utils/common.py",
]


def create_structure():
    print("\n🚀 Creating project folder structure...\n")

    # Create folders
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 Created folder: {folder}")

    # Create files
    for file in FILES:
        if not os.path.exists(file):
            with open(file, "w") as f:
                f.write("# Auto-generated file\n")
            print(f"📄 Created file: {file}")
        else:
            print(f"✔ File already exists: {file}")

    print("\n🎉 Done! Your production-grade folder structure is ready.\n")


if __name__ == "__main__":
    create_structure()
