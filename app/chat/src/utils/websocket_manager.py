from fastapi import WebSocket
from uuid import UUID
from typing import Any
from pydantic import BaseModel


class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}

    def get(self, user_id: UUID) -> WebSocket:
        return self.active_connections.get(user_id)

    async def connect(self, user_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: UUID):
        ws = self.active_connections.pop(user_id, None)
        if ws is None:
            return

        try:
            await ws.close()
        except Exception:
            # ignore errors on close to avoid raising during cleanup
            pass

    async def send(self, user_id: UUID, message: Any):
        ws = self.active_connections.get(user_id)
        if ws is None:
            return
        try:
            # If it's a Pydantic model, convert to json
            if isinstance(message, BaseModel):
                await ws.send_json(message.model_dump())
            elif isinstance(message, str):
                await ws.send_text(message)
            else:
                await ws.send_json(message)
        except Exception:
            # ignore send errors to avoid crashing caller
            pass

websocket_manager = WebSocketManager()
