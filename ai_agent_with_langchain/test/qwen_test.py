from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.bailian.common import file_tools
from app.code_agent.model.qwen import llm_qwen

chat_prompt_template = ChatPromptTemplate.from_messages([
('system', '''
- 你是一个数学方面的专家，擅长使用工具解决各种数学计算问题
- 只要是数学计算问题，必须全部使用工具完成计算
- 如果是综合算式需要你先进行按照计算优先级的规则进行拆分一步一步的使用工具完成计算
'''),
('human', '{question}')
])

tools = file_tools
memory = MemorySaver()

#创建智能体
agent = create_react_agent(
    model=llm_qwen,
    tools=tools,
    checkpointer=memory,
    debug=False
)

chain = chat_prompt_template | agent

config = RunnableConfig(configurable={"thread_id": 1})
res = chain.invoke(input={"question": "100*100=？"}, config=config)
print(res)