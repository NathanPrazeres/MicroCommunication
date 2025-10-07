from fastapi import APIRouter, Response, status
from datetime import datetime, timezone
from models.dto import StatusDto

health_router = APIRouter(tags=["health"])


@health_router.get("/healthz")
def get_liveness(response: Response):
    response.status_code = status.HTTP_200_OK
    return StatusDto(
        status="healthy",
        service="chat-service",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@health_router.get("/readyz")
def get_readiness(response: Response):
    response.status_code = status.HTTP_200_OK
    return StatusDto(
        status="ready",
        service="chat-service",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
