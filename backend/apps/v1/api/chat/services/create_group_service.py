"""
Create group service for creating message groups.
"""

import logging
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.v1.api.chat.models.model import message_groups
from apps.v1.api.chat.schema import CreateGroupRequest
from apps.v1.api.auth.models.model import Users
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class CreateGroupService:
    """
    Service to create a new message group.
    """

    async def create_group(
        self,
        db: AsyncSession,
        body: CreateGroupRequest,
        current_user: Users,
    ):
        """
        Create a new group service method.

        Args:
            db: Database session
            body: CreateGroupRequest containing group_name and members list
            current_user: Currently authenticated user creating the group

        Returns:
            StandardResponse with created group data
        """
        try:
            logger.info("Starting create group workflow")

            # Validate that members list is not empty
            if not body.members:
                logger.error("Members list is empty")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Members list cannot be empty",
                ).make

            # Ensure creator is included in members list
            members_list = list(set(body.members))  # Remove duplicates
            if current_user.id not in members_list:
                members_list.append(current_user.id)

            logger.info(f"Validating member IDs: {members_list}")

            # Validate that all member IDs exist
            stmt = select(Users).filter(Users.id.in_(members_list))
            result = await db.execute(stmt)
            existing_users = result.scalars().all()
            existing_user_ids = {user.id for user in existing_users}

            # Check if all provided member IDs exist
            invalid_member_ids = set(members_list) - existing_user_ids
            if invalid_member_ids:
                logger.error(f"Invalid member IDs: {invalid_member_ids}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=f"Invalid member IDs: {invalid_member_ids}",
                ).make

            logger.info("Creating new group in database")

            # Create new group with creator as admin by default
            new_group = message_groups(
                group_name=body.group_name,
                created_by=current_user.id,
                members=members_list,  # Store as JSON array
                admins=[current_user.id],  # Store creator's ID as admin by default
            )

            db.add(new_group)
            await db.flush()
            await db.refresh(new_group)
            await db.commit()

            logger.info(f"Group created successfully: {new_group.id}, UUID: {new_group.uuid}")

            # Prepare response data
            response_data = {
                "id": new_group.id,
                "uuid": new_group.uuid,
                "group_name": new_group.group_name,
                "created_by": new_group.created_by,
                "members": new_group.members if new_group.members else [],
                "admins": new_group.admins if new_group.admins else [],
                "created_at": new_group.created_at.isoformat() if new_group.created_at else None,
                "updated_at": new_group.updated_at.isoformat() if new_group.updated_at else None,
            }

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_201_CREATED,
                data=response_data,
                message="Group created successfully",
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in create_group_service: {exc}",
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
                f"Unexpected error in create_group_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

