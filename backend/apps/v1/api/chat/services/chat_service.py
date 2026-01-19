"""
Chat Service for Socket.IO
Handles room management, message storage, and user identification
"""

import logging
from typing import Dict, Optional, List
from core.db import SessionLocal
from apps.v1.api.chat.models.model import message_sessions, message_chats, message_groups
from apps.v1.api.chat.models.methods import (
    MessageChatMethod,
    MessageSessionMethod,
    UserMethod,
)
from apps.v1.api.auth.models.model import Users

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat rooms and messages"""

    def __init__(self):
        self.sessions = {}  # {session_id: {room_id, user_id, role_uuid, ...}}
        self.message_chat_method = MessageChatMethod(message_chats)
        self.message_session_method = MessageSessionMethod(message_sessions)
        self.user_method = UserMethod(Users)

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
        db = SessionLocal()
        try:
            # Check if room already exists between these two users
            # Look for existing messages between sender and receiver
            existing_message = self.message_chat_method.find_existing_message_between_users(
                db, sender_id, receiver_id
            )

            if existing_message:
                # Room already exists, get existing room_id
                existing_room_id = existing_message.room_id
                
                # If room_id is still an integer (old data), find the session UUID
                if isinstance(existing_room_id, int) or (isinstance(existing_room_id, str) and existing_room_id.isdigit()):
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
                    f"📦 Found existing room {room_id_uuid} between user {sender_id} and {receiver_id}"
                )

                # Store session info
                self.sessions[session_id] = {
                    "room_id": room_id_uuid,
                    "session_uuid": session_uuid,
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                }

                return {
                    "room_id": room_id_uuid,
                    "session_uuid": session_uuid,
                    "status": "existing",
                }

            # Create new room between these two users
            new_session = self.message_session_method.create(db)

            # Use session UUID as room_id (store UUID instead of integer)
            session_uuid = new_session.uuid
            self.message_session_method.update_room_id(db, new_session, session_uuid)

            logger.info(
                f"🆕 Created new room {session_uuid} between user {sender_id} and {receiver_id}"
            )

            # Store session info
            self.sessions[session_id] = {
                "room_id": session_uuid,
                "session_uuid": session_uuid,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
            }

            return {
                "room_id": session_uuid,
                "session_uuid": session_uuid,
                "status": "new",
            }

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating/getting room: {str(e)}")
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
        db = SessionLocal()
        try:
            # Check if room already exists for this group
            # Look for existing message_sessions with this group_id
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
                # Also check if it's a numeric string (old format)
                is_valid_uuid = (
                    room_id_str 
                    and len(room_id_str) == 36 
                    and room_id_str.count("-") == 4
                )
                
                is_numeric = room_id_str.isdigit() if room_id_str else False
                
                if not is_valid_uuid or is_numeric:
                    # Old format - room_id is integer or invalid, convert to UUID
                    # Use session UUID as the new room_id
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
                        f"🔄 Converted room_id from {room_id_value} to UUID {room_id_uuid} for group {group_id}"
                    )
                else:
                    # Already using UUID format
                    room_id_uuid = room_id_str

                logger.info(
                    f"📦 Found existing room {room_id_uuid} for group {group_id}"
                )

                # Store session info
                self.sessions[session_id] = {
                    "room_id": room_id_uuid,
                    "session_uuid": existing_session.uuid,
                    "group_id": group_id,
                }

                return {
                    "room_id": room_id_uuid,
                    "session_uuid": existing_session.uuid,
                    "status": "existing",
                }

            # Create new room for this group
            new_session = self.message_session_method.create(db)
            session_uuid = new_session.uuid
            
            # Use session UUID as room_id
            self.message_session_method.update_room_id(db, new_session, session_uuid)
            
            # Set group_id in session
            new_session.group_id = group_id
            db.commit()
            db.refresh(new_session)

            logger.info(
                f"🆕 Created new room {session_uuid} for group {group_id}"
            )

            # Store session info
            self.sessions[session_id] = {
                "room_id": session_uuid,
                "session_uuid": session_uuid,
                "group_id": group_id,
            }

            return {
                "room_id": session_uuid,
                "session_uuid": session_uuid,
                "status": "new",
            }

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating/getting room for group: {str(e)}")
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
            Dict with message data including uuid (with UUIDs for sender_id, receiver_id, and room_id)
        """
        db = SessionLocal()
        try:
            session_info = self.sessions.get(session_id, {})
            session_uuid = session_info.get("session_uuid")

            # Get sender UUID
            sender_user = self.user_method.find_by_id(db, sender_id)
            sender_uuid = sender_user.uuid if sender_user else None

            # Get receiver UUID
            receiver_uuid = None
            if receiver_id:
                receiver_user = self.user_method.find_by_id(db, receiver_id)
                receiver_uuid = receiver_user.uuid if receiver_user else None

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

            logger.info(f"💾 Saved message {new_message.uuid} to room {room_id}")

            return {
                "uuid": new_message.uuid,
                "room_id": room_id,  # room_id is already UUID string
                "sender_id": sender_uuid if sender_uuid else None,
                "receiver_id": receiver_uuid if receiver_uuid else None,
                "message": message,
                "message_type": message_type or "text",
                "attachments": attachments if attachments else [],
                "created_at": new_message.created_at.isoformat() if new_message.created_at else None,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error saving message: {str(e)}")
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
        db = SessionLocal()
        try:
            # Try to get user by ID (int) first
            if isinstance(user_id, int):
                user = self.user_method.find_by_id(db, user_id)
            # If not int, try UUID (str)
            elif isinstance(user_id, str):
                user = self.user_method.find_by_uuid(db, user_id)
            else:
                logger.error(f"❌ Invalid user_id type: {type(user_id)}")
                return None
                
            if user:
                return {
                    "id": user.id,
                    "uuid": user.uuid,
                    "role_uuid": user.role_uuid,
                    "email": user.email if hasattr(user, "email") else None,
                }
            return None
        except Exception as e:
            logger.error(f"❌ Error getting user: {str(e)}")
            return None
        finally:
            db.close()

    async def get_room_id_from_uuid(self, room_uuid: str) -> Optional[str]:
        """
        Get room_id (UUID) from session UUID.

        Args:
            room_uuid: Session UUID string

        Returns:
            Room UUID string if found, None otherwise
        """
        db = SessionLocal()
        try:
            session = self.message_session_method.find_by_uuid(db, room_uuid)
            if session:
                return session.room_id  # room_id is now UUID string
            return None
        except Exception as e:
            logger.error(f"❌ Error getting room_id from UUID: {str(e)}")
            return None
        finally:
            db.close()

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information."""
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str):
        """Remove session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ Removed session {session_id}")

    async def get_group_by_id(self, group_id) -> Optional[Dict]:
        """
        Get group details by ID or UUID.

        Args:
            group_id: Group ID (integer) or UUID (string)

        Returns:
            Dict with group details including members list, or None if not found
        """
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
                logger.error(f"❌ Invalid group_id type: {type(group_id)}")
                return None
            
            if group:
                return {
                    "id": group.id,
                    "uuid": group.uuid,
                    "group_name": group.group_name,
                    "created_by": group.created_by,
                    "members": group.members if group.members else [],
                    "admins": group.admins if group.admins else [],
                }
            return None
        except Exception as e:
            logger.error(f"❌ Error getting group: {str(e)}")
            return None
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
        db = SessionLocal()
        try:
            session_info = self.sessions.get(session_id, {})
            session_uuid = session_info.get("session_uuid")

            # Validate room_id is a valid UUID string (it should come from create_or_get_room_for_group)
            # Don't override it - use the room_id that was passed (from the group's room session)
            room_id_str = str(room_id).strip()  # Ensure it's a string and trim whitespace
            
            # Final validation: Ensure room_id is a valid UUID string
            if not (len(room_id_str) == 36 and room_id_str.count("-") == 4):
                logger.error(f"❌ Invalid room_id format before saving: {room_id_str} (type: {type(room_id_str)}, length: {len(room_id_str)})")
                raise ValueError(f"room_id must be a valid UUID string, got: {room_id_str}")

            # Note: message_sessions is already created/updated in create_or_get_room_for_group
            # So we don't need to create it here again

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
            # Since receiver_id column is Integer, we store the list in attachments JSON
            attachments_data = attachments if attachments else []
            # Store receiver_ids in attachments JSON with special metadata key
            # Structure: { "receiver_ids": [1, 2, 3], "files": [...] }
            attachments_metadata = {
                "receiver_ids": receiver_ids,  # Store group member IDs list here (integers for database)
                "files": attachments_data  # Store actual file attachments
            }

            # Create message with receiver_id as None for group messages
            # Store receiver_ids list in attachments JSON since receiver_id is Integer type
            # room_id column is now VARCHAR(36), so it will store UUID strings correctly
            logger.info(f"💾 Saving message with room_id: {room_id_str} (type: {type(room_id_str)}, length: {len(room_id_str)})")
            
            new_message = message_chats(
                room_id=room_id_str,  # Now stored as VARCHAR(36) - will accept UUID string
                sender_id=sender_id,
                receiver_id=None,  # Set to None for group messages (Integer column can't store list)
                message=message,
                message_type=message_type or "text",
                attachments=attachments_metadata,  # Store receiver_ids list in attachments JSON
                group_id=group_id,
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            # Verify room_id was saved correctly
            saved_room_id = str(new_message.room_id) if new_message.room_id else None
            if saved_room_id != room_id_str:
                logger.error(f"❌ Room ID mismatch! Expected: {room_id_str}, Got: {saved_room_id} (type: {type(new_message.room_id)})")
            else:
                logger.info(f"✅ Verified room_id saved correctly: {new_message.room_id}")

            logger.info(f"💾 Saved group message {new_message.uuid} to group {group_id}")

            return {
                "uuid": new_message.uuid,
                "room_id": room_id_str,  # Return the validated UUID string
                "sender_id": sender_uuid if sender_uuid else None,
                "receiver_ids": receiver_uuids,  # Return UUIDs in response
                "group_id": group_id,
                "message": message,
                "message_type": message_type or "text",
                "attachments": attachments_data,  # Return only file attachments
                "created_at": new_message.created_at.isoformat() if new_message.created_at else None,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error saving group message: {str(e)}")
            raise
        finally:
            db.close()

