import asyncio
from mcp_client import get_all_tools 

async def main():
    await get_all_tools()

if __name__ == "__main__":
    asyncio.run(main()) 

