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
    GetMessagesResponse,
    GetRoomInfoResponse
)
from utils.user_info import get_user_info
from prometheus_client import Counter, Gauge
import logging

logger = logging.getLogger(__name__)

chat_router = APIRouter(
    prefix="/api/v1",
    tags=["chat"]
)

websocket_connections_total = Counter(
    "websocket_connections_total",
    "Total number of WebSocket connection attempts",
    ["endpoint", "status"]
)

active_websocket_connections = Gauge(
    "active_websocket_connections",
    "Number of currently active WebSocket connections",
    ["endpoint"]
)


@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Websockets are going to be created by connecting to
    ws://CHAT_SERVICE:CHAT_PORT/ws?token=${token}
    """
    logger.debug("WebSocket connection attempt")
    try:
        claims = await jwt_manager.decode_token(token)
        user_id = claims.get("sub")
        # TODO: make sure this is necessary and works
        if user_id is None:
            raise ValueError() # trigger the except block
    except:
        logger.warning("WebSocket connection rejected: invalid token")
        websocket_connections_total.labels(endpoint="/api/v1/ws", status="rejected").inc()
        await websocket.close(code=1008)
        return

    logger.info("WebSocket connection accepted for user: %s", str(user_id))
    websocket_connections_total.labels(endpoint="/api/v1/ws", status="connected").inc()
    active_websocket_connections.labels(endpoint="/api/v1/ws").inc()

    existing_ws = websocket_manager.get(user_id)
    if existing_ws is not None:
        logger.info("Replacing existing WebSocket connection for user: %s", str(user_id))
        await websocket_manager.disconnect(user_id)

    await websocket_manager.connect(user_id, websocket)

    try:
        user_rooms = await postgres_client.get_user_rooms(user_id)
        user_channels = [f"room:{r.id}" for r in user_rooms]
        logger.debug("User %s subscribed to %d rooms", str(user_id), len(user_channels))

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
        logger.info("WebSocket disconnected for user: %s", str(user_id))
        active_websocket_connections.labels(endpoint="/api/v1/ws").dec()
        await websocket_manager.disconnect(user_id)

@chat_router.get("/rooms", response_model=GetRoomsResponse)
async def get_rooms(claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    logger.debug("Getting rooms for user: %s", str(user_id))
    rooms = await postgres_client.get_user_rooms(user_id)
    return GetRoomsResponse(rooms=rooms)

@chat_router.post("/rooms", response_model=CreateRoomResponse)
async def create_room(req: CreateRoomRequest = Body(...), claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    if not user_id:
        logger.warning("Unauthenticated room creation attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthenticated access is forbidden."
        )

    logger.info("Creating room '%s' for user %s with %d participants", req.name, str(user_id), len(req.participants or []))
    room_id = await postgres_client.create_room(
        name=req.name,
        room_type=req.room_type,
        created_by=user_id,
        participants=(req.participants or []),
        description=req.description
    )

    for uid in (req.participants or []) + [user_id]:
        await redis_client.publish(f"user:{uid}", RoomControlMessage(room_id=room_id, status="added").model_dump_json())

    return CreateRoomResponse(room_id=room_id)

@chat_router.get("/rooms/{room_id}/messages", response_model=GetMessagesResponse)
async def get_room_messages(room_id: UUID, claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    if not user_id:
        logger.warning("Unauthenticated message fetch attempt for room: %s", str(room_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthenticated access is forbidden."
        )

    logger.debug("Fetching messages for room %s by user %s", str(room_id), str(user_id))
    messages = await postgres_client.get_room_messages(user_id, room_id)
    if messages is None:
        logger.warning("User %s attempted to access room %s without membership", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )

    return GetMessagesResponse(messages=messages)

@chat_router.get("/rooms/{room_id}", response_model=GetRoomInfoResponse)
async def get_room_info(room_id: UUID, claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    logger.debug("Fetching room info for %s by user %s", str(room_id), str(user_id))
    room_info = await postgres_client.get_room_info(user_id, room_id)
    if not room_info:
        logger.warning("User %s attempted to access room info for %s without membership", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )

    return GetRoomInfoResponse(room=room_info)

@chat_router.post("/rooms/{room_id}/messages", response_model=SendMessageResponse)
async def send_room_message(room_id: UUID, req: SendMessageRequest = Body(...), claims: dict = Depends(verify_token)):
    """
    NOTE: this endpoint should NOT be used when using realtime communication
    through WebSockets and should only serve as a backup as the last resort.
    """
    user_id = claims.get("sub")
    logger.debug("HTTP message send attempt for room %s by user %s", str(room_id), str(user_id))

    if not await postgres_client.is_user_in_room(user_id, room_id):
        logger.warning("User %s attempted to send message to room %s without membership", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )

    # Yes, I know that it's odd to have two room IDs but
    # this endpoint isn't meant to be used anyways.
    if room_id != req.room_id:
        logger.warning("Room ID mismatch in send message: path=%s, body=%s", str(room_id), str(req.room_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room IDs don't match."
        )

    message = await postgres_client.send_message(user_id, req.room_id, req.content, req.reply_to_id)
    if message is None:
        logger.error("Failed to send message for user %s in room %s", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Message couldn't be sent."
        )

    await redis_client.publish(f"room:{req.room_id}", message.model_dump_json())

    return SendMessageResponse(message=message)

@chat_router.patch("/rooms/{room_id}/messages", response_model=DefaultTextResponse)
async def mark_room_as_read(room_id: UUID, claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    logger.debug("Marking room %s as read for user %s", str(room_id), str(user_id))
    await postgres_client.mark_as_read(user_id, room_id)
    return DefaultTextResponse(message=f"Room {room_id} marked as read.")

@chat_router.get("/rooms/{room_id}/users", response_model=GetRoomUsersResponse)
async def get_room_users(room_id: UUID, claims: dict = Depends(verify_token)):
    user_id = claims.get("sub")
    logger.debug("Fetching users for room %s by user %s", str(room_id), str(user_id))

    if not await postgres_client.is_user_in_room(user_id, room_id):
        logger.warning("User %s attempted to fetch users for room %s without membership", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't a member of this room."
        )

    user_ids = await postgres_client.get_room_users(room_id)
    results = await asyncio.gather(*(get_user_info(u) for u in user_ids))
    users = [user_info for user_info in results if user_info is not None]
    logger.debug("Found %d users in room %s", len(users), str(room_id))
    return GetRoomUsersResponse(users=users)

@chat_router.put("/rooms/{room_id}/users", response_model=DefaultTextResponse)
async def add_room_user(
    room_id: UUID,
    req: AddRemoveRoomUserRequest = Body(...),
    claims: dict = Depends(verify_token)
):
    user_id = claims.get("sub")
    logger.debug("User %s attempting to add user %s to room %s", str(user_id), str(req.user_id), str(room_id))

    if not await postgres_client.is_user_admin(user_id, room_id):
        logger.warning("Non-admin user %s attempted to add user to room %s", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be an admin in the room to add a user."
        )

    # The new user ID is sent in the request body as JSON: { "user_id": "<uuid>" }
    new_user_id = req.user_id
    if not new_user_id:
        logger.warning("Empty user_id in add user request for room %s", str(room_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a user ID to add to the room."
        )

    if await get_user_info(new_user_id) is None:
        logger.warning("Attempted to add non-existent user %s to room %s", str(new_user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesn't exist."
        )

    if await postgres_client.is_user_in_room(new_user_id, room_id):
        logger.warning("Attempted to add user %s who is already in room %s", str(new_user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {new_user_id} is already a member of room {room_id}."
        )

    await postgres_client.add_room_user(new_user_id, room_id)
    await redis_client.publish(
        f"user:{new_user_id}",
        RoomControlMessage(room_id=room_id, status="added").model_dump_json()
    ) # Notify the user that they have been added

    logger.info("User %s added user %s to room %s", str(user_id), str(new_user_id), str(room_id))

    return DefaultTextResponse(message=f"User {new_user_id} added to room {room_id}.")

@chat_router.delete("/rooms/{room_id}/users", response_model=DefaultTextResponse)
async def remove_room_user(
    room_id: UUID,
    req: AddRemoveRoomUserRequest = Body(...),
    claims: dict = Depends(verify_token)
):
    user_id = claims.get("sub")
    logger.debug("User %s attempting to remove user %s from room %s", str(user_id), str(req.user_id), str(room_id))

    # The removed user ID is sent in the request body as JSON: { "user_id": "<uuid>" }
    removed_user_id = req.user_id
    if not removed_user_id:
        logger.warning("Empty user_id in remove user request for room %s", str(room_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a user ID to remove from the room."
        )

    if not str(user_id) == str(removed_user_id) and not await postgres_client.is_user_admin(user_id, room_id):
        logger.warning("Non-admin user %s attempted to remove user from room %s", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be an admin in the room to remove a user."
        )

    if await postgres_client.is_user_admin(user_id=removed_user_id, room_id=room_id, owner_only=True):
        if str(user_id) == str(removed_user_id):
            users = await postgres_client.get_room_users(room_id);
            for uid in users:
                await redis_client.publish(
                    f"user:{uid}",
                    RoomControlMessage(room_id=room_id, status="removed").model_dump_json()
                )
            # Delete room since owner left
            await postgres_client.delete_room(user_id, room_id)
            logger.info("Owner %s deleted room %s", str(user_id), str(room_id))

            return DefaultTextResponse(message=f"Owner {removed_user_id} deleted room {room_id}.")

        logger.warning("Attempted to remove owner %s from room %s", str(removed_user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't remove the owner."
        )

    if not await postgres_client.is_user_in_room(removed_user_id, room_id):
        logger.warning("Attempted to remove user %s who is not in room %s", str(removed_user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {removed_user_id} is not a member of room {room_id}."
        )

    await postgres_client.remove_room_user(removed_user_id, room_id)
    await redis_client.publish(
        f"user:{removed_user_id}",
        RoomControlMessage(room_id=room_id, status="removed").model_dump_json()
    ) # Notify the user that they have been removed

    logger.info("User %s removed user %s from room %s", str(user_id), str(removed_user_id), str(room_id))

    return DefaultTextResponse(message=f"User {removed_user_id} removed from room {room_id}.")

@chat_router.patch("/rooms/{room_id}/users", response_model=DefaultTextResponse)
async def promote_demote(
    room_id: UUID,
    req: PromoteDemoteRoomUserRequest = Body(...),
    claims: dict = Depends(verify_token)
):
    user_id = claims.get("sub")
    logger.debug("User %s attempting to %s user %s in room %s", str(user_id), req.role, str(req.user_id), str(room_id))

    if not await postgres_client.is_user_admin(user_id=user_id, room_id=room_id):
        logger.warning("Non-admin user %s attempted to promote/demote in room %s", str(user_id), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be an admin or owner to promote or demote."
        )

    # The body of the request will be: { "user_id": "<uuid>", "role": "admin" | "member" }
    uid = req.user_id
    if not await postgres_client.is_user_in_room(user_id=uid, room_id=room_id):
        logger.warning("Attempted to promote/demote user %s who is not in room %s", str(uid), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide the user ID of a user in the room to promote/demote."
        )

    if await postgres_client.is_user_admin(user_id=uid, room_id=room_id, owner_only=True):
        logger.warning("Attempted to demote owner %s in room %s", str(uid), str(room_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't demote the owner."
        )

    match req.role:
        case "admin":
            if await postgres_client.is_user_admin(uid, room_id):
                logger.warning("Attempted to promote user %s who is already admin in room %s", str(uid), str(room_id))
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User {uid} is already an admin of room {room_id}."
                )

            await postgres_client.promote_room_user(uid, room_id)
            await redis_client.publish(
                f"user:{uid}",
                RoomControlMessage(room_id=room_id, status="promoted").model_dump_json()
            ) # Notify the user that they have been promoted

            logger.info("User %s promoted user %s to admin in room %s", str(user_id), str(uid), str(room_id))

            return DefaultTextResponse(message=f"User {uid} promoted in room {room_id}.")

        case "member":
            if not await postgres_client.is_user_admin(uid, room_id):
                logger.warning("Attempted to demote user %s who is already member in room %s", str(uid), str(room_id))
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User {uid} is already a member of room {room_id}."
                )

            await postgres_client.demote_room_user(uid, room_id)
            await redis_client.publish(
                f"user:{uid}",
                RoomControlMessage(room_id=room_id, status="demoted").model_dump_json()
            ) # Notify the user that they have been demoted

            logger.info("User %s demoted user %s to member in room %s", str(user_id), str(uid), str(room_id))

            return DefaultTextResponse(message=f"User {uid} demoted in room {room_id}.")

        case _:
            # This code block should be unreachable since the role needs to match one of
            # the two or the request gets rejected by FastAPI (because of the req model)
            logger.error("Invalid role '%s' in promote/demote request", req.role)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must provide a valid role for the user (member or admin)."
            )
