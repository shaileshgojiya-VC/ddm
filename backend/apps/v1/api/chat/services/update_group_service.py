"""
Update group service for modifying group details.
"""

import logging
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.v1.api.chat.models.model import message_groups
from apps.v1.api.chat.schema import UpdateGroupRequest
from apps.v1.api.auth.models.model import Users
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class UpdateGroupService:
    """
    Service to update an existing message group.
    """

    async def update_group(
        self,
        db: AsyncSession,
        group_uuid: str,
        body: UpdateGroupRequest,
        current_user: Users,
    ):
        """
        Update group details.

        Args:
            db: Database session
            group_uuid: UUID of the group to update
            body: UpdateGroupRequest containing updates
            current_user: Currently authenticated user

        Returns:
            StandardResponse with updated group data
        """
        try:
            logger.info(f"Starting update group workflow for UUID: {group_uuid}")

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

            # Determine updated members: append new ones, keep existing
            updated_members = set(members_list)
            if body.members is not None:
                if not body.members:
                    logger.error("Members list is empty")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data=constant_variable.STATUS_NULL,
                        message="Members list cannot be empty",
                    ).make
                new_members = set(body.members)
                updated_members |= new_members  # append, do not remove existing

                # Always include the current user
                updated_members.add(current_user.id)

                # Validate that all member IDs exist
                stmt_users = select(Users).filter(Users.id.in_(updated_members))
                users_result = await db.execute(stmt_users)
                existing_users = users_result.scalars().all()
                existing_user_ids = {user.id for user in existing_users}
                invalid_member_ids = updated_members - existing_user_ids
                if invalid_member_ids:
                    logger.error(f"Invalid member IDs: {invalid_member_ids}")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data=constant_variable.STATUS_NULL,
                        message=f"Invalid member IDs: {invalid_member_ids}",
                    ).make

            # Ensure list for persistence
            updated_members_list = list(updated_members)

            # Update fields
            if body.group_name:
                group.group_name = body.group_name
            group.members = updated_members_list

            await db.commit()
            await db.refresh(group)

            logger.info(f"Group updated successfully: {group.id}")

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
                message="Group updated successfully",
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in update_group_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in update_group_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

