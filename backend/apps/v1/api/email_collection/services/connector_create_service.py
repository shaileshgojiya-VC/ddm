"""
Create email connector service.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import EmailAuthMethod
from apps.v1.api.email_collection.models.model import EmailAuth
from apps.v1.api.email_collection.schema import ConnectorCreateRequest
from apps.v1.api.email_collection.serilizer import ConnectorSerializer
from apps.v1.api.email_collection.utils.graph_client import MicrosoftGraphClient
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ConnectorCreateService:
    """
    Service to create email connector with client credentials validation.
    """

    async def create_connector(
        self,
        db: AsyncSession,
        request_data: ConnectorCreateRequest,
    ):
        """
        Create email connector service method.

        Args:
            db: Database session
            request_data: Connector creation request data

        Returns:
            StandardResponse with created connector data
        """
        try:
            logger.info("STEP 1: Starting connector creation workflow")

            logger.info("STEP 2: Validating Microsoft Graph credentials")
            graph_client = MicrosoftGraphClient(
                tenant_id=request_data.tenant_id,
                client_id=request_data.client_id,
                client_secret=request_data.client_secret,
            )

            is_valid = await graph_client.validate_credentials()
            if not is_valid:
                logger.error("STEP 3: Invalid Microsoft Graph credentials")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_CREDENTIALS,
                ).make

            logger.info("STEP 3: Credentials validated successfully")

            logger.info("STEP 4: Checking for existing connector")
            auth_method = EmailAuthMethod(EmailAuth)
            existing_connector = await auth_method.find_by_email(
                db=db, email=request_data.email
            )

            if existing_connector:
                logger.error("STEP 5: Connector already exists")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.CONNECTOR_ALREADY_EXISTS,
                ).make

            logger.info("STEP 5: Creating connector in database")
            connector_data = {
                "provider": request_data.provider,
                "tenant_id": request_data.tenant_id,
                "client_id": request_data.client_id,
                "client_secret": request_data.client_secret,
                "email": request_data.email,
                "is_active": constant_variable.STATUS_TRUE,
            }

            new_connector = await auth_method.create_connector(
                db=db, connector_data=connector_data
            )

            logger.info("STEP 6: Serializing connector data")
            connector_serializer = ConnectorSerializer()
            serialized_connector = connector_serializer.dump(new_connector)

            logger.info("STEP 7: Connector created successfully")
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_201_CREATED,
                data=serialized_connector,
                message=message_variable.CONNECTOR_CREATED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in connector_create_service: {exc}",
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
                f"Database error in connector_create_service: {exc}",
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
                f"Unexpected error in connector_create_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
