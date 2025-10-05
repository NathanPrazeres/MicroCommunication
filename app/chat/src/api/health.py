from fastapi import APIRouter, Response, status
from datetime import datetime, timezone

health_router = APIRouter(tags=["kubernetes", "status"])

@health_router.get("/healthz")
def get_liveness(response: Response):
    response.status_code = status.HTTP_200_OK
    return {
        "status": "healthy",
        "service": "chat-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@health_router.get("/readyz")
def get_readiness(response: Response):
    response.status_code = status.HTTP_200_OK
    return {
        "status": "ready",
        "service": "chat-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
