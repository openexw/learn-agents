from langchain_core.messages import HumanMessage, SystemMessage
# from decouple import config
from langchain_openai import ChatOpenAI

from typing import List

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_community.chat_models import ChatTongyi
import os

# print(os.environ['DASHSCOPE_API_KEY'])
chat_model = ChatTongyi(model='qwen-max')

prompt = ChatPromptTemplate.from_messages(
    [
        #  this needs to be a tuple so do not forget the , at the end and do not include any , in-between
        (
            "system",
            "你是一名人工智能助理研究员，负责在5段的简短摘要中研究各种主题。"
            "根据用户要求生成最佳研究。"
            "如果用户提出批评，请回复您之前尝试的修改版本。",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

generate = prompt | chat_model

research = ""
request = HumanMessage(
    content="气候变化研究"
)

# test the single generate agent
for chunk in generate.stream({"messages": [request]}):
    print(chunk.content, end="")
    research += chunk.content

research = ""
request = HumanMessage(
    content="Research on climate change"
)


# 反思
reflection_prompt = ChatPromptTemplate.from_messages(
    [
        #  this needs to be a tuple so do not forget the , at the end
        (
            "system",
            "你是高级研究员"
            " 提供详细的建议，包括长度、深度、风格等请求。"
            " 帮助改进此研究。",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
reflect = reflection_prompt | chat_model

print("\n\n\n")
print("============Relect===============")
print("\n\n\n")

reflection = ""
for chunk in reflect.stream({"messages": [request, HumanMessage(content=research)]}):
    print(chunk.content, end="")
    reflection += chunk.content