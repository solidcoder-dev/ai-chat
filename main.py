from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Sequence

from src.composition.coding_wiring import build_coding_chat_session
from src.composition.wiring import build_chat_engine


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["chat", "coding"], default="chat")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--model")
    args = parser.parse_args(argv)
    if args.mode == "coding" and args.workspace is None:
        parser.error("--workspace is required when --mode coding")
    return args


def run_cli(
    argv: Sequence[str] | None = None,
    *,
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
    chat_engine_builder=build_chat_engine,
    coding_session_builder=build_coding_chat_session,
) -> int:
    args = parse_args(argv)
    if args.mode == "coding":
        return _run_coding_cli(
            workspace_path=args.workspace.expanduser().resolve(),
            model=args.model,
            input_func=input_func,
            output_func=output_func,
            coding_session_builder=coding_session_builder,
        )
    return _run_default_cli(
        input_func=input_func,
        output_func=output_func,
        chat_engine_builder=chat_engine_builder,
    )


def _run_default_cli(
    *,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
    chat_engine_builder,
) -> int:
    engine = chat_engine_builder()
    output_func("Chat CLI. Type 'exit' to quit.")
    _chat_loop(engine, input_func=input_func, output_func=output_func)
    return 0


def _run_coding_cli(
    *,
    workspace_path: Path,
    model: str | None,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
    coding_session_builder,
) -> int:
    output_func("Starting MCP filesystem server...")
    output_func("Loading assistant model...")
    session = None
    try:
        session = coding_session_builder(workspace_path, model=model)
    except Exception as exc:
        output_func(f"Failed to start coding assistant: {exc}")
        return 1
    try:
        output_func("Coding assistant started.")
        output_func(f"Workspace: {workspace_path}")
        output_func("Type 'exit' to quit.")
        _chat_loop(
            session.engine,
            input_func=input_func,
            output_func=output_func,
            response_prefix="Assistant: ",
        )
        return 0
    except KeyboardInterrupt:
        output_func("Coding assistant stopped.")
        return 130
    finally:
        if session is not None:
            session.close()


def _chat_loop(
    engine,
    *,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
    response_prefix: str = "",
) -> None:
    chat_id = "cli"
    user_id = "cli-user"
    while True:
        user_input = input_func("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        try:
            response = engine.handle_user_message(
                chat_id=chat_id,
                text=user_input,
                user_id=user_id,
            )
        except Exception as exc:
            output_func(f"Assistant error: {exc}")
            continue
        output_func(f"{response_prefix}{response.content}")


def main() -> None:
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
