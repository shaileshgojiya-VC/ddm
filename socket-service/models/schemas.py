"""
Pydantic schemas for WebSocket events and messages.
"""

from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from utils.constants import (
    VALID_MESSAGE_TYPES,
    MESSAGE_TYPE_TEXT,
    UUID_LENGTH,
    UUID_HYPHEN_COUNT,
)


class BaseEvent(BaseModel):
    """Base event schema."""

    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatMessageEvent(BaseEvent):
    """Chat message event schema."""

    type: Literal["message"] = "message"
    sender_id: str | int = Field(..., description="Sender user ID or UUID")
    receiver_id: str | int = Field(..., description="Receiver user ID or UUID")
    room_id: Optional[str] = Field(None, description="Room UUID (optional)")
    content: Optional[str] = Field(None, description="Message content")
    message_type: str = Field(
        default=MESSAGE_TYPE_TEXT, description="Message type"
    )
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="File attachments"
    )

    @validator("message_type")
    def validate_message_type(cls, v):
        if v not in VALID_MESSAGE_TYPES:
            raise ValueError(
                f"Invalid message_type. Must be one of: {', '.join(VALID_MESSAGE_TYPES)}"
            )
        return v

    @validator("content")
    def validate_content(cls, v, values):
        message_type = values.get("message_type", MESSAGE_TYPE_TEXT)
        if message_type == MESSAGE_TYPE_TEXT and not v:
            raise ValueError("Content is required for text messages")
        return v

    @validator("room_id")
    def validate_room_id(cls, v):
        if v and not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("room_id must be a valid UUID string")
        return v


class GroupMessageEvent(BaseEvent):
    """Group message event schema."""

    type: Literal["group_message"] = "group_message"
    group_id: str | int = Field(..., description="Group ID or UUID")
    sender_id: str | int = Field(..., description="Sender user ID or UUID")
    room_id: Optional[str] = Field(None, description="Room UUID (optional)")
    content: Optional[str] = Field(None, description="Message content")
    message_type: str = Field(
        default=MESSAGE_TYPE_TEXT, description="Message type"
    )
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="File attachments"
    )

    @validator("message_type")
    def validate_message_type(cls, v):
        if v not in VALID_MESSAGE_TYPES:
            raise ValueError(
                f"Invalid message_type. Must be one of: {', '.join(VALID_MESSAGE_TYPES)}"
            )
        return v

    @validator("content")
    def validate_content(cls, v, values):
        message_type = values.get("message_type", MESSAGE_TYPE_TEXT)
        if message_type == MESSAGE_TYPE_TEXT and not v:
            raise ValueError("Content is required for text messages")
        return v


class JoinRoomEvent(BaseEvent):
    """Join room event schema."""

    type: Literal["join_room"] = "join_room"
    room_id: str = Field(..., description="Room UUID")
    user_id: Optional[str | int] = Field(None, description="User ID or UUID")

    @validator("room_id")
    def validate_room_id(cls, v):
        if not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("room_id must be a valid UUID string")
        return v


class LeaveRoomEvent(BaseEvent):
    """Leave room event schema."""

    type: Literal["leave_room"] = "leave_room"
    room_id: str = Field(..., description="Room UUID")
    user_id: Optional[str | int] = Field(None, description="User ID or UUID")

    @validator("room_id")
    def validate_room_id(cls, v):
        if not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("room_id must be a valid UUID string")
        return v


class TypingEvent(BaseEvent):
    """Typing indicator event schema."""

    type: Literal["typing"] = "typing"
    room_id: str = Field(..., description="Room UUID")
    is_typing: bool = Field(..., description="Whether user is typing")

    @validator("room_id")
    def validate_room_id(cls, v):
        if not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("room_id must be a valid UUID string")
        return v


class ReadReceiptEvent(BaseEvent):
    """Read receipt event schema."""

    type: Literal["read_receipt"] = "read_receipt"
    message_id: str = Field(..., description="Message UUID")
    room_id: str = Field(..., description="Room UUID")
    reader_id: Optional[str | int] = Field(None, description="Reader user ID or UUID")

    @validator("room_id", "message_id")
    def validate_uuid(cls, v):
        if not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("Must be a valid UUID string")
        return v


class DeliveryReceiptEvent(BaseEvent):
    """Delivery receipt event schema."""

    type: Literal["delivery_receipt"] = "delivery_receipt"
    message_id: str = Field(..., description="Message UUID")
    room_id: str = Field(..., description="Room UUID")
    receiver_id: Optional[str | int] = Field(
        None, description="Receiver user ID or UUID"
    )

    @validator("room_id", "message_id")
    def validate_uuid(cls, v):
        if not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("Must be a valid UUID string")
        return v


class PresenceEvent(BaseEvent):
    """Presence event schema."""

    type: Literal["presence"] = "presence"
    room_id: str = Field(..., description="Room UUID")
    status: Literal["online", "offline"] = Field(..., description="Presence status")

    @validator("room_id")
    def validate_room_id(cls, v):
        if not (
            isinstance(v, str)
            and len(v) == UUID_LENGTH
            and v.count("-") == UUID_HYPHEN_COUNT
        ):
            raise ValueError("room_id must be a valid UUID string")
        return v


class HeartbeatEvent(BaseEvent):
    """Heartbeat event schema."""

    type: Literal["heartbeat"] = "heartbeat"
    session_id: Optional[str] = Field(None, description="Session ID")


# Response schemas
class BaseResponse(BaseModel):
    """Base response schema."""

    status: Literal["success", "error"]
    message: str
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageResponse(BaseResponse):
    """Message response schema."""

    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Error response schema."""

    status: Literal["error"] = "error"
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

