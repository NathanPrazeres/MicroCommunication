from fastapi import (
    APIRouter,
    WebSocket,
    status,
    HTTPException,
    Body,
    Depends
)
from utils.websocket_manager import websocket_manager
from auth.token import decode_jwt
from src.auth.dependencies import verify_token
from repositories.db_postgres import postgres_client
from services.messages import handle_client_messages, handle_redis_messages
import asyncio
from uuid import UUID
from src.models.schema import AddRoomUserRequest


chat_router = APIRouter(
    prefix="/api/v1",
    tags=["chat"],
    dependencies=[Depends(verify_token)]
)

@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Websockets are going to be created by connecting to
    wss://chat.local/ws?token=${token}

    TODO: are we using chat.local or some other domain?
    """
    try:
        claims = decode_jwt(token)
        user_id = claims.get("sub")
        # TODO: make sure this is necessary and works
        if user_id is None:
            raise ValueError() # trigger the except block
    except:
        await websocket.close(code=1008) # Policy violation
        return

    await websocket_manager.connect(user_id, websocket)

    try:
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
            try:
                await task
            except asyncio.CancelledError:
                pass

    finally:
        websocket_manager.disconnect(user_id)

@chat_router.get("/rooms")
async def get_rooms(claims=Depends(verify_token)):
    pass

@chat_router.post("/rooms")
async def create_room(claims=Depends(verify_token)):
    pass

@chat_router.get("/rooms/{room_id}/users")
async def get_room_users(room_id: UUID, claims=Depends(verify_token)):
    user_id = claims.get("sub")
    if not await postgres_client.user_in_room(user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )
    users = await postgres_client.get_room_users(room_id)
    return {"data": users}

@chat_router.put("/rooms/{room_id}/users")
async def add_room_user(
    room_id: UUID,
    req: AddRoomUserRequest = Body(...),
    claims=Depends(verify_token)
):
    # The new user ID is sent in the request body as JSON: { "user_id": "<uuid>" }
    user_id = claims.get("sub")
    new_user_id = req.user_id
    if not new_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a user ID to add to the room."
        )

    if await postgres_client.user_in_room(new_user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {new_user_id} is already a memeber of room {room_id}."
        )

    await postgres_client.add_user_room(new_user_id, room_id)
    return {"message": f"User {new_user_id} added to room {room_id}."}
