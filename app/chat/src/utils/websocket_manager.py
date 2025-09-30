from fastapi import WebSocket
from uuid import UUID
from typing import Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}

    def get(self, user_id: UUID) -> WebSocket:
        return self.active_connections.get(user_id)

    async def connect(self, user_id: UUID, websocket: WebSocket):
        logger.info("Accepting WebSocket connection for user: %s", str(user_id))
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("WebSocket connected. Active connections: %d", len(self.active_connections))

    async def disconnect(self, user_id: UUID):
        logger.info("Disconnecting WebSocket for user: %s", str(user_id))
        ws = self.active_connections.pop(user_id, None)
        if ws is None:
            logger.warning("Attempted to disconnect non-existent WebSocket for user: %s", str(user_id))
            return

        try:
            await ws.close()
            logger.info("WebSocket closed for user: %s. Active connections: %d", str(user_id), len(self.active_connections))
        except Exception as e:
            # ignore errors on close to avoid raising during cleanup
            logger.error("Error closing WebSocket for user %s: %s", str(user_id), str(e))

    async def send(self, user_id: UUID, message: Any):
        ws = self.active_connections.get(user_id)
        if ws is None:
            logger.warning("Attempted to send message to disconnected user: %s", str(user_id))
            return
        try:
            # If it's a Pydantic model, convert to json
            if isinstance(message, BaseModel):
                logger.debug("Sending JSON message to user: %s", str(user_id))
                await ws.send_json(message.model_dump(mode="json"))
            elif isinstance(message, str):
                logger.debug("Sending text message to user: %s", str(user_id))
                await ws.send_text(message)
            else:
                logger.debug("Sending raw JSON to user: %s", str(user_id))
                await ws.send_json(message)
        except Exception as e:
            # ignore send errors to avoid crashing caller
            logger.error("Error sending message to user %s: %s", str(user_id), str(e))

websocket_manager = WebSocketManager()
