"""
Reset password service for password reset using token.
"""

import logging
import re
from datetime import datetime

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import ResetPasswordRequest
from core.utils import constant_variable, message_variable
from core.utils.helper import PasswordUtils
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ResetPasswordService:
    """
    Service to handle password reset using reset token.
    """

    def _validate_password(self, password: str) -> tuple[bool, str]:
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

    async def reset_password(
        self,
        db: AsyncSession,
        body: ResetPasswordRequest,
    ):
        """
        Reset password using reset token.
        
        Args:
            db: Database session
            body: Reset password request containing token and new password
            
        Returns:
            StandardResponse with reset result
        """
        try:
            logger.info("Starting password reset workflow")

            logger.info("Looking up user by reset token")

            base_method = UserAuthMethod(Users)

            # Find user by reset token (method checks expiration automatically)
            user = await base_method.find_by_reset_token(
                db=db, reset_token=body.reset_token
            )

            # Always return generic message for security
            if not user:
                logger.info("Invalid or expired reset token")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Invalid or expired reset token",
                ).make

            logger.info(f"User found: {user.email}")

            # Check if user is active
            if user.status != Status.ACTIVE:
                logger.info(f"User {user.email} is not active")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message="Account is not active",
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
            password_utils = PasswordUtils()
            hashed_password = password_utils.hash_password(body.new_password)

            logger.info("Updating password in database")

            # Update password in database
            updated_user = await base_method.change_password_by_id(
                db=db, user_id=user.id, hashed_password=hashed_password
            )

            if not updated_user:
                logger.error(f"Failed to update password for user: {user.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Clearing reset token")

            # Clear reset token after successful password reset
            token_cleared = await base_method.clear_reset_token_by_id(
                db=db, user_id=user.id
            )

            if not token_cleared:
                logger.warning(
                    f"Password updated but failed to clear reset token for user: {user.email}"
                )
                # Don't fail the operation, password is already updated

            logger.info("Password reset successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=constant_variable.STATUS_NULL,
                message="Password reset successfully. You can now login with your new password.",
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in reset_password_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=str(exc),
            ).make
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in reset_password_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in reset_password_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make