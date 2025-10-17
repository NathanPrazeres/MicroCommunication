from uuid import UUID
from models.schema import UserInfo
import httpx
import config


async def get_user_info(user_id: UUID) -> UserInfo:
    url = f"http://{config.USER_SERVICE}:{config.USER_PORT}/internal/users/{user_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return UserInfo(**resp.json())
