from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_vm_tools():
    params = {
        "command": "python",
        "args": [
            "/Users/sam/Work/imooc_agent/ai-agent-test/app/code_agent/mcp/vm.py",
        ]
    }

    client, tools = await create_mcp_stdio_client("vm_tools", params)

    return tools