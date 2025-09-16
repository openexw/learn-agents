import os
from typing import Annotated

from dataclasses_json.core import confs
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from dotenv import load_dotenv

load_dotenv('../.env')

from langchain_community.chat_models import ChatTongyi

chat_model = ChatTongyi(model='qwen-max')


class State(TypedDict):
    messages: Annotated[list, add_messages]
    mame: str
    birthday: str


graph_builder = StateGraph(State)
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool

from langgraph.types import Command, interrupt


@tool
# Note that because we are generating a ToolMessage for a state update, we
# generally require the ID of the corresponding tool call. We can use
# LangChain's InjectedToolCallId to signal that this argument should not
# be revealed to the model in the tool's schema.
def human_assistance(
        name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
):
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday,
        },
    )
    # If the information is correct, update the state as-is.
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "Correct"
    # Otherwise, receive information from the human reviewer.
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Made a correction: {human_response}"

    # This time we explicitly update the state with a ToolMessage inside
    # the tool.
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    # We return a Command object in the tool to update our state.
    return Command(update=state_update)


# 添加 tools
from langchain_tavily import TavilySearch

search_tool = TavilySearch(max_results=2)
llm_with_tools = chat_model.bind_tools([search_tool,human_assistance])

from langgraph.prebuilt import ToolNode, tools_condition

tool_node = ToolNode(tools=[search_tool,human_assistance])
graph_builder.add_node("tools", tool_node)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_conditional_edges("chatbot", tools_condition)

from langgraph.checkpoint.memory import MemorySaver

mem = MemorySaver()

# 添加入口
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# 编译图
g = graph_builder.compile(checkpointer=mem)

user_input = (
    "Can you look up when LangGraph was released? "
    "When you have the answer, use the human_assistance tool for review."
)
config = {"configurable": {"thread_id": "1"}}

events = g.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()
