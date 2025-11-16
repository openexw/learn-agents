import json
from datetime import datetime

from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

from pkg.chat_model.qwen import chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
import os
import uuid
# from langgraph.prebuilt import create_react_agent
# from langchain.agents import create_react_agent

DATA_DIR = "data/conversations"

def get_session_history(session_id:str):
    user_id = session_id.split("_")[0]  # 假设 session_id 格式为 "user_id_session"
    dir_path = os.path.join(DATA_DIR, user_id)
    os.makedirs(dir_path, exist_ok=True)
    return FileChatMessageHistory(os.path.join(dir_path, f"{session_id}.json"))

def run_conv(chain):
    chain_with_history = RunnableWithMessageHistory(
        runnable=chain,
        input_messages_key="question",
        history_messages_key="chat_history",
        get_session_history=get_session_history
    )
    session_id = uuid.uuid4()
    user_id = "user1"
    session_id = f"{user_id}_{session_id}" # 根据已有session会话生成
    print("session_id:", session_id)
    while True:
        user_input = input("用户：")
        if user_input.lower() == "exit":
            break
        response = chain_with_history.invoke(
            {"question": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        print("助手：")
        for chunk in response:
            print(chunk, end="")
        print("\n")

def main():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个技术专家，擅长解决各种Web开发中的技术问题"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    file_tools = FileManagementToolkit(root_dir=DATA_DIR).get_tools()

    llm_with_tools = chat_model.bind_tools(tools=file_tools)
    chain = prompt |llm_with_tools | StrOutputParser()

    run_conv(chain)

if __name__ == "__main__":
    main()



