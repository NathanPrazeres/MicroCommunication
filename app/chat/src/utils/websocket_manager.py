from fastapi import WebSocket
from uuid import UUID

class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}

    def get_ws(self, user_id: UUID) -> WebSocket:
        return self.active_connections.get(user_id)

    async def connect(self, user_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: UUID):
        self.active_connections.pop(user_id)

    async def send(self, user_id: UUID, message: str):
        await self.active_connections.get(user_id).send_text(message)


websocket_manager = WebSocketManager()
