import os
from openai import OpenAI


client = OpenAI(
    api_key="sk-d60f9a55704a46d096c51bc200d2b7fd",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen3-235b-a22b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"},
    ],
)
print(completion.model_dump_json())