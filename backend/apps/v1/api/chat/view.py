"""
Chat Socket.IO Views.
Socket.IO implementation with room-based chat for users and sales/management
"""

import logging
import socketio
import json

from apps.v1.api.chat.services.chat_service import ChatService

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.chat.schema import CreateGroupRequest
from apps.v1.api.chat.services.create_group_service import CreateGroupService
from apps.v1.api.chat.services.get_group_service import GetGroupService
from apps.v1.api.chat.services.update_group_service import UpdateGroupService
from apps.v1.api.chat.services.get_chat_history_service import GetChatHistoryService
from apps.v1.api.chat.services.get_user_chats_service import GetUserChatsService
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.auth_dependencies import get_current_user, security

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    allow_eio3=True,
)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Chat API"])

# Initialize chat service
chat_service = ChatService()


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"✅ Client connected: {sid}")

    # Send connection confirmation
    await sio.emit(
        "connection_response",
        {"status": "connected", "message": "Connected successfully", "session_id": sid},
        to=sid,
    )
    logger.info(f"📤 Sent connection response to {sid}")


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"👋 Client disconnected: {sid}")

    # Remove session from memory
    chat_service.remove_session(sid)


@sio.event
async def message(sid, data):
    """
    Handle incoming messages from client.

    Expected data format:
    {
        "sender_id": int or UUID string (sender),
        "receiver_id": int or UUID string (receiver),
        "content": "string" (optional for non-text messages),
        "room_id": UUID string (optional) - if provided, uses existing room,
        "message_type": "text" | "image" | "video" | "file" | "audio" (default: "text"),
        "attachments": [
            {
                "url": "https://...",
                "file_name": "file.jpg",
                "file_type": "image/jpeg",
                "size": 2048000
            }
        ] (optional)
    }
    """
    try:
        logger.info(
            f"📨 Received message from {sid}: {data if not isinstance(data, str) or len(data) < 500 else data[:500] + '...'}"
        )

        # Parse JSON string if needed (Socket.IO usually auto-parses JSON)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON: {e}")
                await sio.emit(
                    "message_response",
                    {
                        "status": "error",
                        "message": "Invalid JSON format. Please ensure your JSON is valid.",
                        "session_id": sid,
                    },
                    to=sid,
                )
                return
            except Exception as e:
                logger.error(f"❌ Failed to parse JSON: {e}")
                logger.error(f"📄 Received data (first 500 chars): {data[:500]}")
                # Try to log the problematic character position if available
                if hasattr(e, "pos"):
                    start = max(0, e.pos - 50)
                    end = min(len(data), e.pos + 50)
                    logger.error(
                        f"📄 Context around error position {e.pos}: {repr(data[start:end])}"
                    )
                await sio.emit(
                    "message_response",
                    {
                        "status": "error",
                        "message": f"Invalid JSON format: {str(e)}. Please ensure your JSON is valid (no control characters, proper quotes, etc.)",
                        "session_id": sid,
                    },
                    to=sid,
                )
                return

        # Validate required fields
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        content = data.get("content")
        room_id = data.get("room_id")
        message_type = data.get("message_type", "text")
        attachments = data.get("attachments", [])

        # Validate message_type
        valid_message_types = ["text", "image", "video", "file", "audio"]
        if message_type not in valid_message_types:
            await sio.emit(
                "message_response",
                {
                    "status": "error",
                    "message": f"Invalid message_type. Must be one of: {', '.join(valid_message_types)}",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Validate required fields
        if not sender_id or not receiver_id:
            await sio.emit(
                "message_response",
                {
                    "status": "error",
                    "message": "Missing required fields: sender_id, receiver_id",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # For text messages, content is required. For other types, content is optional
        if message_type == "text" and not content:
            await sio.emit(
                "message_response",
                {
                    "status": "error",
                    "message": "Content is required for text messages",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # For non-text messages, attachments are required
        if message_type != "text" and not attachments:
            await sio.emit(
                "message_response",
                {
                    "status": "error",
                    "message": f"Attachments are required for {message_type} messages",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Validate attachments format and file types
        if attachments:
            max_video_size = 100 * 1024 * 1024  # 100MB in bytes
            allowed_image_types = ["image/jpeg", "image/jpg", "image/png"]
            allowed_video_types = ["video/mp4", "video/avi", "video/mov", "video/wmv", "video/flv"]
            allowed_file_types = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
                "text/csv",
            ]

            for attachment in attachments:
                if not attachment.get("url") or not attachment.get("file_name"):
                    await sio.emit(
                        "message_response",
                        {
                            "status": "error",
                            "message": "Each attachment must have url and file_name",
                            "session_id": sid,
                        },
                        to=sid,
                    )
                    return

                file_type = attachment.get("file_type", "")
                file_size = attachment.get("size", 0)

                # Validate file type based on message_type
                if message_type == "image" and file_type not in allowed_image_types:
                    await sio.emit(
                        "message_response",
                        {
                            "status": "error",
                            "message": f"Invalid file type for image. Allowed: {', '.join(allowed_image_types)}",
                            "session_id": sid,
                        },
                        to=sid,
                    )
                    return

                if message_type == "video":
                    if file_type not in allowed_video_types:
                        await sio.emit(
                            "message_response",
                            {
                                "status": "error",
                                "message": f"Invalid file type for video. Allowed: {', '.join(allowed_video_types)}",
                                "session_id": sid,
                            },
                            to=sid,
                        )
                        return
                    if file_size > max_video_size:
                        await sio.emit(
                            "message_response",
                            {
                                "status": "error",
                                "message": f"Video file size exceeds maximum limit of 100MB",
                                "session_id": sid,
                            },
                            to=sid,
                        )
                        return

                if message_type == "file" and file_type not in allowed_file_types:
                    await sio.emit(
                        "message_response",
                        {
                            "status": "error",
                            "message": f"Invalid file type. Allowed: PDF, DOC, DOCX, XLS, XLSX, CSV",
                            "session_id": sid,
                        },
                        to=sid,
                    )
                    return

        # Get sender user details (accepts both UUID string and integer ID)
        sender_user = await chat_service.get_user_by_id(sender_id)
        if not sender_user:
            await sio.emit(
                "message_response",
                {
                    "status": "error",
                    "message": "Sender user not found",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Get receiver user details (accepts both UUID string and integer ID)
        receiver_user = await chat_service.get_user_by_id(receiver_id)
        if not receiver_user:
            await sio.emit(
                "message_response",
                {
                    "status": "error",
                    "message": "Receiver user not found",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Use user.id (integer) for database operations
        sender_id_int = sender_user.get("id")
        receiver_id_int = receiver_user.get("id")

        # Get or create room between sender and receiver
        session_info = chat_service.get_session_info(sid)

        # If room_id is provided, validate it's a UUID string
        if room_id:
            # Check if room_id is a UUID string (36 characters with hyphens)
            if isinstance(room_id, str) and len(room_id) == 36 and room_id.count("-") == 4:
                # It's a UUID, verify it exists
                existing_room_id = await chat_service.get_room_id_from_uuid(room_id)
                if not existing_room_id:
                    await sio.emit(
                        "message_response",
                        {
                            "status": "error",
                            "message": "Room not found with provided room_id",
                            "session_id": sid,
                        },
                        to=sid,
                    )
                    return
                # Use the existing room_id UUID
                room_id = existing_room_id
            else:
                await sio.emit(
                    "message_response",
                    {
                        "status": "error",
                        "message": "Invalid room_id format. Must be a UUID string",
                        "session_id": sid,
                    },
                    to=sid,
                )
                return

        if not session_info:
            # Create new room if session doesn't exist
            if not room_id:
                # First message - create or get room between these two users
                room_info = await chat_service.create_or_get_room_between_users(
                    sender_id_int, receiver_id_int, sid
                )
                room_id = room_info["room_id"]
                await sio.enter_room(sid, f"room_{room_id}")
                logger.info(
                    f"🆕 Created/found room {room_id} between user {sender_id_int} and {receiver_id_int}"
                )
            else:
                # Joining existing room - get session info for this room
                room_info = await chat_service.create_or_get_room_between_users(
                    sender_id_int, receiver_id_int, sid
                )
                # Update session with provided room_id
                if room_id != room_info["room_id"]:
                    # Use the provided room_id if it's different
                    session_info = {
                        "room_id": room_id,
                        "session_uuid": room_info.get("session_uuid"),
                        "sender_id": sender_id_int,
                        "receiver_id": receiver_id_int,
                    }
                    chat_service.sessions[sid] = session_info
                else:
                    chat_service.sessions[sid] = {
                        "room_id": room_id,
                        "session_uuid": room_info.get("session_uuid"),
                        "sender_id": sender_id_int,
                        "receiver_id": receiver_id_int,
                    }
                await sio.enter_room(sid, f"room_{room_id}")
                logger.info(f"📦 User {sender_id_int} joined existing room {room_id}")
        else:
            # Use existing room from session
            room_id = session_info.get("room_id") or room_id
            if not room_id:
                # If session exists but no room_id, create one
                room_info = await chat_service.create_or_get_room_between_users(
                    sender_id_int, receiver_id_int, sid
                )
                room_id = room_info["room_id"]
                await sio.enter_room(sid, f"room_{room_id}")
                logger.info(f"🆕 Created room {room_id} for existing session")
            else:
                # Validate room_id is UUID format
                if not (isinstance(room_id, str) and len(room_id) == 36 and room_id.count("-") == 4):
                    # Invalid format, create new room
                    logger.warning(f"⚠️ Invalid room_id format in session, creating new room")
                    room_info = await chat_service.create_or_get_room_between_users(
                        sender_id_int, receiver_id_int, sid
                    )
                    room_id = room_info["room_id"]
                    # Update session with valid UUID room_id
                    session_info["room_id"] = room_id
                    chat_service.sessions[sid] = session_info
                # Ensure user is in the room
                await sio.enter_room(sid, f"room_{room_id}")

        # Save message to database
        saved_message = await chat_service.save_message(
            room_id=room_id,
            sender_id=sender_id_int,
            receiver_id=receiver_id_int,
            message=content,
            message_type=message_type,
            attachments=attachments,
            session_id=sid,
        )

        await sio.emit(
            "message_response",
            {
                "status": "success",
                "message": "Message sent successfully",
                "data": {
                    **saved_message,
                    "room_id": room_id,  # room_id is already UUID string
                },
                "session_id": sid,
            },
            room=f"room_{room_id}",
        )

        logger.info(f"📤 Sent message to room {room_id}")

    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        await sio.emit(
            "message_response",
            {
                "status": "error",
                "message": f"Error processing message: {str(e)}",
                "session_id": sid,
            },
            to=sid,
        )


@sio.event
async def group_message(sid, data):
    """
    Handle incoming group messages from client.

    Expected data format:
    {
        "group_id": UUID string (group UUID),
        "sender_id": UUID string (sender user UUID),
        "content": "string" (message content),
        "room_id": UUID string (optional) - room identifier,
        "message_type": "text" | "image" | "video" | "file" | "audio" (default: "text"),
        "attachments": [
            {
                "url": "https://...",
                "file_name": "file.jpg",
                "file_type": "image/jpeg",
                "size": 2048000
            }
        ] (optional)
    }
    """
    try:
        logger.info(
            f"📨 Received group message from {sid}: {data if not isinstance(data, str) or len(data) < 500 else data[:500] + '...'}"
        )

        # Parse JSON string if needed
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON: {e}")
                await sio.emit(
                    "group_message_response",
                    {
                        "status": "error",
                        "message": "Invalid JSON format. Please ensure your JSON is valid.",
                        "session_id": sid,
                    },
                    to=sid,
                )
                return

        # Validate required fields
        group_id = data.get("group_id")
        sender_id = data.get("sender_id")
        content = data.get("content")
        room_id = data.get("room_id")
        message_type = data.get("message_type", "text")
        attachments = data.get("attachments", [])

        # Validate required fields
        if not group_id or not sender_id:
            await sio.emit(
                "group_message_response",
                {
                    "status": "error",
                    "message": "Missing required fields: group_id, sender_id",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # For text messages, content is required. For other types, content is optional
        if message_type == "text" and not content:
            await sio.emit(
                "group_message_response",
                {
                    "status": "error",
                    "message": "Content is required for text messages",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Validate message_type
        valid_message_types = ["text", "image", "video", "file", "audio"]
        if message_type not in valid_message_types:
            await sio.emit(
                "group_message_response",
                {
                    "status": "error",
                    "message": f"Invalid message_type. Must be one of: {', '.join(valid_message_types)}",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Get sender user details
        sender_user = await chat_service.get_user_by_id(sender_id)
        if not sender_user:
            await sio.emit(
                "group_message_response",
                {
                    "status": "error",
                    "message": "Sender user not found",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        sender_id_int = sender_user.get("id")

        # Get group details
        group = await chat_service.get_group_by_id(group_id)
        if not group:
            await sio.emit(
                "group_message_response",
                {
                    "status": "error",
                    "message": "Group not found",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Validate sender is a member of the group
        members_list = group.get("members", [])
        if sender_id_int not in members_list:
            await sio.emit(
                "group_message_response",
                {
                    "status": "error",
                    "message": "You are not a member of this group",
                    "session_id": sid,
                },
                to=sid,
            )
            return

        # Get receiver IDs (all group members except sender)
        receiver_ids = [member_id for member_id in members_list if member_id != sender_id_int]

        # Get group ID (integer) for database operations
        group_id_int = group.get("id")
        group_uuid = group.get("uuid")

        # Create or get room for this group (room_id is unique per group conversation)
        room_info = await chat_service.create_or_get_room_for_group(
            group_id_int, sid
        )
        room_id = room_info["room_id"]
        logger.info(f"🔑 Using room_id: {room_id} for group {group_id_int}")

        # Join group room (use room_id for socket room name)
        group_room = f"group_{room_id}"
        await sio.enter_room(sid, group_room)
        logger.info(f"📦 User {sender_id_int} joined group room {group_room}")

        # Save group message to database (use integer group_id for database)
        saved_message = await chat_service.save_group_message(
            room_id=room_id,
            sender_id=sender_id_int,
            group_id=group_id_int,
            receiver_ids=receiver_ids,
            message=content,
            message_type=message_type,
            attachments=attachments,
            session_id=sid,
        )

        # Emit message to all group members
        await sio.emit(
            "group_message_response",
            {
                "status": "success",
                "message": "Group message sent successfully",
                "data": {
                    **saved_message,
                    "room_id": room_id,
                    "group_id": group_uuid,  # Return group UUID in response
                },
                "session_id": sid,
            },
            room=group_room,
        )

        logger.info(f"📤 Sent group message to group {group_id} (room: {group_room})")

    except Exception as e:
        logger.error(f"❌ Error processing group message: {str(e)}")
        await sio.emit(
            "group_message_response",
            {
                "status": "error",
                "message": f"Error processing group message: {str(e)}",
                "session_id": sid,
            },
            to=sid,
        )


"""
Chat REST API endpoints.
"""

@router.post("/chat/groups")
async def create_group(
    body: CreateGroupRequest = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new message group.
    
    Args:
        body: CreateGroupRequest containing group_name and members list
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with created group data
    """
    try:
        logger.info("Starting create group endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to create group
        create_group_service = CreateGroupService()
        return await create_group_service.create_group(
            db=db,
            body=body,
            current_user=current_user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in create_group endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/groups/{group_uuid}")
async def get_group(
    group_uuid: str,
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a specific group by UUID.
    
    Args:
        group_uuid: UUID of the group to retrieve
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with group data
    """
    try:
        logger.info(f"Starting get group endpoint for UUID: {group_uuid}")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to get group
        get_group_service = GetGroupService()
        return await get_group_service.get_group(
            db=db,
            group_uuid=group_uuid,
            current_user=current_user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_group endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/groups")
async def list_groups(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: str = Query(None, description="Search by group name"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List groups that the current user is a member of.
    
    Args:
        page: Page number for pagination
        limit: Number of items per page
        search: Search term for group name
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with paginated list of groups
    """
    try:
        logger.info("Starting list groups endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to list groups
        get_group_service = GetGroupService()
        return await get_group_service.list_groups(
            db=db,
            current_user=current_user,
            page=page,
            limit=limit,
            search=search,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in list_groups endpoint: {exc}", exc_info=True)
        raise


@router.put("/chat/groups/{group_uuid}")
async def update_group(
    group_uuid: str,
    body: dict = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update a message group (name and/or members).
    
    Args:
        group_uuid: UUID of the group to update
        body: UpdateGroupRequest containing group_name and/or members
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with updated group data
    """
    try:
        logger.info(f"Starting update group endpoint for UUID: {group_uuid}")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Parse body into UpdateGroupRequest
        from apps.v1.api.chat.schema import UpdateGroupRequest
        update_body = UpdateGroupRequest(**body)
        
        # Call service to update group
        update_group_service = UpdateGroupService()
        return await update_group_service.update_group(
            db=db,
            group_uuid=group_uuid,
            body=update_body,
            current_user=current_user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in update_group endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/user/chats")
async def get_user_chats(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all chats (1:1 and group) for the authenticated user.
    
    Args:
        page: Page number for pagination
        limit: Number of items per page
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with paginated chat list
    """
    try:
        logger.info("Starting get user chats endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to get user chats
        get_user_chats_service = GetUserChatsService()
        return await get_user_chats_service.get_user_chats(
            db=db,
            current_user=current_user,
            page=page,
            limit=limit,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_user_chats endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/history")
async def get_chat_history(
    room_id: str = Query(None, description="Room UUID (for one-on-one or group chats)"),
    group_id: str = Query(None, description="Group UUID (alternative to room_id for group chats)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get chat history for a room or group.
    
    Args:
        room_id: Room UUID (for one-on-one or group chats)
        group_id: Group UUID (alternative to room_id for group chats)
        page: Page number for pagination
        limit: Number of items per page
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with paginated chat history
    """
    try:
        logger.info("Starting get chat history endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to get chat history
        get_chat_history_service = GetChatHistoryService()
        return await get_chat_history_service.get_chat_history(
            db=db,
            current_user=current_user,
            room_id=room_id,
            group_id=group_id,
            page=page,
            limit=limit,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_chat_history endpoint: {exc}", exc_info=True)
        raise

