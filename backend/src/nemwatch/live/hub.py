import asyncio
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket


@dataclass
class ClientConnection:
    queue: asyncio.Queue[dict[str, Any]]
    sender: asyncio.Task[None]


class ConnectionHub:
    def __init__(self, queue_size: int = 100) -> None:
        self.queue_size = queue_size
        self._clients: dict[WebSocket, ClientConnection] = {}

    @property
    def connection_count(self) -> int:
        return len(self._clients)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_size)
        self._clients[websocket] = ClientConnection(
            queue=queue, sender=asyncio.create_task(self._send(websocket, queue))
        )

    async def _send(self, websocket: WebSocket, queue: asyncio.Queue[dict[str, Any]]) -> None:
        while True:
            await websocket.send_json(await queue.get())

    async def broadcast(self, message: dict[str, Any]) -> None:
        slow: list[WebSocket] = []
        for websocket, connection in tuple(self._clients.items()):
            try:
                connection.queue.put_nowait(message)
            except asyncio.QueueFull:
                slow.append(websocket)
        for websocket in slow:
            await websocket.close(code=1013, reason="Live client is too slow")
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        connection = self._clients.pop(websocket, None)
        if connection is not None:
            connection.sender.cancel()

