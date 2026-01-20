from ..application.ports.metrics import Metrics


class NoOpMetrics(Metrics):
    def increment(self, name: str, value: int = 1) -> None:
        return None

    def timing(self, name: str, duration_seconds: float) -> None:
        return None
