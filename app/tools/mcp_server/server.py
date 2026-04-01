from app.tools.mcp_server.tools.google_search import mcp


def start():
    """
    Start the FastMCP server.
    All tools registered via @mcp.tool() will be exposed automatically.
    """
    mcp.run()
