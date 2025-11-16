from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.prebuilt import create_react_agent

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools


def run_agent():
    # memory = MemorySaver()

    # with RedisSaver.from_conn_string("redis://192.168.64.2:6379") as memory:
    #     memory.setup()

    # MONGODB_URI = "mongodb://localhost:27017"
    MONGODB_URI = "mongodb://root:root@192.168.64.2:27017"
    MONGODB_DB = "chat"

    with MongoDBSaver.from_conn_string(MONGODB_URI, MONGODB_DB) as memory:

        agent = create_react_agent(
            model=llm_qwen,
            tools=file_tools,
            checkpointer=memory,
            debug=True,
        )

        config = RunnableConfig(configurable={"thread_id": 2})

        # res = agent.invoke(input={"messages": [("user", "我叫Sam")]}, config=config)
        res = agent.invoke(input={"messages": [("user", "我是谁？")]}, config=config)
        # res = agent.invoke(input={"messages": [("user", "我们刚才聊了什么？")]}, config=config)
        print("=" * 60)
        print(res)
        print("=" * 60)

        memory.close()


if __name__ == "__main__":
    run_agent()