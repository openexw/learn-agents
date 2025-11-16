from langchain_core.tools import  tool
from pydantic import BaseModel, Field

class AddInputArgs(BaseModel):
    a: str = Field(description="first number")
    b: str = Field(description="second number")

@tool(
    description="add two numbers",
    args_schema=AddInputArgs,
    return_direct=True,
)
def add(a, b):
    """add two numbers"""
    return a + b