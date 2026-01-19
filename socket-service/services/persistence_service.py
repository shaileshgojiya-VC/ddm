"""
Persistence service for database operations.
Reuses existing database methods and adds read receipt persistence.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, List

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.db import SessionLocal
from apps.v1.api.chat.models.model import (
    message_chats,
    message_sessions,
    message_groups,
    message_read_receipts,
)
from apps.v1.api.chat.models.methods import (
    MessageChatMethod,
    MessageSessionMethod,
    UserMethod,
    ReadReceiptMethod,
)
from apps.v1.api.auth.models.model import Users

logger = logging.getLogger(__name__)


class PersistenceService:
    """Service for persisting messages and read receipts to database."""

    def __init__(self):
        self.message_chat_method = MessageChatMethod(message_chats)
        self.message_session_method = MessageSessionMethod(message_sessions)
        self.user_method = UserMethod(Users)
        self.read_receipt_method = ReadReceiptMethod(message_read_receipts)

    async def create_or_get_room_between_users(
        self, sender_id: int, receiver_id: int, session_id: str
    ) -> Dict:
        """
        Create a new room or get existing room between two users.

        Args:
            sender_id: Sender user ID
            receiver_id: Receiver user ID
            session_id: Socket.IO session ID

        Returns:
            Dict with room_id, session_uuid, and room status
        """
        logger.info(
            f"STEP 1: Creating or getting room between users {sender_id} and {receiver_id}"
        )

        db = SessionLocal()
        try:
            # Check if room already exists between these two users
            existing_message = (
                self.message_chat_method.find_existing_message_between_users(
                    db, sender_id, receiver_id
                )
            )

            if existing_message:
                # Room already exists, get existing room_id
                existing_room_id = existing_message.room_id

                # If room_id is still an integer (old data), find the session UUID
                if isinstance(existing_room_id, int) or (
                    isinstance(existing_room_id, str) and existing_room_id.isdigit()
                ):
                    # Old format - find session by integer room_id
                    existing_session = self.message_session_method.find_by_id(
                        db, int(existing_room_id)
                    )
                    if existing_session:
                        # Update to use UUID as room_id
                        room_id_uuid = existing_session.uuid
                        self.message_session_method.update_room_id(
                            db, existing_session, room_id_uuid
                        )
                        # Update all messages in this room to use UUID
                        self.message_chat_method.update_messages_by_room_id(
                            db, existing_room_id, room_id_uuid
                        )
                        db.commit()
                        session_uuid = room_id_uuid
                    else:
                        # Create new session with UUID as room_id
                        new_session = self.message_session_method.create(db)
                        session_uuid = new_session.uuid
                        self.message_session_method.update_room_id(
                            db, new_session, session_uuid
                        )
                        # Update all messages to use new UUID room_id
                        self.message_chat_method.update_messages_by_room_id(
                            db, existing_room_id, session_uuid
                        )
                        db.commit()
                        room_id_uuid = session_uuid
                else:
                    # Already using UUID format
                    room_id_uuid = existing_room_id
                    # Get session for this room
                    existing_session = self.message_session_method.find_by_room_id(
                        db, room_id_uuid
                    )
                    if existing_session:
                        session_uuid = existing_session.uuid
                    else:
                        # Create new session for existing room
                        new_session = self.message_session_method.create(
                            db, room_id=room_id_uuid
                        )
                        session_uuid = new_session.uuid

                logger.info(
                    f"STEP 2: Found existing room {room_id_uuid} between users {sender_id} and {receiver_id}"
                )

                return {
                    "room_id": room_id_uuid,
                    "session_uuid": session_uuid,
                    "status": "existing",
                }

            # Create new room between these two users
            logger.info("STEP 2: Creating new room")
            new_session = self.message_session_method.create(db)

            # Use session UUID as room_id (store UUID instead of integer)
            session_uuid = new_session.uuid
            self.message_session_method.update_room_id(db, new_session, session_uuid)

            logger.info(
                f"STEP 3: Created new room {session_uuid} between users {sender_id} and {receiver_id}"
            )

            return {
                "room_id": session_uuid,
                "session_uuid": session_uuid,
                "status": "new",
            }

        except Exception as e:
            db.rollback()
            logger.error(f"STEP 3: Error creating/getting room: {str(e)}")
            raise
        finally:
            db.close()

    async def create_or_get_room_for_group(
        self, group_id: int, session_id: str
    ) -> Dict:
        """
        Create a new room or get existing room for a group.

        Args:
            group_id: Group ID (integer)
            session_id: Socket.IO session ID

        Returns:
            Dict with room_id, session_uuid, and room status
        """
        logger.info(f"STEP 1: Creating or getting room for group {group_id}")

        db = SessionLocal()
        try:
            # Check if room already exists for this group
            existing_session = (
                db.query(message_sessions)
                .filter(message_sessions.group_id == group_id)
                .first()
            )

            if existing_session:
                # Room already exists for this group
                room_id_value = existing_session.room_id

                # Convert to string for validation
                room_id_str = str(room_id_value) if room_id_value else ""

                # Check if room_id is a valid UUID (36 chars with 4 hyphens)
                is_valid_uuid = (
                    room_id_str
                    and len(room_id_str) == 36
                    and room_id_str.count("-") == 4
                )

                is_numeric = room_id_str.isdigit() if room_id_str else False

                if not is_valid_uuid or is_numeric:
                    # Old format - room_id is integer or invalid, convert to UUID
                    room_id_uuid = existing_session.uuid
                    self.message_session_method.update_room_id(
                        db, existing_session, room_id_uuid
                    )

                    # Update all messages in this group to use the new UUID room_id
                    if room_id_value:
                        old_room_id = str(room_id_value)
                        self.message_chat_method.update_messages_by_room_id(
                            db, old_room_id, room_id_uuid
                        )

                    db.commit()
                    logger.info(
                        f"STEP 2: Converted room_id from {room_id_value} to UUID {room_id_uuid} for group {group_id}"
                    )
                else:
                    # Already using UUID format
                    room_id_uuid = room_id_str

                logger.info(
                    f"STEP 2: Found existing room {room_id_uuid} for group {group_id}"
                )

                return {
                    "room_id": room_id_uuid,
                    "session_uuid": existing_session.uuid,
                    "status": "existing",
                }

            # Create new room for this group
            logger.info("STEP 2: Creating new room for group")
            new_session = self.message_session_method.create(db)
            session_uuid = new_session.uuid

            # Use session UUID as room_id
            self.message_session_method.update_room_id(db, new_session, session_uuid)

            # Set group_id in session
            new_session.group_id = group_id
            db.commit()
            db.refresh(new_session)

            logger.info(
                f"STEP 3: Created new room {session_uuid} for group {group_id}"
            )

            return {
                "room_id": session_uuid,
                "session_uuid": session_uuid,
                "status": "new",
            }

        except Exception as e:
            db.rollback()
            logger.error(f"STEP 3: Error creating/getting room for group: {str(e)}")
            raise
        finally:
            db.close()

    async def save_message(
        self,
        room_id: str,
        sender_id: int,
        receiver_id: Optional[int],
        message: Optional[str],
        message_type: str,
        attachments: Optional[list],
        session_id: str,
    ) -> Dict:
        """
        Save message to database.

        Args:
            room_id: Room identifier (UUID)
            sender_id: Sender user ID
            receiver_id: Receiver user ID (optional)
            message: Message content (optional for non-text messages)
            message_type: Message type (text, image, video, file, audio)
            attachments: List of attachment objects
            session_id: Socket.IO session ID

        Returns:
            Dict with message data including uuid
        """
        logger.info(f"STEP 1: Saving message to room {room_id}")

        db = SessionLocal()
        try:
            # Get sender UUID
            sender_user = self.user_method.find_by_id(db, sender_id)
            sender_uuid = sender_user.uuid if sender_user else None

            # Get receiver UUID
            receiver_uuid = None
            if receiver_id:
                receiver_user = self.user_method.find_by_id(db, receiver_id)
                receiver_uuid = receiver_user.uuid if receiver_user else None

            logger.info("STEP 2: Creating message record")

            new_message = message_chats(
                room_id=room_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                message=message,
                message_type=message_type or "text",
                attachments=attachments if attachments else None,
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            logger.info(f"STEP 3: Saved message {new_message.uuid} to room {room_id}")

            return {
                "uuid": new_message.uuid,
                "room_id": room_id,
                "sender_id": sender_uuid if sender_uuid else None,
                "receiver_id": receiver_uuid if receiver_uuid else None,
                "message": message,
                "message_type": message_type or "text",
                "attachments": attachments if attachments else [],
                "created_at": (
                    new_message.created_at.isoformat()
                    if new_message.created_at
                    else None
                ),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"STEP 3: Error saving message: {str(e)}")
            raise
        finally:
            db.close()

    async def save_group_message(
        self,
        room_id: str,
        sender_id: int,
        group_id: int,
        receiver_ids: List[int],
        message: Optional[str],
        message_type: str,
        attachments: Optional[list],
        session_id: str,
    ) -> Dict:
        """
        Save group message to database.

        Args:
            room_id: Room identifier (UUID)
            sender_id: Sender user ID
            group_id: Group ID
            receiver_ids: List of receiver user IDs (group members excluding sender)
            message: Message content (optional for non-text messages)
            message_type: Message type (text, image, video, file, audio)
            attachments: List of attachment objects
            session_id: Socket.IO session ID

        Returns:
            Dict with message data including uuid
        """
        logger.info(f"STEP 1: Saving group message to room {room_id}")

        db = SessionLocal()
        try:
            # Get sender UUID
            sender_user = self.user_method.find_by_id(db, sender_id)
            sender_uuid = sender_user.uuid if sender_user else None

            # Get receiver UUIDs for response
            receiver_uuids = []
            for receiver_id in receiver_ids:
                receiver_user = self.user_method.find_by_id(db, receiver_id)
                if receiver_user:
                    receiver_uuids.append(receiver_user.uuid)

            # Prepare attachments JSON to store receiver_ids list
            attachments_data = attachments if attachments else []
            attachments_metadata = {
                "receiver_ids": receiver_ids,
                "files": attachments_data,
            }

            logger.info("STEP 2: Creating group message record")

            new_message = message_chats(
                room_id=room_id,
                sender_id=sender_id,
                receiver_id=None,  # Set to None for group messages
                message=message,
                message_type=message_type or "text",
                attachments=attachments_metadata,
                group_id=group_id,
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            logger.info(
                f"STEP 3: Saved group message {new_message.uuid} to group {group_id}"
            )

            return {
                "uuid": new_message.uuid,
                "room_id": room_id,
                "sender_id": sender_uuid if sender_uuid else None,
                "receiver_ids": receiver_uuids,
                "group_id": group_id,
                "message": message,
                "message_type": message_type or "text",
                "attachments": attachments_data,
                "created_at": (
                    new_message.created_at.isoformat()
                    if new_message.created_at
                    else None
                ),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"STEP 3: Error saving group message: {str(e)}")
            raise
        finally:
            db.close()

    async def get_user_by_id(self, user_id) -> Optional[Dict]:
        """
        Get user details by ID or UUID.

        Args:
            user_id: User ID (int) or UUID (str)

        Returns:
            Dict with user details including role_uuid
        """
        logger.info(f"STEP 1: Getting user by ID/UUID: {user_id}")

        db = SessionLocal()
        try:
            # Try to get user by ID (int) first
            if isinstance(user_id, int):
                user = self.user_method.find_by_id(db, user_id)
            # If not int, try UUID (str)
            elif isinstance(user_id, str):
                user = self.user_method.find_by_uuid(db, user_id)
            else:
                logger.error(f"STEP 2: Invalid user_id type: {type(user_id)}")
                return None

            if user:
                logger.info(f"STEP 2: Found user {user.id}")
                return {
                    "id": user.id,
                    "uuid": user.uuid,
                    "role_uuid": user.role_uuid,
                    "email": user.email if hasattr(user, "email") else None,
                }
            logger.warning(f"STEP 2: User not found")
            return None
        except Exception as e:
            logger.error(f"STEP 2: Error getting user: {str(e)}")
            return None
        finally:
            db.close()

    async def get_group_by_id(self, group_id) -> Optional[Dict]:
        """
        Get group details by ID or UUID.

        Args:
            group_id: Group ID (integer) or UUID (string)

        Returns:
            Dict with group details including members list, or None if not found
        """
        logger.info(f"STEP 1: Getting group by ID/UUID: {group_id}")

        db = SessionLocal()
        try:
            # Try to get group by UUID first (if string), then by ID (if integer)
            if isinstance(group_id, str):
                group = (
                    db.query(message_groups)
                    .filter(message_groups.uuid == group_id)
                    .first()
                )
            elif isinstance(group_id, int):
                group = (
                    db.query(message_groups)
                    .filter(message_groups.id == group_id)
                    .first()
                )
            else:
                logger.error(f"STEP 2: Invalid group_id type: {type(group_id)}")
                return None

            if group:
                logger.info(f"STEP 2: Found group {group.id}")
                return {
                    "id": group.id,
                    "uuid": group.uuid,
                    "group_name": group.group_name,
                    "created_by": group.created_by,
                    "members": group.members if group.members else [],
                    "admins": group.admins if group.admins else [],
                }
            logger.warning(f"STEP 2: Group not found")
            return None
        except Exception as e:
            logger.error(f"STEP 2: Error getting group: {str(e)}")
            return None
        finally:
            db.close()

    async def save_read_receipt(
        self, message_id: int, reader_id: int, room_id: str
    ) -> Dict:
        """
        Save read receipt to database.

        Args:
            message_id: Message ID (integer)
            reader_id: Reader user ID (integer)
            room_id: Room UUID

        Returns:
            Dict with receipt data including uuid
        """
        logger.info(
            f"STEP 1: Saving read receipt for message {message_id} by reader {reader_id}"
        )

        db = SessionLocal()
        try:
            # Check if receipt already exists
            existing_receipt = self.read_receipt_method.find_by_message_and_reader(
                db, message_id, reader_id
            )

            if existing_receipt:
                logger.info(
                    f"STEP 2: Read receipt already exists for message {message_id} by reader {reader_id}"
                )
                return {
                    "uuid": existing_receipt.uuid,
                    "message_id": message_id,
                    "reader_id": reader_id,
                    "room_id": room_id,
                    "read_at": (
                        existing_receipt.read_at.isoformat()
                        if existing_receipt.read_at
                        else None
                    ),
                }

            # Create new receipt
            logger.info("STEP 2: Creating new read receipt")
            new_receipt = self.read_receipt_method.create(
                db, message_id, reader_id, room_id
            )

            logger.info(
                f"STEP 3: Saved read receipt {new_receipt.uuid} for message {message_id}"
            )

            return {
                "uuid": new_receipt.uuid,
                "message_id": message_id,
                "reader_id": reader_id,
                "room_id": room_id,
                "read_at": (
                    new_receipt.read_at.isoformat() if new_receipt.read_at else None
                ),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"STEP 3: Error saving read receipt: {str(e)}")
            raise
        finally:
            db.close()

    async def get_unread_count(self, room_id: str, user_id: int) -> int:
        """
        Get count of unread messages in a room for a user.

        Args:
            room_id: Room UUID
            user_id: User ID

        Returns:
            Count of unread messages
        """
        logger.info(f"STEP 1: Getting unread count for room {room_id} and user {user_id}")

        db = SessionLocal()
        try:
            # Get all messages in room
            room_messages = (
                db.query(message_chats)
                .filter(message_chats.room_id == room_id)
                .all()
            )

            # Get all read receipts for this user in this room
            read_receipts = (
                db.query(message_read_receipts)
                .filter(
                    message_read_receipts.room_id == room_id,
                    message_read_receipts.reader_id == user_id,
                )
                .all()
            )

            read_message_ids = {receipt.message_id for receipt in read_receipts}

            # Count messages not read by this user
            unread_count = sum(
                1
                for msg in room_messages
                if msg.id not in read_message_ids and msg.sender_id != user_id
            )

            logger.info(
                f"STEP 2: Found {unread_count} unread messages for user {user_id} in room {room_id}"
            )

            return unread_count

        except Exception as e:
            logger.error(f"STEP 2: Error getting unread count: {str(e)}")
            return 0
        finally:
            db.close()

