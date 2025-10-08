from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Literal
from models.dto import MessageDto


class ErrorMessage(BaseModel):
    error: Optional[str] = None
    status: Literal["error"] = "error"

class RoomControlMessage(BaseModel):
    room_id: UUID
    status: Literal["added", "removed", "promoted", "demoted"]

class AddRemoveRoomUserRequest(BaseModel):
    user_id: UUID

class PromoteDemoteRoomUserRequest(BaseModel):
    user_id: UUID
    role: Literal["member", "admin"]

class TextResponse(BaseModel):
    message: str
    status: Literal["ok"] = "ok" # Might change this later

class GetRoomUsersResponse(BaseModel):
    users: list[UUID]

class MessageRequest(BaseModel):
    room_id: UUID
    content: str
    reply_to_id: Optional[UUID] = None

class MessageResponse(BaseModel):
    message: Optional[MessageDto] = None
    status: Literal["ok"] = "ok"
