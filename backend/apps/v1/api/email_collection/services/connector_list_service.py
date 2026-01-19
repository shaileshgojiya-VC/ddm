"""
List email connectors service.
"""

import logging
import math

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import EmailAuthMethod
from apps.v1.api.email_collection.models.model import EmailAuth
from apps.v1.api.email_collection.schema import ConnectorListQueryParams
from apps.v1.api.email_collection.serilizer import ConnectorSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ConnectorListService:
    """
    Service to list email connectors with pagination.
    """

    async def list_connectors(
        self,
        db: AsyncSession,
        query_params: ConnectorListQueryParams,
    ):
        """
        List connectors with filters and pagination service method.

        Args:
            db: Database session
            query_params: Query parameters for filters and pagination

        Returns:
            StandardResponse with paginated connector list
        """
        try:
            logger.info("STEP 1: Starting list connectors workflow")

            logger.info("STEP 2: Applying filters and pagination")
            auth_method = EmailAuthMethod(EmailAuth)
            connectors, total = await auth_method.list_connectors(
                db=db,
                provider=query_params.provider,
                page=query_params.page,
                limit=query_params.limit,
            )

            logger.info("STEP 3: Serializing connector data")
            connector_serializer = ConnectorSerializer()
            serialized_connectors = [
                connector_serializer.dump(connector) for connector in connectors
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
                "connectors": serialized_connectors,
            }

            logger.info("STEP 5: List connectors successful")
            content = {
                "status": constant_variable.STATUS_SUCCESS,
                "data": response_data,
                "pagination": pagination_data,
                "message": message_variable.CONNECTORS_RETRIEVED_SUCCESS,
            }

            return JSONResponse(content=content, status_code=status.HTTP_200_OK)

        except ValueError as exc:
            logger.error(
                f"Validation error in connector_list_service: {exc}",
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
                f"Database error in connector_list_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
