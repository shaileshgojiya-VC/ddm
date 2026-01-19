"""
Refresh token service for authentication.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import RefreshTokenRequest
from apps.v1.api.auth.serializer import RefreshTokenSerializer
from core.utils import constant_variable, message_variable
from core.utils.jwt_hanlder import jwt_handler
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class RefreshTokenService:
    """
    Refresh token service for handling token refresh.
    """

    async def refresh_token(
        self,
        db: AsyncSession,
        body: RefreshTokenRequest,
    ):
        """
        Refresh token service method.

        Args:
            db: Database session
            body: Refresh token request containing refresh_token

        Returns:
            StandardResponse with new access and refresh tokens
        """
        try:
            logger.info("STEP 1: Starting refresh token workflow")

            logger.info("STEP 2: Validating refresh token")

            # Verify refresh token
            try:
                token_payload = jwt_handler.verify_refresh_token(
                    token=body.refresh_token
                )
            except Exception as token_error:
                logger.error(f"Invalid refresh token: {token_error}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_REFRESH_TOKEN,
                ).make

            logger.info("STEP 3: Extracting user information from token")

            # Extract user information from token
            user_id = token_payload.get("user_id")
            if not user_id:
                logger.error("No user_id found in refresh token")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_REFRESH_TOKEN,
                ).make

            logger.info(f"STEP 4: Fetching user from database: {user_id}")

            # Convert user_id from string to int
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid user_id format: {user_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_REFRESH_TOKEN,
                ).make

            # Fetch user from database
            base_method = UserAuthMethod(Users)
            user = await base_method.find_by_id_with_role(db=db, user_id=user_id_int)

            if not user:
                logger.error(f"User not found with id: {user_id_int}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_REFRESH_TOKEN,
                ).make

            logger.info("STEP 5: Checking user status")

            # Verify user is active or pending
            if user.status not in [Status.ACTIVE, Status.PENDING]:
                logger.error(f"User account is inactive: {user.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_403_FORBIDDEN,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_INACTIVE,
                ).make

            logger.info("STEP 6: Generating new access and refresh tokens")

            # Generate new token data
            token_data = {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
            }

            # Create new access token
            access_token = jwt_handler.create_access_token(data=token_data)

            # Create new refresh token
            refresh_token = jwt_handler.create_refresh_token(data=token_data)

            # Get expires_in from JWT handler (convert minutes to seconds)
            expires_in_seconds = jwt_handler.access_token_expire_minutes * 60

            logger.info("STEP 7: Preparing response data")

            # Create dictionary for serialization
            refresh_response = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": expires_in_seconds,
            }

            # Serialize refresh response data using RefreshTokenSerializer
            try:
                refresh_serializer = RefreshTokenSerializer()
                serialized_response = refresh_serializer.dump(refresh_response)
                logger.info(f"STEP 8: Serialization successful for user: {user.email}")
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

            logger.info("STEP 9: Refresh token successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_response,
                message=message_variable.REFRESH_TOKEN_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in refresh_token_service: {exc}",
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
                f"Database error in refresh_token_service: {exc}",
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
                f"Unexpected error in refresh_token_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

