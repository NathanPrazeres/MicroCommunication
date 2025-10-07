from utils.websocket_manager import websocket_manager
from repositories.db_postgres import postgres_client
from repositories.pubsub_redis import redis_client
from fastapi import WebSocketDisconnect
from uuid import UUID
from src.models.schema import MessageRequest, MessageResponse


async def handle_client_messages(user_id: UUID):
    try:
        while True:
            data = await websocket_manager.get_ws(user_id).receive_json()
            # data = {"room_id": 123, "content": "Lorem Ipsum", "reply_to_id": null}
            msg_req = MessageRequest(**data)

            message = await postgres_client.send_message(user_id, msg_req.room_id, msg_req.content)
            if message is None:
                await websocket_manager.send(
                    user_id,
                    MessageResponse(status="error", error="Unauthorized message request.")
                )
                continue

            # Publish to Redis so all other clients get it
            await redis_client.publish(f"room:{msg_req.room_id}", message)

            # Send confirmation back to frontend
            await websocket_manager.send(
                user_id,
                MessageResponse(status="success", message=message)
            )

    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)

async def handle_redis_messages(user_id: UUID, channels: list[str]):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(*channels)

    try:
        async for message in pubsub.listen():
            # Forward message to this user's WebSocket
            if str(message.sender_id) == str(user_id):
                await websocket_manager.send(user_id, message)

    finally:
        await pubsub.unsubscribe(*channels)
