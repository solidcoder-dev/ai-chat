from abc import ABC, abstractmethod

from ..dtos.assistant_request import AssistantRequest
from ..dtos.assistant_response import AssistantResponse


class Assistant(ABC):
    @abstractmethod
    def infer(self, request: AssistantRequest) -> AssistantResponse:
        raise NotImplementedError
