"""
Webhook handler service for Microsoft Graph notifications.
"""

import logging

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.methods.email_method import (
    EmailSyncStateMethod,
)
from apps.v1.api.email_collection.models.model import EmailSyncState
from apps.v1.api.email_collection.services.delta_sync_service import DeltaSyncService
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class WebhookHandlerService:
    """
    Service to handle webhook notifications from Microsoft Graph.
    """

    async def handle_webhook(
        self,
        db: AsyncSession,
        notification_data: dict,
    ):
        """
        Handle webhook notification service method.

        Args:
            db: Database session
            notification_data: Webhook notification data

        Returns:
            StandardResponse with processing results
        """
        try:
            logger.info("STEP 1: Starting webhook handling workflow")

            notifications = notification_data.get("value", [])
            if not notifications:
                logger.warning("STEP 2: No notifications in webhook payload")
                return StandardResponse(
                    status=constant_variable.STATUS_SUCCESS,
                    status_code=status.HTTP_200_OK,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.WEBHOOK_PROCESSED_SUCCESS,
                ).make

            logger.info(f"STEP 2: Processing {len(notifications)} notifications")

            sync_state_method = EmailSyncStateMethod(EmailSyncState)
            delta_sync_service = DeltaSyncService()
            processed_mailboxes = set()

            for notification in notifications:
                try:
                    subscription_id = notification.get("subscriptionId")
                    if not subscription_id:
                        logger.warning("STEP 3: Notification missing subscription ID")
                        continue

                    logger.info(
                        f"STEP 3: Finding sync state for subscription {subscription_id}"
                    )
                    sync_state = await sync_state_method.find_by_subscription_id(
                        db=db, subscription_id=subscription_id
                    )

                    if not sync_state:
                        logger.warning(
                            f"STEP 4: Sync state not found for subscription {subscription_id}"
                        )
                        continue

                    mailbox_id = sync_state.email_mailbox_id
                    if mailbox_id in processed_mailboxes:
                        logger.info(
                            f"STEP 4: Mailbox {mailbox_id} already processed in this batch"
                        )
                        continue

                    logger.info(
                        f"STEP 4: Triggering delta sync for mailbox {mailbox_id}"
                    )
                    await delta_sync_service.perform_delta_sync(
                        db=db,
                        mailbox_id=mailbox_id,
                        folder=sync_state.mailbox_folder,
                    )

                    processed_mailboxes.add(mailbox_id)
                    logger.info(
                        f"STEP 5: Delta sync completed for mailbox {mailbox_id}"
                    )

                except Exception as exc:
                    logger.error(
                        f"Error processing notification: {exc}",
                        exc_info=True,
                    )
                    continue

            logger.info("STEP 6: Webhook processing completed")
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data={
                    "processed_mailboxes": len(processed_mailboxes),
                    "total_notifications": len(notifications),
                },
                message=message_variable.WEBHOOK_PROCESSED_SUCCESS,
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in webhook_handler_service: {exc}",
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
                f"Unexpected error in webhook_handler_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
