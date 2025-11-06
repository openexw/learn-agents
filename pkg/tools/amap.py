import os

from langchain_mcp_adapters.client import MultiServerMCPClient

async def create_mcp_client():
    amap_key = os.environ.get("AMAP_KEY")

    client = MultiServerMCPClient({
        "amap": {
            "url": f"https://mcp.amap.com/sse?key={amap_key}",
            "transport": "sse",
        }
    })

    tools = await client.get_tools()

    return client, tools