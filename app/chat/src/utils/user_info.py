from uuid import UUID
from models.schema import UserInfo
import httpx


USER_SERVICE_URL = "http://user-service:8000/users" # TODO: chage this

async def get_user_info(user_id: UUID) -> UserInfo:
    url = f"{USER_SERVICE_URL}/{user_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return UserInfo(**resp.json())
