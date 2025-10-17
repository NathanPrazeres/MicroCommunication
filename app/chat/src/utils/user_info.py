from uuid import UUID
from models.schema import UserInfo
import httpx
from os import environ as env


USER_SERVICE = env.get("USER_SERVICE") # TODO: chage this

async def get_user_info(user_id: UUID) -> UserInfo:
    url = f"http://{USER_SERVICE}/internal/users/{user_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return UserInfo(**resp.json())
