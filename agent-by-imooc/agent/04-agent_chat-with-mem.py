from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.redis import RedisSaver
from pkg.chat_model.qwen import chat_model
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

DATA_DIR = "../data/conversations"

def create_agent():
    file_tools = FileManagementToolkit(root_dir=DATA_DIR).get_tools()
    with RedisSaver.from_conn_string("redis://127.0.0.1:6379") as mem:
        agent = create_react_agent(
            model=chat_model,
            tools=file_tools,
            checkpointer=mem,
            debug=True,
        )
        return agent

def run_agent():
    config = RunnableConfig(configurable={"thread_id": 1})
    agent = create_agent()

    res = agent.invoke(input={"messages": [("user", "我是Sam")]}, config=config)
    res = agent.invoke(input={"messages": [("user", "我是谁？")]}, config=config)


if __name__ == "__main__":
    run_agent()
