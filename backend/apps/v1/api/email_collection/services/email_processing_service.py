"""
Email processing service to fetch emails by email address.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import EmailMethod
from apps.v1.api.email_collection.models.model import Emails
from apps.v1.api.email_collection.serilizer import EmailProcessingSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class EmailProcessingService:
    """
    Service to fetch and process emails by email address.
    """

    async def get_emails_by_address(
        self,
        db: AsyncSession,
        email_address: str,
    ):
        """
        Get all emails for a given email address.

        Args:
            db: Database session
            email_address: Email address to search for

        Returns:
            StandardResponse with email processing data
        """
        try:
            logger.info(f"STEP 1: Starting email processing for {email_address}")

            logger.info("STEP 2: Fetching emails from database")
            email_method = EmailMethod(Emails)
            emails = await email_method.find_emails_by_email_address(
                db=db, email_address=email_address
            )

            if not emails:
                logger.warning(f"STEP 3: No emails found for {email_address}")
                return StandardResponse(
                    status=constant_variable.STATUS_SUCCESS,
                    status_code=status.HTTP_200_OK,
                    data=[],
                    message=message_variable.EMAILS_RETRIEVED_SUCCESS,
                ).make

            logger.info(f"STEP 3: Processing {len(emails)} emails")
            serializer = EmailProcessingSerializer()
            processed_emails = []

            for email in emails:
                try:
                    # Skip if required fields are missing
                    if not email.sent_at or not email.received_at:
                        logger.warning(
                            f"Skipping email {email.id} - missing sent_at or received_at"
                        )
                        continue

                    # Prepare data according to EmailProcessingSerializer
                    email_data = {
                        "conversation_id": email.conversation_id or 0,
                        "sent_at": email.sent_at,
                        "recevied_at": email.received_at,
                        "subject": email.subject or "",
                        "context": email.content_text or "",
                    }

                    # Serialize the data
                    serialized = serializer.dump(email_data)
                    processed_emails.append(serialized)

                except Exception as exc:
                    logger.error(
                        f"Error processing email {email.id}: {exc}",
                        exc_info=True,
                    )
                    continue

            logger.info(
                f"STEP 4: Successfully processed {len(processed_emails)} emails"
            )
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=processed_emails,
                message=message_variable.EMAILS_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in email_processing_service: {exc}",
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
                f"Database error in email_processing_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in email_processing_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
