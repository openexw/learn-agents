from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser, JsonOutputParser
from langchain.output_parsers import BooleanOutputParser, DatetimeOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.bailian.common import chat_prompt_template, llm

# parser = StrOutputParser()
# parser = CommaSeparatedListOutputParser()
# parser = BooleanOutputParser()
# parser = JsonOutputParser()
parser = DatetimeOutputParser()
instructions = parser.get_format_instructions()

chain = chat_prompt_template | llm | parser

prompt = ChatPromptTemplate.from_messages([
    ("system", f"必须按照以下格式返回日期时间：{instructions}"),
    ("human", "请将以下自然语言转换为标准日期时间格式：{text}")
])

chain = prompt | llm | parser

resp = chain.invoke({"text": "二零二五年五月一日上午十点十分"})

print(resp)
