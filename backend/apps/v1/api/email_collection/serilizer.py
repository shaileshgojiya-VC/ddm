"""
Marshmallow serializers for email collection.
"""

from datetime import datetime
from typing import Optional

from marshmallow import Schema, fields


class ConnectorSerializer(Schema):
    """Email connector serializer."""

    id = fields.Int(data_key="id", required=True)
    provider = fields.Str(data_key="provider", required=True)
    tenant_id = fields.Str(data_key="tenant_id", required=True)
    client_id = fields.Str(data_key="client_id", required=True)
    email = fields.Email(data_key="email", required=True)
    is_active = fields.Bool(data_key="is_active", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class MailboxSerializer(Schema):
    """Mailbox serializer."""

    id = fields.Int(data_key="id", required=True)
    email_auth_id = fields.Int(data_key="email_auth_id", required=True)
    app_id = fields.Int(data_key="app_id", required=True)
    email = fields.Email(data_key="email", required=True)
    is_active = fields.Bool(data_key="is_active", required=True)
    last_synced_at = fields.DateTime(
        data_key="last_synced_at", required=False, allow_none=True
    )
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class SubscriptionSerializer(Schema):
    """Subscription serializer."""

    id = fields.Int(data_key="id", required=True)
    email_mailbox_id = fields.Int(data_key="email_mailbox_id", required=True)
    mailbox_folder = fields.Str(data_key="mailbox_folder", required=True)
    subscription_id = fields.Str(
        data_key="subscription_id", required=False, allow_none=True
    )
    subscription_expiration = fields.DateTime(
        data_key="subscription_expiration", required=False, allow_none=True
    )
    sync_status = fields.Str(data_key="sync_status", required=True)
    last_synced_at = fields.DateTime(
        data_key="last_synced_at", required=False, allow_none=True
    )
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class EmailSerializer(Schema):
    """Email serializer."""

    id = fields.Int(data_key="id", required=True)
    microsoft_message_id = fields.Str(data_key="microsoft_message_id", required=True)
    conversation_id = fields.Int(
        data_key="conversation_id", required=False, allow_none=True
    )
    sender_email = fields.Str(data_key="sender_email", required=False, allow_none=True)
    sender_name = fields.Str(data_key="sender_name", required=False, allow_none=True)
    subject = fields.Str(data_key="subject", required=False, allow_none=True)
    sent_at = fields.DateTime(data_key="sent_at", required=False, allow_none=True)
    received_at = fields.DateTime(
        data_key="received_at", required=False, allow_none=True
    )
    has_attachment = fields.Bool(data_key="has_attachment", required=True)
    is_reply = fields.Bool(data_key="is_reply", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class ConversationSerializer(Schema):
    """Conversation serializer."""

    id = fields.Int(data_key="id", required=True)
    microsoft_conversation_id = fields.Str(
        data_key="microsoft_conversation_id", required=False, allow_none=True
    )
    subject = fields.Str(data_key="subject", required=False, allow_none=True)
    participants_json = fields.Dict(
        data_key="participants_json", required=False, allow_none=True
    )
    total_emails = fields.Int(data_key="total_emails", required=True)
    conversation_started_at = fields.DateTime(
        data_key="conversation_started_at", required=False, allow_none=True
    )
    conversation_ended_at = fields.DateTime(
        data_key="conversation_ended_at", required=False, allow_none=True
    )
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class AttachmentSerializer(Schema):
    """Attachment serializer."""

    id = fields.Int(data_key="id", required=True)
    email_id = fields.Int(data_key="email_id", required=True)
    attachment_id = fields.Str(
        data_key="attachment_id", required=False, allow_none=True
    )
    filename = fields.Str(data_key="filename", required=False, allow_none=True)
    content_type = fields.Str(data_key="content_type", required=False, allow_none=True)
    size = fields.Int(data_key="size", required=False, allow_none=True)
    storage_path = fields.Str(data_key="storage_path", required=False, allow_none=True)
    is_inline = fields.Bool(data_key="is_inline", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class EmailProcessingSerializer(Schema):
    """Email processing serializer."""

    conversation_id = fields.Int(
        data_key="conversation_id", required=True, allow_none=False
    )
    sent_at = fields.DateTime(data_key="sent_at", required=True, allow_none=False)
    recevied_at = fields.DateTime(
        data_key="recevied_at", required=True, allow_none=False
    )
    subject = fields.Str(data_key="subject", required=True, allow_none=True)
    context = fields.Str(data_key="context", required=True, allow_none=True)
