from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket(
    "/ws",
    name="WebSocket байланысы",
)
async def websocket_endpoint(websocket: WebSocket):
    """
    summary: Клиенттерге хабарламаларды нақты уақытта таратуға арналған WebSocket байланысы.
    description: Бұл WebSocket эндпоинты клиенттерге нақты уақытта хабарламаларды таратуға мүмкіндік береді. Әрбір қосылған клиент хабарлама жібере алады және барлық клиенттерге таратылады.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"📢 {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
