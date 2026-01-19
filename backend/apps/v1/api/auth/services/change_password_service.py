"""
Change password service for updating user password.
"""

import logging
import re
from typing import Tuple

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import ChangePasswordRequest
from apps.v1.api.auth.serializer import ChangePasswordSerializer
from core.utils import constant_variable, message_variable
from core.utils.helper import PasswordUtils
from core.utils.jwt_hanlder import jwt_handler
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ChangePasswordService:
    """
    Service to change user password.
    """

    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, message_variable.PASSWORD_REQUIREMENTS_NOT_MET

        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(
            re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password)
        )

        if not (has_upper and has_lower and has_digit and has_special):
            return False, message_variable.PASSWORD_REQUIREMENTS_NOT_MET

        return True, ""

    async def change_password(
        self,
        db: AsyncSession,
        body: ChangePasswordRequest,
        current_user: Users,
    ):
        """
        Change user password service method.

        Args:
            db: Database session
            body: Change password request
            current_user: Currently authenticated user

        Returns:
            StandardResponse with new access token and user data
        """
        try:
            logger.info("Starting password change workflow")

            logger.info("Validating current password")

            base_method = UserAuthMethod(Users)

            # Verify current password
            password_utils = PasswordUtils()
            if not password_utils.verify_password(
                plain_password=body.current_password,
                hashed_password=current_user.hashed_password,
            ):
                logger.error(f"Invalid current password for user: {current_user.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_CURRENT_PASSWORD,
                ).make

            logger.info("Validating password confirmation")

            # Verify new password and confirm password match
            if body.new_password != body.confirm_password:
                logger.error("New password and confirm password do not match")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.PASSWORD_MISMATCH,
                ).make

            logger.info("Validating new password requirements")

            # Validate new password meets requirements
            is_valid, error_message = self._validate_password(body.new_password)
            if not is_valid:
                logger.error(f"Password validation failed: {error_message}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=error_message,
                ).make

            logger.info("Hashing new password")

            # Hash new password
            hashed_password = password_utils.hash_password(body.new_password)

            logger.info("Updating password in database")

            # Update password in database
            updated_user = await base_method.change_password_by_id(
                db=db, user_id=current_user.id, hashed_password=hashed_password
            )

            if not updated_user:
                logger.error(
                    f"Failed to update password for user: {current_user.email}"
                )
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Generating new JWT token")

            # Generate new JWT token
            token_data = {
                "user_id": str(updated_user.id),
                "email": updated_user.email,
                "name": updated_user.name,
            }

            access_token = jwt_handler.create_access_token(data=token_data)

            # Get expires_in from JWT handler (convert minutes to seconds)
            expires_in = jwt_handler.access_token_expire_minutes * 60

            logger.info("Serializing response data")

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
            
            user_dict = {
                "id": str(updated_user.id),
                "name": updated_user.name,
                "email": updated_user.email,
                "role": role_dict,
                "status": updated_user.status.value if isinstance(updated_user.status, Status) else str(updated_user.status),
                "password_changed_at": updated_user.updated_at,
            }
            
            change_password_response_data = {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in,
                "requires_password_change": False,
                "user": user_dict,
            }

            # Serialize response data
            try:
                change_password_serializer = ChangePasswordSerializer()
                serialized_response = change_password_serializer.dump(
                    change_password_response_data
                )
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

            logger.info("Password change successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_response,
                message=message_variable.PASSWORD_CHANGED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in change_password_service: {exc}",
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
                f"Database error in change_password_service: {exc}",
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
                f"Unexpected error in change_password_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
