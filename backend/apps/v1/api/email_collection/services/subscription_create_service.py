"""
Create webhook subscription service.
"""

import logging
from datetime import datetime

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.model import EmailMailboxes, EmailSyncState
from apps.v1.api.email_collection.models.methods.email_method import (
    EmailMailboxMethod,
    EmailSyncStateMethod,
)
from apps.v1.api.email_collection.models.attribute import SyncStatus, MailboxFolder
from apps.v1.api.email_collection.schema import SubscriptionCreateRequest
from apps.v1.api.email_collection.serilizer import SubscriptionSerializer
from apps.v1.api.email_collection.utils.graph_client import MicrosoftGraphClient
from config.env_config import settings
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class SubscriptionCreateService:
    """
    Service to create webhook subscription for mailbox.
    """

    async def create_subscription(
        self,
        db: AsyncSession,
        request_data: SubscriptionCreateRequest,
    ):
        """
        Create webhook subscription service method.

        Args:
            db: Database session
            request_data: Subscription creation request data

        Returns:
            StandardResponse with created subscription data
        """
        try:
            logger.info("STEP 1: Starting subscription creation workflow")

            logger.info("STEP 2: Validating mailbox")
            mailbox_method = EmailMailboxMethod(EmailMailboxes)
            mailbox = await mailbox_method.find_by_id(
                db=db, mailbox_id=request_data.email_mailbox_id
            )

            if not mailbox:
                logger.error("STEP 3: Mailbox not found")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.MAILBOX_NOT_FOUND,
                ).make

            if not mailbox.is_active:
                logger.error("STEP 3: Mailbox is inactive")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.MAILBOX_INACTIVE,
                ).make

            logger.info("STEP 3: Getting connector credentials")
            connector = mailbox.email_auth
            if not connector:
                logger.error("STEP 4: Connector not found")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.CONNECTOR_NOT_FOUND,
                ).make

            logger.info("STEP 4: Creating Microsoft Graph subscription")
            graph_client = MicrosoftGraphClient(
                tenant_id=connector.tenant_id,
                client_id=connector.client_id,
                client_secret=connector.client_secret,
            )

            webhook_url = request_data.notification_url or settings.OUTLOOK_WEBHOOK_URL
            if not webhook_url:
                logger.error("STEP 5: Webhook URL not provided")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.WEBHOOK_URL_REQUIRED,
                ).make

            subscription_result = await graph_client.create_subscription(
                user_email=mailbox.email,
                notification_url=webhook_url,
            )

            logger.info("STEP 5: Creating sync state in database")
            sync_state_method = EmailSyncStateMethod(EmailSyncState)

            existing_sync_state = await sync_state_method.find_by_mailbox_and_folder(
                db=db,
                mailbox_id=request_data.email_mailbox_id,
                folder=request_data.mailbox_folder or MailboxFolder.INBOX.value,
            )

            expiration_datetime = None
            if subscription_result.get("expirationDateTime"):
                expiration_datetime = datetime.fromisoformat(
                    subscription_result["expirationDateTime"].replace("Z", "+00:00")
                )

            if existing_sync_state:
                logger.info("STEP 6: Updating existing sync state")
                update_data = {
                    "subscription_id": subscription_result["id"],
                    "subscription_expiration": expiration_datetime,
                    "sync_status": SyncStatus.SYNC_ACTIVE.value,
                }
                updated_sync_state = await sync_state_method.update_sync_state(
                    db=db,
                    sync_state_id=existing_sync_state.id,
                    update_data=update_data,
                )
                sync_state = updated_sync_state
            else:
                logger.info("STEP 6: Creating new sync state")
                sync_state_data = {
                    "email_mailbox_id": request_data.email_mailbox_id,
                    "mailbox_folder": request_data.mailbox_folder
                    or MailboxFolder.INBOX.value,
                    "subscription_id": subscription_result["id"],
                    "subscription_expiration": expiration_datetime,
                    "sync_status": SyncStatus.SYNC_ACTIVE.value,
                }
                sync_state = await sync_state_method.create_sync_state(
                    db=db, sync_state_data=sync_state_data
                )

            logger.info("STEP 7: Serializing subscription data")
            subscription_serializer = SubscriptionSerializer()
            serialized_subscription = subscription_serializer.dump(sync_state)

            logger.info("STEP 8: Subscription created successfully")
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_201_CREATED,
                data=serialized_subscription,
                message=message_variable.SUBSCRIPTION_CREATED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in subscription_create_service: {exc}",
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
                f"Database error in subscription_create_service: {exc}",
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
                f"Unexpected error in subscription_create_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
