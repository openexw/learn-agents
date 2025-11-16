import os
import asyncio

from langchain.agents import initialize_agent, AgentType
from langchain_core.prompts import PromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.bailian.common import llm, file_tools


async def create_amap_mcp_client():
    amap_key = os.environ.get("AMAP_KEY")

    mcp_config = {
        "amap": {
            "url": f"https://mcp.amap.com/sse?key={amap_key}",
            "transport": "sse",
        }
    }

    client = MultiServerMCPClient(mcp_config)

    tools = await client.get_tools()
    print(tools)

    return client, tools


async def create_and_run_agent():
    client, tools = await create_amap_mcp_client()

    print(file_tools)

    agent = initialize_agent(
        llm=llm,
        tools=tools + file_tools,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    prompt_template = PromptTemplate.from_template("你是一个智能助手，可以调用高德 MCP 工具。\n\n {input}")
    prompt = prompt_template.format(input="""
##我五一计划去昆明游玩4天的旅行攻略。

#帮制作旅行攻略，考虑出行时间和路线，以及天气状况路线规划。

#制作网页地图自定义绘制旅游路线和位置。

##网页使用简约美观页面风格，景区图片以卡片展示。

#行程规划结果在高德地图app展示，并集成到h5页面中。

##同一天行程景区之间我想打车前往。

#生成文件名 kmTravel.html，保存到：/Users/sam/Work/imooc_agent/ai-code_agent-test/.temp 目录下。
""")
    print(prompt)

    resp = await agent.ainvoke(prompt)
    print(resp)

    return resp


asyncio.run(create_and_run_agent())