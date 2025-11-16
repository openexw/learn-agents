from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough, RunnableBranch

from app.bailian.common import llm

# joke_chain = ChatPromptTemplate.from_template("tell me a joke about {topic}") | llm
# poem_chain = ChatPromptTemplate.from_template("write a 2-line poem about {topic}") | llm
#
# parallel_chain = RunnableParallel(joke=joke_chain, poem=poem_chain)
#
# result = parallel_chain.invoke({"topic": "AI"})
# print(result)


uppercase_lambda = RunnableLambda(lambda x: x.upper())
# result = uppercase_lambda.invoke("hello world")  # 输出 "HELLO WORLD"
# print(result)

branch1_lambda = RunnableLambda(lambda x: x.lower())
branch2_lambda = RunnableLambda(lambda x: x.upper())
branch3_lambda = RunnableLambda(lambda x: x)

chain = (llm | StrOutputParser() | uppercase_lambda | RunnableBranch(
    (lambda x: "QWEN" in x, branch1_lambda),
    (lambda x: "OPENAI" in x, branch2_lambda),
    branch3_lambda,
))
result = chain.invoke("who are you?")
print(result)