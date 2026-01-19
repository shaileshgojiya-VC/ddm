"""
Connection manager for WebSocket connections, rooms, and presence.
"""

import logging
from typing import Dict, Set, Optional
from datetime import datetime
from utils.constants import ROOM_PREFIX, GROUP_ROOM_PREFIX, USER_ROOM_PREFIX

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections, room memberships, and presence state.
    """

    def __init__(self):
        # {session_id: {user_id, rooms, connected_at, ...}}
        self.connections: Dict[str, Dict] = {}

        # {room_id: {session_id1, session_id2, ...}}
        self.rooms: Dict[str, Set[str]] = {}

        # {user_id: {room_id: last_seen, ...}}
        self.presence: Dict[int, Dict[str, datetime]] = {}

        # {user_id: {session_id1, session_id2, ...}} - Multiple connections per user
        self.user_connections: Dict[int, Set[str]] = {}

    def connect(
        self, session_id: str, user_id: int, room_id: Optional[str] = None
    ) -> None:
        """
        Register a new WebSocket connection.

        Args:
            session_id: Socket.IO session ID
            user_id: User ID (integer)
            room_id: Optional room ID to join immediately
        """
        logger.info(f"STEP 1: Connecting session {session_id} for user {user_id}")

        # Store connection info
        self.connections[session_id] = {
            "user_id": user_id,
            "rooms": set(),
            "connected_at": datetime.utcnow(),
        }

        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(session_id)

        # Initialize presence
        if user_id not in self.presence:
            self.presence[user_id] = {}

        # Join room if provided
        if room_id:
            self.join_room(session_id, room_id)

        logger.info(f"STEP 2: Session {session_id} connected for user {user_id}")

    def disconnect(self, session_id: str) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            session_id: Socket.IO session ID
        """
        logger.info(f"STEP 1: Disconnecting session {session_id}")

        if session_id not in self.connections:
            logger.warning(f"Session {session_id} not found in connections")
            return

        connection = self.connections[session_id]
        user_id = connection.get("user_id")

        # Leave all rooms
        rooms_to_leave = list(connection.get("rooms", set()))
        for room_id in rooms_to_leave:
            self.leave_room(session_id, room_id)

        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(session_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove connection
        del self.connections[session_id]

        logger.info(f"STEP 2: Session {session_id} disconnected")

    def join_room(self, session_id: str, room_id: str) -> bool:
        """
        Add a connection to a room.

        Args:
            session_id: Socket.IO session ID
            room_id: Room UUID

        Returns:
            bool: True if joined successfully, False otherwise
        """
        logger.info(f"STEP 1: Joining session {session_id} to room {room_id}")

        if session_id not in self.connections:
            logger.error(f"Session {session_id} not found")
            return False

        # Initialize room if it doesn't exist
        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        # Add session to room
        self.rooms[room_id].add(session_id)

        # Add room to connection's rooms
        self.connections[session_id]["rooms"].add(room_id)

        # Update presence
        user_id = self.connections[session_id].get("user_id")
        if user_id:
            if user_id not in self.presence:
                self.presence[user_id] = {}
            self.presence[user_id][room_id] = datetime.utcnow()

        logger.info(f"STEP 2: Session {session_id} joined room {room_id}")

        return True

    def leave_room(self, session_id: str, room_id: str) -> bool:
        """
        Remove a connection from a room.

        Args:
            session_id: Socket.IO session ID
            room_id: Room UUID

        Returns:
            bool: True if left successfully, False otherwise
        """
        logger.info(f"STEP 1: Leaving session {session_id} from room {room_id}")

        if session_id not in self.connections:
            logger.error(f"Session {session_id} not found")
            return False

        # Remove session from room
        if room_id in self.rooms:
            self.rooms[room_id].discard(session_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

        # Remove room from connection's rooms
        self.connections[session_id]["rooms"].discard(room_id)

        logger.info(f"STEP 2: Session {session_id} left room {room_id}")

        return True

    def get_room_sessions(self, room_id: str) -> Set[str]:
        """
        Get all session IDs in a room.

        Args:
            room_id: Room UUID

        Returns:
            Set of session IDs
        """
        return self.rooms.get(room_id, set())

    def get_user_sessions(self, user_id: int) -> Set[str]:
        """
        Get all session IDs for a user.

        Args:
            user_id: User ID

        Returns:
            Set of session IDs
        """
        return self.user_connections.get(user_id, set())

    def get_connection_info(self, session_id: str) -> Optional[Dict]:
        """
        Get connection information.

        Args:
            session_id: Socket.IO session ID

        Returns:
            Connection info dict or None
        """
        return self.connections.get(session_id)

    def is_user_online(self, user_id: int, room_id: Optional[str] = None) -> bool:
        """
        Check if user is online (optionally in a specific room).

        Args:
            user_id: User ID
            room_id: Optional room ID

        Returns:
            bool: True if user is online
        """
        if user_id not in self.user_connections:
            return False

        if room_id:
            return room_id in self.presence.get(user_id, {})

        return len(self.user_connections[user_id]) > 0

    def update_presence(self, user_id: int, room_id: str) -> None:
        """
        Update user presence in a room.

        Args:
            user_id: User ID
            room_id: Room UUID
        """
        if user_id not in self.presence:
            self.presence[user_id] = {}
        self.presence[user_id][room_id] = datetime.utcnow()

    def get_room_members(self, room_id: str) -> Set[int]:
        """
        Get all user IDs in a room.

        Args:
            room_id: Room UUID

        Returns:
            Set of user IDs
        """
        user_ids = set()
        for session_id in self.get_room_sessions(room_id):
            connection = self.get_connection_info(session_id)
            if connection:
                user_ids.add(connection.get("user_id"))
        return user_ids

    def format_room_name(self, room_id: str, is_group: bool = False) -> str:
        """
        Format room name for Socket.IO.

        Args:
            room_id: Room UUID
            is_group: Whether this is a group room

        Returns:
            Formatted room name
        """
        prefix = GROUP_ROOM_PREFIX if is_group else ROOM_PREFIX
        return f"{prefix}{room_id}"


# Global connection manager instance
connection_manager = ConnectionManager()

