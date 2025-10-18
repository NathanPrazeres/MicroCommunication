from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Literal
from models.dto import MessageDto, RoomDto


##################################
#     Internal Communication     #
##################################
class ErrorMessage(BaseModel):
    error: Optional[str] = None
    status: Literal["error"] = "error"

class RoomControlMessage(BaseModel):
    room_id: UUID
    status: Literal["added", "removed", "promoted", "demoted"]

class SendMessageResponse(BaseModel):
    message: Optional[MessageDto] = None
    status: Literal["ok"] = "ok"

class UserInfo(BaseModel):
    id: UUID
    name: str
    email: str

####################
#     Requests     #
####################
class CreateRoomRequest(BaseModel):
    name: Optional[str]
    description: Optional[str]
    room_type: Literal["direct", "group", "channel"]
    participants: Optional[list[UUID]]

class AddRemoveRoomUserRequest(BaseModel):
    user_id: UUID

class PromoteDemoteRoomUserRequest(BaseModel):
    user_id: UUID
    role: Literal["member", "admin"]

class SendMessageRequest(BaseModel):
    room_id: UUID
    content: str
    reply_to_id: Optional[UUID] = None

#####################
#     Responses     #
#####################
class CreateRoomResponse(BaseModel):
    room_id: UUID

class DefaultTextResponse(BaseModel):
    message: str

class GetRoomUsersResponse(BaseModel):
    users: list[UserInfo]

class GetRoomsResponse(BaseModel):
    rooms: list[RoomDto]

class GetMessagesResponse(BaseModel):
    messages: list[MessageDto]
