"""
Email update service for secure email change workflow.

Implements multi-step email verification:
1. User initiates email change with password verification
2. Verification token sent to new email
3. User confirms from old email with link
4. Email updated after both verifications
"""

import logging
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import (
    UpdateEmailInitiateRequest,
    UpdateEmailInitiateResponse,
    VerifyNewEmailRequest,
    VerifyNewEmailResponse,
    ConfirmEmailUpdateRequest,
    ConfirmEmailUpdateResponse,
)
from core.utils import constant_variable, message_variable
from core.utils.email_service import render_email_template, send_email
from core.utils.helper import generate_random_string, PasswordUtils
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class UpdateEmailService:
    """Service for secure email update workflow."""

    def __init__(self):
        self.base_method = UserAuthMethod(Users)
        self.password_utils = PasswordUtils()
        self.token_lifetime_hours = 24
        self.token_length = 32

    async def initiate_email_change(
        self, db: AsyncSession, body: UpdateEmailInitiateRequest, current_user: Users
    ):
        """
        Initiate email change by verifying current password.

        Sends verification token to new email address.

        Args:
            db: Database session
            body: UpdateEmailInitiateRequest with new_email and current_password
            current_user: Currently authenticated user

        Returns:
            StandardResponse with verification status
        """
        try:
            logger.info(f"Initiating email change for user: {current_user.email}")

            # Verify current password
            if not self._verify_current_password(
                body.current_password, current_user.hashed_password
            ):
                logger.warning(
                    f"Invalid password attempt for user: {current_user.email}"
                )
                return self._error_response(
                    message_variable.INVALID_CURRENT_PASSWORD,
                    status.HTTP_401_UNAUTHORIZED,
                )

            # Check if new email is already in use
            existing_user = await self.base_method.find_by_email(
                db=db, email=body.new_email
            )
            if existing_user:
                logger.warning(f"Email already in use: {body.new_email}")
                return self._error_response(
                    message_variable.EMAIL_ALREADY_EXISTS,
                    status.HTTP_400_BAD_REQUEST,
                )

            # Generate verification token
            email_token = generate_random_string(self.token_length)
            token_expiry = datetime.utcnow() + timedelta(
                hours=self.token_lifetime_hours
            )

            # Store pending email and token
            updated_user = await self.base_method.update_user_by_id(
                db=db,
                user_id=current_user.id,
                update_data={
                    "pending_email": body.new_email,
                    "pending_email_token": email_token,
                    "pending_email_token_expires_at": token_expiry,
                },
            )

            if not updated_user:
                logger.error(
                    f"Failed to store pending email for user: {current_user.id}"
                )
                return self._error_response(
                    message_variable.SOMETHING_WENT_WRONG,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Send verification email to new address
            await self._send_verification_email(
                new_email=body.new_email,
                user_name=current_user.name,
                verification_token=email_token,
            )

            logger.info(f"Email verification token sent to: {body.new_email}")

            response_data = UpdateEmailInitiateResponse(
                message="Verification email sent to your new email address",
                verification_required=True,
                pending_email=body.new_email,
            )

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data.model_dump(),
                message="Verification email sent successfully",
            ).make

        except Exception as e:
            logger.error(f"Error in initiate_email_change: {str(e)}")
            return self._error_response(
                message_variable.SOMETHING_WENT_WRONG,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def verify_new_email(
        self, db: AsyncSession, body: VerifyNewEmailRequest, current_user: Users
    ):
        """
        Verify new email via token.

        Sends confirmation link to old email for final authorization.

        Args:
            db: Database session
            body: VerifyNewEmailRequest with email_token
            current_user: Currently authenticated user

        Returns:
            StandardResponse with confirmation link status
        """
        try:
            logger.info(f"Verifying new email token for user: {current_user.email}")

            # Validate token exists and matches
            if (
                current_user.pending_email_token != body.email_token
                or not current_user.pending_email
            ):
                logger.warning(f"Invalid email token for user: {current_user.email}")
                return self._error_response(
                    "Invalid or expired token",
                    status.HTTP_400_BAD_REQUEST,
                )

            # Check token expiry
            if datetime.utcnow() > current_user.pending_email_token_expires_at:
                logger.warning(f"Email token expired for user: {current_user.email}")
                return self._error_response(
                    "Token has expired",
                    status.HTTP_400_BAD_REQUEST,
                )

            # Generate confirmation token for old email
            confirmation_token = generate_random_string(self.token_length)
            confirmation_expiry = datetime.utcnow() + timedelta(
                hours=self.token_lifetime_hours
            )

            # Store confirmation token temporarily
            # Note: We reuse reset_token field for confirmation since password reset won't conflict
            updated_user = await self.base_method.update_user_by_id(
                db=db,
                user_id=current_user.id,
                update_data={
                    "reset_token": confirmation_token,  # Temporary reuse
                    "reset_token_expires_at": confirmation_expiry,
                },
            )

            if not updated_user:
                logger.error(
                    f"Failed to store confirmation token for user: {current_user.id}"
                )
                return self._error_response(
                    message_variable.SOMETHING_WENT_WRONG,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Send confirmation link to old email
            await self._send_confirmation_email(
                old_email=current_user.email,
                new_email=current_user.pending_email,
                user_name=current_user.name,
                confirmation_token=confirmation_token,
            )

            logger.info(f"Confirmation email sent to: {current_user.email}")

            response_data = VerifyNewEmailResponse(
                message="Confirmation email sent to your current email address",
                confirmation_link_sent=True,
                confirmation_email=current_user.email,
            )

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data.model_dump(),
                message="Confirmation email sent to your current email",
            ).make

        except Exception as e:
            logger.error(f"Error in verify_new_email: {str(e)}")
            return self._error_response(
                message_variable.SOMETHING_WENT_WRONG,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def confirm_email_update(
        self, db: AsyncSession, body: ConfirmEmailUpdateRequest, current_user: Users
    ):
        """
        Confirm email update from old email confirmation link.

        Finalizes email change after both verifications complete.

        Args:
            db: Database session
            body: ConfirmEmailUpdateRequest with confirmation_token and password
            current_user: Currently authenticated user

        Returns:
            StandardResponse with updated email confirmation
        """
        try:
            logger.info(f"Confirming email update for user: {current_user.email}")

            # Verify current password
            if not self._verify_current_password(
                body.current_password, current_user.hashed_password
            ):
                logger.warning(
                    f"Invalid password for confirmation: {current_user.email}"
                )
                return self._error_response(
                    message_variable.INVALID_CURRENT_PASSWORD,
                    status.HTTP_401_UNAUTHORIZED,
                )

            # Validate confirmation token
            if current_user.reset_token != body.confirmation_token:
                logger.warning(
                    f"Invalid confirmation token for user: {current_user.email}"
                )
                return self._error_response(
                    "Invalid confirmation token",
                    status.HTTP_400_BAD_REQUEST,
                )

            # Check token expiry
            if datetime.utcnow() > current_user.reset_token_expires_at:
                logger.warning(
                    f"Confirmation token expired for user: {current_user.email}"
                )
                return self._error_response(
                    "Confirmation link has expired",
                    status.HTTP_400_BAD_REQUEST,
                )

            # Validate pending email exists
            if not current_user.pending_email:
                logger.warning(f"No pending email found for user: {current_user.email}")
                return self._error_response(
                    "No pending email change found",
                    status.HTTP_400_BAD_REQUEST,
                )

            # Update email and clear pending data
            updated_user = await self.base_method.update_user_by_id(
                db=db,
                user_id=current_user.id,
                update_data={
                    "email": current_user.pending_email,
                    "pending_email": None,
                    "pending_email_token": None,
                    "pending_email_token_expires_at": None,
                    "email_verified_at": datetime.utcnow(),
                    "reset_token": None,
                    "reset_token_expires_at": None,
                },
            )

            if not updated_user:
                logger.error(f"Failed to update email for user: {current_user.id}")
                return self._error_response(
                    message_variable.SOMETHING_WENT_WRONG,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Send welcome email to new address
            await self._send_welcome_email(
                email=updated_user.email,
                user_name=updated_user.name,
            )

            logger.info(f"Email successfully updated for user: {updated_user.id}")

            response_data = ConfirmEmailUpdateResponse(
                message="Email successfully updated",
                new_email=updated_user.email,
                updated_at=str(updated_user.email_verified_at),
            )

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data.model_dump(),
                message="Email updated successfully",
            ).make

        except Exception as e:
            logger.error(f"Error in confirm_email_update: {str(e)}")
            return self._error_response(
                message_variable.SOMETHING_WENT_WRONG,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _verify_current_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify password matches hash."""
        return self.password_utils.verify_password(plain_password, hashed_password)

    def _error_response(self, message: str, status_code: int):
        """Create standardized error response."""
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status_code,
            data=constant_variable.STATUS_NULL,
            message=message,
        ).make

    async def _send_verification_email(
        self, new_email: str, user_name: str, verification_token: str
    ):
        """Send verification email to new address."""
        verification_url = (
            f"http://localhost:3000/auth/verify-email?token={verification_token}"
        )

        email_body = f"""
        <html>
            <body>
                <h2>Verify Your New Email Address</h2>
                <p>Hi {user_name},</p>
                <p>You've requested to update your email address. Click the link below to verify your new email:</p>
                <p><a href="{verification_url}">Verify Email Address</a></p>
                <p>This link will expire in {self.token_lifetime_hours} hours.</p>
                <p>If you didn't request this change, please ignore this email.</p>
            </body>
        </html>
        """

        await send_email(
            to=new_email,
            subject="Verify Your New Email Address",
            body=email_body,
            html=True,
        )

    async def _send_confirmation_email(
        self,
        old_email: str,
        new_email: str,
        user_name: str,
        confirmation_token: str,
    ):
        """Send confirmation email to old address."""
        confirmation_url = (
            f"http://localhost:3000/auth/confirm-email?token={confirmation_token}"
        )

        email_body = f"""
        <html>
            <body>
                <h2>Confirm Your Email Change</h2>
                <p>Hi {user_name},</p>
                <p>Your email is about to be changed from <strong>{old_email}</strong> to <strong>{new_email}</strong>.</p>
                <p>Click the link below to confirm this change:</p>
                <p><a href="{confirmation_url}">Confirm Email Change</a></p>
                <p>This link will expire in {self.token_lifetime_hours} hours.</p>
                <p>If you didn't request this change, please ignore this email and your current email will remain unchanged.</p>
            </body>
        </html>
        """

        await send_email(
            to=old_email,
            subject="Confirm Your Email Change",
            body=email_body,
            html=True,
        )

    async def _send_welcome_email(self, email: str, user_name: str):
        """Send welcome email after successful change."""
        email_body = f"""
        <html>
            <body>
                <h2>Email Updated Successfully</h2>
                <p>Hi {user_name},</p>
                <p>Your email address has been successfully updated to <strong>{email}</strong>.</p>
                <p>Please use this new email for all future logins.</p>
                <p>If you have any questions, please contact our support team.</p>
            </body>
        </html>
        """

        await send_email(
            to=email,
            subject="Your Email Has Been Updated",
            body=email_body,
            html=True,
        )
