import asyncio
from mcp_client.adapters import get_all_tools

async def main():
    print("Testing MCP tools connectivity...")
    tools = await get_all_tools()
    print(f"Total tools loaded: {len(tools)}")

if __name__ == "__main__":
    asyncio.run(main())
