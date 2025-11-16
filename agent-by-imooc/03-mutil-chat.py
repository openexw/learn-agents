import json
from datetime import datetime

from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from pkg.chat_model.qwen import chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
import uuid
import os

# 对话目录设计：data/conversations/{user_id}/{session_id}
DATA_DIR = "data/conversations"

def get_file_path(session_id:str):
    user_id = session_id.split("_")[0]  # 假设 session_id 格式为 "user_id_session"
    dir_path = os.path.join(DATA_DIR, user_id)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{session_id}.json")

def save_conv_history(session_id,messages):
    file_path = get_file_path(session_id)
    data = [
        {
            "session_id": session_id,
            "sender": "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": msg.content,
            "timestamp": datetime.now().isoformat(),
        }
        for msg in messages
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
def load_conversation_history(session_id):
    """从文件中加载历史记录为消息列表"""
    file_path = get_file_path(session_id)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [
                HumanMessage(content=msg["content"]) if msg["sender"] == "user"
                else AIMessage(content=msg["content"])
                for msg in json.load(f)
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_session_history(session_id):
    """返回对应会话的历史记录（返回 BaseChatMessageHistory 实例）"""
    history = load_conversation_history(session_id)
    return InMemoryChatMessageHistory(messages=history)

def run_conv(chain):
    chain_with_history = RunnableWithMessageHistory(
        runnable=chain,
        input_messages_key="question",
        history_messages_key="chat_history",
        get_session_history=get_session_history,
    )
    user_id = "user1"
    session_id = user_id + "_" + "82b8d5d4-8ebf-4a55-a892-426542deb8c8"  # 根据已有session会话生成
    # session_id = uuid.uuid4()
    print("session_id:", session_id)
    while True:
        user_input = input("用户：")
        if user_input.lower() == "exit":
            break
        response = chain_with_history.invoke(
            {"question": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        # 构建新消息并保存
        new_messages = load_conversation_history(session_id) + [HumanMessage(user_input), AIMessage(response)]
        save_conv_history(session_id, new_messages)

        print("助手：")
        for chunk in response:
            print(chunk, end="")
        print("\n")
    # user_input = "你的目标是什么？"
    # response = chain_with_history.invoke(
    #     {"question": user_input},
    #     config={"configurable": {"session_id": session_id}},
    # )
    # print("助手：")
    # for chunk in response:
    #     print(chunk, end="")
    # print("\n")

def main():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个技术专家，擅长解决各种Web开发中的技术问题"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    chain = prompt | chat_model | StrOutputParser()

    run_conv(chain)

if __name__ == "__main__":
    main()



