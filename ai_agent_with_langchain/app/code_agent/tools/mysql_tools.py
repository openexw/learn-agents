from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_mysql_tools():
    params = {
        "command": "python",
        "args": [
            "/Users/sam/Work/imooc_agent/ai-agent-test/app/code_agent/mcp/mysql_tools.py",
        ]
    }

    client, tools = await create_mcp_stdio_client("mysql_tools", params)

    return tools