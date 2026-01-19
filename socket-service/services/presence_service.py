"""
Presence service for tracking online/offline status.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from connection_manager import connection_manager
from utils.constants import STATUS_ONLINE, STATUS_OFFLINE, CONNECTION_TIMEOUT

logger = logging.getLogger(__name__)


class PresenceService:
    """Service for managing user presence status."""

    def __init__(self):
        self.presence_cache: Dict[int, Dict[str, datetime]] = {}

    def update_presence(self, user_id: int, room_id: str) -> None:
        """
        Update user presence in a room.

        Args:
            user_id: User ID
            room_id: Room UUID
        """
        logger.info(f"STEP 1: Updating presence for user {user_id} in room {room_id}")

        if user_id not in self.presence_cache:
            self.presence_cache[user_id] = {}

        self.presence_cache[user_id][room_id] = datetime.utcnow()
        connection_manager.update_presence(user_id, room_id)

        logger.info(f"STEP 2: Presence updated for user {user_id} in room {room_id}")

    def get_presence_status(
        self, user_id: int, room_id: Optional[str] = None
    ) -> str:
        """
        Get user presence status.

        Args:
            user_id: User ID
            room_id: Optional room ID

        Returns:
            Presence status: "online" or "offline"
        """
        logger.info(f"STEP 1: Getting presence status for user {user_id}")

        is_online = connection_manager.is_user_online(user_id, room_id)

        status = STATUS_ONLINE if is_online else STATUS_OFFLINE

        logger.info(f"STEP 2: User {user_id} is {status}")

        return status

    def get_online_users_in_room(self, room_id: str) -> Set[int]:
        """
        Get all online user IDs in a room.

        Args:
            room_id: Room UUID

        Returns:
            Set of online user IDs
        """
        logger.info(f"STEP 1: Getting online users in room {room_id}")

        room_members = connection_manager.get_room_members(room_id)
        online_users = {
            user_id
            for user_id in room_members
            if connection_manager.is_user_online(user_id, room_id)
        }

        logger.info(f"STEP 2: Found {len(online_users)} online users in room {room_id}")

        return online_users

    def cleanup_stale_presence(self) -> None:
        """
        Clean up stale presence entries (users who haven't been active recently).
        """
        logger.info("STEP 1: Cleaning up stale presence entries")

        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=CONNECTION_TIMEOUT)

        stale_users = []

        for user_id, rooms in self.presence_cache.items():
            stale_rooms = [
                room_id
                for room_id, last_seen in rooms.items()
                if last_seen < timeout_threshold
            ]

            for room_id in stale_rooms:
                del rooms[room_id]

            if not rooms:
                stale_users.append(user_id)

        for user_id in stale_users:
            del self.presence_cache[user_id]

        logger.info(f"STEP 2: Cleaned up {len(stale_users)} stale user presence entries")


# Global presence service instance
presence_service = PresenceService()

