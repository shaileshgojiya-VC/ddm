"""
List email mailboxes service.
"""

import logging
import math

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import EmailMailboxMethod
from apps.v1.api.email_collection.models.model import EmailMailboxes
from apps.v1.api.email_collection.schema import MailboxListQueryParams
from apps.v1.api.email_collection.serilizer import MailboxSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class MailboxListService:
    """
    Service to list email mailboxes with pagination.
    """

    async def list_mailboxes(
        self,
        db: AsyncSession,
        query_params: MailboxListQueryParams,
    ):
        """
        List mailboxes with filters and pagination service method.

        Args:
            db: Database session
            query_params: Query parameters for filters and pagination

        Returns:
            StandardResponse with paginated mailbox list
        """
        try:
            logger.info("STEP 1: Starting list mailboxes workflow")

            logger.info("STEP 2: Applying filters and pagination")
            mailbox_method = EmailMailboxMethod(EmailMailboxes)
            mailboxes, total = await mailbox_method.list_mailboxes(
                db=db,
                email_auth_id=query_params.email_auth_id,
                app_id=query_params.app_id,
                page=query_params.page,
                limit=query_params.limit,
            )

            logger.info("STEP 3: Serializing mailbox data")
            mailbox_serializer = MailboxSerializer()
            serialized_mailboxes = [
                mailbox_serializer.dump(mailbox) for mailbox in mailboxes
            ]

            logger.info("STEP 4: Calculating pagination metadata")
            total_pages = (
                math.ceil(total / query_params.limit) if query_params.limit > 0 else 0
            )

            pagination_data = {
                "page": query_params.page,
                "limit": query_params.limit,
                "total": total,
                "pages": total_pages,
            }

            response_data = {
                "mailboxes": serialized_mailboxes,
            }

            logger.info("STEP 5: List mailboxes successful")
            content = {
                "status": constant_variable.STATUS_SUCCESS,
                "data": response_data,
                "pagination": pagination_data,
                "message": message_variable.MAILBOXES_RETRIEVED_SUCCESS,
            }

            return JSONResponse(content=content, status_code=status.HTTP_200_OK)

        except ValueError as exc:
            logger.error(
                f"Validation error in mailbox_list_service: {exc}",
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
                f"Database error in mailbox_list_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
