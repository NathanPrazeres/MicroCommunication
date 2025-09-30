from uuid import UUID
from models.schema import UserDto
import httpx
import config
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def get_user_info(user_id: UUID) -> Optional[UserDto]:
    logger.info("Fetching Info for user: %s", str(user_id))
    url = f"http://{config.USER_SERVICE}/internal/users/{user_id}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError):
            logging.error("Fetching Info failed for user: %s", str(user_id))
            return None
        data = resp.json()
        return UserDto(id=data.get("user_id"), name=data.get("username"), email=data.get("email"))
