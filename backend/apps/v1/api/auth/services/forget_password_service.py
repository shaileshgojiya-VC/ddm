"""
Forget password service for password reset requests.
"""

import logging
import os
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import ForgetPasswordRequest
from apps.v1.api.auth.serializer import ForgetPasswordSerializer
from core.utils import constant_variable, message_variable
from core.utils.email_service import render_email_template, send_email
from core.utils.helper import generate_random_string
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ForgetPasswordService:
    """
    Service to handle forget password requests.
    """

    async def forget_password(
        self,
        db: AsyncSession,
        body: ForgetPasswordRequest,
    ):
        """
        Forget password service method.

        Args:
            db: Database session
            body: Forget password request containing email

        Returns:
            StandardResponse with reset token information
        """
        try:
            logger.info("Starting forget password workflow")

            logger.info(f"Looking up user with email: {body.email}")

            base_method = UserAuthMethod(Users)

            # Find user by email
            user = await base_method.find_by_email(db=db, email=body.email)

            # Always return success message for security (don't reveal if email exists)
            # But only process if user exists and is active
            if not user:
                logger.info(
                    f"User not found with email: {body.email} (returning generic success)"
                )
                # Return success message even if user doesn't exist (security best practice)
                response_data = {
                    "email": body.email,
                    "reset_token_sent": True,
                    "expires_in": 3600,
                }

                forget_password_serializer = ForgetPasswordSerializer()
                serialized_response = forget_password_serializer.dump(response_data)

                return StandardResponse(
                    status=constant_variable.STATUS_SUCCESS,
                    status_code=status.HTTP_200_OK,
                    data=serialized_response,
                    message=message_variable.FORGET_PASSWORD_SUCCESS,
                ).make

            logger.info(f"User found: {user.email}")

            # Check if user is active (only active users can reset password)
            if user.status != Status.ACTIVE:
                logger.info(
                    f"User {user.email} is not active, returning generic success"
                )
                # Return success message for security
                response_data = {
                    "email": body.email,
                    "reset_token_sent": True,
                    "expires_in": 3600,
                }

                forget_password_serializer = ForgetPasswordSerializer()
                serialized_response = forget_password_serializer.dump(response_data)

                return StandardResponse(
                    status=constant_variable.STATUS_SUCCESS,
                    status_code=status.HTTP_200_OK,
                    data=serialized_response,
                    message=message_variable.FORGET_PASSWORD_SUCCESS,
                ).make

            logger.info("Generating reset token")

            # Generate secure reset token
            reset_token = generate_random_string(length=64)

            # Set expiration (1 hour = 3600 seconds)
            expires_in_seconds = 3600
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)

            logger.info("Storing reset token in database")

            # Store reset token in database
            token_stored = await base_method.generate_reset_token_by_id(
                db=db,
                user_id=user.id,
                reset_token=reset_token,
                expires_at=expires_at,
            )

            if not token_stored:
                logger.error(f"Failed to store reset token for user: {user.email}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("Preparing email content")

            # Prepare email template variables
            frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
            reset_link = f"{frontend_base_url}/reset-password?token={reset_token}"

            email_variables = {
                "name": user.name,
                "user_email": user.email,
                "reset_token": reset_token,
                "reset_link": reset_link,
                "expires_in_hours": 1,
            }

            # Render email template (you may need to create this template)
            email_body = None
            try:
                # Try to render password reset email template
                email_body = render_email_template(
                    "emails/forget_password.html", **email_variables
                )
            except FileNotFoundError:
                logger.warning("Password reset email template not found, using default")

            logger.info("Sending password reset email")

            # Send email with reset token
            try:
                await send_email(
                    to=user.email,
                    subject="Password Reset Request",
                    body=email_body,
                    html=True,
                )
                logger.info(f"Password reset email sent successfully to: {user.email}")
            except Exception as email_error:
                logger.error(
                    f"Failed to send password reset email to {user.email}: {email_error}",
                    exc_info=True,
                )
                # Don't fail the entire operation, but log the error
                # Token is already stored, user can request again if needed

            logger.info("Serializing response data")

            # Prepare response data
            response_data = {
                "email": user.email,
                "reset_token_sent": True,
                "expires_in": expires_in_seconds,
            }

            # Serialize response data
            try:
                forget_password_serializer = ForgetPasswordSerializer()
                serialized_response = forget_password_serializer.dump(response_data)
                logger.info(f"Serialization successful for email: {user.email}")
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

            logger.info("Forget password request successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_response,
                message=message_variable.FORGET_PASSWORD_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in forget_password_service: {exc}",
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
                f"Database error in forget_password_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in forget_password_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
