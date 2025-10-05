from fastapi import (
    APIRouter,
    WebSocket
)
from utils.websocket_manager import websocket_manager
from utils.validation import jwt_validator
from repositories.db_postgres import postgres_client
from services.messages import handle_client_messages, handle_redis_messages
import asyncio

chat_router = APIRouter(prefix="/api/v1", tags=["chat"])

@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Websockets are going to be created by connecting to
    wss://chat.local/ws?token=${token}

    TODO: are we using chat.local or some other domain?
    """
    try:
        claims = jwt_validator.verify(token)
        user_id = claims.sub
    except:
        await websocket.close(code=1008) # Policy violation
        return

    await websocket_manager.connect(user_id, websocket)

    user_rooms = await postgres_client.get_user_rooms(user_id)
    user_channels = [f"room:{r}" for r in user_rooms]

    client_task = asyncio.create_task(handle_client_messages(user_id))
    redis_task = asyncio.create_task(handle_redis_messages(user_id, user_channels))

    _, pending = await asyncio.wait(
        [client_task, redis_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()

    websocket_manager.disconnect(user_id)

@chat_router.get("/rooms")
def get_rooms():
    pass

@chat_router.post("/rooms")
def create_room():
    pass

@chat_router.get("rooms/{room_id}/users")
def get_room_users(room_id: int):
    postgres_client.get_room_users(room_id)
