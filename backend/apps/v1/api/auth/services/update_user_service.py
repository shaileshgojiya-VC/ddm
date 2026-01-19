"""
Update user service for updating user information.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import UpdateUserRequest
from apps.v1.api.auth.serializer import UserDetailsSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class UpdateUserService:
    """
    Service to update user information.
    """

    async def update_user(
        self,
        db: AsyncSession,
        user_id: str,
        body: UpdateUserRequest,
        current_user: Users,
    ):
        """
        Update user by ID service method.

        Args:
            db: Database session
            user_id: ID of the user to update
            body: Update user request containing fields to update
            current_user: Currently authenticated user

        Returns:
            StandardResponse with updated user details
        """
        try:
            logger.info("Starting user update workflow")

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

            base_method = UserAuthMethod(Users)

            # Fetch user to update using ID
            user_to_update = await base_method.find_by_id(db=db, entity_id=user_id_int)

            if not user_to_update:
                logger.info(f"User not found with ID: {user_id_int}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_NOT_FOUND,
                ).make

            logger.info(f"User found: {user_to_update.email}")

            logger.info("Validating authorization")

            # Check authorization: Admin can update any user, users can update their own profile
            # For now, we'll allow users to update their own profile
            # In the future, you might want to check if current_user has admin role
            if current_user.id != user_to_update.id:
                # Check if current_user is admin (you can add role-based check here)
                # For now, we'll allow if current_user is active
                if current_user.status != Status.ACTIVE:
                    logger.error(
                        f"User {current_user.email} is not authorized to update user {user_to_update.email}"
                    )
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_403_FORBIDDEN,
                        data=constant_variable.STATUS_NULL,
                        message=message_variable.UNAUTHORIZED,
                    ).make

            logger.info("Preparing update data")

            # Prepare update data - only include fields that are provided
            update_data = {}

            if body.name is not None:
                update_data["name"] = body.name

            if body.phone_number is not None:
                update_data["phone_number"] = body.phone_number

            if body.location is not None:
                update_data["location"] = body.location

            if body.status is not None:
                # Validate status value
                try:
                    status_enum = Status(body.status.lower())
                    update_data["status"] = status_enum
                except ValueError:
                    logger.error(f"Invalid status value: {body.status}")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data=constant_variable.STATUS_NULL,
                        message=f"Invalid status value. Must be one of: {', '.join([s.value for s in Status])}",
                    ).make

            if not update_data:
                logger.info("No fields to update")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="No fields provided for update",
                ).make

            logger.info(f"Updating user with data: {update_data}")

            # Update user in database using ID
            updated_user = await base_method.update_user_by_id(
                db=db, user_id=user_id_int, update_data=update_data
            )

            if not updated_user:
                logger.error(f"Failed to update user with ID: {user_id_int}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Serializing updated user data")

            # Prepare response data
            # Convert role object to dict with id field
            role_dict = None
            if updated_user.role:
                # Convert module IDs to module names
                module_ids = updated_user.role.module_list or []
                module_names = await base_method.get_module_names_by_ids(
                    db=db, module_ids=module_ids
                )
                
                role_dict = {
                    "id": str(updated_user.role.id),
                    "name": updated_user.role.name,
                    "description": updated_user.role.description or "",
                    "module_list": module_names,
                }
            
            user_response_data = {
                "id": str(updated_user.id),
                "name": updated_user.name,
                "email": updated_user.email,
                "role": role_dict,
                "phone_number": updated_user.phone_number,
                "location": updated_user.location,
                "profile_image_url": updated_user.profile_image_url,
                "status": updated_user.status.value
                if isinstance(updated_user.status, Status)
                else str(updated_user.status),
                "parent_id": str(updated_user.parent_user_id)
                if updated_user.parent_user_id
                else None,
                "created_by": str(updated_user.created_by)
                if updated_user.created_by
                else None,
                "joined_at": updated_user.joined_at,
                "created_at": updated_user.created_at,
                "updated_at": updated_user.updated_at,
            }

            # Serialize user data
            try:
                user_serializer = UserDetailsSerializer()
                serialized_user = user_serializer.dump(user_response_data)
                logger.info(f"Serialization successful for user: {updated_user.email}")
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

            logger.info("User update successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_user,
                message=message_variable.USER_UPDATED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in update_user_service: {exc}",
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
                f"Database error in update_user_service: {exc}",
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
                f"Unexpected error in update_user_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
