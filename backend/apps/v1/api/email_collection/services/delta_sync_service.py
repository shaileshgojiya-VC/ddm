"""
Delta sync service for email synchronization.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.models.attribute import SyncStatus
from apps.v1.api.email_collection.models.methods.email_method import (
    ConversationMethod,
    EmailAttachmentMethod,
    EmailMailboxMethod,
    EmailMethod,
    EmailSyncStateMethod,
)
from apps.v1.api.email_collection.models.model import (
    Conversations,
    EmailAttachments,
    EmailMailboxes,
    Emails,
    EmailSyncState,
)
from apps.v1.api.email_collection.utils.graph_client import MicrosoftGraphClient
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class DeltaSyncService:
    """
    Service to perform delta sync for email synchronization.
    """

    async def perform_delta_sync(
        self,
        db: AsyncSession,
        mailbox_id: int,
        folder: str = "Inbox",
    ):
        """
        Perform delta sync for mailbox service method.

        Args:
            db: Database session
            mailbox_id: Mailbox ID
            folder: Mailbox folder name

        Returns:
            StandardResponse with sync results
        """
        try:
            logger.info(f"STEP 1: Starting delta sync for mailbox {mailbox_id}")

            logger.info("STEP 2: Loading mailbox and connector")
            mailbox_method = EmailMailboxMethod(EmailMailboxes)
            mailbox = await mailbox_method.find_by_id(db=db, mailbox_id=mailbox_id)

            if not mailbox:
                logger.error("STEP 3: Mailbox not found")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.MAILBOX_NOT_FOUND,
                ).make

            connector = mailbox.email_auth
            if not connector:
                logger.error("STEP 3: Connector not found")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.CONNECTOR_NOT_FOUND,
                ).make

            logger.info("STEP 3: Loading sync state")
            sync_state_method = EmailSyncStateMethod(EmailSyncState)
            sync_state = await sync_state_method.find_by_mailbox_and_folder(
                db=db, mailbox_id=mailbox_id, folder=folder
            )

            delta_link = sync_state.delta_link if sync_state else None

            logger.info("STEP 4: Initializing Graph client")
            graph_client = MicrosoftGraphClient(
                tenant_id=connector.tenant_id,
                client_id=connector.client_id,
                client_secret=connector.client_secret,
            )

            logger.info("STEP 5: Fetching messages via delta query")
            delta_result = await graph_client.get_user_messages_delta(
                user_email=mailbox.email, delta_link=delta_link
            )

            messages = delta_result.get("value", [])
            new_delta_link = delta_result.get("@odata.deltaLink")

            logger.info(f"STEP 6: Processing {len(messages)} messages")
            processed_count = 0
            conversation_method = ConversationMethod(Conversations)
            email_method = EmailMethod(Emails)
            attachment_method = EmailAttachmentMethod(EmailAttachments)

            for message_data in messages:
                try:
                    await self._process_message(
                        db=db,
                        message_data=message_data,
                        conversation_method=conversation_method,
                        email_method=email_method,
                        attachment_method=attachment_method,
                        graph_client=graph_client,
                        mailbox_email=mailbox.email,
                    )
                    processed_count += 1
                except Exception as exc:
                    logger.error(
                        f"Error processing message {message_data.get('id')}: {exc}",
                        exc_info=True,
                    )
                    continue

            logger.info("STEP 7: Updating sync state")
            if sync_state:
                update_data = {
                    "delta_link": new_delta_link,
                    "last_synced_at": datetime.utcnow(),
                    "sync_status": SyncStatus.SYNC_ACTIVE.value,
                }
                await sync_state_method.update_sync_state(
                    db=db, sync_state_id=sync_state.id, update_data=update_data
                )
            else:
                sync_state_data = {
                    "email_mailbox_id": mailbox_id,
                    "mailbox_folder": folder,
                    "delta_link": new_delta_link,
                    "sync_status": SyncStatus.INITIAL_SYNC_COMPLETED.value,
                    "last_synced_at": datetime.utcnow(),
                }
                await sync_state_method.create_sync_state(
                    db=db, sync_state_data=sync_state_data
                )

            await mailbox_method.update_last_synced(
                db=db, mailbox_id=mailbox_id, synced_at=datetime.utcnow()
            )

            logger.info("STEP 8: Delta sync completed successfully")
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data={
                    "processed_count": processed_count,
                    "total_messages": len(messages),
                },
                message=message_variable.DELTA_SYNC_SUCCESS,
            ).make

        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in delta_sync_service: {exc}",
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
                f"Unexpected error in delta_sync_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def _process_message(
        self,
        db: AsyncSession,
        message_data: dict,
        conversation_method: ConversationMethod,
        email_method: EmailMethod,
        attachment_method: EmailAttachmentMethod,
        graph_client: MicrosoftGraphClient,
        mailbox_email: str,
    ):
        """
        Process a single message and store in database.

        Args:
            db: Database session
            message_data: Message data from Graph API
            conversation_method: Conversation method instance
            email_method: Email method instance
            attachment_method: Attachment method instance
            graph_client: Graph client instance
            mailbox_email: Mailbox email address
        """
        message_id = message_data.get("id")
        conversation_id = message_data.get("conversationId")

        sender = message_data.get("sender", {})
        sender_email = sender.get("emailAddress", {}).get("address") if sender else None
        sender_name = sender.get("emailAddress", {}).get("name") if sender else None

        to_recipients = message_data.get("toRecipients", [])
        receiver_list = [
            recipient.get("emailAddress", {}).get("address")
            for recipient in to_recipients
        ]

        body = message_data.get("body", {})
        content_text = body.get("content") if body else None

        sent_datetime = None
        if message_data.get("sentDateTime"):
            sent_datetime = datetime.fromisoformat(
                message_data["sentDateTime"].replace("Z", "+00:00")
            )

        received_datetime = None
        if message_data.get("receivedDateTime"):
            received_datetime = datetime.fromisoformat(
                message_data["receivedDateTime"].replace("Z", "+00:00")
            )

        conversation = None
        if conversation_id:
            conversation_data = {
                "microsoft_conversation_id": conversation_id,
                "subject": message_data.get("subject"),
                "participants_json": {
                    "sender": sender_email,
                    "receivers": receiver_list,
                },
                "total_emails": 1,
                "conversation_started_at": sent_datetime or received_datetime,
            }
            conversation = await conversation_method.find_or_create_by_microsoft_id(
                db=db,
                microsoft_conversation_id=conversation_id,
                conversation_data=conversation_data,
            )

        email_data = {
            "microsoft_message_id": message_id,
            "conversation_id": conversation.id if conversation else None,
            "sender_email": sender_email,
            "sender_name": sender_name,
            "receiver_string": ", ".join(receiver_list) if receiver_list else None,
            "receiver_json": receiver_list if receiver_list else None,
            "subject": message_data.get("subject"),
            "content_text": content_text,
            "sent_at": sent_datetime,
            "received_at": received_datetime,
            "has_attachment": message_data.get("hasAttachments", False),
            "is_reply": False,
        }

        email = await email_method.find_or_create_by_microsoft_id(
            db=db,
            microsoft_message_id=message_id,
            email_data=email_data,
        )

        if message_data.get("hasAttachments"):
            attachments = await graph_client.get_message_attachments(
                user_email=mailbox_email, message_id=message_id
            )

            for attachment_data in attachments:
                attachment_db_data = {
                    "email_id": email.id,
                    "attachment_id": attachment_data.get("id"),
                    "filename": attachment_data.get("name"),
                    "content_type": attachment_data.get("contentType"),
                    "size": attachment_data.get("size"),
                    "storage_path": None,
                }
                await attachment_method.create_attachment(
                    db=db, attachment_data=attachment_db_data
                )

        if conversation:
            await conversation_method.update_conversation_count(
                db=db, conversation_id=conversation.id
            )
