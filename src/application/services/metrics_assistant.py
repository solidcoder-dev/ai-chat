from __future__ import annotations

from time import perf_counter

from ..dtos.assistant_request import AssistantRequest
from ..dtos.assistant_response import AssistantResponse
from ..ports.assistant import Assistant
from ..ports.metrics import Metrics


class MetricsAssistant(Assistant):
    def __init__(self, inner: Assistant, metrics: Metrics) -> None:
        self._inner = inner
        self._metrics = metrics

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        self._metrics.increment("assistant.infer.count")
        start = perf_counter()
        try:
            response = self._inner.infer(request)
        except Exception:
            self._metrics.increment("assistant.infer.error")
            raise
        finally:
            duration = perf_counter() - start
            self._metrics.timing("assistant.infer.duration_seconds", duration)

        self._metrics.increment(f"assistant.infer.kind.{response.kind}")
        return response
