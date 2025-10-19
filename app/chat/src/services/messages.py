from utils.websocket_manager import websocket_manager
from repositories.db_postgres import postgres_client
from repositories.pubsub_redis import redis_client
from fastapi import WebSocketDisconnect
from uuid import UUID
from pydantic import ValidationError
from models.schema import (
    SendMessageRequest,
    SendMessageResponse,
    RoomControlMessage,
    ErrorMessage,
    WsError,
    WsSendResponse,
    WsControl,
    WsMessage
)
from models.dto import MessageDto
from datetime import datetime


async def handle_client_messages(user_id: UUID):
    try:
        while True:
            payload = await websocket_manager.get(user_id).receive_json()
            # payload = { type: "send_message", data: { "room_id": 123, "content": "Lorem Ipsum", "reply_to_id": null } }
            type = payload.get("type")
            if type == "send_message":
                data = payload.get("data")
                try:
                    msg_req = SendMessageRequest(**data)
                except ValidationError:
                    await websocket_manager.send(
                        user_id,
                        WsError(
                            data=ErrorMessage(error="Invalid message payload."),
                            ts=datetime.now()
                        )
                    )
                    continue

                message = await postgres_client.send_message(user_id, msg_req.room_id, msg_req.content, msg_req.reply_to_id)
                if message is None:
                    await websocket_manager.send(
                        user_id,
                        WsError(
                            data=ErrorMessage(error="Unauthorized message request."),
                            ts=datetime.now()
                        )
                    )
                    continue

                # Publish to Redis so all other users in the room get it
                await redis_client.publish(f"room:{msg_req.room_id}", message.model_dump_json())

                # Send confirmation back to frontend
                await websocket_manager.send(
                    user_id,
                    WsSendResponse(
                        data=SendMessageResponse(message=message),
                        ts=datetime.now()
                    )
                )
            else:
                await websocket_manager.send(
                        user_id,
                        WsError(
                            data=ErrorMessage(error="Malformed request."),
                            ts=datetime.now()
                        )
                    )

    except WebSocketDisconnect:
        await websocket_manager.disconnect(user_id)

async def handle_redis_messages(user_id: UUID, room_channels: list[str]):
    pubsub = redis_client.pubsub()
    user_channel = f"user:{user_id}"
    channels = room_channels + [user_channel]
    await pubsub.subscribe(*channels)

    try:
        async for message in pubsub.listen():
            if message['type'] != "message":
                continue
            channel = message['channel']
            data = message['data']
            try:
                if channel == user_channel:
                    # This is a control message for the user
                    control = RoomControlMessage.model_validate_json(data)
                    room_id = control.room_id
                    status = control.status

                    if status == "added":
                        # Subscribe to the new room channel
                        await pubsub.subscribe(f"room:{room_id}")
                    elif status == "removed":
                        await pubsub.unsubscribe(f"room:{room_id}")

                    # Notify user
                    await websocket_manager.send(
                        user_id,
                        WsControl(data=control, ts=datetime.now())
                    )
                else:
                    # Forward message to this user's WebSocket
                    msg = MessageDto.model_validate_json(data)
                    if msg.sender_id != user_id:
                        await websocket_manager.send(
                            user_id,
                            WsMessage(data=msg, ts=datetime.now())
                        )
            except ValidationError:
                await websocket_manager.send(
                    user_id,
                    WsError(
                        data=ErrorMessage(error=f"Error parsing JSON: {data}"),
                        ts=datetime.now()
                    )
                )
    finally:
        await pubsub.unsubscribe(*channels)
