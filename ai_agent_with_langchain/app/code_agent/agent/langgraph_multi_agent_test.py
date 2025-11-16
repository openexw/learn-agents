from langchain_core.messages import convert_to_messages
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from app.code_agent.model.qwen import llm_qwen

def pretty_print_messages(update, last_message=False):
    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        print(update_label)

        messages = convert_to_messages(node_update['messages'])
        if last_message:
            messages = messages[-1:]

        for message in messages:
            pretty_message = message.pretty_repr(html=True)
            print(pretty_message)

        print("\n\n")

def add(a: float, b: float) -> float:
    """add two numbers"""
    return a + b

def multiply(a: float, b: float) -> float:
    """multiply two numbers"""
    return a * b

def web_search(query: str) -> str:
    """Search the web for information."""
    return (
        "Here are the headcounts for each of the FAANG companies in 2024:\n"
        "1. **Facebook (Meta)**: 67,317 employees.\n"
        "2. **Apple**: 164,000 employees.\n"
        "3. **Amazon**: 1,551,000 employees.\n"
        "4. **Netflix**: 14,000 employees.\n"
        "5. **Google (Alphabet)**: 181,269 employees."
    )

math_agent = create_react_agent(
    model=llm_qwen,
    tools=[add, multiply],
    name="math_expert",
    prompt="你是一个数学专家，一次执行只使用一个工具"
)

research_agent = create_react_agent(
    model=llm_qwen,
    tools=[web_search],
    name="research_expert",
    prompt="你是一个世界级的调研专家，能够使用web_search工具，不要使用任何数学工具"
)

workflow = create_supervisor(
    agents=[math_agent, research_agent],
    model=llm_qwen,
    prompt=(
        "You are a team supervisor managing a research expert and a math expert. "
        "For current events, use research_agent. "
        "For math problems, use math_agent."
    )
)

app = workflow.compile()

for chunk in app.stream({
    "messages": [
        {
            "role": "user",
            "content": "what's the combined headcount of the FAANG companies in 2024?"
        }
    ]
}):
    pretty_print_messages(chunk)
