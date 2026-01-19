"""
User login service for authentication.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import UserLoginRequest
from apps.v1.api.auth.serializer import UserLoginSerializer
from core.utils import constant_variable, message_variable
from core.utils.helper import PasswordUtils
from core.utils.jwt_hanlder import jwt_handler
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class UserLoginService:
    """
    User login service for handling user authentication (non-admin roles).
    """

    async def user_login(
        self,
        db: AsyncSession,
        body: UserLoginRequest,
    ):
        """
        User login service method.

        Args:
            db: Database session
            body: User login request containing email and password

        Returns:
            StandardResponse with login result
        """
        try:
            logger.info("STEP 1: Starting user login workflow")

            logger.info("STEP 2: Validating input data")

            base_method = UserAuthMethod(Users)

            user = await base_method.find_by_email(db=db, email=body.email)

            if not user:
                logger.info(f"User not found with email: {body.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_EMAIL_OR_PASSWORD,
                ).make

            logger.info("STEP 3: Verifying password")

            # Verify password
            password_utils = PasswordUtils()
            if not password_utils.verify_password(
                plain_password=body.password,
                hashed_password=user.hashed_password,
            ):
                logger.info(f"Invalid password for email: {body.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_EMAIL_OR_PASSWORD,
                ).make

            logger.info("STEP 4: Checking user status")

            # Allow PENDING and ACTIVE users to login
            # PENDING users need to change their temporary password
            if user.status not in [Status.ACTIVE, Status.PENDING]:
                logger.info(f"User account is inactive: {body.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_INACTIVE,
                ).make

            logger.info("STEP 5: Verifying user role (non-admin)")

            # Verify user has role assigned
            if not user.role:
                logger.info(f"User has no role assigned: {body.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.UNAUTHORIZED,
                ).make

            # Verify user does NOT have admin role (case-insensitive check)
            admin_role_name = "admin"
            if user.role.name.lower() == admin_role_name:
                logger.info(
                    f"User {user.email} with admin role is not authorized for user login. Use /admin-login instead."
                )
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message="Admin users must use /admin-login endpoint",
                ).make

            logger.info(
                f"STEP 5.5: User role verified (non-admin) for user: {user.email}"
            )

            logger.info("STEP 6: Updating last login timestamp")

            # Update last login timestamp
            last_login_updated = await base_method.update_last_login(
                db=db, user_id=user.id
            )
            if not last_login_updated:
                logger.warning(f"Failed to update last login for user: {user.email}")

            logger.info("STEP 7: Generating JWT tokens")

            # Generate JWT token data
            token_data = {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
            }

            # Create access token
            access_token = jwt_handler.create_access_token(data=token_data)

            # Create refresh token
            refresh_token = jwt_handler.create_refresh_token(data=token_data)

            # Get expires_in from JWT handler (convert minutes to seconds)
            expires_in_seconds = jwt_handler.access_token_expire_minutes * 60

            logger.info("STEP 8: Preparing response data")

            # Create dictionary for serialization
            # Set required_password_change to True if user status is PENDING
            # Convert role object to dict with id field
            user_dict = {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": {
                    "id": str(user.role.id) if user.role else None,
                    "name": user.role.name if user.role else None,
                    "description": user.role.description if user.role else None,
                } if user.role else None,
                "status": user.status.value if isinstance(user.status, Status) else str(user.status),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            
            login_response = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": expires_in_seconds,
                "requires_password_change": (user.status == Status.PENDING),
                "user": user_dict,
            }

            # Serialize login response data using UserLoginSerializer
            try:
                user_serializer = UserLoginSerializer()
                serialized_user = user_serializer.dump(login_response)
                logger.info(f"STEP 9: Serialization successful for user: {user.email}")
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

            logger.info("STEP 10: User login successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_user,
                message=message_variable.LOGIN_SUCCESSFUL,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in user_login_service: {exc}",
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
                f"Database error in user_login_service: {exc}",
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
                f"Unexpected error in user_login_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
