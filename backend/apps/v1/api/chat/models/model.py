import uuid
from sqlalchemy import Column, Integer, String, Text, JSON
from core.db import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from core.utils import constant_variable as constant


class MessageSessions(Base, TimestampMixin):
    __tablename__ = "message_sessions"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Message session unique identifier",
    )
    uuid = Column(
        String(36),
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        nullable=constant.STATUS_FALSE,
        default=lambda: str(uuid.uuid4()),
        comment="Message session UUID",
    )
    room_id = Column(String(36), nullable=constant.STATUS_TRUE, comment="Room identifier (UUID)")
    group_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Group identifier")


class MessageChats(Base, TimestampMixin):
    __tablename__ = "message_chats"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Message chat unique identifier",
    )
    uuid = Column(
        String(36),
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        nullable=constant.STATUS_FALSE,
        default=lambda: str(uuid.uuid4()),
        comment="Message chat UUID",
    )
    room_id = Column(String(36), nullable=constant.STATUS_TRUE, comment="Room identifier (UUID)")
    sender_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Sender identifier")
    receiver_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Receiver identifier")
    message = Column(Text, nullable=constant.STATUS_TRUE, comment="Message content")
    message_type = Column(String(20), nullable=constant.STATUS_TRUE, default="text", comment="Message type: text, image, video, file, audio")
    attachments = Column(JSON, nullable=constant.STATUS_TRUE, comment="File attachments (JSON array)")
    group_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Group identifier")


class MessageGroups(Base, TimestampMixin):
    __tablename__ = "message_groups"
    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Message group unique identifier",
    )
    group_name = Column(String(255), nullable=constant.STATUS_TRUE, comment="Group name")
    created_by = Column(Integer, nullable=constant.STATUS_TRUE, comment="Created by")
    members = Column(JSON, nullable=constant.STATUS_TRUE, default=list, comment="Members (JSON array)")
    admins = Column(JSON, nullable=constant.STATUS_TRUE, default=list, comment="Admins (JSON array)")
