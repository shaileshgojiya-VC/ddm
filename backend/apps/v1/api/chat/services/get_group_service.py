"""
Get group service for retrieving group information.
"""

import logging
from datetime import datetime
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.v1.api.chat.models.model import message_groups
from apps.v1.api.auth.models.model import Users
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetGroupService:
    """
    Service to get group details and list groups.
    """

    async def get_group(
        self,
        db: AsyncSession,
        group_uuid: str,
        current_user: Users,
    ):
        """
        Get a specific group by UUID service method.

        Args:
            db: Database session
            group_uuid: UUID of the group to retrieve
            current_user: Currently authenticated user

        Returns:
            StandardResponse with group data
        """
        try:
            logger.info(f"Starting get group workflow for UUID: {group_uuid}")

            # Fetch group by UUID
            stmt = select(message_groups).filter(message_groups.uuid == group_uuid)
            result = await db.execute(stmt)
            group = result.scalar_one_or_none()

            if not group:
                logger.error(f"Group not found with UUID: {group_uuid}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="Group not found",
                ).make

            # Check if user is a member of the group
            members_list = group.members if group.members else []
            if current_user.id not in members_list:
                logger.error(f"User {current_user.id} is not a member of group {group_uuid}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message="You are not a member of this group",
                ).make

            logger.info(f"Group retrieved successfully: {group.id}")

            # Prepare response data
            response_data = {
                "id": group.id,
                "uuid": group.uuid,
                "group_name": group.group_name,
                "created_by": group.created_by,
                "members": group.members if group.members else [],
                "admins": group.admins if group.admins else [],
                "created_at": group.created_at.isoformat() if group.created_at else None,
                "updated_at": group.updated_at.isoformat() if group.updated_at else None,
            }

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data,
                message="Group retrieved successfully",
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in get_group_service: {exc}",
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
                f"Unexpected error in get_group_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def list_groups(
        self,
        db: AsyncSession,
        current_user: Users,
        page: int = 1,
        limit: int = 10,
        search: str = None,
    ):
        """
        List groups that the current user is a member of service method.

        Args:
            db: Database session
            current_user: Currently authenticated user
            page: Page number for pagination
            limit: Number of items per page
            search: Search term for group name

        Returns:
            StandardResponse with paginated list of groups
        """
        try:
            logger.info("Starting list groups workflow")

            # Build query to get groups where user is a member
            # For MySQL, we'll fetch and filter in Python for reliability
            stmt = select(message_groups)

            # Apply search filter if provided
            if search:
                stmt = stmt.where(message_groups.group_name.like(f"%{search}%"))

            # Execute query to get all matching groups
            result = await db.execute(stmt)
            all_groups = result.scalars().all()

            # Filter groups where user is a member (check if user ID is in members JSON array)
            user_groups = []
            for group in all_groups:
                members_list = group.members if group.members else []
                if current_user.id in members_list:
                    user_groups.append(group)

            # Get total count after filtering
            total = len(user_groups)

            # Apply pagination
            offset = (page - 1) * limit
            # Sort by created_at descending (most recent first), fallback to datetime.min if created_at is None
            groups = sorted(
                user_groups,
                key=lambda g: g.created_at if g.created_at else datetime.min,
                reverse=True
            )[offset:offset + limit]

            logger.info(f"Found {len(groups)} groups (total: {total}) for user {current_user.id}")

            # Prepare response data
            groups_data = []
            for group in groups:
                groups_data.append({
                    "id": group.id,
                    "uuid": group.uuid,
                    "group_name": group.group_name,
                    "created_by": group.created_by,
                    "members": group.members if group.members else [],
                    "admins": group.admins if group.admins else [],
                    "created_at": group.created_at.isoformat() if group.created_at else None,
                    "updated_at": group.updated_at.isoformat() if group.updated_at else None,
                })

            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit if total > 0 else 0

            response_data = {
                "items": groups_data,
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
                message="Groups retrieved successfully",
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in list_groups_service: {exc}",
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
                f"Unexpected error in list_groups_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

