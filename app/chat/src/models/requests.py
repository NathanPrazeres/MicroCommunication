from pydantic import BaseModel
from uuid import UUID

class AddRoomUserRequest(BaseModel):
    user_id: UUID
