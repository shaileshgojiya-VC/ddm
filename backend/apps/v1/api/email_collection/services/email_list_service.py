"""
List emails service.
"""

import logging
import math

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import EmailMethod
from apps.v1.api.email_collection.models.model import Emails
from apps.v1.api.email_collection.schema import EmailListQueryParams
from apps.v1.api.email_collection.serilizer import EmailSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class EmailListService:
    """
    Service to list emails with filters and pagination.
    """

    async def list_emails(
        self,
        db: AsyncSession,
        query_params: EmailListQueryParams,
    ):
        """
        List emails with filters and pagination service method.

        Args:
            db: Database session
            query_params: Query parameters for filters and pagination

        Returns:
            StandardResponse with paginated email list
        """
        try:
            logger.info("STEP 1: Starting list emails workflow")

            logger.info("STEP 2: Applying filters and pagination")
            email_method = EmailMethod(Emails)
            emails, total = await email_method.list_emails(
                db=db,
                mailbox_id=query_params.mailbox_id,
                conversation_id=query_params.conversation_id,
                search=query_params.search,
                page=query_params.page,
                limit=query_params.limit,
            )

            logger.info("STEP 3: Serializing email data")
            email_serializer = EmailSerializer()
            serialized_emails = [email_serializer.dump(email) for email in emails]

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
                "emails": serialized_emails,
            }

            logger.info("STEP 5: List emails successful")
            content = {
                "status": constant_variable.STATUS_SUCCESS,
                "data": response_data,
                "pagination": pagination_data,
                "message": message_variable.EMAILS_RETRIEVED_SUCCESS,
            }

            return JSONResponse(content=content, status_code=status.HTTP_200_OK)

        except ValueError as exc:
            logger.error(
                f"Validation error in email_list_service: {exc}",
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
                f"Database error in email_list_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
