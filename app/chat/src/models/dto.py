from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class StatusDto(BaseModel):
    status: str
    service: str
    timestamp: str

class MessageDto(BaseModel):
    id: UUID
    room_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    reply_to_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime

class UserDto(BaseModel):
    id: UUID
    username: str

class RoomDto(BaseModel):
    id: UUID
    name: Optional[str]
    description: Optional[str]
    room_type: Literal["direct", "group", "channel"]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
