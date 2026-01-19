"""
Chat handler for message events, room join/leave, and typing indicators.
"""

import logging
from typing import Dict, Any, Optional
from models.schemas import (
    ChatMessageEvent,
    GroupMessageEvent,
    JoinRoomEvent,
    LeaveRoomEvent,
    TypingEvent,
    MessageResponse,
    ErrorResponse,
)
from connection_manager import connection_manager
from services.persistence_service import PersistenceService
from services.pubsub_service import pubsub_service
from services.presence_service import presence_service
from utils.constants import (
    EVENT_MESSAGE,
    EVENT_GROUP_MESSAGE,
    EVENT_JOIN_ROOM,
    EVENT_LEAVE_ROOM,
    EVENT_TYPING,
    EVENT_MESSAGE_RESPONSE,
    EVENT_GROUP_MESSAGE_RESPONSE,
    EVENT_TYPING_RESPONSE,
    ROOM_PREFIX,
    GROUP_ROOM_PREFIX,
    STATUS_SUCCESS,
    STATUS_ERROR,
)

logger = logging.getLogger(__name__)
persistence_service = PersistenceService()


async def handle_message(sio, sid: str, data: Dict[str, Any]) -> None:
    """
    Handle incoming chat message event.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        data: Message event data
    """
    logger.info(f"STEP 1: Handling message event from session {sid}")

    try:
        # Validate schema
        try:
            message_event = ChatMessageEvent(**data)
        except Exception as exc:
            logger.error(f"STEP 2: Invalid message schema: {exc}")
            await sio.emit(
                EVENT_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message=f"Invalid message format: {str(exc)}",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        # Get connection info
        connection_info = connection_manager.get_connection_info(sid)
        if not connection_info:
            logger.error(f"STEP 2: Connection not found for session {sid}")
            await sio.emit(
                EVENT_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Connection not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        user_id = connection_info.get("user_id")

        # Get user details
        sender_user = await persistence_service.get_user_by_id(
            message_event.sender_id
        )
        receiver_user = await persistence_service.get_user_by_id(
            message_event.receiver_id
        )

        if not sender_user or not receiver_user:
            logger.error("STEP 2: User not found")
            await sio.emit(
                EVENT_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="User not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        sender_id_int = sender_user.get("id")
        receiver_id_int = receiver_user.get("id")

        # Validate sender matches connection
        if sender_id_int != user_id:
            logger.error(
                f"STEP 2: Sender ID {sender_id_int} does not match connection user {user_id}"
            )
            await sio.emit(
                EVENT_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Unauthorized: sender_id does not match authenticated user",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        logger.info("STEP 2: Message validated, creating/getting room")

        # Create or get room
        room_info = await persistence_service.create_or_get_room_between_users(
            sender_id_int, receiver_id_int, sid
        )
        room_id = room_info["room_id"]

        # Join room if not already joined
        room_name = connection_manager.format_room_name(room_id)
        if room_id not in connection_info.get("rooms", set()):
            connection_manager.join_room(sid, room_id)
            await sio.enter_room(sid, room_name)

        logger.info("STEP 3: Saving message to database")

        # Save message to database
        saved_message = await persistence_service.save_message(
            room_id=room_id,
            sender_id=sender_id_int,
            receiver_id=receiver_id_int,
            message=message_event.content,
            message_type=message_event.message_type,
            attachments=message_event.attachments,
            session_id=sid,
        )

        logger.info("STEP 4: Publishing message to Redis Pub/Sub")

        # Publish to Redis Pub/Sub for multi-instance broadcasting
        await pubsub_service.publish_to_room(
            room_id=room_id,
            event_type=EVENT_MESSAGE,
            data=saved_message,
        )

        logger.info("STEP 5: Broadcasting message to local connections")

        # Broadcast to local connections in room
        response_data = {
            **saved_message,
            "room_id": room_id,
        }

        await sio.emit(
            EVENT_MESSAGE_RESPONSE,
            MessageResponse(
                status=STATUS_SUCCESS,
                message="Message sent successfully",
                session_id=sid,
                data=response_data,
            ).dict(),
            room=room_name,
        )

        # Update presence
        presence_service.update_presence(user_id, room_id)

        logger.info(f"STEP 6: Message handled successfully for room {room_id}")

    except Exception as exc:
        logger.error(f"STEP 6: Error handling message: {exc}", exc_info=True)
        await sio.emit(
            EVENT_MESSAGE_RESPONSE,
            ErrorResponse(
                status=STATUS_ERROR,
                message=f"Error processing message: {str(exc)}",
                session_id=sid,
            ).dict(),
            to=sid,
        )


async def handle_group_message(sio, sid: str, data: Dict[str, Any]) -> None:
    """
    Handle incoming group message event.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        data: Group message event data
    """
    logger.info(f"STEP 1: Handling group message event from session {sid}")

    try:
        # Validate schema
        try:
            group_message_event = GroupMessageEvent(**data)
        except Exception as exc:
            logger.error(f"STEP 2: Invalid group message schema: {exc}")
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message=f"Invalid message format: {str(exc)}",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        # Get connection info
        connection_info = connection_manager.get_connection_info(sid)
        if not connection_info:
            logger.error(f"STEP 2: Connection not found for session {sid}")
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Connection not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        user_id = connection_info.get("user_id")

        # Get sender user details
        sender_user = await persistence_service.get_user_by_id(
            group_message_event.sender_id
        )
        if not sender_user:
            logger.error("STEP 2: Sender user not found")
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Sender user not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        sender_id_int = sender_user.get("id")

        # Validate sender matches connection
        if sender_id_int != user_id:
            logger.error(
                f"STEP 2: Sender ID {sender_id_int} does not match connection user {user_id}"
            )
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Unauthorized: sender_id does not match authenticated user",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        # Get group details
        group = await persistence_service.get_group_by_id(
            group_message_event.group_id
        )
        if not group:
            logger.error("STEP 2: Group not found")
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Group not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        # Validate sender is a member
        members_list = group.get("members", [])
        if sender_id_int not in members_list:
            logger.error("STEP 2: User is not a member of the group")
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="You are not a member of this group",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        logger.info("STEP 3: Creating/getting room for group")

        # Create or get room for group
        group_id_int = group.get("id")
        room_info = await persistence_service.create_or_get_room_for_group(
            group_id_int, sid
        )
        room_id = room_info["room_id"]

        # Join group room if not already joined
        group_room_name = connection_manager.format_room_name(room_id, is_group=True)
        if room_id not in connection_info.get("rooms", set()):
            connection_manager.join_room(sid, room_id)
            await sio.enter_room(sid, group_room_name)

        logger.info("STEP 4: Saving group message to database")

        # Get receiver IDs (all group members except sender)
        receiver_ids = [
            member_id for member_id in members_list if member_id != sender_id_int
        ]

        # Save group message to database
        saved_message = await persistence_service.save_group_message(
            room_id=room_id,
            sender_id=sender_id_int,
            group_id=group_id_int,
            receiver_ids=receiver_ids,
            message=group_message_event.content,
            message_type=group_message_event.message_type,
            attachments=group_message_event.attachments,
            session_id=sid,
        )

        logger.info("STEP 5: Publishing group message to Redis Pub/Sub")

        # Publish to Redis Pub/Sub
        await pubsub_service.publish_to_room(
            room_id=room_id,
            event_type=EVENT_GROUP_MESSAGE,
            data=saved_message,
        )

        logger.info("STEP 6: Broadcasting group message to local connections")

        # Broadcast to local connections in group room
        response_data = {
            **saved_message,
            "room_id": room_id,
            "group_id": group.get("uuid"),
        }

        await sio.emit(
            EVENT_GROUP_MESSAGE_RESPONSE,
            MessageResponse(
                status=STATUS_SUCCESS,
                message="Group message sent successfully",
                session_id=sid,
                data=response_data,
            ).dict(),
            room=group_room_name,
        )

        # Update presence
        presence_service.update_presence(user_id, room_id)

        logger.info(f"STEP 7: Group message handled successfully for room {room_id}")

    except Exception as exc:
        logger.error(f"STEP 7: Error handling group message: {exc}", exc_info=True)
        await sio.emit(
            EVENT_GROUP_MESSAGE_RESPONSE,
            ErrorResponse(
                status=STATUS_ERROR,
                message=f"Error processing group message: {str(exc)}",
                session_id=sid,
            ).dict(),
            to=sid,
        )


async def handle_join_room(sio, sid: str, data: Dict[str, Any]) -> None:
    """
    Handle join room event.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        data: Join room event data
    """
    logger.info(f"STEP 1: Handling join room event from session {sid}")

    try:
        # Validate schema
        try:
            join_event = JoinRoomEvent(**data)
        except Exception as exc:
            logger.error(f"STEP 2: Invalid join room schema: {exc}")
            return

        # Join room
        connection_manager.join_room(sid, join_event.room_id)
        room_name = connection_manager.format_room_name(join_event.room_id)
        await sio.enter_room(sid, room_name)

        # Update presence
        connection_info = connection_manager.get_connection_info(sid)
        if connection_info:
            user_id = connection_info.get("user_id")
            presence_service.update_presence(user_id, join_event.room_id)

        logger.info(f"STEP 2: Session {sid} joined room {join_event.room_id}")

    except Exception as exc:
        logger.error(f"STEP 2: Error handling join room: {exc}", exc_info=True)


async def handle_leave_room(sio, sid: str, data: Dict[str, Any]) -> None:
    """
    Handle leave room event.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        data: Leave room event data
    """
    logger.info(f"STEP 1: Handling leave room event from session {sid}")

    try:
        # Validate schema
        try:
            leave_event = LeaveRoomEvent(**data)
        except Exception as exc:
            logger.error(f"STEP 2: Invalid leave room schema: {exc}")
            return

        # Leave room
        connection_manager.leave_room(sid, leave_event.room_id)
        room_name = connection_manager.format_room_name(leave_event.room_id)
        await sio.leave_room(sid, room_name)

        logger.info(f"STEP 2: Session {sid} left room {leave_event.room_id}")

    except Exception as exc:
        logger.error(f"STEP 2: Error handling leave room: {exc}", exc_info=True)


async def handle_typing(sio, sid: str, data: Dict[str, Any]) -> None:
    """
    Handle typing indicator event.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        data: Typing event data
    """
    logger.info(f"STEP 1: Handling typing event from session {sid}")

    try:
        # Validate schema
        try:
            typing_event = TypingEvent(**data)
        except Exception as exc:
            logger.error(f"STEP 2: Invalid typing schema: {exc}")
            return

        # Get connection info
        connection_info = connection_manager.get_connection_info(sid)
        if not connection_info:
            return

        user_id = connection_info.get("user_id")
        room_name = connection_manager.format_room_name(typing_event.room_id)

        # Broadcast typing indicator to room (excluding sender)
        await sio.emit(
            EVENT_TYPING_RESPONSE,
            {
                "room_id": typing_event.room_id,
                "user_id": user_id,
                "is_typing": typing_event.is_typing,
            },
            room=room_name,
            skip_sid=sid,
        )

        logger.info(
            f"STEP 2: Typing indicator broadcasted for user {user_id} in room {typing_event.room_id}"
        )

    except Exception as exc:
        logger.error(f"STEP 2: Error handling typing: {exc}", exc_info=True)


async def handle_redis_message(sio, data: Dict[str, Any]) -> None:
    """
    Handle message received from Redis Pub/Sub.

    Args:
        sio: Socket.IO server instance
        data: Message data from Redis
    """
    try:
        event_type = data.get("event_type")
        room_id = data.get("room_id")
        message_data = data.get("data", {})

        if not room_id:
            return

        room_name = connection_manager.format_room_name(room_id)

        # Broadcast to local connections in room
        if event_type == EVENT_MESSAGE:
            await sio.emit(
                EVENT_MESSAGE_RESPONSE,
                MessageResponse(
                    status=STATUS_SUCCESS,
                    message="Message received",
                    data=message_data,
                ).dict(),
                room=room_name,
            )
        elif event_type == EVENT_GROUP_MESSAGE:
            group_room_name = connection_manager.format_room_name(
                room_id, is_group=True
            )
            await sio.emit(
                EVENT_GROUP_MESSAGE_RESPONSE,
                MessageResponse(
                    status=STATUS_SUCCESS,
                    message="Group message received",
                    data=message_data,
                ).dict(),
                room=group_room_name,
            )

    except Exception as exc:
        logger.error(f"Error handling Redis message: {exc}", exc_info=True)

