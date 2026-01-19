"""
OAuth account database model.

This model stores Microsoft OAuth account information including
tokens, expiration times, and account status.
"""

import enum
import json
import logging

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    JSON,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship, foreign

from config.db_config import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from core.utils import constant_variable as constant

logger = logging.getLogger(__name__)


class SafeJSON(TypeDecorator):
    """
    Custom JSON type that handles malformed JSON gracefully.
    Uses Text as base to avoid SQLAlchemy's JSON processor that fails on malformed JSON.
    Returns None if JSON parsing fails instead of raising an exception.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Process value when binding to database."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to serialize JSON value: {str(e)[:100]}. Returning None.")
                return None
        if isinstance(value, str):
            # If it's already a string, validate it's valid JSON
            try:
                json.loads(value)  # Validate
                return value
            except (json.JSONDecodeError, TypeError, ValueError):
                # If invalid, try to serialize it as a string value
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Process JSON value from database, handling malformed JSON."""
        if value is None:
            return None

        # If already parsed (dict/list), return as-is
        if isinstance(value, (dict, list)):
            return value

        # If it's a string, try to parse it
        if isinstance(value, str):
            # Skip if empty string
            if not value.strip():
                return None
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(
                    f"Failed to parse JSON value (email_id may be affected): {str(e)[:100]}. "
                    f"Returning None. Value preview: {str(value)[:100]}"
                )
                return None

        # For any other type, return as-is
        return value


class EmailSourceType(str, enum.Enum):
    """Email source type enum."""

    outlook = "outlook"
    bitrix24 = "bitrix24"
    onedrive = "onedrive"


class EmailMappingTable(str, enum.Enum):
    """Email mapping table enum."""

    request = "request"
    supplier = "supplier"


class EmailAuth(Base, TimestampMixin):
    """
    OAuth account storage model.

    Stores Microsoft OAuth account information for Outlook and OneDrive.
    Supports multiple providers and handles token lifecycle management.
    """

    __tablename__ = "email_auth"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)
    provider = Column(String(255), nullable=constant.STATUS_FALSE, index=constant.STATUS_TRUE)
    tenant_id = Column(String(255), nullable=constant.STATUS_FALSE)
    email = Column(String(255), nullable=constant.STATUS_FALSE, index=constant.STATUS_TRUE)
    email_domain_name = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Domain name extracted from email",
    )
    client_id = Column(String(255), nullable=constant.STATUS_FALSE)
    client_secret = Column(String(255), nullable=constant.STATUS_FALSE)
    is_active = Column(Boolean, default=constant.STATUS_TRUE, nullable=constant.STATUS_FALSE)

    # Relationships
    mailboxes = relationship("EmailMailboxes", back_populates="email_auth")


class EmailMailboxes(Base, TimestampMixin):
    """
    Email mailboxes model for tracking which emails to sync.

    Stores mailbox configuration for email synchronization,
    including app association, email address, sync status, and last sync timestamp.
    """

    __tablename__ = "email_mailboxes"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Mailbox unique identifier",
    )

    email_auth_id = Column(
        Integer,
        ForeignKey("email_auth.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Email auth account ID (FK → email_auth.id)",
    )

    app_id = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Application ID associated with this mailbox",
    )

    email = Column(
        String(255),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
        comment="Email address to sync",
    )
    email_domain_name = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Domain name extracted from email",
    )

    is_active = Column(
        Boolean,
        default=constant.STATUS_TRUE,
        nullable=constant.STATUS_FALSE,
        comment="Whether this mailbox is active for syncing",
    )

    last_synced_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Timestamp of last successful sync",
    )

    # Relationships
    email_auth = relationship("EmailAuth", back_populates="mailboxes")
    sync_states = relationship("EmailSyncState", back_populates="mailbox")


class EmailSyncState(Base, TimestampMixin):
    """
    Email sync state model for tracking synchronization status.
    """

    __tablename__ = "email_sync_state"
    id = Column(Integer, primary_key=constant.STATUS_TRUE)
    email_mailbox_id = Column(
        Integer,
        ForeignKey("email_mailboxes.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    mailbox_folder = Column(String(255), nullable=constant.STATUS_TRUE)
    delta_link = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Microsoft Graph delta link URL (can be 500+ characters)",
    )
    subscription_id = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="Microsoft Graph subscription ID (GUID format)",
    )
    subscription_expiration = Column(DateTime, nullable=constant.STATUS_TRUE)
    sync_status = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Synchronization status",
    )
    last_synced_at = Column(DateTime, nullable=constant.STATUS_TRUE)

    # Relationships
    mailbox = relationship("EmailMailboxes", back_populates="sync_states")


class Conversations(Base, TimestampMixin):
    """
    Conversation model for grouping related emails in a thread.
    """

    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Conversation unique identifier",
    )

    microsoft_conversation_id = Column(
        String(500),
        nullable=constant.STATUS_TRUE,
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Microsoft Message Thread ID (can be 200+ chars)",
    )

    subject = Column(Text, nullable=constant.STATUS_TRUE, comment="Conversation subject")

    participants_json = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="All participants in the conversation as JSON",
    )

    total_emails = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        default=0,
        comment="Total number of messages in conversation",
    )

    conversation_started_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        comment="Timestamp of first message in conversation",
    )

    conversation_ended_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        comment="Timestamp of last message in conversation",
    )

    # Relationships
    # Note: conversation_id in Emails is a String matching microsoft_conversation_id
    # Using lambda with foreign() to mark Emails.conversation_id as the foreign side
    emails = relationship(
        "Emails",
        back_populates="conversation",
        primaryjoin=lambda: Conversations.microsoft_conversation_id
        == foreign(Emails.conversation_id),
    )


class Emails(Base, TimestampMixin):
    """
    Email model for storing email data.
    """

    __tablename__ = "emails"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Email unique identifier",
    )

    microsoft_message_id = Column(
        String(500),
        nullable=constant.STATUS_TRUE,
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Microsoft messageId from Outlook (can be 200+ chars)",
    )

    conversation_id = Column(
        String(500),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Email conversation identifier",
    )

    sender_email = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Email sender address",
    )
    sender_domain_name = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Domain name extracted from sender_email",
    )

    sender_name = Column(
        String(500),
        nullable=constant.STATUS_TRUE,
        comment="Email sender name (can include special chars)",
    )

    receiver_string = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Email receiver address(es) as text",
    )
    receiver_domain_name = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="Domain names extracted from receiver_string (JSON array)",
    )

    receiver_json = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="Email receiver address(es) as JSON",
    )
    receiver_json_domain_name = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="Domain names extracted from receiver_json (JSON array)",
    )

    cc_emails = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="CC recipient emails as JSON array",
    )
    cc_emails_domain_name = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="Domain names extracted from cc_emails (JSON array)",
    )

    bcc_emails = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="BCC recipient emails as JSON array",
    )
    bcc_emails_domain_name = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="Domain names extracted from bcc_emails (JSON array)",
    )

    subject = Column(Text, nullable=constant.STATUS_TRUE, comment="Email subject")

    content_text = Column(
        LONGTEXT,
        nullable=constant.STATUS_TRUE,
        comment="Email body content (plain text) - can be very long",
    )

    sent_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Email sent timestamp",
    )

    received_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Email received timestamp",
    )

    has_attachment = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
        comment="Whether email has attachments",
    )

    message_order = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        comment="Order of message in conversation (calculated)",
    )

    is_reply = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether this email is a reply",
    )

    reply_to_message_id = Column(
        Integer,
        ForeignKey("emails.id"),
        nullable=constant.STATUS_TRUE,
        comment="ID of email this is replying to (FK → emails.id)",
    )

    mapping_id = Column(
        String(100),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="ID mapping to external entities (deal_id, lead_id, etc.)",
    )

    source_type = Column(
        Enum(EmailSourceType, native_enum=False, length=20),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Source type of the email mapping (outlook, bitrix24, onedrive)",
    )

    mapping_table = Column(
        Enum(EmailMappingTable, native_enum=False, length=20),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Target mapping table (request, supplier)",
    )

    # Relationships
    # Note: conversation_id is a String matching Conversations.microsoft_conversation_id
    # Using lambda with foreign() to mark Emails.conversation_id as the foreign side
    conversation = relationship(
        "Conversations",
        back_populates="emails",
        primaryjoin=lambda: foreign(Emails.conversation_id)
        == Conversations.microsoft_conversation_id,
    )
    supplier_emails = relationship(
        "SupplierEmail",
        primaryjoin="Emails.id == SupplierEmail.email_id",
        back_populates="emails",
        lazy="selectin",
    )
    attachments = relationship("EmailAttachments", back_populates="email")
    reply_to = relationship("Emails", remote_side=[id], foreign_keys=[reply_to_message_id])


class EmailAttachments(Base, TimestampMixin):
    """
    Email attachments model for storing attachment metadata and file paths.
    """

    __tablename__ = "email_attachments"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Attachment unique identifier",
    )

    email_id = Column(
        Integer,
        ForeignKey("emails.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
        comment="Email ID (FK → emails.id)",
    )

    attachment_id = Column(
        String(500),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Attachment ID from Outlook (can be long)",
    )

    filename = Column(String(500), nullable=constant.STATUS_TRUE, comment="Attachment filename")

    content_type = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="Attachment content type (MIME type)",
    )

    size = Column(
        BigInteger,
        nullable=constant.STATUS_TRUE,
        comment="Attachment size in bytes (supports files > 2GB)",
    )

    storage_path = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Storage path (S3 URL or file path - can be very long)",
    )

    is_inline = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
        comment="Whether attachment is inline",
    )

    last_modified = Column(
        DateTime, nullable=constant.STATUS_TRUE, comment="Last modified timestamp"
    )

    # Relationships
    email = relationship("Emails", back_populates="attachments")
