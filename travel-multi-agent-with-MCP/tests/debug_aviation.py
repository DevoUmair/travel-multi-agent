import os
import sys
import shutil
import asyncio
import traceback
from dotenv import load_dotenv

load_dotenv()

AVIATION_KEY = os.getenv("AVIATIONSTACK_API_KEY", "") or os.getenv("AVIATION_STACK_API_KEY", "")

async def test_cmd(cmd, args, env_vars):
    print(f"\nTesting command: {cmd} {' '.join(args)}")
    try:
        proc = await asyncio.create_subprocess_exec(
            cmd, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env_vars
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        print(f"  Exit Code: {proc.returncode}")
        if stdout:
            print(f"  Stdout: {stdout.decode(errors='ignore')[:300].strip()}")
        if stderr:
            print(f"  Stderr: {stderr.decode(errors='ignore')[:300].strip()}")
        return proc.returncode == 0
    except Exception as e:
        print(f"  Execution Error: {e}")
        return False

async def main():
    print("=" * 60)
    print("  AVIATIONSTACK MCP COMMAND VARIATION TESTER")
    print("=" * 60)
    print(f"API Key found: {AVIATION_KEY[:6]}*** (length {len(AVIATION_KEY)})")

    env1 = os.environ.copy()
    env1["AVIATIONSTACK_API_KEY"] = AVIATION_KEY
    env1["AVIATION_STACK_API_KEY"] = AVIATION_KEY

    print("\n--- [Test 1] Standard uvx invocation ---")
    await test_cmd("uvx", ["aviationstack-mcp"], env1)

    print("\n--- [Test 2] uvx with Python 3.12 flag ---")
    await test_cmd("uvx", ["--python", "3.12", "aviationstack-mcp"], env1)

    print("\n--- [Test 3] uvx passing --api-key argument ---")
    await test_cmd("uvx", ["aviationstack-mcp", "--api-key", AVIATION_KEY], env1)

    print("\n--- [Test 4] uvx passing both --python 3.12 and --api-key ---")
    await test_cmd("uvx", ["--python", "3.12", "aviationstack-mcp", "--api-key", AVIATION_KEY], env1)

    print("\n--- [Test 5] MCP Client test with python 3.12 flag ---")
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        mcp_client = MultiServerMCPClient({
            "aviationstack": {
                 "transport": "stdio",
                "command": "uvx",
                "args": [
                    "--with",
                    "fastmcp",
                    "aviationstack-mcp"
                ],
                "env": env1
            }
        })
        print("  Connecting to MCP server...")
        tools = await mcp_client.get_tools(server_name="aviationstack")
        print(f"  ✅ Success! Connected and found {len(tools)} tools:")
        for t in tools:
            print(f"     - {t.name}")
    except Exception as e:
        print(f"  ❌ MCP Connection failed: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
