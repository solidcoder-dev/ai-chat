from src.composition.wiring import build_chat_engine


def main() -> None:
    engine = build_chat_engine()
    chat_id = "cli"
    user_id = "cli-user"

    print("Chat CLI. Type 'exit' to quit.")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        response = engine.handle_user_message(chat_id=chat_id, text=user_input, user_id=user_id)
        print(response.content)


if __name__ == "__main__":
    main()
