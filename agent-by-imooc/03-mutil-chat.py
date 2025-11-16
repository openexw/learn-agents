
from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from pkg.chat_model.qwen import chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
import uuid

story = {}
def get_session_history(session_id: str):
    if session_id not in story:
        story[session_id] = ChatMessageHistory()
    print("历史消息：",story)
    return story[session_id]


def run_conv(chain):
    chain_with_history = RunnableWithMessageHistory(
        runnable=chain,
        input_messages_key="question",
        history_messages_key="chat_history",
        get_session_history=get_session_history,
    )
    session_id = uuid.uuid4()
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



