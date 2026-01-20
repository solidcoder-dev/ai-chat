from abc import ABC, abstractmethod


class Metrics(ABC):
    @abstractmethod
    def increment(self, name: str, value: int = 1) -> None:
        raise NotImplementedError

    @abstractmethod
    def timing(self, name: str, duration_seconds: float) -> None:
        raise NotImplementedError
