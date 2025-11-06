from langchain_core.tools import  tool
from pydantic import BaseModel, Field


class AddInputArgs(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")

@tool(
    description="add two numbers",
    args_schema=AddInputArgs,
    return_direct=False,
)
def add(a, b: int) -> int:
    return a + b
