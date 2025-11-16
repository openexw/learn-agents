import asyncio

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import StdioServerParameters, stdio_client, ClientSession
from langgraph.prebuilt import create_react_agent

from app.bailian.common import llm


async def mcp_playwright_client():
    # 本地启动
    server_params = StdioServerParameters(
        command="node",
        # 替换为你本地的 @executeautomation/playwright-mcp-server 地址
        args=["/Users/sam/.nvm/versions/node/v18.16.0/lib/node_modules/@executeautomation/playwright-mcp-server/dist/index.js"]
    )

    # 远程启动（拉取最新版本的包）
    # server_params = StdioServerParameters(
    #     command="npx",
    #     args=["-y", "@executeautomation/playwright-mcp-server"],
    # )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # 获取 MCP Tools
            tools = await load_mcp_tools(session)
            print(tools)

            agent = create_react_agent(model=llm, tools=tools, debug=True)
            response = await agent.ainvoke(input={"messages": [("user", "在百度中查询北京今天的天气，读取页面信息并告诉我北京今天的温度、湿度、出行建议")]})

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

asyncio.run(mcp_playwright_client())