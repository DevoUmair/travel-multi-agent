import asyncio
from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, logger, WEATHER_SERVER_PATH
from mcp_client.client import client

# LLM setup for tools / extractors
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)

# Shared tool caches and locks
_tavily_tool = None
_aviation_tools = {}
_weather_tool = None
_forecast_tool = None

_lock = asyncio.Lock()


async def get_all_tools():
    """Diagnostic tool loader to check connection status of all MCP servers."""
    all_tools = []
    for server_name in ("tavily", "aviationstack", "weather"):
        try:
            tools = await client.get_tools(server_name=server_name)
            all_tools.extend(tools)
            logger.info(f"Available tools from {server_name} MCP: {[t.name for t in tools]}")
        except Exception as error:
            logger.error(f"Could not connect to {server_name} MCP: {error}")
    return all_tools


async def initialize_tavily_tool():
    global _tavily_tool
    if _tavily_tool is not None:
        return _tavily_tool

    async with _lock:
        if _tavily_tool is not None:
            return _tavily_tool

        tools = await client.get_tools(server_name="tavily")
        tools_by_name = {tool.name: tool for tool in tools}
        _tavily_tool = tools_by_name.get("tavily_search")
        if _tavily_tool is None:
            raise RuntimeError("Tavily MCP connected, but 'tavily_search' tool was not found.")
        return _tavily_tool


async def tavily_mcp_search(query: str):
    """Invoke Tavily MCP search."""
    try:
        tool = await initialize_tavily_tool()
        return await tool.ainvoke({"query": query})
    except Exception as e:
        logger.error(f"Tavily MCP search failed: {e}")
        return f"Hotel/Web search unavailable: {str(e)}"


async def initialize_aviation_tools():
    global _aviation_tools
    if _aviation_tools:
        return _aviation_tools

    async with _lock:
        if _aviation_tools:
            return _aviation_tools

        tools = await client.get_tools(server_name="aviationstack")
        _aviation_tools = {tool.name: tool for tool in tools}
        if not _aviation_tools:
            raise RuntimeError("AviationStack MCP connected but returned no tools.")
        return _aviation_tools


async def aviation_mcp_call(tool_name: str, tool_args: dict = None):
    """Invoke an AviationStack MCP tool by name."""
    try:
        tools = await initialize_aviation_tools()
        tool = tools.get(tool_name)
        if tool is None:
            raise ValueError(f"AviationStack tool '{tool_name}' not found.")
        return await tool.ainvoke(tool_args or {})
    except Exception as e:
        logger.error(f"AviationStack MCP call '{tool_name}' failed: {e}")
        return f"Flight information unavailable: {str(e)}"


async def initialize_weather_tools():
    global _weather_tool, _forecast_tool
    if _weather_tool is not None and _forecast_tool is not None:
        return _weather_tool, _forecast_tool

    async with _lock:
        if _weather_tool is not None and _forecast_tool is not None:
            return _weather_tool, _forecast_tool

        if not WEATHER_SERVER_PATH.exists():
            raise FileNotFoundError(f"Weather MCP server file not found: {WEATHER_SERVER_PATH}")

        tools = await client.get_tools(server_name="weather")
        tools_by_name = {tool.name: tool for tool in tools}
        _weather_tool = tools_by_name.get("get_current_weather")
        _forecast_tool = tools_by_name.get("get_forecast")

        if _weather_tool is None or _forecast_tool is None:
            raise RuntimeError("Missing Weather MCP tools.")
        return _weather_tool, _forecast_tool


async def weather_mcp_search(city: str):
    """Invoke Weather MCP current weather tool."""
    try:
        w_tool, _ = await initialize_weather_tools()
        return await w_tool.ainvoke({"city": city})
    except Exception as e:
        logger.error(f"Weather MCP search failed: {e}")
        return f"Current weather unavailable: {str(e)}"


async def forecast_mcp_search(city: str):
    """Invoke Weather MCP forecast tool."""
    try:
        _, f_tool = await initialize_weather_tools()
        return await f_tool.ainvoke({"city": city})
    except Exception as e:
        logger.error(f"Forecast MCP search failed: {e}")
        return f"Weather forecast unavailable: {str(e)}"


def extract_destination(query: str) -> str:
    """Extract destination city or country from user query using LLM."""
    prompt = f"""
    Extract only the destination city or country from this query.
    Query: {query}
    Return only the destination name.
    """
    response = llm.invoke(prompt)
    return response.content.strip()
