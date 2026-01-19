"""
Get chat history service for retrieving chat messages.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from apps.v1.api.chat.models.model import message_chats, message_groups
from apps.v1.api.auth.models.model import Users
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetChatHistoryService:
    """
    Service to get chat history for one-on-one or group chats.
    """

    async def get_chat_history(
        self,
        db: AsyncSession,
        current_user: Users,
        room_id: Optional[str] = None,
        group_id: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ):
        """
        Get chat history service method.

        Args:
            db: Database session
            current_user: Currently authenticated user
            room_id: Room UUID (for one-on-one or group chats)
            group_id: Group UUID (alternative to room_id for group chats)
            page: Page number for pagination
            limit: Number of items per page

        Returns:
            StandardResponse with paginated chat history
        """
        try:
            logger.info(f"Starting get chat history workflow for user {current_user.id}")

            # Validate that at least one identifier is provided
            if not room_id and not group_id:
                logger.error("Either room_id or group_id must be provided")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Either room_id or group_id must be provided",
                ).make

            # If group_id is provided, get the group and validate membership
            group = None
            if group_id:
                stmt = select(message_groups).filter(message_groups.uuid == group_id)
                result = await db.execute(stmt)
                group = result.scalar_one_or_none()

                if not group:
                    logger.error(f"Group not found with UUID: {group_id}")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_404_NOT_FOUND,
                        data=constant_variable.STATUS_NULL,
                        message="Group not found",
                    ).make

                # Check if user is a member of the group
                members_list = group.members if group.members else []
                if current_user.id not in members_list:
                    logger.error(f"User {current_user.id} is not a member of group {group_id}")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_403_FORBIDDEN,
                        data=constant_variable.STATUS_NULL,
                        message="You are not a member of this group",
                    ).make

                # Use group UUID as room_id if room_id not provided
                if not room_id:
                    room_id = group.uuid

            # Build query to get messages
            stmt = select(message_chats).filter(message_chats.room_id == room_id)

            # For one-on-one chats, also verify user is sender or receiver
            if not group:
                stmt = stmt.filter(
                    or_(
                        message_chats.sender_id == current_user.id,
                        message_chats.receiver_id == current_user.id
                    )
                )

            # Order by created_at descending (most recent first)
            stmt = stmt.order_by(message_chats.created_at.desc())

            # Get total count
            count_stmt = select(func.count(message_chats.id)).filter(message_chats.room_id == room_id)
            if not group:
                count_stmt = count_stmt.filter(
                    or_(
                        message_chats.sender_id == current_user.id,
                        message_chats.receiver_id == current_user.id
                    )
                )
            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            # Apply pagination
            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)

            # Execute query
            result = await db.execute(stmt)
            messages = result.scalars().all()

            logger.info(f"Found {len(messages)} messages (total: {total}) for room {room_id}")

            # Prepare response data
            messages_data = []
            for message in messages:
                # Get sender UUID
                sender_stmt = select(Users).filter(Users.id == message.sender_id)
                sender_result = await db.execute(sender_stmt)
                sender_user = sender_result.scalar_one_or_none()
                sender_uuid = sender_user.uuid if sender_user else None

                # Get receiver UUID (for one-on-one chats)
                receiver_uuid = None
                receiver_uuids = []
                if message.receiver_id:
                    receiver_stmt = select(Users).filter(Users.id == message.receiver_id)
                    receiver_result = await db.execute(receiver_stmt)
                    receiver_user = receiver_result.scalar_one_or_none()
                    receiver_uuid = receiver_user.uuid if receiver_user else None

                # For group messages, extract receiver_ids from attachments
                if message.group_id and message.attachments:
                    attachments_data = message.attachments
                    if isinstance(attachments_data, dict) and "receiver_ids" in attachments_data:
                        receiver_id_list = attachments_data.get("receiver_ids", [])
                        # Convert receiver IDs to UUIDs
                        for receiver_id in receiver_id_list:
                            receiver_stmt = select(Users).filter(Users.id == receiver_id)
                            receiver_result = await db.execute(receiver_stmt)
                            receiver_user = receiver_result.scalar_one_or_none()
                            if receiver_user:
                                receiver_uuids.append(receiver_user.uuid)

                # Extract file attachments (exclude receiver_ids metadata)
                file_attachments = []
                if message.attachments:
                    attachments_data = message.attachments
                    if isinstance(attachments_data, dict) and "files" in attachments_data:
                        file_attachments = attachments_data.get("files", [])
                    elif isinstance(attachments_data, list):
                        file_attachments = attachments_data

                # Get group UUID if group_id exists
                group_uuid = None
                if message.group_id:
                    group_stmt = select(message_groups).filter(message_groups.id == message.group_id)
                    group_result = await db.execute(group_stmt)
                    group_obj = group_result.scalar_one_or_none()
                    group_uuid = group_obj.uuid if group_obj else None

                message_data = {
                    "uuid": message.uuid,
                    "room_id": message.room_id,
                    "sender_id": sender_uuid,
                    "receiver_id": receiver_uuid,  # For one-on-one chats
                    "receiver_ids": receiver_uuids if receiver_uuids else None,  # For group chats
                    "group_id": group_uuid,  # Group UUID if group message
                    "message": message.message,
                    "message_type": message.message_type or "text",
                    "attachments": file_attachments,
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                    "updated_at": message.updated_at.isoformat() if message.updated_at else None,
                }
                messages_data.append(message_data)

            # Reverse to show oldest first (since we ordered by desc)
            messages_data.reverse()

            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit if total > 0 else 0

            response_data = {
                "items": messages_data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data,
                message="Chat history retrieved successfully",
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in get_chat_history_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
            
        except Exception as exc:
            logger.error(
                f"Unexpected error in get_chat_history_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

