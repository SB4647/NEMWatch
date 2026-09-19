import asyncio

import pytest

from nemwatch.live.hub import ConnectionHub


class FakeSocket:
    def __init__(self) -> None:
        self.sent = []
        self.closed = None

    async def accept(self):
        return None

    async def send_json(self, message):
        self.sent.append(message)

    async def close(self, code, reason):
        self.closed = (code, reason)


@pytest.mark.anyio
async def test_hub_broadcasts_without_blocking_on_send() -> None:
    hub = ConnectionHub(queue_size=1)
    socket = FakeSocket()
    await hub.connect(socket)  # type: ignore[arg-type]
    await hub.broadcast({"type": "dispatch_observed", "data": {}})
    await asyncio.sleep(0)
    assert socket.sent == [{"type": "dispatch_observed", "data": {}}]
    await hub.disconnect(socket)  # type: ignore[arg-type]
