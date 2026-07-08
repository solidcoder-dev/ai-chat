from typing import Sequence

from ..application.dtos.tool_spec import ToolSpec


class OllamaToolMapper:
    def __init__(self, tools: Sequence[ToolSpec]) -> None:
        self._tools = list(tools)
        self._provider_to_internal_names = {
            self.to_provider_name(tool.name): tool.name for tool in self._tools
        }

    def to_ollama_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": self.to_provider_name(tool.name),
                    "description": tool.description,
                    "parameters": tool.parameters_schema,
                },
            }
            for tool in self._tools
        ]

    def to_provider_name(self, internal_name: str) -> str:
        return internal_name.replace(".", "__")

    def to_internal_name(self, provider_name: str) -> str:
        try:
            return self._provider_to_internal_names[provider_name]
        except KeyError as exc:
            raise ValueError(f"Unknown Ollama tool name: {provider_name}") from exc
