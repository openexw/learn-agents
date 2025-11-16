from langchain_core.prompts import ChatPromptTemplate, ChatMessagePromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

llm = ChatOpenAI(
    model="qwen-max-latest",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr("sk-d60f9a55704a46d096c51bc200d2b7fd"),
    streaming=True,
)

system_message_template = ChatMessagePromptTemplate.from_template(
    template="你是一位{role}专家，擅长回答{domain}领域的问题",
    role="system",
)

human_message_template = ChatMessagePromptTemplate.from_template(
    template="用户问题：{question}",
    role="user",
)

# 创建提示词模板
chat_prompt_template = ChatPromptTemplate.from_messages([
    system_message_template,
    human_message_template,
])

# 模板+变量=>提示词
prompt = chat_prompt_template.format_messages(
    role="编程",
    domain="Web开发",
    question="你擅长什么？"
)

# print(prompt)

example_template = "输入：{input}\n输出：{output}"

examples = [
    {"input": "将'Hello'翻译成中文", "output": "你好"},
    {"input": "将'Goodbye'翻译成中文", "output": "再见"},
    {"input": "将'Pen'翻译成中文", "output": "钢笔"},
]

few_shot_prompt_template = FewShotPromptTemplate(
    examples=examples,
    example_prompt=PromptTemplate.from_template(example_template),
    prefix="请将以下英文翻译成中文：",
    suffix="输入：{text}\n输出：",
    input_variables=["text"],
)

print(few_shot_prompt_template)

prompt = few_shot_prompt_template.format(text="Thank you!")
print(prompt)

# resp = llm.stream(prompt)

chain = few_shot_prompt_template | llm

resp = chain.stream(input={"text": "Thank you!"})

for chunk in resp:
    print(chunk.content, end="")