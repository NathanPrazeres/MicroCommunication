from utils.websocket_manager import websocket_manager
from repositories.db_postgres import postgres_client
from repositories.pubsub_redis import redis_client
from fastapi import WebSocketDisconnect
from uuid import UUID
from pydantic import ValidationError
from models.schema import MessageRequest, MessageResponse, RoomControlMessage, ErrorMessage
from models.dto import MessageDto


async def handle_client_messages(user_id: UUID):
    try:
        while True:
            data = await websocket_manager.get(user_id).receive_json()
            # data = {"room_id": 123, "content": "Lorem Ipsum", "reply_to_id": null}
            msg_req = MessageRequest(**data)

            message = await postgres_client.send_message(user_id, msg_req.room_id, msg_req.content)
            if message is None:
                await websocket_manager.send(
                    user_id,
                    ErrorMessage(error="Unauthorized message request.")
                )
                continue

            # Publish to Redis so all other users in the room get it
            await redis_client.publish(f"room:{msg_req.room_id}", message.model_dump_json())

            # Send confirmation back to frontend
            await websocket_manager.send(
                user_id,
                MessageResponse(message=message)
            )

    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)

async def handle_redis_messages(user_id: UUID, room_channels: list[str]):
    pubsub = redis_client.pubsub()
    user_channel = f"user:{user_id}"
    channels = room_channels + [user_channel]
    await pubsub.subscribe(*channels)

    try:
        async for message in pubsub.listen():
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
                            control
                        )
                else:
                    # Forward message to this user's WebSocket
                    msg = MessageDto.model_validate_json(data)
                    if msg.sender_id != user_id:
                        await websocket_manager.send(user_id, msg)
            except ValidationError:
                await websocket_manager.send(
                    user_id,
                    ErrorMessage(error=f"Error parsing JSON: {data}")
                )
    finally:
        await pubsub.unsubscribe(*channels)
