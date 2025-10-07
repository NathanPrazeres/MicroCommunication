from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Literal
from models.dto import MessageDto


class ErrorMessage(BaseModel):
    error: Optional[str] = None
    status: Literal["error"] = "error"

class RoomControlMessage(BaseModel):
    status: Literal["added", "removed", "promoted"]
    room_id: UUID

class AddRoomUserRequest(BaseModel):
    user_id: UUID

class MessageRequest(BaseModel):
    room_id: UUID
    content: str
    reply_to_id: Optional[UUID] = None

class MessageResponse(BaseModel):
    message: Optional[MessageDto] = None
    status: Literal["ok"] = "ok"
