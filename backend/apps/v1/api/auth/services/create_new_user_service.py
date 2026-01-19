"""
Admin create new user service for user creation.
"""

import logging
import os
from datetime import datetime

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Roles, Users
from apps.v1.api.auth.schema import AdminCreateUser
from apps.v1.api.auth.serializer import AdminCreateUserSerializer
from core.utils import constant_variable, message_variable
from core.utils.email_service import render_email_template, send_email
from core.utils.helper import PasswordUtils, generate_temporary_password
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class CreateNewUserService:
    """
    Service to create a new user by admin.
    """

    async def create_new_user(
        self,
        db: AsyncSession,
        body: AdminCreateUser,
        current_user: Users,
    ):
        """
        Create a new user service method.

        Args:
            db: Database session
            body: Admin create user request containing user details
            current_user: Authenticated admin user creating this user

        Returns:
            StandardResponse with user creation result
        """
        try:
            logger.info("Starting user creation workflow")

            logger.info("Validating input data")

            base_method = UserAuthMethod(Users)
            role_method = UserAuthMethod(Roles)

            # Check if email already exists
            existing_user = await base_method.find_by_email(db=db, email=body.email)

            if existing_user:
                # Check if user is soft deleted
                is_soft_deleted = (
                    existing_user.status == Status.DELETED or existing_user.deleted_at is not None
                )

                if is_soft_deleted:
                    logger.info(
                        f"Email exists but user is soft deleted: {body.email}. "
                        "Restoring and reactivating user account."
                    )
                    # Restore the soft-deleted user instead of creating new one
                    # This will be handled after role validation
                    restore_existing_user = True
                else:
                    logger.info(f"Email already exists in database: {body.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_ALREADY_EXISTS,
                ).make
            else:
                restore_existing_user = False

            logger.info("Validating role ID")

            # Convert role_id (string) to int
            try:
                role_id = int(body.role_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid role ID format: {body.role_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Invalid role ID format",
                ).make

            # Check if role exists
            role = await role_method.find_by_id(db=db, entity_id=role_id)

            if not role:
                logger.info(f"Role not found with ID: {role_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.ROLE_NOT_FOUND,
                ).make

            logger.info("Generating temporary password")

            # Generate temporary password
            temporary_password = generate_temporary_password()
            password_utils = PasswordUtils()
            hashed_password = password_utils.hash_password(temporary_password)

            logger.info("Preparing user data")

            # Prepare user data - use authenticated user's ID for created_by
            # bitrix_id is required (non-nullable), set to 0 for admin-created users
            # Set status to PENDING for users with temporary password - they need to change it on first login
            user_data = {
                "name": body.name,
                "email": body.email,
                "bitrix_id": 0,  # Default value for admin-created users (no Bitrix ID yet)
                "role_id": role_id,
                "created_by": current_user.id,
                "hashed_password": hashed_password,
                "status": Status.PENDING,
                "joined_at": datetime.utcnow(),
            }

            if restore_existing_user:
                logger.info("Restoring soft-deleted user account")

                # Restore the soft-deleted user by updating their data
                # Update the existing soft-deleted user
                new_user = await base_method.update_user_by_id(
                    db=db, user_id=existing_user.id, update_data=user_data
                )

                if not new_user:
                    logger.error(f"Failed to restore user with email: {body.email}")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data=constant_variable.STATUS_NULL,
                        message=message_variable.SOMETHING_WENT_WRONG,
                    ).make

                logger.info(f"Successfully restored user account: {body.email}")
            else:
                logger.info("Creating new user in database")

            # Create user in database
            new_user = await base_method.create_user(db=db, user_data=user_data)

            if not new_user:
                logger.error(f"Failed to create user with email: {body.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Preparing email content")

            # Prepare email template variables
            email_variables = {
                "name": body.name,
                "user_email": body.email,
                "temporary_password": temporary_password,
                "login_link": f"{os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')}",
            }

            # Render email template
            try:
                email_body = render_email_template(
                    constant_variable.ADMIN_USER_INVITE_HTML_FILE, **email_variables
                )
            except FileNotFoundError as e:
                logger.error(f"Email template not found: {e}")
                # Continue without email, but log the error
                email_body = None

            logger.info("Sending email to user")

            # Send email with temporary password
            try:
                if email_body:
                    await send_email(
                        to=body.email,
                        subject=constant_variable.NEW_USER_SUBJECT,
                        body=email_body,
                        html=True,
                    )
                    logger.info(f"Email sent successfully to: {body.email}")
                else:
                    logger.warning(f"Email not sent - template rendering failed for: {body.email}")
            except Exception as email_error:
                logger.error(
                    f"Failed to send email to {body.email}: {email_error}",
                    exc_info=True,
                )
                # Don't fail the entire operation if email fails
                # User is already created, just log the error

            logger.info("Serializing user data")

            # Prepare response data with requires_password_change flag
            # Create dictionary for serialization
            # Convert role object to dict with id field
            role_dict = None
            if new_user.role:
                # Convert module IDs to module names
                module_ids = new_user.role.module_list or []
                module_names = await base_method.get_module_names_by_ids(
                    db=db, module_ids=module_ids
                )

                role_dict = {
                    "id": str(new_user.role.id),
                    "name": new_user.role.name,
                    "description": new_user.role.description or "",
                    "module_list": module_names,
                    "status": (
                        new_user.role.status.value
                        if isinstance(new_user.role.status, Status)
                        else str(new_user.role.status)
                    ),
                    "created_at": new_user.role.created_at,
                }

            user_response_data = {
                "id": str(new_user.id),
                "name": new_user.name,
                "email": new_user.email,
                "role": role_dict,
                "status": (
                    new_user.status.value
                    if isinstance(new_user.status, Status)
                    else str(new_user.status)
                ),
                "requires_password_change": True,
                "created_by": str(new_user.created_by) if new_user.created_by else "",
                "created_at": new_user.created_at,
            }

            # Serialize user data
            try:
                user_serializer = AdminCreateUserSerializer()
                serialized_user = user_serializer.dump(user_response_data)
                logger.info(f"Serialization successful for user: {new_user.email}")
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

            logger.info("User creation successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_201_CREATED,
                data=serialized_user,
                message=message_variable.USER_CREATION_EMAIL_SENT,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in create_new_user_service: {exc}",
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
                f"Database error in create_new_user_service: {exc}",
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
                f"Unexpected error in create_new_user_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
