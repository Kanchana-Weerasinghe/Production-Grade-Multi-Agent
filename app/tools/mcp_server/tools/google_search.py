from fastmcp import FastMCP
import requests
from app.config.settings import settings

mcp = FastMCP("Search Tools")

@mcp.tool()
def google_search(query: str) -> dict:
    """
    Search the web using Tavily API and return results.
    """
    url = "https://api.tavily.com/search"
    payload = {
        "query": query,
        "api_key": settings.TAVILY_API_KEY,
        "include_answer": True
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "query": query,
            "results": [],
            "status": "error",
            "error": str(e),
            "provider": "TavilyAPI"
        }


