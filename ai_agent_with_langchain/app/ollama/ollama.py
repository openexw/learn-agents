from langchain_ollama.chat_models import ChatOllama


if __name__ == "__main__":
    llm = ChatOllama(model="deepseek-r1:7b")
    messages = [
        (
            "system",
            "You are a helpful assistant that translates English to French. Translate the user sentence.",
        ),
        ("human", "I love programming."),
    ]
    resp = llm.stream(messages)

    for chunk in resp:
        print(chunk.content, end="")
