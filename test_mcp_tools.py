import asyncio
import os

from dotenv import load_dotenv
from fastmcp import Client


async def main():
    load_dotenv()

    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp")
    print(f"Connecting to MCP server: {mcp_url}")

    client = Client(mcp_url)

    async with client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}")

        print("\nTesting check_db_version:")
        result = await client.call_tool("check_db_version", {})
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())