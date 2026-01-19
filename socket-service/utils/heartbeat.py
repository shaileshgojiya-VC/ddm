"""
Heartbeat utilities for WebSocket connection health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict

from utils.constants import HEARTBEAT_INTERVAL, CONNECTION_TIMEOUT

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """Manages heartbeat/ping-pong for WebSocket connections."""

    def __init__(self):
        self.last_heartbeat: Dict[str, datetime] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    def register_connection(self, session_id: str) -> None:
        """
        Register a new connection for heartbeat monitoring.

        Args:
            session_id: Socket.IO session ID
        """
        logger.info(f"STEP 1: Registering heartbeat for session {session_id}")
        self.last_heartbeat[session_id] = datetime.utcnow()
        logger.info(f"STEP 2: Heartbeat registered for session {session_id}")

    def update_heartbeat(self, session_id: str) -> None:
        """
        Update last heartbeat timestamp for a connection.

        Args:
            session_id: Socket.IO session ID
        """
        self.last_heartbeat[session_id] = datetime.utcnow()

    def is_connection_alive(self, session_id: str) -> bool:
        """
        Check if connection is still alive based on last heartbeat.

        Args:
            session_id: Socket.IO session ID

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if session_id not in self.last_heartbeat:
            return False

        last_heartbeat = self.last_heartbeat[session_id]
        timeout_threshold = datetime.utcnow() - timedelta(seconds=CONNECTION_TIMEOUT)

        return last_heartbeat > timeout_threshold

    def unregister_connection(self, session_id: str) -> None:
        """
        Unregister a connection from heartbeat monitoring.

        Args:
            session_id: Socket.IO session ID
        """
        logger.info(f"STEP 1: Unregistering heartbeat for session {session_id}")

        if session_id in self.last_heartbeat:
            del self.last_heartbeat[session_id]

        if session_id in self.heartbeat_tasks:
            task = self.heartbeat_tasks[session_id]
            if not task.done():
                task.cancel()
            del self.heartbeat_tasks[session_id]

        logger.info(f"STEP 2: Heartbeat unregistered for session {session_id}")

    async def start_heartbeat_task(
        self, session_id: str, sio, emit_heartbeat_func
    ) -> None:
        """
        Start heartbeat task for a connection.

        Args:
            session_id: Socket.IO session ID
            sio: Socket.IO server instance
            emit_heartbeat_func: Function to emit heartbeat event
        """
        logger.info(f"STEP 1: Starting heartbeat task for session {session_id}")

        async def heartbeat_loop():
            try:
                while True:
                    await asyncio.sleep(HEARTBEAT_INTERVAL)

                    if not self.is_connection_alive(session_id):
                        logger.warning(
                            f"Heartbeat timeout for session {session_id}, disconnecting"
                        )
                        await sio.disconnect(session_id)
                        break

                    # Emit heartbeat ping
                    await emit_heartbeat_func(session_id)

            except asyncio.CancelledError:
                logger.info(f"Heartbeat task cancelled for session {session_id}")
            except Exception as exc:
                logger.error(
                    f"Error in heartbeat loop for session {session_id}: {exc}",
                    exc_info=True,
                )

        task = asyncio.create_task(heartbeat_loop())
        self.heartbeat_tasks[session_id] = task

        logger.info(f"STEP 2: Heartbeat task started for session {session_id}")


# Global heartbeat manager instance
heartbeat_manager = HeartbeatManager()

