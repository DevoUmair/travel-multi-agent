import sys
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.settings import (
    TAVILY_API_KEY,
    AVIATION_ENV,
    WEATHER_ENV,
    WEATHER_SERVER_PATH
)

# Initialize multi-server MCP client
client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
    },
    "aviationstack": {
        "transport": "stdio",
        "command": "uvx",
        "args": [
            "--with",
            "fastmcp",
            "aviationstack-mcp"
        ],
        "env": AVIATION_ENV
    },
    "weather": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [str(WEATHER_SERVER_PATH)],
        "env": WEATHER_ENV
    }
})
