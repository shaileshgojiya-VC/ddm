"""
Create email mailbox service.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import (
    EmailAuthMethod,
    EmailMailboxMethod,
)
from apps.v1.api.email_collection.models.model import EmailAuth, EmailMailboxes
from apps.v1.api.email_collection.schema import MailboxCreateRequest
from apps.v1.api.email_collection.serilizer import MailboxSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class MailboxCreateService:
    """
    Service to create email mailbox.
    """

    async def create_mailbox(
        self,
        db: AsyncSession,
        request_data: MailboxCreateRequest,
    ):
        """
        Create email mailbox service method.

        Args:
            db: Database session
            request_data: Mailbox creation request data

        Returns:
            StandardResponse with created mailbox data
        """
        try:
            logger.info("STEP 1: Starting mailbox creation workflow")

            logger.info("STEP 2: Validating email auth connector")
            auth_method = EmailAuthMethod(EmailAuth)
            connector = await auth_method.find_by_id(
                db=db, connector_id=request_data.email_auth_id
            )

            if not connector:
                logger.error("STEP 3: Connector not found")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.CONNECTOR_NOT_FOUND,
                ).make

            if not connector.is_active:
                logger.error("STEP 3: Connector is inactive")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.CONNECTOR_INACTIVE,
                ).make

            logger.info("STEP 3: Checking for existing mailbox")
            mailbox_method = EmailMailboxMethod(EmailMailboxes)
            existing_mailbox = await mailbox_method.find_by_email(
                db=db, email=request_data.email
            )

            if existing_mailbox:
                logger.error("STEP 4: Mailbox already exists")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.MAILBOX_ALREADY_EXISTS,
                ).make

            logger.info("STEP 4: Creating mailbox in database")
            mailbox_data = {
                "email_auth_id": request_data.email_auth_id,
                "app_id": request_data.app_id,
                "email": request_data.email,
                "is_active": constant_variable.STATUS_TRUE,
            }

            new_mailbox = await mailbox_method.create_mailbox(
                db=db, mailbox_data=mailbox_data
            )

            logger.info("STEP 5: Serializing mailbox data")
            mailbox_serializer = MailboxSerializer()
            serialized_mailbox = mailbox_serializer.dump(new_mailbox)

            logger.info("STEP 6: Mailbox created successfully")
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_201_CREATED,
                data=serialized_mailbox,
                message=message_variable.MAILBOX_CREATED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in mailbox_create_service: {exc}",
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
                f"Database error in mailbox_create_service: {exc}",
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
                f"Unexpected error in mailbox_create_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
