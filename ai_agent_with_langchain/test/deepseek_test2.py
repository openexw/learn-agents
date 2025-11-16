import os

from langchain_community.chat_models.tongyi import ChatTongyi

llm = ChatTongyi(
    model="deepseek-r1-0528",
    api_key=os.environ.get("BAILIAN_API_KEY"),
    streaming=True,
)

is_thinking = True

for chunk in llm.stream("你是谁？"):
    if chunk.additional_kwargs["reasoning_content"]:
        print(chunk.additional_kwargs["reasoning_content"], end="")
    elif chunk.content:
        if is_thinking:
            is_thinking = False
            print("\n")
        print(chunk.content, end="")
    else:
        print("\n")