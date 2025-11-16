import os

from langchain_openai import ChatOpenAI

llm_qwen = ChatOpenAI(
    # model="qwen-max",
    # model="qwen3-235b-a22b",
    model="qwen3-coder-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ.get("BAILIAN_API_KEY"),
    streaming=True,
)