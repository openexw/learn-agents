import asyncio
from langgraph.graph import END, MessageGraph
from typing import List, Sequence, Any, Coroutine
from langgraph.graph import MessageGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
# from decouple import config
from langchain_openai import ChatOpenAI

from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_community.chat_models import ChatTongyi
import os

from dotenv import load_dotenv

load_dotenv()



from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()

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
reflect = reflection_prompt | chat_model | generate


async def generation_node(state: Sequence[BaseMessage]):
    # return await generate.ainvoke({"messages": state}, config={"callbacks": [langfuse_handler]})
    return await generate.ainvoke({"messages": state})


async def reflection_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    # Other messages we need to adjust
    cls_map = {"ai": HumanMessage, "human": AIMessage}

    # First message is the original user request. We hold it the same for all nodes
    translated = [messages[0]] + [
        cls_map[msg.type](content=msg.content) for msg in messages[1:]
    ]
    # res = await reflect.ainvoke({"messages": translated}, config={"callbacks": [langfuse_handler]})
    res = await reflect.ainvoke({"messages": translated})

    # this will be treated as a feedback for the generator
    return HumanMessage(content=res.content)


def should_continue(state: List[BaseMessage]):
    if len(state) > 6:
        # End after 5 iterations
        return END
    return "reflect"

builder = MessageGraph()
builder.add_node("generate", generation_node)
builder.add_node("reflect", reflection_node)
builder.set_entry_point("generate")

builder.add_conditional_edges("generate", should_continue)
builder.add_edge("reflect", "generate")
graph = builder.compile()


async def stream_responses():
    async for event in graph.astream(
            [
                request
            ],
    ):
        print(event)
        print("---")


asyncio.run(stream_responses())
