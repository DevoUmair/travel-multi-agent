# mcp_client package initialization
from mcp_client.client import client
from mcp_client.adapters import (
    get_all_tools,
    aviation_mcp_call,
    tavily_mcp_call,
    weather_mcp_call,
    forecast_mcp_call,
    extract_destination,
)

__all__ = [
    "client",
    "get_all_tools",
    "aviation_mcp_call",
    "tavily_mcp_call",
    "weather_mcp_call",
    "forecast_mcp_call",
    "extract_destination",
]

