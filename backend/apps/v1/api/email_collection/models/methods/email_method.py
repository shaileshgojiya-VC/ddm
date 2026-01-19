"""
Email collection database methods for email-related database operations.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import select, func, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.v1.api.email_collection.models.model import (
    EmailAuth,
    EmailMailboxes,
    EmailSyncState,
    Conversations,
    Emails,
    EmailAttachments,
)
from core.utils import constant_variable as constant

logger = logging.getLogger(__name__)


class EmailAuthMethod:
    """
    Email auth database methods for connector-related database queries.
    """

    def __init__(self, model):
        self.model = model

    async def create_connector(
        self, db: AsyncSession, connector_data: dict
    ) -> EmailAuth:
        """
        Create a new email connector.

        Args:
            db: Database session
            connector_data: Dictionary containing connector data

        Returns:
            Created EmailAuth instance
        """
        try:
            logger.info("STEP 1: Creating email connector")
            new_connector = self.model(**connector_data)
            db.add(new_connector)
            await db.flush()
            await db.refresh(new_connector)
            await db.commit()
            logger.info(f"STEP 2: Email connector created with ID: {new_connector.id}")
            return new_connector
        except SQLAlchemyError as exc:
            logger.error(f"Database error creating connector: {exc}", exc_info=True)
            await db.rollback()
            raise

    async def find_by_id(
        self, db: AsyncSession, connector_id: int
    ) -> Optional[EmailAuth]:
        """
        Find connector by ID.

        Args:
            db: Database session
            connector_id: Connector ID

        Returns:
            EmailAuth instance or None
        """
        try:
            stmt = select(self.model).filter(self.model.id == connector_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding connector: {exc}", exc_info=True)
            raise

    async def find_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[EmailAuth]:
        """
        Find connector by email.

        Args:
            db: Database session
            email: Email address

        Returns:
            EmailAuth instance or None
        """
        try:
            stmt = select(self.model).filter(self.model.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding connector by email: {exc}", exc_info=True)
            raise

    async def list_connectors(
        self,
        db: AsyncSession,
        provider: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[EmailAuth], int]:
        """
        List connectors with filters and pagination.

        Args:
            db: Database session
            provider: Filter by provider
            page: Page number
            limit: Page limit

        Returns:
            Tuple of (list of connectors, total count)
        """
        try:
            logger.info("STEP 1: Starting list connectors query")
            stmt = select(self.model)

            if provider:
                stmt = stmt.filter(self.model.provider == provider)

            count_stmt = select(func.count(self.model.id))
            if provider:
                count_stmt = count_stmt.filter(self.model.provider == provider)

            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)
            stmt = stmt.order_by(self.model.created_at.desc())

            result = await db.execute(stmt)
            connectors = result.scalars().all()

            logger.info(f"STEP 2: Found {len(connectors)} connectors")
            return list(connectors), total
        except SQLAlchemyError as exc:
            logger.error(f"Database error listing connectors: {exc}", exc_info=True)
            raise


class EmailMailboxMethod:
    """
    Email mailbox database methods for mailbox-related database queries.
    """

    def __init__(self, model):
        self.model = model

    async def create_mailbox(
        self, db: AsyncSession, mailbox_data: dict
    ) -> EmailMailboxes:
        """
        Create a new mailbox.

        Args:
            db: Database session
            mailbox_data: Dictionary containing mailbox data

        Returns:
            Created EmailMailboxes instance
        """
        try:
            logger.info("STEP 1: Creating email mailbox")
            new_mailbox = self.model(**mailbox_data)
            db.add(new_mailbox)
            await db.flush()
            await db.refresh(new_mailbox)
            await db.commit()
            logger.info(f"STEP 2: Email mailbox created with ID: {new_mailbox.id}")
            return new_mailbox
        except SQLAlchemyError as exc:
            logger.error(f"Database error creating mailbox: {exc}", exc_info=True)
            await db.rollback()
            raise

    async def find_by_id(
        self, db: AsyncSession, mailbox_id: int
    ) -> Optional[EmailMailboxes]:
        """
        Find mailbox by ID.

        Args:
            db: Database session
            mailbox_id: Mailbox ID

        Returns:
            EmailMailboxes instance or None
        """
        try:
            stmt = (
                select(self.model)
                .options(selectinload(self.model.email_auth))
                .filter(self.model.id == mailbox_id)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding mailbox: {exc}", exc_info=True)
            raise

    async def find_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[EmailMailboxes]:
        """
        Find mailbox by email.

        Args:
            db: Database session
            email: Email address

        Returns:
            EmailMailboxes instance or None
        """
        try:
            stmt = select(self.model).filter(self.model.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding mailbox by email: {exc}", exc_info=True)
            raise

    async def list_mailboxes(
        self,
        db: AsyncSession,
        email_auth_id: Optional[int] = None,
        app_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[EmailMailboxes], int]:
        """
        List mailboxes with filters and pagination.

        Args:
            db: Database session
            email_auth_id: Filter by email auth ID
            app_id: Filter by app ID
            page: Page number
            limit: Page limit

        Returns:
            Tuple of (list of mailboxes, total count)
        """
        try:
            logger.info("STEP 1: Starting list mailboxes query")
            stmt = select(self.model).options(selectinload(self.model.email_auth))

            if email_auth_id:
                stmt = stmt.filter(self.model.email_auth_id == email_auth_id)
            if app_id:
                stmt = stmt.filter(self.model.app_id == app_id)

            count_stmt = select(func.count(self.model.id))
            if email_auth_id:
                count_stmt = count_stmt.filter(
                    self.model.email_auth_id == email_auth_id
                )
            if app_id:
                count_stmt = count_stmt.filter(self.model.app_id == app_id)

            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)
            stmt = stmt.order_by(self.model.created_at.desc())

            result = await db.execute(stmt)
            mailboxes = result.scalars().all()

            logger.info(f"STEP 2: Found {len(mailboxes)} mailboxes")
            return list(mailboxes), total
        except SQLAlchemyError as exc:
            logger.error(f"Database error listing mailboxes: {exc}", exc_info=True)
            raise

    async def update_last_synced(
        self, db: AsyncSession, mailbox_id: int, synced_at: datetime
    ) -> bool:
        """
        Update last synced timestamp for mailbox.

        Args:
            db: Database session
            mailbox_id: Mailbox ID
            synced_at: Sync timestamp

        Returns:
            True if updated, False otherwise
        """
        try:
            stmt = select(self.model).filter(self.model.id == mailbox_id)
            result = await db.execute(stmt)
            mailbox = result.scalar_one_or_none()

            if mailbox:
                mailbox.last_synced_at = synced_at
                await db.commit()
                return True
            return False
        except SQLAlchemyError as exc:
            logger.error(f"Database error updating last synced: {exc}", exc_info=True)
            await db.rollback()
            return False


class EmailSyncStateMethod:
    """
    Email sync state database methods for sync state-related database queries.
    """

    def __init__(self, model):
        self.model = model

    async def create_sync_state(
        self, db: AsyncSession, sync_state_data: dict
    ) -> EmailSyncState:
        """
        Create a new sync state.

        Args:
            db: Database session
            sync_state_data: Dictionary containing sync state data

        Returns:
            Created EmailSyncState instance
        """
        try:
            logger.info("STEP 1: Creating email sync state")
            new_sync_state = self.model(**sync_state_data)
            db.add(new_sync_state)
            await db.flush()
            await db.refresh(new_sync_state)
            await db.commit()
            logger.info(f"STEP 2: Email sync state created with ID: {new_sync_state.id}")
            return new_sync_state
        except SQLAlchemyError as exc:
            logger.error(f"Database error creating sync state: {exc}", exc_info=True)
            await db.rollback()
            raise

    async def find_by_mailbox_and_folder(
        self, db: AsyncSession, mailbox_id: int, folder: str
    ) -> Optional[EmailSyncState]:
        """
        Find sync state by mailbox ID and folder.

        Args:
            db: Database session
            mailbox_id: Mailbox ID
            folder: Mailbox folder name

        Returns:
            EmailSyncState instance or None
        """
        try:
            stmt = (
                select(self.model)
                .filter(self.model.email_mailbox_id == mailbox_id)
                .filter(self.model.mailbox_folder == folder)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error finding sync state: {exc}", exc_info=True
            )
            raise

    async def find_by_subscription_id(
        self, db: AsyncSession, subscription_id: str
    ) -> Optional[EmailSyncState]:
        """
        Find sync state by subscription ID.

        Args:
            db: Database session
            subscription_id: Microsoft subscription ID

        Returns:
            EmailSyncState instance or None
        """
        try:
            stmt = (
                select(self.model)
                .options(selectinload(self.model.mailbox))
                .filter(self.model.subscription_id == subscription_id)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error finding sync state by subscription: {exc}", exc_info=True
            )
            raise

    async def update_sync_state(
        self,
        db: AsyncSession,
        sync_state_id: int,
        update_data: dict,
    ) -> Optional[EmailSyncState]:
        """
        Update sync state.

        Args:
            db: Database session
            sync_state_id: Sync state ID
            update_data: Dictionary containing update data

        Returns:
            Updated EmailSyncState instance or None
        """
        try:
            stmt = select(self.model).filter(self.model.id == sync_state_id)
            result = await db.execute(stmt)
            sync_state = result.scalar_one_or_none()

            if not sync_state:
                return None

            for key, value in update_data.items():
                if value is not None and hasattr(sync_state, key):
                    setattr(sync_state, key, value)

            await db.commit()
            await db.refresh(sync_state)
            return sync_state
        except SQLAlchemyError as exc:
            logger.error(f"Database error updating sync state: {exc}", exc_info=True)
            await db.rollback()
            raise


class ConversationMethod:
    """
    Conversation database methods for conversation-related database queries.
    """

    def __init__(self, model):
        self.model = model

    async def find_or_create_by_microsoft_id(
        self, db: AsyncSession, microsoft_conversation_id: str, conversation_data: dict
    ) -> Conversations:
        """
        Find or create conversation by Microsoft conversation ID.

        Args:
            db: Database session
            microsoft_conversation_id: Microsoft conversation ID
            conversation_data: Dictionary containing conversation data

        Returns:
            Conversations instance
        """
        try:
            stmt = select(self.model).filter(
                self.model.microsoft_conversation_id == microsoft_conversation_id
            )
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                return conversation

            new_conversation = self.model(**conversation_data)
            db.add(new_conversation)
            await db.flush()
            await db.refresh(new_conversation)
            await db.commit()
            return new_conversation
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding/creating conversation: {exc}", exc_info=True)
            await db.rollback()
            raise

    async def update_conversation_count(
        self, db: AsyncSession, conversation_id: int
    ) -> bool:
        """
        Update total email count for conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            True if updated, False otherwise
        """
        try:
            count_stmt = select(func.count(Emails.id)).filter(
                Emails.conversation_id == conversation_id
            )
            result = await db.execute(count_stmt)
            count = result.scalar() or 0

            stmt = select(self.model).filter(self.model.id == conversation_id)
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.total_emails = count
                await db.commit()
                return True
            return False
        except SQLAlchemyError as exc:
            logger.error(f"Database error updating conversation count: {exc}", exc_info=True)
            await db.rollback()
            return False


class EmailMethod:
    """
    Email database methods for email-related database queries.
    """

    def __init__(self, model):
        self.model = model

    async def find_or_create_by_microsoft_id(
        self, db: AsyncSession, microsoft_message_id: str, email_data: dict
    ) -> Emails:
        """
        Find or create email by Microsoft message ID.

        Args:
            db: Database session
            microsoft_message_id: Microsoft message ID
            email_data: Dictionary containing email data

        Returns:
            Emails instance
        """
        try:
            stmt = select(self.model).filter(
                self.model.microsoft_message_id == microsoft_message_id
            )
            result = await db.execute(stmt)
            email = result.scalar_one_or_none()

            if email:
                return email

            new_email = self.model(**email_data)
            db.add(new_email)
            await db.flush()
            await db.refresh(new_email)
            await db.commit()
            return new_email
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding/creating email: {exc}", exc_info=True)
            await db.rollback()
            raise

    async def list_emails(
        self,
        db: AsyncSession,
        mailbox_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Emails], int]:
        """
        List emails with filters and pagination.

        Args:
            db: Database session
            mailbox_id: Filter by mailbox ID (requires join)
            conversation_id: Filter by conversation ID
            search: Search in subject or sender
            page: Page number
            limit: Page limit

        Returns:
            Tuple of (list of emails, total count)
        """
        try:
            logger.info("STEP 1: Starting list emails query")
            stmt = select(self.model).options(selectinload(self.model.conversation))

            if conversation_id:
                stmt = stmt.filter(self.model.conversation_id == conversation_id)

            if search:
                search_pattern = f"%{search}%"
                stmt = stmt.filter(
                    or_(
                        self.model.subject.ilike(search_pattern),
                        self.model.sender_email.ilike(search_pattern),
                    )
                )

            count_stmt = select(func.count(self.model.id))
            if conversation_id:
                count_stmt = count_stmt.filter(
                    self.model.conversation_id == conversation_id
                )
            if search:
                search_pattern = f"%{search}%"
                count_stmt = count_stmt.filter(
                    or_(
                        self.model.subject.ilike(search_pattern),
                        self.model.sender_email.ilike(search_pattern),
                    )
                )

            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)
            # MySQL doesn't support NULLS LAST, so we use COALESCE to put NULLs at the end
            # For DESC order, we use a very old date for NULLs so they sort last
            stmt = stmt.order_by(
                func.coalesce(self.model.received_at, datetime(1970, 1, 1)).desc()
            )

            result = await db.execute(stmt)
            emails = result.scalars().all()

            logger.info(f"STEP 2: Found {len(emails)} emails")
            return list(emails), total
        except SQLAlchemyError as exc:
            logger.error(f"Database error listing emails: {exc}", exc_info=True)
            raise

    async def find_emails_by_email_address(
        self,
        db: AsyncSession,
        email_address: str,
    ) -> List[Emails]:
        """
        Find all emails where the given email address is sender or receiver.

        Args:
            db: Database session
            email_address: Email address to search for

        Returns:
            List of Emails instances
        """
        try:
            logger.info(f"STEP 1: Finding emails for email address: {email_address}")
            email_lower = email_address.lower().strip()

            # Search in sender_email and receiver_json
            # For receiver_json, we need to check if email is in the JSON array
            stmt = (
                select(self.model)
                .options(selectinload(self.model.conversation))
                .filter(
                    or_(
                        func.lower(self.model.sender_email) == email_lower,
                        self.model.receiver_string.ilike(f"%{email_lower}%"),
                    )
                )
                .order_by(
                    func.coalesce(self.model.received_at, datetime(1970, 1, 1)).desc()
                )
            )

            result = await db.execute(stmt)
            emails = result.scalars().all()

            # Filter by receiver_json in Python (more reliable than SQL JSON functions)
            filtered_emails = []
            for email in emails:
                # Check sender
                if email.sender_email and email.sender_email.lower() == email_lower:
                    filtered_emails.append(email)
                    continue
                
                # Check receiver_json
                if email.receiver_json:
                    receiver_emails = [
                        str(rec).lower() for rec in email.receiver_json
                    ]
                    if email_lower in receiver_emails:
                        filtered_emails.append(email)
                        continue
                
                # Check receiver_string as fallback
                if email.receiver_string and email_lower in email.receiver_string.lower():
                    filtered_emails.append(email)

            logger.info(f"STEP 2: Found {len(filtered_emails)} emails for {email_address}")
            return filtered_emails
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error finding emails by email address: {exc}", exc_info=True
            )
            raise


class EmailAttachmentMethod:
    """
    Email attachment database methods for attachment-related database queries.
    """

    def __init__(self, model):
        self.model = model

    async def create_attachment(
        self, db: AsyncSession, attachment_data: dict
    ) -> EmailAttachments:
        """
        Create a new attachment.

        Args:
            db: Database session
            attachment_data: Dictionary containing attachment data

        Returns:
            Created EmailAttachments instance
        """
        try:
            logger.info("STEP 1: Creating email attachment")
            new_attachment = self.model(**attachment_data)
            db.add(new_attachment)
            await db.flush()
            await db.refresh(new_attachment)
            await db.commit()
            logger.info(f"STEP 2: Email attachment created with ID: {new_attachment.id}")
            return new_attachment
        except SQLAlchemyError as exc:
            logger.error(f"Database error creating attachment: {exc}", exc_info=True)
            await db.rollback()
            raise

    async def find_by_email_id(
        self, db: AsyncSession, email_id: int
    ) -> List[EmailAttachments]:
        """
        Find attachments by email ID.

        Args:
            db: Database session
            email_id: Email ID

        Returns:
            List of EmailAttachments instances
        """
        try:
            stmt = select(self.model).filter(self.model.email_id == email_id)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            logger.error(f"Database error finding attachments: {exc}", exc_info=True)
            raise

