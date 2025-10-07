from utils.websocket_manager import websocket_manager
from repositories.db_postgres import postgres_client
from repositories.pubsub_redis import redis_client
from fastapi import WebSocketDisconnect
from uuid import UUID
from models.schema import MessageRequest, MessageResponse, RoomControlMessage
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
                    MessageResponse(status="error", error="Unauthorized message request.")
                )
                continue

            # Publish to Redis so all other users in the room get it
            await redis_client.publish(f"room:{msg_req.room_id}", message.model_dump_json())

            # Send confirmation back to frontend
            await websocket_manager.send(
                user_id,
                MessageResponse(status="success", message=message)
            )

    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)

async def handle_redis_messages(user_id: UUID, channels: list[str]):
    pubsub = redis_client.pubsub()
    user_channel = f"user:{user_id}"
    await pubsub.subscribe(*(channels + [user_channel]))

    try:
        async for message in pubsub.listen():
            channel = message['channel']
            data = message['data']
            if channel == user_channel:
                # This is a control message for the user
                control = RoomControlMessage.model_validate_json(data)
                status = control.status
                room_id = control.room_id

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

    finally:
        await pubsub.unsubscribe(*channels)
