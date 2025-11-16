import uuid

from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnableParallel
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.prompts.multi_chat_prompts import multi_chat_prompt


def get_session_history(session_id: str):
    return FileChatMessageHistory(f"{session_id}.json")

file_toolkit = FileManagementToolkit(root_dir="/Users/sam/llm/.temp")
file_tools = file_toolkit.get_tools()

llm_with_tools = llm_qwen.bind_tools(tools=file_tools)

# 串行写法1
# chain = multi_chat_prompt.pipe(llm_with_tools).pipe(StrOutputParser())

# 串行写法2
# chain = multi_chat_prompt | llm_with_tools | StrOutputParser()

# 串行写法3
chain = RunnableSequence(
    first=multi_chat_prompt,
    middle=[llm_with_tools],
    last=StrOutputParser()
)

chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

# chat_session_id = uuid.uuid4()
chat_session_id = "1"

while True:
    user_input = input("用户：")
    if user_input.lower() == "exit" or user_input.lower() == "quit":
        break

    print("助理：", end="")
    for chunk in chain_with_history.stream(
        {"question": user_input},
        config={"configurable": {"session_id": chat_session_id}},
    ):
        print(chunk, end="")

    print("\n")
