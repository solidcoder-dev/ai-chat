from typing import Optional


class ApplicationError(Exception):
    """Base class for application-level errors."""


class InfrastructureError(ApplicationError):
    """Base class for infrastructure adapter failures."""


class ModelNotAvailableError(InfrastructureError):
    def __init__(self, model: str, message: str) -> None:
        super().__init__(f"Model '{model}' not available: {message}")
        self.model = model


class ToolCallingNotSupportedError(InfrastructureError):
    def __init__(self, model: str) -> None:
        super().__init__(
            "\n".join(
                [
                    f"Selected model '{model}' does not support tool calling.",
                    "Use a tool-capable model, for example:",
                    "  ollama pull llama3.1:8b",
                    "  python3 main.py --mode coding --workspace . --model llama3.1:8b",
                ]
            )
        )
        self.model = model


class LlmProviderError(InfrastructureError):
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None) -> None:
        status = f" (status {status_code})" if status_code is not None else ""
        super().__init__(f"{provider} error{status}: {message}")
        self.provider = provider
        self.status_code = status_code
