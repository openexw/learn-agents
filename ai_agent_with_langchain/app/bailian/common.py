import os

from langchain_core.prompts import ChatMessagePromptTemplate, ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import FileManagementToolkit
from pydantic import BaseModel, Field

llm = ChatOpenAI(
    model="qwen-max",
    # model="qwen3-235b-a22b",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ.get("BAILIAN_API_KEY"),
    streaming=True,
)

system_message_template = ChatMessagePromptTemplate.from_template(
    template="你是一位{role}专家，擅长回答{domain}领域的问题",
    role="system",
)

human_message_template = ChatMessagePromptTemplate.from_template(
    template="用户问题：{question}",
    role="user",
)

# 创建提示词模板
chat_prompt_template = ChatPromptTemplate.from_messages([
    system_message_template,
    human_message_template,
])


class AddInputArgs(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")


@tool(
    description="add two numbers",
    args_schema=AddInputArgs,
    return_direct=False,
)
def add(a, b):
    """add two numbers"""
    return a + b


def create_calc_tools():
    return [add]


calc_tools = create_calc_tools()

file_toolkit = FileManagementToolkit(root_dir="/Users/sam/Work/imooc_agent/ai-agent-test/.temp")
file_tools = file_toolkit.get_tools()