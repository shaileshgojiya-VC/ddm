"""
Email collection attributes and constants.
"""

from enum import Enum


class SyncStatus(str, Enum):
    """Email sync status values."""

    INITIAL_SYNC_PENDING = "INITIAL_SYNC_PENDING"
    INITIAL_SYNC_IN_PROGRESS = "INITIAL_SYNC_IN_PROGRESS"
    INITIAL_SYNC_COMPLETED = "INITIAL_SYNC_COMPLETED"
    SYNC_ACTIVE = "SYNC_ACTIVE"
    SYNC_PAUSED = "SYNC_PAUSED"
    SYNC_ERROR = "SYNC_ERROR"


class MailboxFolder(str, Enum):
    """Standard mailbox folder names."""

    INBOX = "Inbox"
    SENT = "SentItems"
    DRAFTS = "Drafts"
    DELETED = "DeletedItems"
    ARCHIVE = "Archive"


class ChangeType(str, Enum):
    """Webhook change types."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
