"""
Spreadsheet-based email sync service.

This service reads email addresses from an uploaded spreadsheet and syncs
only emails that have conversations with those addresses.
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Set

import pandas as pd
from fastapi import UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    EmailAuth,
    EmailMailboxes,
    Emails,
    EmailSyncState,
)
from apps.v1.api.email_collection.schema import SpreadsheetSyncRequest
from apps.v1.api.email_collection.utils.graph_client import MicrosoftGraphClient
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class SpreadsheetSyncService:
    """
    Service to sync emails from spreadsheet with filtered conversations.
    """

    async def sync_from_spreadsheet(
        self,
        db: AsyncSession,
        file: UploadFile,
        request_data: SpreadsheetSyncRequest,
    ):
        """
        Sync emails from uploaded spreadsheet.

        Args:
            db: Database session
            file: Uploaded spreadsheet file
            request_data: Spreadsheet sync request data

        Returns:
            StandardResponse with sync results
        """
        try:
            logger.info("STEP 1: Starting spreadsheet sync workflow")

            # Read spreadsheet
            logger.info("STEP 2: Reading spreadsheet file")
            spreadsheet_emails = await self._read_spreadsheet_emails(
                file=file, email_column=request_data.email_column
            )

            if not spreadsheet_emails:
                logger.error("STEP 3: No emails found in spreadsheet")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="No emails found in spreadsheet",
                ).make

            logger.info(
                f"STEP 3: Found {len(spreadsheet_emails)} unique emails in spreadsheet"
            )

            # Get all active connectors
            logger.info("STEP 4: Fetching active connectors")
            connectors = await self._get_all_active_connectors(db=db)

            if not connectors:
                logger.error("STEP 5: No active connectors found")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="No active connectors found",
                ).make

            logger.info(f"STEP 5: Found {len(connectors)} active connectors")

            # Process each connector
            total_conversations = 0
            total_emails = 0
            processed_connectors = 0
            failed_connectors = 0
            errors = []

            mailbox_method = EmailMailboxMethod(EmailMailboxes)

            for connector in connectors:
                try:
                    logger.info(f"STEP 6: Processing connector: {connector.email}")

                    # Get or create mailbox
                    mailbox = await self._get_or_create_mailbox(
                        db=db,
                        connector=connector,
                        mailbox_method=mailbox_method,
                        app_id=request_data.app_id,
                    )

                    # Sync filtered emails
                    result = await self._sync_filtered_emails(
                        db=db,
                        connector=connector,
                        mailbox=mailbox,
                        spreadsheet_emails=spreadsheet_emails,
                        folder=request_data.folder,
                    )

                    total_conversations += result["conversations"]
                    total_emails += result["emails"]
                    processed_connectors += 1

                    logger.info(
                        f"✓ Completed {connector.email}: "
                        f"{result['conversations']} conversations, "
                        f"{result['emails']} emails stored"
                    )

                except Exception as exc:
                    logger.error(
                        f"✗ Failed to process {connector.email}: {exc}",
                        exc_info=True,
                    )
                    failed_connectors += 1
                    errors.append(f"{connector.email}: {str(exc)}")
                    continue

            logger.info("STEP 7: Spreadsheet sync completed")
            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data={
                    "total_conversations": total_conversations,
                    "total_emails": total_emails,
                    "processed_connectors": processed_connectors,
                    "failed_connectors": failed_connectors,
                    "spreadsheet_emails_count": len(spreadsheet_emails),
                    "errors": errors[:10] if errors else [],
                },
                message=message_variable.SPREADSHEET_SYNC_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in spreadsheet_sync_service: {exc}",
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
                f"Database error in spreadsheet_sync_service: {exc}",
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
                f"Unexpected error in spreadsheet_sync_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def _read_spreadsheet_emails(
        self, file: UploadFile, email_column: str
    ) -> Set[str]:
        """
        Read email addresses from uploaded spreadsheet.

        Args:
            file: Uploaded file
            email_column: Column name containing emails

        Returns:
            Set of email addresses
        """
        try:
            # Read file content
            contents = await file.read()
            file_extension = file.filename.split(".")[-1].lower()

            # Parse based on file type
            if file_extension == "xlsx":
                df = pd.read_excel(BytesIO(contents))
            elif file_extension == "csv":
                df = pd.read_csv(BytesIO(contents))
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            # Check if column exists
            if email_column not in df.columns:
                available_columns = ", ".join(df.columns.tolist())
                raise ValueError(
                    f"Column '{email_column}' not found in spreadsheet. "
                    f"Available columns: {available_columns}"
                )

            # Extract unique emails
            emails = (
                df[email_column]
                .dropna()
                .astype(str)
                .str.strip()
                .str.lower()
                .unique()
                .tolist()
            )

            # Filter valid email-like strings
            valid_emails = {email for email in emails if "@" in email and "." in email}

            logger.info(f"Extracted {len(valid_emails)} valid emails from spreadsheet")
            return valid_emails

        except Exception as exc:
            logger.error(f"Error reading spreadsheet: {exc}", exc_info=True)
            raise

    async def _get_all_active_connectors(self, db: AsyncSession) -> List[EmailAuth]:
        """
        Get all active connectors from database.

        Args:
            db: Database session

        Returns:
            List of active connectors
        """
        try:
            stmt = (
                select(EmailAuth)
                .filter(EmailAuth.is_active.is_(True))
                .options(selectinload(EmailAuth.mailboxes))
            )
            result = await db.execute(stmt)
            connectors = result.scalars().all()
            return list(connectors)

        except Exception as exc:
            logger.error(f"Error fetching connectors: {exc}", exc_info=True)
            raise

    async def _get_or_create_mailbox(
        self,
        db: AsyncSession,
        connector: EmailAuth,
        mailbox_method: EmailMailboxMethod,
        app_id: int,
    ) -> EmailMailboxes:
        """
        Get or create mailbox for connector.

        Args:
            db: Database session
            connector: EmailAuth connector
            mailbox_method: Mailbox method instance
            app_id: Application ID

        Returns:
            EmailMailboxes instance
        """
        try:
            mailbox = await mailbox_method.find_by_email(db=db, email=connector.email)

            if mailbox:
                return mailbox

            mailbox_data = {
                "email_auth_id": connector.id,
                "app_id": app_id,
                "email": connector.email,
                "is_active": constant_variable.STATUS_TRUE,
            }

            mailbox = await mailbox_method.create_mailbox(
                db=db, mailbox_data=mailbox_data
            )
            return mailbox

        except Exception as exc:
            logger.error(f"Error getting/creating mailbox: {exc}", exc_info=True)
            raise

    async def _sync_filtered_emails(
        self,
        db: AsyncSession,
        connector: EmailAuth,
        mailbox: EmailMailboxes,
        spreadsheet_emails: Set[str],
        folder: str,
    ) -> Dict[str, int]:
        """
        Sync filtered emails for a connector.

        Args:
            db: Database session
            connector: EmailAuth connector
            mailbox: EmailMailboxes instance
            spreadsheet_emails: Set of spreadsheet email addresses
            folder: Mailbox folder name

        Returns:
            Dictionary with sync results
        """
        try:
            # Initialize Graph client
            graph_client = MicrosoftGraphClient(
                tenant_id=connector.tenant_id,
                client_id=connector.client_id,
                client_secret=connector.client_secret,
            )

            # Get sync state
            sync_state_method = EmailSyncStateMethod(EmailSyncState)
            sync_state = await sync_state_method.find_by_mailbox_and_folder(
                db=db, mailbox_id=mailbox.id, folder=folder
            )

            delta_link = sync_state.delta_link if sync_state else None

            # Fetch filtered messages
            delta_result = await graph_client.get_user_messages_delta_filtered(
                user_email=connector.email,
                filter_emails=list(spreadsheet_emails),
                delta_link=delta_link,
            )

            messages = delta_result.get("value", [])
            new_delta_link = delta_result.get("@odata.deltaLink")

            logger.info(
                f"Found {len(messages)} filtered messages for {connector.email}"
            )

            # Group messages by conversation
            conversations_dict: Dict[str, List[Dict[str, Any]]] = {}
            for message in messages:
                conversation_id = message.get("conversationId")
                if conversation_id:
                    if conversation_id not in conversations_dict:
                        conversations_dict[conversation_id] = []
                    conversations_dict[conversation_id].append(message)

            # Store conversations
            conversation_method = ConversationMethod(Conversations)
            email_method = EmailMethod(Emails)
            attachment_method = EmailAttachmentMethod(EmailAttachments)

            stored_conversations = 0
            stored_emails = 0

            for conversation_id, conv_messages in conversations_dict.items():
                try:
                    # Sort messages by time
                    conv_messages.sort(
                        key=lambda x: x.get("receivedDateTime", ""), reverse=False
                    )

                    first_message = conv_messages[0]
                    last_message = conv_messages[-1]

                    # Extract timestamps
                    sent_datetime = None
                    if first_message.get("sentDateTime"):
                        sent_datetime = datetime.fromisoformat(
                            first_message["sentDateTime"].replace("Z", "+00:00")
                        )

                    received_datetime = None
                    if last_message.get("receivedDateTime"):
                        received_datetime = datetime.fromisoformat(
                            last_message["receivedDateTime"].replace("Z", "+00:00")
                        )

                    # Extract participants
                    participants = self._extract_participants(conv_messages)

                    # Create or update conversation
                    conversation_data = {
                        "microsoft_conversation_id": conversation_id,
                        "subject": first_message.get("subject"),
                        "participants_json": participants,
                        "total_emails": len(conv_messages),
                        "conversation_started_at": sent_datetime,
                        "conversation_ended_at": received_datetime,
                    }

                    conversation = (
                        await conversation_method.find_or_create_by_microsoft_id(
                            db=db,
                            microsoft_conversation_id=conversation_id,
                            conversation_data=conversation_data,
                        )
                    )

                    # Store emails in order
                    for index, message_data in enumerate(conv_messages):
                        await self._store_email(
                            db=db,
                            message_data=message_data,
                            conversation=conversation,
                            message_order=index + 1,
                            email_method=email_method,
                            attachment_method=attachment_method,
                            graph_client=graph_client,
                            mailbox_email=connector.email,
                        )
                        stored_emails += 1

                    # Update conversation count
                    await conversation_method.update_conversation_count(
                        db=db, conversation_id=conversation.id
                    )

                    stored_conversations += 1

                except Exception as exc:
                    logger.error(
                        f"Error storing conversation {conversation_id}: {exc}",
                        exc_info=True,
                    )
                    continue

            # Update sync state
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
                    "email_mailbox_id": mailbox.id,
                    "mailbox_folder": folder,
                    "delta_link": new_delta_link,
                    "sync_status": SyncStatus.INITIAL_SYNC_COMPLETED.value,
                    "last_synced_at": datetime.utcnow(),
                }
                await sync_state_method.create_sync_state(
                    db=db, sync_state_data=sync_state_data
                )

            # Update mailbox last synced
            mailbox_method = EmailMailboxMethod(EmailMailboxes)
            await mailbox_method.update_last_synced(
                db=db, mailbox_id=mailbox.id, synced_at=datetime.utcnow()
            )

            return {
                "conversations": stored_conversations,
                "emails": stored_emails,
            }

        except Exception as exc:
            logger.error(
                f"Error syncing filtered emails for {connector.email}: {exc}",
                exc_info=True,
            )
            raise

    async def _store_email(
        self,
        db: AsyncSession,
        message_data: Dict[str, Any],
        conversation: Conversations,
        message_order: int,
        email_method: EmailMethod,
        attachment_method: EmailAttachmentMethod,
        graph_client: MicrosoftGraphClient,
        mailbox_email: str,
    ):
        """
        Store email in database.

        Args:
            db: Database session
            message_data: Message data from Graph API
            conversation: Conversation object
            message_order: Order of message in conversation
            email_method: Email method instance
            attachment_method: Attachment method instance
            graph_client: Graph client instance
            mailbox_email: Mailbox email address
        """
        message_id = message_data.get("id")

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

        is_reply = message_data.get("isReply", False) or message_order > 1

        email_data = {
            "microsoft_message_id": message_id,
            "conversation_id": conversation.id,
            "sender_email": sender_email,
            "sender_name": sender_name,
            "receiver_string": ", ".join(receiver_list) if receiver_list else None,
            "receiver_json": receiver_list if receiver_list else None,
            "subject": message_data.get("subject"),
            "content_text": content_text,
            "sent_at": sent_datetime,
            "received_at": received_datetime,
            "has_attachment": message_data.get("hasAttachments", False),
            "message_order": message_order,
            "is_reply": is_reply,
        }

        email = await email_method.find_or_create_by_microsoft_id(
            db=db,
            microsoft_message_id=message_id,
            email_data=email_data,
        )

        if message_data.get("hasAttachments"):
            try:
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
            except Exception as exc:
                logger.warning(
                    f"Error fetching attachments for message {message_id}: {exc}"
                )

    def _extract_participants(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Extract all participants from conversation messages.

        Args:
            messages: List of message dictionaries

        Returns:
            Dictionary with participants grouped by role
        """
        participants = {
            "senders": set(),
            "receivers": set(),
            "cc": set(),
        }

        for message in messages:
            sender = message.get("sender", {})
            if sender:
                sender_email = sender.get("emailAddress", {}).get("address")
                if sender_email:
                    participants["senders"].add(sender_email.lower())

            to_recipients = message.get("toRecipients", [])
            for recipient in to_recipients:
                email = recipient.get("emailAddress", {}).get("address")
                if email:
                    participants["receivers"].add(email.lower())

            cc_recipients = message.get("ccRecipients", [])
            for recipient in cc_recipients:
                email = recipient.get("emailAddress", {}).get("address")
                if email:
                    participants["cc"].add(email.lower())

        return {
            "senders": list(participants["senders"]),
            "receivers": list(participants["receivers"]),
            "cc": list(participants["cc"]),
        }
