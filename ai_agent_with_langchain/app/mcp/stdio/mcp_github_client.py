import asyncio

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import StdioServerParameters, stdio_client, ClientSession
from langgraph.prebuilt import create_react_agent

from app.bailian.common import llm


async def mcp_github_client():
    # 本地启动
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": "替换为你的github personal access token",
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # 获取 MCP Tools
            tools = await load_mcp_tools(session)
            print(tools)

            agent = create_react_agent(model=llm, tools=tools, debug=True)
            response = await agent.ainvoke(input={"messages": [("user", "查看sam9831有哪些代码仓库？Star数是多少？")]})

            print(response)

            messages = response["messages"]
            for message in messages:
                if isinstance(message, HumanMessage):
                    print("用户:", message.content)
                elif isinstance(message, AIMessage):
                    if message.content:
                        print("助理:", message.content)
                    else:
                        for tool_call in message.tool_calls:
                            print("助理[调用工具]:", tool_call["name"], tool_call["args"])
                elif isinstance(message, ToolMessage):
                    print("调用工具:", message.name)

asyncio.run(mcp_github_client())