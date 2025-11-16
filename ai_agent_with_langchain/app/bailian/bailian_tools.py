from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.bailian.common import chat_prompt_template, llm

class AddInputArgs(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")

@tool(
    description="add two numbers",
    args_schema=AddInputArgs,
)
def add(a, b):
    """add two numbers"""
    return a + b

# add_tools = Tool.from_function(
#     func=add,
#     name="add",
#     description="add two numbers",
# )

tool_dict = {
    "add": add
}

llm_with_tools = llm.bind_tools([add])

chain = chat_prompt_template | llm_with_tools

resp = chain.invoke(input={"role": "计算", "domain": "数学计算", "question": "使用工具计算：100+100=?"})

print(resp)

for tool_calls in resp.tool_calls:
    print(tool_calls)

    args = tool_calls["args"]
    print(args)

    func_name = tool_calls["name"]
    print(func_name)

    tool_func = tool_dict[func_name]

    tool_content = tool_func.invoke(args)
    print(tool_content)
