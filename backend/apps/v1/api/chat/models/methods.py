"""
Model methods for chat messages and sessions.
"""

from sqlalchemy.orm import Session
from apps.v1.api.chat.models.model import (
    message_chats,
    message_sessions,
    message_read_receipts,
)
from apps.v1.api.auth.models.model import Users


class MessageChatMethod:
    """This class defines methods for message_chats model operations."""

    def __init__(self, model):
        self.model = model

    def find_existing_message_between_users(
        self, db: Session, sender_id: int, receiver_id: int
    ):
        """
        Find the most recent message between two users (bidirectional).
        
        Args:
            db: Database session
            sender_id: Sender user ID
            receiver_id: Receiver user ID
            
        Returns:
            Most recent message_chats object or None if no messages exist
        """
        return (
            db.query(self.model)
            .filter(
                (
                    (self.model.sender_id == sender_id)
                    & (self.model.receiver_id == receiver_id)
                )
                | (
                    (self.model.sender_id == receiver_id)
                    & (self.model.receiver_id == sender_id)
                )
            )
            .order_by(self.model.created_at.desc())
            .first()
        )

    def update_messages_by_room_id(
        self, db: Session, old_room_id, new_room_id: str
    ):
        """
        Update room_id for all messages in a room.
        
        Args:
            db: Database session
            old_room_id: Old room_id (int or str)
            new_room_id: New room_id (UUID string)
            
        Returns:
            Number of rows updated
        """
        result = (
            db.query(self.model)
            .filter(self.model.room_id == old_room_id)
            .update({"room_id": new_room_id})
        )
        return result


class MessageSessionMethod:
    """This class defines methods for message_sessions model operations."""

    def __init__(self, model):
        self.model = model

    def find_by_id(self, db: Session, session_id: int):
        """
        Find session by ID.
        
        Args:
            db: Database session
            session_id: Session ID (integer)
            
        Returns:
            message_sessions object or None
        """
        return (
            db.query(self.model)
            .filter(self.model.id == session_id)
            .first()
        )

    def find_by_room_id(self, db: Session, room_id: str):
        """
        Find session by room_id (UUID).
        
        Args:
            db: Database session
            room_id: Room ID (UUID string)
            
        Returns:
            message_sessions object or None
        """
        return (
            db.query(self.model)
            .filter(self.model.room_id == room_id)
            .first()
        )

    def find_by_uuid(self, db: Session, session_uuid: str):
        """
        Find session by UUID.
        
        Args:
            db: Database session
            session_uuid: Session UUID string
            
        Returns:
            message_sessions object or None
        """
        return (
            db.query(self.model)
            .filter(self.model.uuid == session_uuid)
            .first()
        )

    def create(self, db: Session, room_id: str = None):
        """
        Create a new message session.
        
        Args:
            db: Database session
            room_id: Optional room_id (UUID string)
            
        Returns:
            Created message_sessions object
        """
        # Ensure room_id is stored as string (UUID format)
        room_id_str = str(room_id).strip() if room_id else None
        new_session = self.model(room_id=room_id_str) if room_id_str else self.model()
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    def update_room_id(self, db: Session, session_obj, room_id: str):
        """
        Update room_id for a session.
        
        Args:
            db: Database session
            session_obj: message_sessions object to update
            room_id: New room_id (UUID string)
        """
        # Ensure room_id is stored as string (UUID format)
        room_id_str = str(room_id).strip() if room_id else None
        session_obj.room_id = room_id_str
        db.commit()
        db.refresh(session_obj)


class UserMethod:
    """This class defines methods for Users model operations."""

    def __init__(self, model):
        self.model = model

    def find_by_id(self, db: Session, user_id: int):
        """
        Find user by ID.
        
        Args:
            db: Database session
            user_id: User ID (integer)
            
        Returns:
            Users object or None
        """
        return (
            db.query(self.model)
            .filter(self.model.id == user_id)
            .first()
        )

    def find_by_uuid(self, db: Session, user_uuid: str):
        """
        Find user by UUID.
        
        Args:
            db: Database session
            user_uuid: User UUID string
            
        Returns:
            Users object or None
        """
        return (
            db.query(self.model)
            .filter(self.model.uuid == user_uuid)
            .first()
        )


class ReadReceiptMethod:
    """This class defines methods for message_read_receipts model operations."""

    def __init__(self, model):
        self.model = model

    def create(
        self,
        db: Session,
        message_id: int,
        reader_id: int,
        room_id: str,
    ):
        """
        Create a new read receipt.

        Args:
            db: Database session
            message_id: Message ID (FK to message_chats.id)
            reader_id: Reader user ID (FK to users.id)
            room_id: Room UUID

        Returns:
            Created message_read_receipts object
        """
        new_receipt = self.model(
            message_id=message_id,
            reader_id=reader_id,
            room_id=room_id,
        )
        db.add(new_receipt)
        db.commit()
        db.refresh(new_receipt)
        return new_receipt

    def find_by_message_and_reader(
        self, db: Session, message_id: int, reader_id: int
    ):
        """
        Find read receipt by message ID and reader ID.

        Args:
            db: Database session
            message_id: Message ID
            reader_id: Reader user ID

        Returns:
            message_read_receipts object or None
        """
        return (
            db.query(self.model)
            .filter(
                self.model.message_id == message_id,
                self.model.reader_id == reader_id,
            )
            .first()
        )

    def find_by_message_id(self, db: Session, message_id: int):
        """
        Find all read receipts for a message.

        Args:
            db: Database session
            message_id: Message ID

        Returns:
            List of message_read_receipts objects
        """
        return (
            db.query(self.model)
            .filter(self.model.message_id == message_id)
            .all()
        )

    def find_by_room_id(self, db: Session, room_id: str):
        """
        Find all read receipts for a room.

        Args:
            db: Database session
            room_id: Room UUID

        Returns:
            List of message_read_receipts objects
        """
        return (
            db.query(self.model)
            .filter(self.model.room_id == room_id)
            .all()
        )
