from src.infrastructure.in_memory_chat_repo import InMemoryChatRepo
from src.infrastructure.ollama_assistant import OllamaAssistant
from src.infrastructure.simple_chat_engine import SimpleChatEngine


def main() -> None:
    chat_repo = InMemoryChatRepo()
    assistant = OllamaAssistant(model="llama3")
    engine = SimpleChatEngine(chat_repo=chat_repo, assistant=assistant)

    response = engine.handle_user_message(
        chat_id="demo",
        text="Give me a one sentence summary of the solar system.",
    )

    print(response.content)


if __name__ == "__main__":
    main()
