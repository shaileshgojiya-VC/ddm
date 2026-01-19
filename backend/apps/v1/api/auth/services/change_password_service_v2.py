"""
Change password service (refactored) for updating user password.

Follows SOLID principles with single responsibility:
- Service handles only orchestration
- Validation delegated to validators
- Password operations delegated to password utils
- DB operations delegated to model methods
"""

import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import ChangePasswordRequest
from core.utils import constant_variable, message_variable
from core.utils.helper import PasswordUtils
from core.utils.jwt_hanlder import jwt_handler
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ChangePasswordServiceV2:
    """Service to change user password (refactored version)."""

    def __init__(self):
        self.base_method = UserAuthMethod(Users)
        self.password_utils = PasswordUtils()

    async def change_password(
        self,
        db: AsyncSession,
        body: ChangePasswordRequest,
        current_user: Users,
    ):
        """
        Change user password with validation.

        Args:
            db: Database session
            body: ChangePasswordRequest
            current_user: Authenticated user

        Returns:
            StandardResponse with new token
        """
        try:
            logger.info(f"Password change initiated for user: {current_user.email}")

            # Step 1: Validate current password
            validation_error = self._validate_current_password(
                body.current_password, current_user.hashed_password
            )
            if validation_error:
                return validation_error

            # Step 2: Validate password confirmation
            validation_error = self._validate_password_match(
                body.new_password, body.confirm_password
            )
            if validation_error:
                return validation_error

            # Step 3: Validate password strength
            validation_error = self._validate_password_strength(body.new_password)
            if validation_error:
                return validation_error

            # Step 4: Hash and update password
            hashed_password = self.password_utils.hash_password(body.new_password)
            updated_user = await self.base_method.update_user_by_id(
                db=db,
                user_id=current_user.id,
                update_data={"hashed_password": hashed_password},
            )

            if not updated_user:
                logger.error(f"Failed to update password for user: {current_user.id}")
                return self._error_response(
                    message_variable.SOMETHING_WENT_WRONG,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Step 5: Generate new token and return
            new_token = self._generate_access_token(updated_user)
            response = self._build_response(updated_user, new_token)

            logger.info(f"Password successfully changed for user: {updated_user.email}")
            return response

        except Exception as e:
            logger.error(f"Error in change_password: {str(e)}")
            return self._error_response(
                message_variable.SOMETHING_WENT_WRONG,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _validate_current_password(self, plain: str, hashed: str):
        """Verify current password is correct."""
        if not self.password_utils.verify_password(plain, hashed):
            logger.warning("Invalid current password provided")
            return self._error_response(
                message_variable.INVALID_CURRENT_PASSWORD,
                status.HTTP_401_UNAUTHORIZED,
            )
        return None

    def _validate_password_match(self, new_password: str, confirm_password: str):
        """Verify passwords match."""
        if new_password != confirm_password:
            logger.warning("Password confirmation mismatch")
            return self._error_response(
                message_variable.PASSWORD_MISMATCH,
                status.HTTP_400_BAD_REQUEST,
            )
        return None

    def _validate_password_strength(self, password: str):
        """Validate password meets requirements."""
        import re

        if len(password) < 8:
            return self._error_response(
                message_variable.PASSWORD_REQUIREMENTS_NOT_MET,
                status.HTTP_400_BAD_REQUEST,
            )

        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(
            re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password)
        )

        if not (has_upper and has_lower and has_digit and has_special):
            return self._error_response(
                message_variable.PASSWORD_REQUIREMENTS_NOT_MET,
                status.HTTP_400_BAD_REQUEST,
            )

        return None

    def _generate_access_token(self, user: Users) -> str:
        """Generate JWT token for user."""
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
        }
        return jwt_handler.create_access_token(data=token_data)

    async def _build_response(self, user: Users, token: str):
        """Build successful response with token."""
        expires_in = jwt_handler.access_token_expire_minutes * 60

        response_data = {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "requires_password_change": False,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "password_changed_at": str(user.updated_at),
            },
        }

        return StandardResponse(
            status=constant_variable.STATUS_SUCCESS,
            status_code=status.HTTP_200_OK,
            data=response_data,
            message="Password changed successfully",
        ).make

    def _error_response(self, message: str, status_code: int):
        """Create standardized error response."""
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status_code,
            data=constant_variable.STATUS_NULL,
            message=message,
        ).make
