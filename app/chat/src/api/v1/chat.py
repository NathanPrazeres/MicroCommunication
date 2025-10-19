from fastapi import (
    APIRouter,
    WebSocket,
    status,
    HTTPException,
    Body,
    Depends
)
from utils.websocket_manager import websocket_manager
from auth.dependencies import verify_token
from repositories.db_postgres import postgres_client
from repositories.pubsub_redis import redis_client
from services.messages import handle_client_messages, handle_redis_messages
from utils.jwt_manager import jwt_manager
import asyncio
from uuid import UUID
from models.schema import (
    GetRoomsResponse,
    CreateRoomRequest,
    CreateRoomResponse,
    AddRemoveRoomUserRequest,
    PromoteDemoteRoomUserRequest,
    DefaultTextResponse,
    GetRoomUsersResponse,
    RoomControlMessage,
    SendMessageRequest,
    SendMessageResponse,
    GetMessagesResponse
)
from utils.user_info import get_user_info


chat_router = APIRouter(
    prefix="/api/v1",
    tags=["chat"]
)

@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Websockets are going to be created by connecting to
    ws://CHAT_SERVICE:CHAT_PORT/ws?token=${token}
    """
    try:
        claims = await jwt_manager.decode_token(token)
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
        user_channels = [f"room:{r.id}" for r in user_rooms]

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
        await websocket_manager.disconnect(user_id)

@chat_router.get("/rooms", response_model=GetRoomsResponse)
async def get_rooms(claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    return GetRoomsResponse(
        rooms=(await postgres_client.get_user_rooms(user_id))
    )

@chat_router.post("/rooms", response_model=CreateRoomResponse)
async def create_room(req: CreateRoomRequest = Body(...), claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthenticated access is forbidden."
        )

    room_id = await postgres_client.create_room(
        name=req.name,
        room_type=req.room_type,
        created_by=user_id,
        participants=(req.participants or []),
        description=req.description
    )

    for uid in req.participants:
        await redis_client.publish(f"user:{uid}", RoomControlMessage(room_id=room_id, status="added").model_dump_json())

    return CreateRoomResponse(room_id=room_id)

@chat_router.get("/rooms/{room_id}/messages", response_model=GetMessagesResponse)
async def get_room_messages(room_id: UUID, claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")

    messages = await postgres_client.get_room_messages(user_id, room_id)
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )

    return GetMessagesResponse(messages=messages)

@chat_router.post("/rooms/{room_id}/messages", response_model=SendMessageResponse)
async def send_room_message(room_id: UUID, req: SendMessageRequest = Body(...), claims: dict = Depends(verify_token)):
    """
    NOTE: this endpoint should NOT be used when using realime communication
    through WebSockets and should only serve as a backup as the last resort.
    """
    user_id = claims.get("sub")
    if not await postgres_client.is_user_in_room(user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )

    # Yes, I know that it's odd to have two room IDs but
    # this endpoint isn't meant to be used anyways.
    if room_id != req.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room IDs don't match."
        )

    message = await postgres_client.send_message(user_id, req.room_id, req.content, req.reply_to_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Message couldn't be sent."
        )

    await redis_client.publish(f"room:{req.room_id}", message.model_dump_json())

    return SendMessageResponse(message=message)

@chat_router.get("/rooms/{room_id}/users", response_model=GetRoomUsersResponse)
async def get_room_users(room_id: UUID, claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    if not await postgres_client.is_user_in_room(user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )
    user_ids = await postgres_client.get_room_users(room_id)
    results = await asyncio.gather(*(get_user_info(u) for u in user_ids))
    users = [user_info for user_info in results if user_info is not None]
    # NOTE: the line above creates a list of tasks to be executed asynchronously in parallel
    return GetRoomUsersResponse(users=users)

@chat_router.put("/rooms/{room_id}/users", response_model=DefaultTextResponse)
async def add_room_user(
    room_id: UUID,
    req: AddRemoveRoomUserRequest = Body(...),
    claims: dict = Depends(verify_token)
):
    user_id = claims.get("sub")
    # TODO: verify that the user doing the adding is an admin
    # The new user ID is sent in the request body as JSON: { "user_id": "<uuid>" }
    new_user_id = req.user_id
    if not new_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a user ID to add to the room."
        )

    if await get_user_info(new_user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesn't exist."
        )

    if await postgres_client.is_user_in_room(new_user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {new_user_id} is already a memeber of room {room_id}."
        )

    await postgres_client.add_room_user(new_user_id, room_id)
    await redis_client.publish(
        f"user:{new_user_id}",
        RoomControlMessage(room_id=room_id, status="added").model_dump_json()
    ) # Notify the user that they have been added

    return DefaultTextResponse(message=f"User {new_user_id} added to room {room_id}.")

@chat_router.delete("/rooms/{room_id}/users", response_model=DefaultTextResponse)
async def remove_room_user(
    room_id: UUID,
    req: AddRemoveRoomUserRequest = Body(...),
    claims: dict = Depends(verify_token)
):
    user_id = claims.get("sub")
    # TODO: verify that the user doing the removing is an admin
    # The removed user ID is sent in the request body as JSON: { "user_id": "<uuid>" }
    removed_user_id = req.user_id
    if not removed_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a user ID to remove from the room."
        )

    if not await postgres_client.is_user_in_room(removed_user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {removed_user_id} is not a memeber of room {room_id}."
        )

    await postgres_client.remove_room_user(removed_user_id, room_id)
    await redis_client.publish(
        f"user:{removed_user_id}",
        RoomControlMessage(room_id=room_id, status="removed").model_dump_json()
    ) # Notify the user that they have been removed

    return DefaultTextResponse(message=f"User {removed_user_id} removed from room {room_id}.")

@chat_router.patch("/rooms/{room_id}/users", response_model=DefaultTextResponse)
async def promote_demote(
    room_id: UUID,
    req: PromoteDemoteRoomUserRequest = Body(...),
    claims: dict = Depends(verify_token)
):
    user_id = claims.get("sub")
    if not await postgres_client.is_user_admin(user_id=user_id, room_id=room_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be an admin or owner to promote or demote."
        )

    # The body of the request will be: { "user_id": "<uuid>", "role": "admin" | "member" }
    uid = req.user_id
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a user ID to promote/demote."
        )
    if await postgres_client.is_user_admin(user_id=uid, room_id=room_id, owner_only=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't demote the owner."
        )

    match req.role:
        case "admin":
            if await postgres_client.is_user_admin(uid, room_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User {uid} is already an admin of room {room_id}."
                )

            await postgres_client.promote_room_user(uid, room_id)
            await redis_client.publish(
                f"user:{uid}",
                RoomControlMessage(room_id=room_id, status="promoted").model_dump_json()
            ) # Notify the user that they have been promoted

            return DefaultTextResponse(message=f"User {uid} promoted in room {room_id}.")

        case "member":
            if not await postgres_client.is_user_admin(uid, room_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User {uid} is already an member of room {room_id}."
                )

            await postgres_client.demote_room_user(uid, room_id)
            await redis_client.publish(
                f"user:{uid}",
                RoomControlMessage(room_id=room_id, status="demoted").model_dump_json()
            ) # Notify the user that they have been demoted

            return DefaultTextResponse(message=f"User {uid} demoted in room {room_id}.")

        case _:
            # This code block should be unreachable since the role needs to match one of
            # the two or the request gets rejected by FastAPI (because of the req model)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must provide a valid role for the user (member or admin)."
            )
