from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone


class LogBuffer:
    SOURCE_COLORS = {
        "price_adapter": "text-blue-400",
        "trade_adapter": "text-yellow-400",
        "strategy": "text-green-400",
        "system": "text-purple-400",
        "error": "text-red-400",
    }

    def __init__(self, max_size: int = 500):
        self._buffer: deque[dict] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def add(self, source: str, message: str) -> dict:
        message = message.strip()
        color = self.SOURCE_COLORS.get(source, "text-gray-400")
        if any(
            word in message.lower()
            for word in ("error", "exception", "traceback", "failed")
        ):
            color = self.SOURCE_COLORS["error"]
        entry = {
            "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "content": f"[{source.upper()}] {message}",
            "color": color,
            "_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._buffer.append(entry)
        return {k: v for k, v in entry.items() if k != "_timestamp"}

    def get_since(self, since: str | None = None, limit: int = 100) -> list[dict]:
        with self._lock:
            entries = list(self._buffer)
        if since:
            entries = [entry for entry in entries if entry["_timestamp"] > since]
        return [
            {k: v for k, v in item.items() if k != "_timestamp"}
            for item in entries[-limit:]
        ]

    def get_all(self) -> list[dict]:
        with self._lock:
            size = len(self._buffer)
        return self.get_since(limit=size or 1)

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
