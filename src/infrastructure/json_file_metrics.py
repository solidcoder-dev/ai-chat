from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..application.ports.metrics import Metrics


class JsonFileMetrics(Metrics):
    def __init__(self, path: str = "metrics.json") -> None:
        self._path = path
        self._events: List[Dict[str, Any]] = []

    def increment(self, name: str, value: int = 1) -> None:
        self._events.append(
            {
                "type": "counter",
                "name": name,
                "value": value,
                "ts": self._now_iso(),
            }
        )
        self._flush()

    def timing(self, name: str, duration_seconds: float) -> None:
        self._events.append(
            {
                "type": "timing",
                "name": name,
                "duration_seconds": duration_seconds,
                "ts": self._now_iso(),
            }
        )
        self._flush()

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as handle:
            json.dump(self._events, handle, indent=2)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
