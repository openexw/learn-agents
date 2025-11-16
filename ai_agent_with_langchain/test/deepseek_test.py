import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

llm = ChatOpenAI(
    model="deepseek-r1-0528",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ.get("BAILIAN_API_KEY"),
    streaming=True,
)

class Result(BaseModel):
    thinking: str = Field("解释你的思考过程")
    result: str = Field("问题的结果")

parser = JsonOutputParser(pydantic_object=Result)
instructions = parser.get_format_instructions()

chain = llm | parser

response = chain.invoke(f"""返回体遵守以下规则：
{instructions}

问题：
你是谁？""")

print(response)