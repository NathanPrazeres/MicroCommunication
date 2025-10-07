from utils.websocket_manager import websocket_manager
from repositories.db_postgres import postgres_client
from repositories.pubsub_redis import redis_client
from fastapi import WebSocketDisconnect
from uuid import UUID


async def handle_client_messages(user_id: UUID):
    try:
        while True:
            data = await websocket_manager.get_ws(user_id).receive_json()
            # {"type": "message", "room_id": 123, "content": "Lorem Ipsum"}
            if data["type"] == "message":
                room_id = data["room_id"]
                content = data["content"]

                # TODO: remove this, for testing purposes only
                await websocket_manager.send(user_id, f"You wrote: {content}")

                message = await postgres_client.send_message(user_id, room_id, content)
                if message is None:
                    # TODO: give some kind of error to the frontend for unauthorized access
                    continue

                # Publish to Redis so all other clients get it
                await redis_client.publish(f"room:{room_id}", message)

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
