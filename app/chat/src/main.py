from fastapi import (
    FastAPI,
    APIRouter,
    Response,
    status,
    WebSocket,
    WebSocketDisconnect
)
from datetime import datetime, timezone
from utils.websocket_manager import manager

app = FastAPI()
router = APIRouter(prefix="/api/v1", tags=["api", "chat"])

### App ###

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send(client_id, f"You wrote: {data}")
            # TODO: change this, it's just a placeholder
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.get("/rooms")
def get_rooms():
    pass

@app.post("/rooms")
def create_room():
    pass

@app.get("rooms/{room_id}/users")
def get_room_users(room_id: int):
    pass


### Kubernetes ###

@router.get("/healthz")
def get_liveness(response: Response):
    response.status_code = status.HTTP_200_OK
    return {
        "status": "healthy",
        "service": "chat-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/readyz")
def get_readiness(response: Response):
    response.status_code = status.HTTP_200_OK
    return {
        "status": "ready",
        "service": "chat-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(router)
