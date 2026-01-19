from typing import Optional


class ApplicationError(Exception):
    """Base class for application-level errors."""


class InfrastructureError(ApplicationError):
    """Base class for infrastructure adapter failures."""


class ModelNotAvailableError(InfrastructureError):
    def __init__(self, model: str, message: str) -> None:
        super().__init__(f"Model '{model}' not available: {message}")
        self.model = model


class LlmProviderError(InfrastructureError):
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None) -> None:
        status = f" (status {status_code})" if status_code is not None else ""
        super().__init__(f"{provider} error{status}: {message}")
        self.provider = provider
        self.status_code = status_code
