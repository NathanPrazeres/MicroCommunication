from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Literal
from models.dto import MessageDto, RoomDto
from datetime import datetime


##################################
#     Internal Communication     #
##################################
class ErrorMessage(BaseModel):
    error: Optional[str] = None

class RoomControlMessage(BaseModel):
    room_id: UUID
    status: Literal["added", "removed", "promoted", "demoted"]

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

class SendMessageResponse(BaseModel):
    message: Optional[MessageDto] = None

###################################
#     WebSocket Communication     #
###################################
class WsMessage(BaseModel):
    type: Literal["message"] = "message"
    data: MessageDto
    ts: Optional[datetime] = None

class WsControl(BaseModel):
    type: Literal["control"] = "control"
    data: RoomControlMessage
    ts: Optional[datetime] = None

class WsSendResponse(BaseModel):
    type: Literal["send_response"] = "send_response"
    data: SendMessageResponse
    ts: Optional[datetime] = None

class WsError(BaseModel):
    type: Literal["error"] = "error"
    data: ErrorMessage
    ts: Optional[datetime] = None