from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from pkg.chat_model.qwen import chat_model
from langchain_community.agent_toolkits.file_management import FileManagementToolkit
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_core.messages import HumanMessage

DATA_DIR = "../data/conversations"

def create_agent():
    mem = MemorySaver()
    file_tools = FileManagementToolkit(root_dir=DATA_DIR).get_tools()
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

    res = agent.invoke(input={"messages": [HumanMessage("帮我创建一个 a.json 的文件")]}, config=config)
    print(res)


if __name__ == "__main__":
    run_agent()
