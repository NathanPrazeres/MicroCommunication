from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Literal
from models.dto import MessageDto


class AddRoomUserRequest(BaseModel):
    user_id: UUID

class MessageRequest(BaseModel):
    room_id: UUID
    content: str
    reply_to_id: Optional[UUID] = None

class MessageResponse(BaseModel):
    status: Literal["success", "error"]
    message: Optional[MessageDto] = None
    error: Optional[str] = None
