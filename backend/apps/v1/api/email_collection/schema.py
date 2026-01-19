"""
Email collection Pydantic schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class ConnectorCreateRequest(BaseModel):
    """Request schema for creating email connector."""

    provider: str = Field(..., description="Email provider (outlook, gmail, exchange)")
    tenant_id: str = Field(..., description="Azure tenant ID")
    client_id: str = Field(..., description="Azure client ID")
    client_secret: str = Field(..., description="Azure client secret")
    email: EmailStr = Field(..., description="Email address for the connector")


class ConnectorResponse(BaseModel):
    """Response schema for email connector."""

    id: int
    provider: str
    tenant_id: str
    client_id: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MailboxCreateRequest(BaseModel):
    """Request schema for creating mailbox."""

    email_auth_id: int = Field(..., description="Email auth connector ID")
    app_id: int = Field(..., description="Application ID")
    email: EmailStr = Field(..., description="Email address to sync")


class MailboxResponse(BaseModel):
    """Response schema for mailbox."""

    id: int
    email_auth_id: int
    app_id: int
    email: str
    is_active: bool
    last_synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCreateRequest(BaseModel):
    """Request schema for creating webhook subscription."""

    email_mailbox_id: int = Field(..., description="Mailbox ID")
    mailbox_folder: str = Field(default="Inbox", description="Mailbox folder name")
    notification_url: str = Field(..., description="Webhook notification URL")


class SubscriptionResponse(BaseModel):
    """Response schema for subscription."""

    id: int
    email_mailbox_id: int
    mailbox_folder: str
    subscription_id: Optional[str]
    subscription_expiration: Optional[datetime]
    sync_status: str
    last_synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookNotificationRequest(BaseModel):
    """Request schema for webhook notification."""

    value: List[dict] = Field(..., description="List of notification items")


class EmailListQueryParams(BaseModel):
    """Query parameters for listing emails."""

    mailbox_id: Optional[int] = None
    conversation_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    search: Optional[str] = None


class EmailResponse(BaseModel):
    """Response schema for email."""

    id: int
    microsoft_message_id: str
    conversation_id: Optional[int]
    sender_email: Optional[str]
    sender_name: Optional[str]
    subject: Optional[str]
    sent_at: Optional[datetime]
    received_at: Optional[datetime]
    has_attachment: bool
    is_reply: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response schema for conversation."""

    id: int
    microsoft_conversation_id: Optional[str]
    subject: Optional[str]
    participants_json: Optional[dict]
    total_emails: int
    conversation_started_at: Optional[datetime]
    conversation_ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    """Response schema for attachment."""

    id: int
    email_id: int
    attachment_id: Optional[str]
    filename: Optional[str]
    content_type: Optional[str]
    size: Optional[int]
    storage_path: Optional[str]
    is_inline: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectorListQueryParams(BaseModel):
    """Query parameters for listing connectors."""

    provider: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class MailboxListQueryParams(BaseModel):
    """Query parameters for listing mailboxes."""

    email_auth_id: Optional[int] = None
    app_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class SpreadsheetSyncRequest(BaseModel):
    """Request schema for spreadsheet-based email sync."""

    app_id: int = Field(..., description="Application ID")
    email_column: Optional[str] = Field(
        default="email", description="Column name containing email addresses"
    )
    folder: str = Field(default="Inbox", description="Mailbox folder name")


class EmailProcessingRequest(BaseModel):
    """Request schema for email processing."""

    conversation_id: int = Field(..., description="Conversation ID")
    sent_at: datetime = Field(..., description="Sent at")
    received_at: datetime = Field(..., description="Received at")
    subject: str = Field(..., description="Subject")
    context: str = Field(..., description="Context")
