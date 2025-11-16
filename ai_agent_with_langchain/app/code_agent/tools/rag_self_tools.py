from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_rag_self_tools():
    params = {
        "command": "python",
        "args": [
            "/Users/sam/Work/imooc_agent/ai-agent-test/app/code_agent/rag/rag.py",
        ]
    }

    client, tools = await create_mcp_stdio_client("self_rag_tools", params)

    return tools