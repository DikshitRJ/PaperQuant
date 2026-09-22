import asyncio
import json

import pytest

websocket_module = pytest.importorskip("api.websocket")


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message):
        self.messages.append(message)


def test_broadcast_wraps_event_type_data_and_timestamp():
    async def run():
        manager = websocket_module.ConnectionManager()
        first = FakeWebSocket()
        second = FakeWebSocket()
        manager.active_connections.extend([first, second])

        await manager.broadcast("log", {"content": "hello"})

        payload = json.loads(first.messages[0])
        assert payload["type"] == "log"
        assert payload["data"] == {"content": "hello"}
        assert payload["timestamp"]
        assert len(second.messages) == 1

    asyncio.run(run())


def test_broadcast_removes_connections_that_fail_to_send():
    class BrokenWebSocket(FakeWebSocket):
        async def send_text(self, message):
            raise RuntimeError("closed")

    async def run():
        manager = websocket_module.ConnectionManager()
        broken = BrokenWebSocket()
        manager.active_connections.append(broken)

        await manager.broadcast("error", {"code": "x"})

        assert broken not in manager.active_connections

    asyncio.run(run())
