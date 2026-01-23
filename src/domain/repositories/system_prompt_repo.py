from abc import ABC, abstractmethod

from ..system_prompt import SystemPrompt


class SystemPromptRepo(ABC):
    @abstractmethod
    def load_prompt(self, prompt_id: str) -> SystemPrompt:
        raise NotImplementedError

    @abstractmethod
    def save_prompt(self, prompt: SystemPrompt) -> None:
        raise NotImplementedError
