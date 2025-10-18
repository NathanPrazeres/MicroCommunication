from uuid import UUID
from models.schema import UserInfo
import httpx
import config
from typing import Optional


async def get_user_info(user_id: UUID) -> Optional[UserInfo]:
    url = f"http://{config.USER_SERVICE}:{config.USER_PORT}/internal/users/{user_id}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError):
            return None
        return UserInfo(**resp.json())
