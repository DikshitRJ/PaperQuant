from __future__ import annotations

import threading
import time


class StatsTracker:
    def __init__(self, max_points: int = 2000):
        self._points: list[tuple[float, float]] = []
        self._max_points = max_points
        self._lock = threading.Lock()

    def record(self, pnl: float, timestamp: float | None = None) -> None:
        with self._lock:
            self._points.append((timestamp or time.time(), float(pnl)))
            del self._points[: -self._max_points]

    def chart(self) -> dict:
        with self._lock:
            points = list(self._points)
        return {
            "timestamps": [
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) for ts, _ in points
            ],
            "pnl_values": [value for _, value in points],
            "interval_seconds": 60,
        }

    def clear(self) -> None:
        with self._lock:
            self._points.clear()
