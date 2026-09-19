from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["live"])


@router.websocket("/ws/market")
async def market_socket(websocket: WebSocket) -> None:
    hub = websocket.app.state.hub
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
