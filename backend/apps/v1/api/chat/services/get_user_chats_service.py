"""
Get user chats service for retrieving all chats for the authenticated user.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from apps.v1.api.chat.models.model import message_chats, message_groups
from apps.v1.api.auth.models.model import Users
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetUserChatsService:
    """
    Service to get all chats (1:1 and group) for the current user.
    """

    async def get_user_chats(
        self,
        db: AsyncSession,
        current_user: Users,
        page: int = 1,
        limit: int = 50,
    ):
        """
        Get all chats for the authenticated user with pagination.

        Args:
            db: Database session
            current_user: Currently authenticated user
            page: Page number for pagination
            limit: Number of items per page

        Returns:
            StandardResponse with paginated chat list
        """
        try:
            logger.info("Starting get user chats workflow")

            # Fetch all groups and find those where the user is a member
            groups_result = await db.execute(select(message_groups))
            all_groups = groups_result.scalars().all()
            user_group_ids = [
                g.id for g in all_groups
                if current_user.id in (g.members or [])
            ]
            group_uuid_map = {g.id: g.uuid for g in all_groups}

            # Build filters
            filters = [
                or_(
                    message_chats.sender_id == current_user.id,
                    message_chats.receiver_id == current_user.id,
                )
            ]
            if user_group_ids:
                filters.append(message_chats.group_id.in_(user_group_ids))

            stmt = select(message_chats).where(or_(*filters))
            stmt = stmt.order_by(message_chats.created_at.desc())

            # Count total
            count_stmt = select(func.count(message_chats.id)).where(or_(*filters))
            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            # Pagination
            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)

            result = await db.execute(stmt)
            messages = result.scalars().all()

            logger.info(f"Found {len(messages)} messages (total: {total}) for user {current_user.id}")

            # Collect unique user ids to map to UUIDs
            user_ids = set()
            for msg in messages:
                if msg.sender_id:
                    user_ids.add(msg.sender_id)
                if msg.receiver_id:
                    user_ids.add(msg.receiver_id)
            users_map = {}
            if user_ids:
                users_result = await db.execute(select(Users).where(Users.id.in_(user_ids)))
                users = users_result.scalars().all()
                users_map = {u.id: u.uuid for u in users}

            # Prepare response data
            messages_data = []
            for message in messages:
                # Attachments: extract files, ignore metadata
                file_attachments = []
                if message.attachments:
                    attachments_data = message.attachments
                    if isinstance(attachments_data, dict) and "files" in attachments_data:
                        file_attachments = attachments_data.get("files", [])
                    elif isinstance(attachments_data, list):
                        file_attachments = attachments_data

                receiver_uuid = users_map.get(message.receiver_id) if message.receiver_id else None
                sender_uuid = users_map.get(message.sender_id) if message.sender_id else None

                # For group messages, add group UUID
                group_uuid = group_uuid_map.get(message.group_id) if message.group_id else None

                messages_data.append({
                    "uuid": message.uuid,
                    "room_id": message.room_id,
                    "sender_id": sender_uuid,
                    "receiver_id": receiver_uuid,
                    "group_id": group_uuid,
                    "message": message.message,
                    "message_type": message.message_type or "text",
                    "attachments": file_attachments,
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                    "updated_at": message.updated_at.isoformat() if message.updated_at else None,
                })

            # Reverse to chronological (oldest first)
            messages_data.reverse()

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
                message="User chats retrieved successfully",
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in get_user_chats_service: {exc}",
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
                f"Unexpected error in get_user_chats_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

