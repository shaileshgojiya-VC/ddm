"""
Delete user service for soft deleting users.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.serializer import UserDeleteSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class DeleteUserService:
    """
    Service to soft delete a user.
    """

    async def delete_user(
        self,
        db: AsyncSession,
        user_id: str,
        current_user: Users,
    ):
        """
        Soft delete user by ID service method.

        Args:
            db: Database session
            user_id: ID of the user to delete
            current_user: Currently authenticated user

        Returns:
            StandardResponse with deletion result
        """
        try:
            logger.info("Starting user deletion workflow")

            logger.info("Loading current user with role relationship")

            # Reload current user with role relationship
            base_method = UserAuthMethod(Users)
            current_user_with_role = await base_method.find_by_id_with_role(
                db=db, user_id=current_user.id
            )

            if not current_user_with_role:
                logger.error(f"Current user not found: {current_user.id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Verifying admin authorization")

            # Check if current user is admin
            # Admin is determined by having a role with name "admin" (case-insensitive)
            if not current_user_with_role.role:
                logger.error(f"User {current_user.email} has no role assigned")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.DELETE_ACCESS_DENIED,
                    errors={"permission": [message_variable.ONLY_ADMIN_CAN_DELETE]},
                ).make

            # Check if user has admin role (case-insensitive check)
            if current_user_with_role.role.name.lower() != "admin":
                logger.error(
                    f"User {current_user_with_role.email} with role {current_user_with_role.role.name} is not authorized to delete users"
                )
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.DELETE_ACCESS_DENIED,
                    errors={"permission": [message_variable.ONLY_ADMIN_CAN_DELETE]},
                ).make

            logger.info(
                f"Admin authorization verified: {current_user_with_role.email}"
            )

            # Convert user_id (string) to int
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid user ID format: {user_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Invalid user ID format",
                ).make

            logger.info(f"Fetching user with ID: {user_id_int}")

            # Fetch user to delete using ID
            user_to_delete = await base_method.find_by_id(db=db, entity_id=user_id_int)

            if not user_to_delete:
                logger.info(f"User not found with ID: {user_id_int}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_NOT_FOUND,
                ).make

            logger.info(f"User found: {user_to_delete.email}")

            # Check if user is already deleted
            if (
                user_to_delete.status == Status.DELETED
                or user_to_delete.deleted_at is not None
            ):
                logger.info(f"User {user_to_delete.email} is already deleted")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="User is already deleted",
                ).make

            logger.info("Soft deleting user")

            # Soft delete user using ID
            deleted_user = await base_method.soft_delete_user_by_id(
                db=db, user_id=user_id_int
            )

            if not deleted_user:
                logger.error(f"Failed to delete user with ID: {user_id_int}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Serializing deleted user data")

            # Prepare response data
            user_response_data = {
                "id": str(deleted_user.id),
                "status": deleted_user.status.value
                if isinstance(deleted_user.status, Status)
                else str(deleted_user.status),
                "deleted_at": deleted_user.deleted_at,
            }

            # Serialize user data
            try:
                user_serializer = UserDeleteSerializer()
                serialized_user = user_serializer.dump(user_response_data)
                logger.info(
                    f"Serialization successful for deleted user: {deleted_user.email}"
                )
            except ValueError as serialization_error:
                logger.error(
                    f"Serialization validation error: {serialization_error}",
                    exc_info=True,
                )
                raise
            except Exception as serialization_error:
                logger.error(
                    f"Serialization error: {serialization_error}",
                    exc_info=True,
                )
                raise

            logger.info("User deletion successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_user,
                message=message_variable.USER_DELETED,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in delete_user_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=str(exc),
            ).make
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in delete_user_service: {exc}",
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
                f"Unexpected error in delete_user_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
